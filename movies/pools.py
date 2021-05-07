import collections
from concurrent.futures import ThreadPoolExecutor as Executor

probe_pool = Executor()
convert_pool = Executor(max_workers=1)
future_queue = []


def wait_for_all_futures():
    try:
        for f in future_queue:
            f.result(timeout=None)
    except KeyboardInterrupt:
        probe_pool.shutdown(cancel_futures=True)
        convert_pool.shutdown(cancel_futures=True)
        raise
