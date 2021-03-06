# Generated by Django 3.1.7 on 2021-03-07 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MovieDirectory',
            fields=[
                ('path', models.CharField(max_length=1024, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'Movie directory',
                'verbose_name_plural': 'Movie directories',
            },
        ),
        migrations.CreateModel(
            name='MovieFile',
            fields=[
                ('path', models.CharField(max_length=1024, primary_key=True, serialize=False)),
                ('original_size', models.BigIntegerField(null=True)),
                ('probed', models.BooleanField(db_index=True, default=False)),
                ('probed_width', models.IntegerField(null=True)),
                ('probed_height', models.IntegerField(null=True)),
                ('probed_video_codec', models.TextField(null=True)),
                ('converted', models.BooleanField(null=True)),
                ('output_path', models.CharField(max_length=1024, null=True)),
                ('output_size', models.BigIntegerField(null=True)),
            ],
            options={
                'verbose_name': 'Movie file',
                'verbose_name_plural': 'Movie files',
            },
        ),
    ]
