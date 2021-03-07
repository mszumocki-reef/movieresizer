from django.core.management import BaseCommand


class Command(BaseCommand):
    """Scan all configured directories, exit when scanning is complete"""

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--replace', action='store_true',
            help='Replace old files with new ones.',
        )
        parser.add_argument(
            '--limit', action='store', type=int,
            help='Limit to first N files'
        )

    def handle(self, *args, **options):
        from movies.models import all_to_convert
        replace = options.get('replace')
        limit = options.get('limit')
        q = all_to_convert()
        if limit:
            q = q[:limit]
        total = q.count()
        for i, m in enumerate(q):
            print(f'Converting {i+1}/{total}: {m}')
            m.convert(replace=replace)