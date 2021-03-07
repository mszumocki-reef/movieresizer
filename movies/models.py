import os
from pathlib import Path

import traceback
import ffmpeg

from django.db import models

OUTPUT_PATH = Path(r'D:\output')

FILTER_CRITERIA = {
    'max_width': 1280,
    'max_height': 720,
    'accepted_codecs': {'hevc'},
}

OUTPUT_PROFILE = {
    'video_codec': 'hevc_amf',
    'resize_to': 'hd720',
    'resize_filter': 'scale',
}
OUTPUT_SUFFIX = '.mkv'


# Create your models here.

def path_field(**kwargs):
    return models.CharField(max_length=1024, **kwargs)


def video_codec(streams):
    for stream in streams:
        if stream.get('codec_type') == 'video':
            return stream


def to_output_path(path):
    path = Path(path)
    output_path = OUTPUT_PATH.joinpath(*path.parts[1:])
    return output_path.with_suffix(OUTPUT_SUFFIX)


def all_to_convert():
    cond = models.Q(probed_width__gt=FILTER_CRITERIA['max_width']) | models.Q(probed_height__gt=FILTER_CRITERIA['max_height'])
    cond = cond | ~models.Q(probed_video_codec__in=FILTER_CRITERIA['accepted_codecs'])
    query = MovieFile.objects.filter(cond, converted=False, probed=True).order_by('-width')
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
    converted = models.BooleanField(default=False)
    output_path = path_field(null=True)
    output_size = models.BigIntegerField(null=True)

    class Meta:
        verbose_name = 'Movie file'
        verbose_name_plural = 'Movie files'
        ordering = ('path',)

    def probe(self):
        try:
            info = ffmpeg.probe(self.path)
            vc = video_codec(info['streams'])
            if vc:
                self.probed_video_codec = vc['codec_tag_string']
                self.probed_width = vc['coded_width']
                self.probed_height = vc['coded_height']
            self.probed = True
            self.save()
        except Exception:
            traceback.print_exc()
        print('.', end='')

    def convert(self, replace=False):
        if not Path(self.path).exists():
            return
        try:
            op = to_output_path(self.path)
            if op.exists():
                op.unlink()
            else:
                os.makedirs(op.parent, exist_ok=True)
            self.output_path = str(op)
            p = ffmpeg.input(self.path)
            if self.probed_width > FILTER_CRITERIA['max_width'] or self.probed_height > FILTER_CRITERIA['max_height']:
                p = p.filter(OUTPUT_PROFILE['resize_filter'], size=OUTPUT_PROFILE['resize_to'], force_original_aspect_ratio='decrease')
            p = p.output(self.output_path, vcodec=OUTPUT_PROFILE['video_codec'])
            p.run()
            self.output_size = op.stat().st_size
            self.converted = True
            if self.output_size >= self.original_size:
                op.unlink()
                self.output_path = None
            self.save()
            if replace:
                self.replace()

        except Exception:
            traceback.print_exc()

    def replace(self):
        if self.converted and self.output_path:
            op = Path(self.output_path)
            original = Path(self.path)
            new = original.with_suffix(OUTPUT_SUFFIX)
            print(f'Replacing {original} ({self.original_size}) with {op} as {new} ({self.output_size})')
            op.replace(new)
            original.unlink()
            self.path = str(new)
            self.output_path = None
            self.save()
