import os
import signal
import time
from datetime import datetime
from typing import List
import psutil
from redis.client import Redis

from common.data.source_model import SourceModel
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, config, datetime_now
from rtmp.docker_manager import DockerManager
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from sustain.failed_stream.failed_stream_model import FailedStreamModel, WatchDogOperations
from sustain.failed_stream.failed_stream_repository import FailedStreamRepository
from sustain.failed_stream.zombie_repository import ZombieRepository
from sustain.rec_stuck.rec_stuck_model import RecStuckModel
from sustain.rec_stuck.rec_stuck_repository import RecStuckRepository
from sustain.scheduler import setup_scheduler
from utils.dir import str_to_datetime
from utils.json_serializer import serialize_json_dic


class WatchDogTimer:
    def __init__(self, connection_main: Redis):
        self.conn = connection_main
        self.source_repository = SourceRepository(self.conn)
        self.stream_repository = StreamRepository(self.conn)
        self.failed_stream_repository = FailedStreamRepository(self.conn)
        self.zombie_repository = ZombieRepository(self.conn)
        self.restart_stream_event_bus = EventBus('restart_stream_request')
        self.interval: int = max(config.ffmpeg.watch_dog_interval, 10)
        logger.info(f'watchdog interval is: {self.interval}')
        self.failed_process_interval: float = max(config.ffmpeg.watch_dog_failed_wait_interval, 1.)
        logger.info(f'watch_dog failed_process_interval is : {self.failed_process_interval}')
        self.zombie_counter = 1
        self.zombie_multiplier: int = 6
        self.last_check_running_processes_date = datetime.now()
        self.last_kill_zombie_processes_date = datetime.now()

    def __start_prev_streams(self):
        stream_models = self.stream_repository.get_all()
        for stream_model in stream_models:
            self.__publish_restart(self.source_repository.get(stream_model.id))

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

    def __publish_restart(self, source_model: SourceModel):
        dic = source_model.__dict__
        self.restart_stream_event_bus.publish_async(serialize_json_dic(dic))

    def __recover(self, op: WatchDogOperations, stream_model: StreamModel):
        source_id = stream_model.id
        source_model = self.source_repository.get(source_id)  # if it wasn't deleted before.

        def log_failed():
            if source_model is None:
                return
            failed_stream_model: FailedStreamModel = self.failed_stream_repository.get(source_id)
            if failed_stream_model is None:
                failed_stream_model = FailedStreamModel().map_from_source(source_model)
            failed_stream_model.set_failed_count(op)
            self.failed_stream_repository.add(failed_stream_model)

        log_failed()
        self.__publish_restart(source_model)
        time.sleep(self.failed_process_interval)

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

    def _check_running_processes(self) -> List[StreamModel]:
        broken_streams: List[StreamModel] = []
        now = datetime.now()
        if (now - self.last_check_running_processes_date).seconds < self.interval:
            logger.warn(f'last_check_running_processes_date({self.last_check_running_processes_date}) is not satisfied with current time({now})')
            return broken_streams
        self.last_check_running_processes_date = now
        stream_models = self.stream_repository.get_all()
        rec_stuck_repository = RecStuckRepository(self.conn)
        self.__remove_zombie_rec_stuck_models(stream_models, rec_stuck_repository)
        for stream_model in stream_models:
            if self.__check_rtmp_container(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_rtmp_feeder_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_hls_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_ffmpeg_reader_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_record_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_snapshot_process(stream_model):
                broken_streams.append(stream_model)
                continue
            if self.__check_record_stuck_process(stream_model, rec_stuck_repository):
                broken_streams.append(stream_model)
        return broken_streams

    def __check_rtmp_container(self, stream_model: StreamModel) -> bool:
        op = WatchDogOperations.check_rtmp_container
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')
        docker_manager = DockerManager(self.conn)
        container = docker_manager.get_container(stream_model)
        if container is None or container.status != 'running':
            logger.warning(
                f'a failed RTMP container was detected for model {stream_model.name} (container name:{stream_model.rtmp_container_name}) and will be recovered')
            self.__recover(op, stream_model)
            return True
        return False

    def __check_process(self, op: WatchDogOperations, stream_model: StreamModel, pid: int) -> bool:
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')
        if not psutil.pid_exists(pid):
            logger.warning(
                f'a failed FFmpeg process was detected ({op}) for model {stream_model.name} (pid:{pid}) and will be recovered')
            self.__recover(op, stream_model)
            return True
        return False

    def __check_rtmp_feeder_process(self, stream_model: StreamModel):
        op = WatchDogOperations.check_rtmp_feeder_process
        return self.__check_process(op, stream_model, stream_model.rtmp_feeder_pid)

    def __check_hls_process(self, stream_model: StreamModel):
        if not stream_model.is_hls_enabled():
            return False
        op = WatchDogOperations.check_hls_process
        return self.__check_process(op, stream_model, stream_model.hls_pid)

    def __check_ffmpeg_reader_process(self, stream_model: StreamModel):
        if not stream_model.is_ffmpeg_reader_enabled():
            return False
        op = WatchDogOperations.check_ffmpeg_reader_process
        return self.__check_process(op, stream_model, stream_model.ffmpeg_reader_pid)

    def __check_record_process(self, stream_model: StreamModel):
        if not stream_model.is_record_enabled():
            return False
        op = WatchDogOperations.check_record_process
        return self.__check_process(op, stream_model, stream_model.record_pid)

    def __check_snapshot_process(self, stream_model: StreamModel):
        if not stream_model.is_ffmpeg_snapshot_enabled():
            return False
        op = WatchDogOperations.check_snapshot_process
        return self.__check_process(op, stream_model, stream_model.snapshot_pid)

    def __check_record_stuck_process(self, stream_model: StreamModel, rec_stuck_repository: RecStuckRepository):
        op = WatchDogOperations.check_record_stuck_process
        logger.info(f'{op.value} is being executed for {stream_model.id} at {datetime.now()}')

        def refresh(old: RecStuckModel, curr: RecStuckModel):
            old.last_modified_file = curr.last_modified_file
            old.last_modified_size = curr.last_modified_size
            old.last_check_at = datetime_now()
            rec_stuck_repository.add(old)

        def check_time(rsm: RecStuckModel, sm: StreamModel) -> bool:
            last_check_at_time = str_to_datetime(rsm.last_check_at)
            diff_sec = (datetime.now() - last_check_at_time).seconds
            min_sec = (sm.record_segment_interval * 60 * 2)
            return diff_sec > min_sec

        if stream_model.record_enabled:
            db_model = rec_stuck_repository.get(stream_model.id)
            if db_model is None:
                db_model = RecStuckModel().from_stream(stream_model)
                db_model.last_check_at = datetime_now()
                rec_stuck_repository.add(db_model)
            else:
                if not check_time(db_model, stream_model):
                    logger.info(f'source({stream_model.id}) min interval does not meet for record restuck')
                    return False

                current = RecStuckModel().from_stream(stream_model)
                if db_model.last_modified_file != current.last_modified_file:  # means file has been already changed
                    refresh(db_model, current)
                    return False
                if db_model.last_modified_size < current.last_modified_size:  # means everything works as expected
                    refresh(db_model, current)
                    return False

                db_model.failed_count += 1
                db_model.failed_modified_file = db_model.last_modified_file
                db_model.last_check_at = datetime_now()
                rec_stuck_repository.add(db_model)

                self.__recover(op, stream_model)
                return True
        return False

    def _kill_zombie_processes(self, broken_streams: List[StreamModel]):
        now = datetime.now()
        if (now - self.last_kill_zombie_processes_date).seconds < self.interval:
            logger.warn(f'last_kill_zombie_processes_date({self.last_kill_zombie_processes_date}) is not satisfied with current time({now})')
            return broken_streams
        self.last_kill_zombie_processes_date = now
        stream_models = self.stream_repository.get_all()
        stream_models.extend(broken_streams)
        self.__check_zombie_ffmpeg_processes(stream_models)
        self.__check_unstopped_rtmp_server_containers(stream_models)

    def __check_zombie_ffmpeg_processes(self, stream_models: List[StreamModel]):
        logger.info(f'check_zombie_ffmpeg_processes is being executed at {datetime.now()}')
        models_pid_dic = {}

        def add_pid(pid: int):
            if pid > 0:
                models_pid_dic[pid] = pid

        for stream_model in stream_models:
            add_pid(stream_model.rtmp_feeder_pid)
            add_pid(stream_model.hls_pid)
            add_pid(stream_model.ffmpeg_reader_pid)
            add_pid(stream_model.record_pid)
            add_pid(stream_model.snapshot_pid)
            add_pid(stream_model.concat_demuxer_pid)
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
        prefixes = tuple(['srs_', 'srsrt_', 'livego_', 'nms_'])
        for container in containers:
            if container.name.startswith(prefixes) and container.name not in valid_containers_name_dic:
                try:
                    self.zombie_repository.add('docker', container.name)
                    docker_manager.stop_container(container)
                    logger.warn(f'an unstopped rtmp server container has been detected and stopped, container name: {container.name}')
                except BaseException as e:
                    logger.error(f'an error occurred during stopping a zombie rtmp server container, ex: {e} at {datetime.now()}')
