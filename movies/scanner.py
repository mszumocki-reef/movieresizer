from pathlib import Path

from django.db import transaction

from .models import MovieDirectory, MovieFile
from .pools import probe_pool, future_queue

INCLUDED = {'.asf', '.avi', '.mp4', '.mov', '.mkv', '.wmv'}


def perform_scanning():
    for directory in MovieDirectory.objects.all().values_list('path', flat=True):
        directory = Path(directory)
        if directory.exists() and directory.is_dir():
            scan(directory)


def scan(directory):
    for child in directory.iterdir():
        if child.exists():
            if child.is_dir():
                scan(child)
            else:
                suffix = child.suffix
                if suffix.lower() in INCLUDED:
                    check_file(child)


def check_file(path):
    stats = path.stat()
    movie, is_new = MovieFile.objects.get_or_create(
        path=str(path),
        defaults=dict(original_size=stats.st_size)
    )
    if not is_new and movie.original_size != stats.st_size:
        movie.clear()
    if not movie.probed:
        future_queue.append(probe_pool.submit(movie.probe))
