import os
import subprocess
import time
from abc import abstractmethod, ABC
from datetime import datetime
from threading import Thread
from typing import List
import psutil

from command_builder import CommandBuilder
from common.data.source_model import SourceModel, RmtpServerType
from common.data.source_repository import SourceRepository
from common.utilities import logger, config
from readers.direct_reader import DirectReader
from readers.ffmpeg_reader import FFmpegReaderOptions, FFmpegReader
from rtmp.docker_manager import DockerManager
from stream.base_stream_event_handler import BaseStreamEventHandler
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from utils.dir import get_hls_path
from utils.json_serializer import serialize_json


class StartStreamEventHandler(BaseStreamEventHandler):
    def __init__(self, source_repository: SourceRepository, stream_repository: StreamRepository):
        super().__init__(stream_repository, 'start_stream_response')
        self.source_repository = source_repository
        logger.info(f'StartStreamEventHandler initialized at {datetime.now()}')

    def publish_async(self, stream_model: StreamModel):
        stream_model_json = serialize_json(stream_model)
        self.event_bus.publish_async(stream_model_json)

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        is_valid_msg, stream_model, source_model = self.parse_message(dic)
        if not is_valid_msg:
            return
        logger.info(f'StartStreamEventHandler handle called {datetime.now()}')
        need_reload = stream_model is None or not psutil.pid_exists(stream_model.rtmp_feeder_pid)
        if need_reload:
            stream_model = StreamModel().map_from_source(source_model)
            self.stream_repository.add(stream_model)  # to prevent missing fields because of the update operation.
            starters: List[ProcessStarter] = [RtmpProcessStarter(self.source_repository, self.stream_repository)]
            if stream_model.is_hls_enabled():
                starters.append(HlsProcessStarter(self.stream_repository))
            elif stream_model.is_ffmpeg_reader_enabled():
                starters.append(FFmpegReaderProcessesStarter(self.stream_repository))
            if stream_model.is_record_enabled():
                starters.append(RecordProcessStarter(self.stream_repository))
            if stream_model.is_snapshot_enabled():
                starters.append(SnapshotProcessStarter(self.stream_repository))
            for starter in starters:
                starter.start_process(source_model, stream_model)
        self.publish_async(stream_model)


class ProcessStarter(ABC):
    def __init__(self, stream_repository: StreamRepository):
        self.stream_repository = stream_repository

    @abstractmethod
    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        raise NotImplementedError('StartStreamEventHandler._create_process')

    @abstractmethod
    def _execute_process(self, proc: any):
        raise NotImplementedError('StartStreamEventHandler._execute_process')

    @abstractmethod
    def _dispose_process(self, proc: any):
        raise NotImplementedError('StartStreamEventHandler._dispose_process')

    @staticmethod
    def _wait_extra(stream_model: StreamModel):
        if stream_model.rtmp_server_type == RmtpServerType.LIVEGO:
            time.sleep(config.ffmpeg.rtmp_server_init_interval)  # otherwise, rtmp won't work for LIVEGO

    @staticmethod
    def __start_thread(target, args):
        th = Thread(target=target, args=args)
        th.daemon = True
        th.start()

    def start_process(self, source_model: SourceModel, stream_model: StreamModel):
        try:
            proc = self._create_process(source_model, stream_model)
            self.stream_repository.add(stream_model)
        except BaseException as e1:
            logger.error(f'an error occurred during the creation of a subprocess operation, err: {e1} at {datetime.now()}')
            return

        def fn(ps: ProcessStarter, p):
            try:
                ps._execute_process(p)
            except BaseException as e2:
                logger.error(f'an error occurred during the executing of a subprocess operation, err: {e2} at {datetime.now()}')
                return
            finally:
                try:
                    ps._dispose_process(p)
                except BaseException as e3:
                    logger.error(f'an error occurred during the disposing subprocess operation, err: {e3} at {datetime.now()}')

        self.__start_thread(fn, [self, proc])


class SubProcessTemplate(ProcessStarter, ABC):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    def _execute_process(self, proc: any):
        proc.wait()

    def _dispose_process(self, proc: any):
        proc.terminate()


class RtmpProcessStarter(SubProcessTemplate):
    def __init__(self, source_repository: SourceRepository, stream_repository: StreamRepository):
        super().__init__(stream_repository)
        self.source_repository = source_repository
        self.docker_manager = DockerManager(stream_repository.connection)

    @staticmethod
    def __wait_for(rtmp_model):
        rtmp_model.init_channel_key()

    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        rtmp_model, _ = self.docker_manager.run(stream_model.rtmp_server_type, stream_model.id)
        self.__wait_for(rtmp_model)
        rtmp_model.map_to(stream_model)
        source_model.rtmp_address = stream_model.rtmp_address
        self.source_repository.add(source_model)

        cmd_builder = CommandBuilder(source_model)
        args = cmd_builder.build_input()
        args.extend(cmd_builder.build_output())
        if not stream_model.is_direct_reader_enabled():
            proc = subprocess.Popen(args)  # do not use PIPE, otherwise FFmpeg recording process will be stuck.
            logger.info(f'stream RTMP feeder subprocess has been opened at {datetime.now()}')
            stream_model.rtmp_feeder_pid = proc.pid
        else:
            options = _create_ffmpeg_reader_options(stream_model)
            dr = DirectReader(options, args)
            stream_model.rtmp_feeder_pid = dr.get_pid()
            logger.info(f'starting Direct Reader process at {datetime.now()}')
            proc = dr.create_process_proxy()
        stream_model.rtmp_feeder_args = ' '.join(args)
        return proc


class HlsProcessStarter(SubProcessTemplate):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    @staticmethod
    def __wait_for(stream_model: StreamModel):
        max_retry = config.ffmpeg.max_operation_retry_count
        retry_count = 0
        hls_output_path = get_hls_path(stream_model.id)
        while retry_count < max_retry:
            if os.path.exists(hls_output_path):
                logger.info(f'HLS stream file created at {datetime.now()}')
                break
            time.sleep(1.)
            retry_count += 1

    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        self._wait_extra(stream_model)
        cmd_builder = CommandBuilder(source_model)
        args = cmd_builder.build_hls_stream()
        proc = subprocess.Popen(args)
        logger.info(f'stream HLS subprocess has been opened at {datetime.now()}')
        stream_model.hls_pid = proc.pid
        stream_model.hls_args = ' '.join(args)
        self.__wait_for(stream_model)
        return proc


class RecordProcessStarter(SubProcessTemplate):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        self._wait_extra(stream_model)
        cmd_builder = CommandBuilder(source_model)
        args = cmd_builder.build_record()
        if stream_model.is_ai_clip_enabled():
            svc_args = cmd_builder.build_ai_clip()
            length = len(svc_args)
            svc_args = svc_args[3:length]
            args.extend(svc_args)
        proc = subprocess.Popen(args)
        logger.info(f'recording subprocess has been opened at {datetime.now()}')
        stream_model.record_pid = proc.pid
        stream_model.record_args = ' '.join(args)
        return proc


class FFmpegReaderTemplate(ProcessStarter, ABC):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    def _execute_process(self, ffmpeg_reader: any):
        ffmpeg_reader.read()

    def _dispose_process(self, ffmpeg_reader: any):
        ffmpeg_reader.close()


class SnapshotProcessStarter(FFmpegReaderTemplate):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        options = FFmpegReaderOptions()
        options.id = stream_model.id
        options.name = stream_model.name
        options.address = stream_model.rtmp_address
        options.frame_rate = stream_model.snapshot_frame_rate
        options.width = stream_model.snapshot_width
        options.height = stream_model.snapshot_height
        options.ai_clip_enabled = stream_model.ai_clip_enabled
        ffmpeg_reader = FFmpegReader(options)
        stream_model.snapshot_pid = ffmpeg_reader.get_pid()
        logger.info(f'starting Snapshot process at {datetime.now()}')
        return ffmpeg_reader


class FFmpegReaderProcessesStarter(FFmpegReaderTemplate):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository)

    def _create_process(self, source_model: SourceModel, stream_model: StreamModel) -> any:
        self._wait_extra(stream_model)
        options = _create_ffmpeg_reader_options(stream_model)
        ffmpeg_reader = FFmpegReader(options)
        stream_model.ffmpeg_reader_pid = ffmpeg_reader.get_pid()
        logger.info(f'starting FFmpegReader process at {datetime.now()}')
        return ffmpeg_reader


def _create_ffmpeg_reader_options(stream_model: StreamModel) -> FFmpegReaderOptions:
    options = FFmpegReaderOptions()
    options.id = stream_model.id
    options.name = stream_model.name
    options.address = stream_model.rtmp_address
    options.frame_rate = stream_model.ffmpeg_reader_frame_rate
    options.width = stream_model.ffmpeg_reader_width
    options.height = stream_model.ffmpeg_reader_height
    options.pubsub_channel = f'ffrs{stream_model.id}'
    return options
