# Generated by Django 3.1.7 on 2021-03-17 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0004_moviefile_force_convert'),
    ]

    operations = [
        migrations.AddField(
            model_name='moviefile',
            name='error',
            field=models.BooleanField(default=False),
        ),
    ]
