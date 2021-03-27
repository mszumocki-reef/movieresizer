from django.core.management import BaseCommand
import movies.models
from movies.pools import future_queue, convert_pool, wait_for_all_futures


def convert_one(m, i, total):
    print(f'Converting {i + 1}/{total}: {m}')
    m.convert(replace=True)


class Command(BaseCommand):
    """Scan all configured directories, exit when scanning is complete"""

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--limit', action='store', type=int,
            help='Limit to first N files'
        )
        parser.add_argument(
            'filters', nargs='*',
            help='Additional filters (key=value)'
        )
        parser.add_argument(
            '--dry-run', action='store_true'
        )

    def handle(self, *args, **options):
        movies.models.SHOW_PROGRESS = True
        limit = options.get('limit')
        filters = {}
        for s in options.get('filters'):
            key, value = s.split('=')
            filters[key] = value
        q = movies.models.all_to_convert(**filters)
        if options.get('dry_run'):
            print(q.query)
        if limit:
            q = q[:limit]
        total = q.count()
        for i, m in enumerate(q):
            if options.get('dry_run'):
                print(m)
            else:
                future_queue.append(convert_pool.submit(convert_one, m, i, total))
        wait_for_all_futures()
