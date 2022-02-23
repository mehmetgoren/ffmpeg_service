import time
from threading import Thread
from typing import Callable

import schedule


def setup_scheduler(interval: int, fn: Callable, use_async: bool):
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(interval).seconds.do(fn)
    if use_async:
        while True:
            scheduler_instance.run_pending()
            time.sleep(1.)
    else:
        while True:
            th = Thread(target=scheduler_instance.run_pending)
            th.daemon = True
            th.start()
            time.sleep(1.)
