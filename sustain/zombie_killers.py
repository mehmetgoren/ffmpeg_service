import os
import signal
from datetime import datetime
import psutil

from common.utilities import crate_redis_connection, RedisDb, logger, config
from rtmp.docker_manager import DockerManager
from stream.stream_repository import StreamRepository
from sustain.scheduler import setup_scheduler

__connection_main = crate_redis_connection(RedisDb.MAIN)
__stream_repository = StreamRepository(__connection_main)


def __check_zombie_ffmpeg_processes():
    logger.info(f'checking zombie ffmpeg processes at {datetime.now()}')
    models = __stream_repository.get_all()
    if len(models) == 0:
        logger.info(f'no stream operation exists, checking zombie FFmpeg process operation is now exiting at {datetime.now()}')
        return
    models_pid_dic = {}
    for model in models:
        models_pid_dic[model.pid] = model.pid
        if model.record_flv_pid > 0:
            models_pid_dic[model.record_flv_pid] = model.record_flv_pid
    all_process_list = psutil.process_iter()
    for proc in all_process_list:
        if proc.name() == "ffmpeg" and proc.pid not in models_pid_dic:
            try:
                args = proc.cmdline()
                if len(args) == 8 and args[4] == 'image2' and args[5] == '-vframes':
                    continue  # which means it is RtspVideoEditor' FFmpeg subprocess
                os.kill(proc.pid, signal.SIGKILL)
                logger.warn(f'a zombie FFmpeg process was detected and killed - {proc.pid} at {datetime.now()}')
            except BaseException as e:
                logger.error(f'an error occurred during killing a zombie FFmpeg process, ex: {e} at {datetime.now()}')


def __check_unstopped_rtmp_server_containers():
    models = __stream_repository.get_all()
    if len(models) == 0:
        logger.info(f'no stream operation exists, checking zombie RTMP server container operation is now exiting at {datetime.now()}')
        return
    logger.info(f'checking unstopped rtmp server containers at {datetime.now()}')
    containers_name_dic = {}
    count = 0
    for model in models:
        if len(model.rtmp_container_name) > 0:
            containers_name_dic[model.rtmp_container_name] = model.rtmp_container_name
            count += 1
    if count == 0:
        logger.info(f'no set container for rtmp server, checking unstopped rtmp server container is now exiting at {datetime.now()}')
        return
    docker_manager = DockerManager(__connection_main)
    containers = docker_manager.get_all_containers()
    prefixes = tuple(['srs_', 'livego_', 'nms_'])
    for container in containers:
        if container.name.startswith(prefixes) and container.name not in containers_name_dic:
            try:
                docker_manager.stop_container(container)
                logger.warn(f'an unstopped rtmp server container has been detected and stopped, container name: {container.name}')
            except BaseException as e:
                logger.error(f'an error occurred during stopping a zombie rtmp server container, ex: {e} at {datetime.now()}')


def check_zombie_ffmpeg_processes():
    setup_scheduler(config.ffmpeg.check_zombie_ffmpeg_processes_interval, __check_zombie_ffmpeg_processes, True)


def check_unstopped_rtmp_server_containers():
    setup_scheduler(config.ffmpeg.check_unstopped_containers_interval, __check_unstopped_rtmp_server_containers, False)
