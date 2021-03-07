import collections
from concurrent.futures import ThreadPoolExecutor as Executor

probe_pool = Executor(max_workers=10)
convert_pool = Executor(max_workers=1)
future_queue = []


def wait_for_all_futures():
    for f in future_queue:
        f.result(timeout=None)
