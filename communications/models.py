from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from booking.models import Course


def get_avatar_image_path(instance, filename):
    return f'avatars/user_{instance.user.username}_{instance.user.id}/{filename}'


class Announcement(models.Model):
    title = models.CharField(
        max_length=45
    )
    content = models.TextField(
        max_length=1500
    )
    author = models.ForeignKey(
        User,
        limit_choices_to={'groups__name': 'course_coordinators'},
        related_name='announcements',
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        Course,
        related_name='announcement',
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        ordering = (
            '-timestamp',
        )


class Comment(models.Model):
    content = models.TextField(
        max_length=500,
        verbose_name='Kommentar'
    )
    author = models.ForeignKey(
        User,
        limit_choices_to={'groups__name': 'course_coordinators'},
        related_name='comments',
        on_delete=models.CASCADE,
    )
    announcement = models.ForeignKey(
        Announcement,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.content

    def get_absolute_url(self):
        return reverse('announcement_detail',
                       kwargs={'pk': self.announcement.pk, 'slug': self.announcement.course.slug})


class Avatar(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        blank=True,
        upload_to=get_avatar_image_path,
    )
