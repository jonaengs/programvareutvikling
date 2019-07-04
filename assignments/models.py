import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from booking.models import Course


def get_exercise_filepath(instance, filename):
    return f'exercises/{instance.course.course_code}/user_{instance.student.id}/{filename}/'


class Exercise(models.Model):
    course = models.ForeignKey(
        Course,
        related_name='exercise_uploads',
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        User,
        related_name='exercises',
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to=get_exercise_filepath
    )
    feedback_text = models.TextField(
        max_length=1500,
        blank=True,
        null=True,
    )
    approved = models.NullBooleanField(
        blank=True,
    )
    feedback_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='reviews',
        on_delete=models.DO_NOTHING,
    )
    upload_datetime = models.DateTimeField(
        default=timezone.now
    )

    def delete(self, using=None, keep_parents=False):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(using, keep_parents)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return f'{self.student} - {self.filename} - {self.course.course_code}'

    class Meta:
        ordering = [
            '-upload_datetime',  # then sort by upload time within these groups
            'approved',  # exercises without reviews on top
        ]
