import time
from threading import Thread
from typing import Callable

import schedule


def setup_scheduler(interval: int, fn: Callable, use_async: bool):
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(interval).seconds.do(fn)
    if use_async:
        while True:
            runnable_jobs = (job for job in scheduler_instance.jobs if job.should_run)
            if len(sorted(runnable_jobs)) > 0:
                th = Thread(target=scheduler_instance.run_pending)
                th.daemon = True
                th.start()
            time.sleep(1.)
    else:
        while True:
            scheduler_instance.run_pending()
            time.sleep(1.)
