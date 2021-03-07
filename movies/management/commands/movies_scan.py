from django.core.management import BaseCommand


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
        from movies.scanner import perform_scanning
        from movies.pools import wait_for_all_futures
        if options.get('force_probe'):
            print('Force probe')
            from movies.models import MovieFile
            MovieFile.objects.all().update(probed=False)
        perform_scanning()
        wait_for_all_futures()
