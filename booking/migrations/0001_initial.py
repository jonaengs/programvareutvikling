# Generated by Django 2.1.6 on 2019-03-25 14:03

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingInterval',
            fields=[
                ('day', models.CharField(choices=[('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday')], max_length=20)),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('max_available_assistants', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('nk', models.CharField(max_length=32, primary_key=True, serialize=False, unique=True)),
                ('assistants', models.ManyToManyField(blank=True, limit_choices_to={'groups__name': 'assistants'}, related_name='setup_booking_intervals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-course', 'day', 'start'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, unique=True)),
                ('course_code', models.CharField(max_length=10, unique=True)),
                ('slug', models.SlugField()),
                ('assistants', models.ManyToManyField(blank=True, limit_choices_to={'groups__name': 'assistants'}, related_name='assisting_courses', to=settings.AUTH_USER_MODEL)),
                ('course_coordinator', models.OneToOneField(blank=True, limit_choices_to={'groups__name': 'course_coordinators'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supervising_course', to=settings.AUTH_USER_MODEL)),
                ('students', models.ManyToManyField(blank=True, limit_choices_to={'groups__name': 'students'}, related_name='enrolled_courses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReservationConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assistant', models.ForeignKey(limit_choices_to={'groups__name': 'assistants'}, on_delete=django.db.models.deletion.CASCADE, related_name='student_connections', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReservationInterval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField(default=0)),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('booking_interval', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_intervals', to='booking.BookingInterval')),
            ],
            options={
                'ordering': ['booking_interval__day'],
            },
        ),
        migrations.AddField(
            model_name='reservationconnection',
            name='reservation_interval',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connections', to='booking.ReservationInterval'),
        ),
        migrations.AddField(
            model_name='reservationconnection',
            name='student',
            field=models.ForeignKey(limit_choices_to={'groups__name': 'students'}, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='bookinginterval',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_intervals', to='booking.Course'),
        ),
    ]
