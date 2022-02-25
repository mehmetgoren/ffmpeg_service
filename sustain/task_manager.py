import os
import signal
import sys
import time
from multiprocessing import Process
from typing import List
import psutil
from rq import Queue, Connection, Worker
from rq.command import send_stop_job_command, send_kill_horse_command, send_shutdown_command
from rq.job import Job, get_current_job, Retry

from common.utilities import crate_redis_connection, RedisDb, logger, config
from event_listeners import listen_editor_event, listen_start_stream_event, listen_stop_stream_event, listen_restart_stream_event
from sustain.failed_stream.failed_stream_repository import FailedStreamRepository
from sustain.failed_stream.zombie_repository import ZombieRepository
from sustain.rec_stuck.rec_stuck_repository import RecStuckRepository
from sustain.task.task_model import TaskModel, TaskOp
from sustain.task.task_repository import TaskRepository
from sustain.kill_prevs import kill_all_prev_ffmpeg_procs, reset_rtmp_container_ports, remove_all_prev_rtmp_containers
from sustain.watchdog_timer import WatchDogTimer

__connection_main = crate_redis_connection(RedisDb.MAIN)
__connection_rq = crate_redis_connection(RedisDb.RQ)
__task_repository = TaskRepository(__connection_main)
__rec_stuck_repository = RecStuckRepository(__connection_main)
__failed_stream_repository = FailedStreamRepository(__connection_main)
__zombie_repository = ZombieRepository(__connection_main)
__queue = Queue(connection=__connection_rq)
__watchdog = WatchDogTimer(__connection_main)

__max_retry = Retry(max=sys.maxsize)
__func_dic = {
    TaskOp.listen_start_stream_event: listen_start_stream_event,
    TaskOp.listen_stop_stream_event: listen_stop_stream_event,
    TaskOp.listen_restart_stream_event: listen_restart_stream_event,
    TaskOp.listen_editor_event: listen_editor_event,
    TaskOp.watchdog: __watchdog.start
}
__wait_for = config.ffmpeg.start_task_wait_for_interval


def __proxy_func(op: TaskOp):  # added only for getting job_id, worker_name, pid and worker pid
    task = __task_repository.get(op)
    current_job = get_current_job()
    task.job_id = current_job.id
    task.worker_name = current_job.worker_name
    task.pid = os.getpid()
    task.worker_pid = psutil.Process(os.getpid()).ppid()
    __task_repository.add(task)
    try:
        func = __func_dic[task.op]
        func()
    finally:
        exception_name, exception_value, _ = sys.exc_info()
        task.exception_msg = f'{exception_name} - {exception_value}'
        task.failed_count += 1
        __task_repository.add(task)
        time.sleep(1.)


def __init_tasks() -> (List[Job], BaseException):
    jobs: List[Job] = []
    err = None
    try:
        tasks = __task_repository.get_all()
        tasks = sorted(tasks, key=lambda x: int(x.op))
        for task in tasks:
            job = __queue.enqueue(__proxy_func, task.op, job_timeout=-1, retry=__max_retry)
            jobs.append(job)
    except BaseException as ex:
        logger.error(ex)
        err = ex
    if err is None:
        logger.info('all tasks have been initialized')
    return jobs, err


def __start_worker():
    worker = Worker(['default'], connection=__connection_rq)
    worker.work(burst=True)


def __start_workers(jobs: List[Job]):
    logger.info(f'jobs count: {len(jobs)}')
    with Connection(connection=__connection_rq):
        for _ in jobs:
            worker_proc = Process(target=__start_worker)
            worker_proc.start()
            time.sleep(__wait_for)


def __delete_all_rq():
    __connection_rq.flushdb()


def __kil_process(op: str, pid: int):
    try:
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
    except BaseException as e:
        logger.error(f'an error occurred during killing {op} process rq command, err: {e}')


def __kill_all_previous_jobs():
    tasks = __task_repository.get_all()
    for task in tasks:
        try:
            if len(task.job_id) > 0:
                send_stop_job_command(__connection_rq, task.job_id)
        except BaseException as e:
            logger.error(f'an error occurred during the stopping rq command, op: {TaskOp.str(task.op)}, err: {e}')
        try:
            if len(task.worker_name) > 0:
                send_kill_horse_command(__connection_rq, task.worker_name)
        except BaseException as e:
            logger.error(f'an error occurred during the killing rq command, op: {TaskOp.str(task.op)}, err: {e}')
        try:
            if len(task.worker_name) > 0:
                send_shutdown_command(__connection_rq, task.worker_name)
        except BaseException as e:
            logger.error(f'an error occurred during the shutting-down rq command, op: {TaskOp.str(task.op)}, err: {e}')
        __kil_process('task process', task.pid)
        __kil_process('worker process', task.worker_pid)


def clean_others_previous():
    kill_all_prev_ffmpeg_procs()
    reset_rtmp_container_ports(__connection_main)
    remove_all_prev_rtmp_containers(__connection_main)


def clean_my_previous():
    __kill_all_previous_jobs()
    __delete_all_rq()
    __task_repository.remove_all()
    __rec_stuck_repository.remove_all()
    __failed_stream_repository.remove_all()
    __zombie_repository.remove_all()


def add_tasks():
    task = TaskModel()
    task.set_op(TaskOp.listen_start_stream_event)
    __task_repository.add(task)
    task.set_op(TaskOp.listen_stop_stream_event)
    __task_repository.add(task)
    task.set_op(TaskOp.listen_restart_stream_event)
    __task_repository.add(task)
    task.set_op(TaskOp.listen_editor_event)
    __task_repository.add(task)
    task.set_op(TaskOp.watchdog)
    __task_repository.add(task)


def start_tasks():
    jobs, err = __init_tasks()
    if err is not None:
        logger.error(f'error while initializing tasks: {err}, the operation will be terminated')
        sys.exit(1)
    __start_workers(jobs)
