import os
import signal
import time
from datetime import datetime
from enum import Enum
from typing import List
import psutil
from redis.client import Redis

from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, config
from rtmp.docker_manager import DockerManager
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from sustain.failed_stream.failed_stream_model import FailedStreamModel
from sustain.failed_stream.failed_stream_repository import FailedStreamRepository
from sustain.failed_stream.zombie_repository import ZombieRepository
from sustain.rec_stuck.rec_stuck_model import RecStuckModel
from sustain.rec_stuck.rec_stuck_repository import RecStuckRepository
from sustain.scheduler import setup_scheduler
from utils.json_serializer import serialize_json_dic


class WatchDogOperations(str, Enum):
    check_stream_process = 'check_stream_process'
    check_record_process = 'check_record_process'
    check_reader_process = 'check_reader_process'
    check_record_stuck_process = 'check_record_stuck_process'


class WatchDogTimer:
    def __init__(self, connection_main: Redis):
        self.conn = connection_main
        self.source_repository = SourceRepository(self.conn)
        self.stream_repository = StreamRepository(self.conn)
        self.failed_stream_repository = FailedStreamRepository(self.conn)
        self.zombie_repository = ZombieRepository(self.conn)
        self.restart_stream_event_bus = EventBus('restart_stream_request')
        self.interval = max(config.ffmpeg.watch_dog_interval, 10)
        logger.info(f'watchdog interval is: {self.interval}')
        self.failed_process_interval: float = max(config.ffmpeg.watch_dog_failed_wait_interval, 1.)
        logger.info(f'watch_dog failed_process_interval is : {self.failed_process_interval}')
        self.zombie_counter = 1
        self.zombie_multiplier: int = 6
        self.last_check_record_stuck_process_datetime = datetime.now()

    def __start_prev_streams(self):
        stream_models = self.stream_repository.get_all()
        for stream_model in stream_models:
            self.__publish_restart(stream_model.id)

    def start(self):
        self.__start_prev_streams()
        setup_scheduler(self.interval, self.__tick, True)

    def __tick(self):
        logger.info(f'watchdog timer is starting at {datetime.now()}')

        broken_streams = self._check_running_processes()
        if self.zombie_counter % self.zombie_multiplier == 0:
            self._kill_zombie_processes(broken_streams)
        self.zombie_counter += 1
        if self.zombie_counter > self.zombie_multiplier * 1000:
            self.zombie_counter = 1

        logger.info(f'watchdog timer has been finished at {datetime.now()}')

    def _check_running_processes(self) -> List[StreamModel]:
        stream_models = self.stream_repository.get_all()
        rec_stuck_repository = RecStuckRepository(self.conn)
        self.__remove_zombie_rec_stuck_models(stream_models, rec_stuck_repository)
        broken_streams: List[StreamModel] = []
        for stream_model in stream_models:
            if self.__check_stream_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_record_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_reader_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if (datetime.now() - self.last_check_record_stuck_process_datetime).seconds > 180:
                if self.__check_record_stuck_process(stream_model, rec_stuck_repository):
                    broken_streams.append(stream_model)
                self.last_check_record_stuck_process_datetime = datetime.now()
        return broken_streams

    def __log_failed_process(self, source_id: str, op: WatchDogOperations):
        source_model = self.source_repository.get(source_id)  # if it wasn't deleted before.
        if source_model is None:
            return
        failed_stream_model: FailedStreamModel = self.failed_stream_repository.get(source_id)
        if failed_stream_model is None:
            failed_stream_model = FailedStreamModel().map_from_source(source_model)
        failed_stream_model.watch_dog_interval = self.interval
        if op == WatchDogOperations.check_stream_process:
            failed_stream_model.stream_failed_count += 1
        elif op == WatchDogOperations.check_record_process:
            failed_stream_model.record_failed_count += 1
        elif op == WatchDogOperations.check_reader_process:
            failed_stream_model.reader_failed_count += 1
        elif op == WatchDogOperations.check_record_stuck_process:
            failed_stream_model.record_stuck_failed_count += 1
        else:
            raise NotImplementedError(op.value)
        self.failed_stream_repository.add(failed_stream_model)

    @staticmethod
    def __remove_zombie_rec_stuck_models(stream_models: List[StreamModel], rec_stuck_repository: RecStuckRepository):
        logger.info(f'__remove_zombie_rec_stuck_models is being executed at {datetime.now()}')
        streams_dic = {stream_model.id: stream_model for stream_model in stream_models}
        rec_stuck_models = rec_stuck_repository.get_all()
        # let's check zombie record first.
        for rec_stuck_model in rec_stuck_models:
            if rec_stuck_model.id not in streams_dic:
                rec_stuck_repository.remove(rec_stuck_model)
                logger.warn('a zombie recording stuck model found on recstucks and removed')

    def __publish_restart(self, source_id: str):
        source_model = self.source_repository.get(source_id)
        dic = source_model.__dict__
        self.restart_stream_event_bus.publish_async(serialize_json_dic(dic))

    def __check_stream_process(self, stream_model: StreamModel):
        op = WatchDogOperations.check_stream_process
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')
        if not psutil.pid_exists(stream_model.pid):
            logger.warning(
                f'a failed FFmpeg stream process was detected for model {stream_model.name} (pid:{stream_model.pid}) and will be recovered')
            self.__log_failed_process(stream_model.id, op)
            self.__publish_restart(stream_model.id)
            time.sleep(self.failed_process_interval)
            return True
        return False

    def __check_record_process(self, stream_model: StreamModel):
        op = WatchDogOperations.check_record_process
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')
        if stream_model.is_flv_record_enabled() and not psutil.pid_exists(stream_model.record_flv_pid):
            stream_model.record_flv_failed_count += 1
            self.stream_repository.update(stream_model, ['record_flv_failed_count'])
            logger.warn(
                f'a failed FFmpeg record process was detected for model {stream_model.name} (pid:{stream_model.pid}) and will be recovered')
            self.__log_failed_process(stream_model.id, op)
            self.__publish_restart(stream_model.id)
            time.sleep(self.failed_process_interval)
            return True
        return False

    def __check_reader_process(self, stream_model: StreamModel):
        op = WatchDogOperations.check_reader_process
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')
        if stream_model.is_reader_enabled() and not psutil.pid_exists(stream_model.reader_pid):
            stream_model.reader_failed_count += 1
            self.stream_repository.update(stream_model, ['reader_failed_count'])
            logger.warn(
                f'a failed FFmpeg reader process was detected for model {stream_model.name} (pid:{stream_model.pid}) and will be recovered')
            self.__log_failed_process(stream_model.id, op)
            self.__publish_restart(stream_model.id)
            time.sleep(self.failed_process_interval)
            return True
        return False

    def __check_record_stuck_process(self, stream_model: StreamModel, rec_stuck_repository: RecStuckRepository):
        op = WatchDogOperations.check_record_stuck_process
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')

        def refresh(old: RecStuckModel, curr: RecStuckModel):
            old.last_modified_file = curr.last_modified_file
            old.last_modified_size = curr.last_modified_size
            rec_stuck_repository.add(old)

        if stream_model.record:
            db_model = rec_stuck_repository.get(stream_model.id)
            if db_model is None:
                db_model = RecStuckModel().from_stream(stream_model)
                rec_stuck_repository.add(db_model)
            else:
                current = RecStuckModel().from_stream(stream_model)
                if db_model.last_modified_file != current.last_modified_file:  # means file has been already changed
                    refresh(db_model, current)
                    return False
                if db_model.last_modified_size < current.last_modified_size:  # means everything works as expected
                    refresh(db_model, current)
                    return False

                logger.warn(
                    f'a failed FFmpeg stuck record process was detected for model {stream_model.name} (pid:{stream_model.pid}) and will be recovered')
                self.__log_failed_process(stream_model.id, op)
                # let' s relive the zombie
                db_model.failed_count += 1
                db_model.failed_modified_file = db_model.last_modified_file
                rec_stuck_repository.add(db_model)
                self.__publish_restart(stream_model.id)
                time.sleep(self.failed_process_interval)
                return True
        return False

    def _kill_zombie_processes(self, broken_streams: List[StreamModel]):
        stream_models = self.stream_repository.get_all()
        stream_models.extend(broken_streams)
        self.__check_zombie_ffmpeg_processes(stream_models)
        self.__check_unstopped_rtmp_server_containers(stream_models)

    def __check_zombie_ffmpeg_processes(self, stream_models: List[StreamModel]):
        logger.info(f'check_zombie_ffmpeg_processes is being executed at {datetime.now()}')
        models_pid_dic = {}
        for stream_model in stream_models:
            if stream_model.pid > 0:
                models_pid_dic[stream_model.pid] = stream_model.pid
            if stream_model.record_flv_pid > 0:
                models_pid_dic[stream_model.record_flv_pid] = stream_model.record_flv_pid
            if stream_model.reader_pid > 0:
                models_pid_dic[stream_model.reader_pid] = stream_model.reader_pid
        all_process_list = psutil.process_iter()
        for proc in all_process_list:
            if proc.name() == "ffmpeg" and proc.pid not in models_pid_dic:
                try:
                    args = proc.cmdline()
                    if len(args) == 8 and args[4] == 'image2' and args[5] == '-vframes':
                        continue  # which means it is RtspVideoEditor' FFmpeg subprocess
                    self.zombie_repository.add('ffmpeg', str(proc.pid))
                    os.kill(proc.pid, signal.SIGKILL)
                    logger.warn(f'a zombie FFmpeg process was detected and killed - {proc.pid} at {datetime.now()}')
                except BaseException as e:
                    logger.error(f'an error occurred during killing a zombie FFmpeg process, ex: {e} at {datetime.now()}')

    def __check_unstopped_rtmp_server_containers(self, stream_models: List[StreamModel]):
        logger.info(f'check_unstopped_rtmp_server_containers is being executed at {datetime.now()}')
        valid_containers_name_dic = {}
        count = 0
        for stream_model in stream_models:
            if len(stream_model.rtmp_container_name) > 0:
                valid_containers_name_dic[stream_model.rtmp_container_name] = stream_model.rtmp_container_name
                count += 1
        if count == 0:
            return
        docker_manager = DockerManager(self.conn)
        containers = docker_manager.get_all_containers()
        prefixes = tuple(['srs_', 'livego_', 'nms_'])
        for container in containers:
            if container.name.startswith(prefixes) and container.name not in valid_containers_name_dic:
                try:
                    self.zombie_repository.add('docker', container.name)
                    docker_manager.stop_container(container)
                    logger.warn(f'an unstopped rtmp server container has been detected and stopped, container name: {container.name}')
                except BaseException as e:
                    logger.error(f'an error occurred during stopping a zombie rtmp server container, ex: {e} at {datetime.now()}')
