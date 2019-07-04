import calendar
import hashlib
from datetime import time

from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User, Group
from django.template.defaultfilters import slugify


class Course(models.Model):
    OPEN_BOOKING_TIME = 8  # hour
    CLOSE_BOOKING_TIME = 18  # hour
    BOOKING_INTERVAL_LENGTH = 2  # hours
    RESERVATION_LENGTH = 15  # minutes
    NUM_DAYS_IN_WORK_WEEK = 5
    NUM_RESERVATIONS_IN_BOOKING_INTERVAL = (BOOKING_INTERVAL_LENGTH * 60) // RESERVATION_LENGTH

    title = models.CharField(
        max_length=50,
        unique=True,
    )
    course_code = models.CharField(
        max_length=10,
        unique=True,
    )
    slug = models.SlugField()
    students = models.ManyToManyField(
        User,
        limit_choices_to={'groups__name': "students"},
        related_name="enrolled_courses",
        blank=True,
    )
    assistants = models.ManyToManyField(
        User,
        limit_choices_to={'groups__name': "assistants"},
        related_name="assisting_courses",
        blank=True,
    )
    course_coordinator = models.OneToOneField(
        User,
        limit_choices_to={'groups__name': "course_coordinators"},
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="supervising_course",
    )

    def __str__(self):
        return self.title

    def _generate_booking_intervals(self):
        """
        generates booking intervals associated with a course. 5 2-hour intervals for every weekday
        """
        for day in range(self.NUM_DAYS_IN_WORK_WEEK):
            for hour in range(self.OPEN_BOOKING_TIME,
                              self.CLOSE_BOOKING_TIME,
                              self.BOOKING_INTERVAL_LENGTH):
                start = time(hour=hour, minute=00)
                end = time(hour=hour + 2, minute=00)
                self.booking_intervals.create(day=day, start=start, end=end)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.course_code)
        super().save(**kwargs)
        if not self.booking_intervals.all():
            self._generate_booking_intervals()


class BookingInterval(models.Model):
    DAY_CHOICES = [(str(i), calendar.day_name[i]) for i in range(0, 5)]

    course = models.ForeignKey(
        Course,
        related_name='booking_intervals',
        on_delete=models.CASCADE,
    )
    day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
    )
    start = models.TimeField()
    end = models.TimeField()
    max_available_assistants = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0)
        ]
    )
    assistants = models.ManyToManyField(
        User,
        limit_choices_to={'groups__name': "assistants"},
        blank=True,
        related_name='setup_booking_intervals',
    )
    nk = models.CharField(
        max_length=32,
        blank=False,
        unique=True,
        primary_key=True,
    )

    class Meta:
        ordering = [
            '-course', 'day', 'start'
        ]

    def _generate_reservation_intervals(self):
        for i in range(Course.NUM_RESERVATIONS_IN_BOOKING_INTERVAL):
            j = i + 1
            self.reservation_intervals.add(
                ReservationInterval.objects.create(
                    index=i,
                    start=time(hour=self.start.hour + (15 * i) // 60, minute=(15 * i) % 60),
                    end=time(hour=self.start.hour + (15 * j) // 60, minute=(15 * j) % 60),
                    booking_interval=self,
                )
            )

    def save(self, **kwargs):
        if not self.nk:
            self.nk = hashlib.md5(
                f'{self.start}-{self.get_day_display()}-{self.course.course_code}'
                    .encode('utf-8')).hexdigest()
        super().save(**kwargs)
        if not self.reservation_intervals.all():
            self._generate_reservation_intervals()

    def __str__(self):
        return f'{self.course.course_code} {self.get_day_display()} {self.start}-{self.end}'


class ReservationInterval(models.Model):
    booking_interval = models.ForeignKey(
        BookingInterval,
        related_name='reservation_intervals',
        on_delete=models.CASCADE,
    )
    index = models.IntegerField(default=0)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = [
            'booking_interval__day'
        ]


class ReservationConnection(models.Model):
    reservation_interval = models.ForeignKey(
        ReservationInterval,
        on_delete=models.CASCADE,
        related_name='connections',
    )
    student = models.ForeignKey(
        User,
        limit_choices_to={'groups__name': "students"},
        related_name='reservations',
        on_delete=models.CASCADE,
    )
    assistant = models.ForeignKey(
        User,
        limit_choices_to={'groups__name': "assistants"},
        related_name='student_connections',
        on_delete=models.CASCADE,
    )

    def _get_available_assistant(self):
        all_bi_assistants = self.reservation_interval.booking_interval.assistants.all()
        reserved_assistants = User.objects.filter(student_connections__in=self.reservation_interval.connections.all())
        available_assistants = all_bi_assistants.difference(reserved_assistants)  # all assistants minus reserved ones
        assert available_assistants.count() > 0, 'No assistants available for this reservation interval'
        return available_assistants[0]

    def save(self, **kwargs):
        if self.pk is None:  # only runs on object creation
            self.assistant = self._get_available_assistant()
        super().save(**kwargs)

    class Meta:
        ordering = [
            'reservation_interval',  # sort by day
            'reservation_interval__start',  # then sort by start time within the day
        ]