from django.core.management import BaseCommand

from movies.scanner import perform_scanning, cleanup
from movies.pools import wait_for_all_futures
from movies.models import MovieFile


class Command(BaseCommand):
    """Scan all configured directories, exit when scanning is complete"""

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--force-probe', action='store_true',
            help='Force probing of all files.',
        )

    def handle(self, *args, **options):
        if options.get('force_probe'):
            MovieFile.objects.all().update(probed=False)
        perform_scanning()
        wait_for_all_futures()
        deleted = cleanup()
        remaining = MovieFile.objects.all().count()
        print(f"\n{remaining} files in DB, {deleted} stale files removed")

