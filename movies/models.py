import os
import shutil
import traceback
from pathlib import Path

import ffmpeg
import humanize
from django.conf import settings
from django.db import models

STRIP_IN_FILENAMES = ['720p', '1080p', '[', ']', '576p']
SHOW_PROGRESS = False


def filesize(value):
    return humanize.naturalsize(value, binary=True)


def path_field(**kwargs):
    return models.CharField(max_length=1024, **kwargs)


def video_codec(streams):
    for stream in streams:
        if stream.get('codec_type') == 'video':
            return stream


def to_output_path(path):
    path = Path(path)
    output_path = str(settings.OUTPUT_PROFILE['output_path'].joinpath(*path.parts[1:]).with_suffix(''))
    for x in STRIP_IN_FILENAMES:
        output_path = output_path.replace(x, '')
    output_path = output_path.replace('.', ' ')
    output_path = output_path.replace('_', '-')
    output_path = output_path.strip()

    return Path(output_path).with_suffix(settings.OUTPUT_PROFILE['output_suffix'])


def all_to_convert(**kwargs):
    cond = (models.Q(probed_width__gt=settings.FILTER_CRITERIA['max_width']) |
            models.Q(probed_height__gt=settings.FILTER_CRITERIA['max_height']))
    cond = cond | ~models.Q(probed_video_codec__in=settings.FILTER_CRITERIA['accepted_codecs'])
    cond = cond | models.Q(force_convert=True) | models.Q(**settings.FILTER_CRITERIA['other_conditions'])
    query = MovieFile.objects.filter(
        cond,
        converted=False,
        probed=True,
        error=False,
    ).order_by('-force_convert', *settings.FILTER_CRITERIA['order'])
    return query


class MovieDirectory(models.Model):
    path = path_field(primary_key=True)

    class Meta:
        verbose_name = 'Movie directory'
        verbose_name_plural = 'Movie directories'


class MovieFile(models.Model):
    path = path_field(primary_key=True)
    original_size = models.BigIntegerField(null=True)
    probed = models.BooleanField(default=False, db_index=True)
    probed_width = models.IntegerField(null=True)
    probed_height = models.IntegerField(null=True)
    probed_video_codec = models.TextField(null=True)
    probed_bitrate = models.IntegerField(default=0, db_index=True)
    force_convert = models.BooleanField(default=False)
    converted = models.BooleanField(default=False)
    output_path = path_field(null=True)
    output_size = models.BigIntegerField(null=True)
    error = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Movie file'
        verbose_name_plural = 'Movie files'
        ordering = ('path',)

    def __str__(self):
        if ' ' in self.path:
            return f'"{self.path}"'
        return self.path

    @property
    def original_size_human(self):
        return filesize(self.original_size)

    @property
    def output_size_human(self):
        return filesize(self.output_size) if self.output_size else 0

    def probe(self):
        if not Path(self.path).exists():
            self.delete()
            return
        try:
            info = ffmpeg.probe(self.path)
            vc = video_codec(info['streams'])
            if vc:
                self.probed_video_codec = vc['codec_tag_string']
                self.probed_width = vc['coded_width']
                self.probed_height = vc['coded_height']
            try:
                self.probed_bitrate = info['format']['bit_rate']
            except KeyError:
                pass
            self.probed = True
            self.save()
        except Exception as exc:
            print(f'Could not probe file {self}: {exc}')
            traceback.print_exc()
        print('.', end='')

    def convert(self, replace=True):
        if not Path(self.path).exists():
            self.delete()
            return
        try:
            op = to_output_path(self.path)
            if op.exists():
                op.unlink()
            else:
                os.makedirs(op.parent, exist_ok=True)
            self.output_path = str(op)
            p = ffmpeg.input(self.path)
            if (self.probed_width > settings.FILTER_CRITERIA['max_width'] or
                self.probed_height > settings.FILTER_CRITERIA['max_height']):
                p = p.filter(settings.OUTPUT_PROFILE['resize_filter'],
                             size=settings.OUTPUT_PROFILE['resize_to'],
                             force_original_aspect_ratio='decrease')
            kwargs = settings.OUTPUT_PROFILE['output_settings'].copy()
            bitrate = settings.OUTPUT_PROFILE['max_bitrate']
            if self.probed_bitrate:
                bitrate = min(bitrate, self.probed_bitrate // settings.OUTPUT_PROFILE['bitrate_reduction'])
                if bitrate < settings.OUTPUT_PROFILE['max_bitrate']:
                    print(f'Dynamic bitrate: {bitrate} because of original bitrate {self.probed_bitrate}')
            kwargs['b:v'] = str(bitrate)
            p = p.output(self.output_path, **kwargs)
            try:
                p.run(cmd=settings.OUTPUT_PROFILE['command_args'], quiet=True)
            except ffmpeg.Error as exc:
                raise FFMpegError(exc.stderr)

            self.output_size = op.stat().st_size
            self.converted = True
            if self.output_size >= self.original_size:
                print(f'\n{self.path}: Output was larger than input: {self.output_size_human} > {self.original_size_human}')
                op.unlink()
                self.output_path = None
            self.save()
            if replace:
                self.replace()

        except KeyboardInterrupt:
            return
        except Exception:
            traceback.print_exc()
            self.error = True
            self.save()

    def replace(self):
        if self.converted and self.output_path:
            op = Path(self.output_path)
            original = Path(self.path)
            new = original.with_suffix(settings.OUTPUT_PROFILE['output_suffix'])
            print(f'\nReplacing {original} ({self.original_size_human}) with {op} as {new} ({self.output_size_human})\n')
            shutil.copy(op, new)
            op.unlink()
            original.unlink()
            MovieFile.objects.filter(path=self.path).delete()
            self.path = str(new)
            self.output_path = None
            self.save()

    def clear(self, new_size=None):
        self.converted = self.probed = self.error = False
        self.output_size = self.output_path = self.probed_video_codec = self.probed_height = self.probed_width = None
        self.original_size = new_size or Path(self.path).stat().st_size
        self.save()


class FFMpegError(Exception):
    pass
