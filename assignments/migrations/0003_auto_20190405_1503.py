# Generated by Django 2.0.10 on 2019-04-05 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0002_auto_20190327_1648'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exercise',
            options={'ordering': ['-upload_datetime', 'approved']},
        ),
        migrations.AlterField(
            model_name='exercise',
            name='approved',
            field=models.NullBooleanField(),
        ),
    ]
