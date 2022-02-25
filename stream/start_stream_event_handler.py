import os
import os.path
import time
import subprocess
from datetime import datetime
from typing import List
from threading import Thread
import psutil

from command_builder import CommandBuilder, get_hls_output_path
from common.data.source_model import SourceModel, RmtpServerType
from common.data.source_repository import SourceRepository
from common.utilities import logger, config
from readers.disk_image_reader import DiskImageReader, DiskImageReaderOptions
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions
from rtmp.docker_manager import DockerManager
from stream.req_resp import StartStreamRequestEvent
from stream.stream_model import StreamModel, StreamType
from stream.stream_repository import StreamRepository
from stream.base_stream_event_handler import BaseStreamEventHandler
from utils.json_serializer import serialize_json


class StartStreamEventHandler(BaseStreamEventHandler):
    def __init__(self, source_repository: SourceRepository, stream_repository: StreamRepository):
        super().__init__(stream_repository, 'start_stream_response')
        self.source_repository = source_repository
        logger.info(f'StartStreamEventHandler initialized at {datetime.now()}')

    @staticmethod
    def __start_thread(target, args):
        th = Thread(target=target, args=args)
        th.daemon = True
        th.start()

    def publish_async(self, stream_model: StreamModel):
        stream_model_json = serialize_json(stream_model)
        self.event_bus.publish_async(stream_model_json)

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        is_valid_msg, prev_stream_model, source_model = self.parse_message(dic)
        if not is_valid_msg:
            return
        logger.info(f'StartStreamEventHandler handle called {datetime.now()}')
        need_reload = prev_stream_model is None or not psutil.pid_exists(prev_stream_model.pid)
        if need_reload:
            stream_model = StreamModel().map_from_source(source_model)
            self.stream_repository.add(stream_model)  # to prevent missing fields because of the update operation.
            if source_model.stream_type == StreamType.DirectRead:
                direct = DirectReadHandler(stream_model, self)
                self.__start_thread(direct.start_ffmpeg_process, [])
            else:
                if source_model.stream_type == StreamType.HLS:
                    concrete = StartHlsStreamEventHandler(self)
                elif source_model.stream_type == StreamType.FLV:
                    concrete = StartFlvStreamHandler(self)
                else:
                    raise NotImplementedError(f'StreamType of {source_model.stream_type} is not supported')
                concrete.set_values(stream_model)
                self.__start_thread(self.__start_ffmpeg_process, [source_model, stream_model])
                concrete.wait_for(stream_model)
                self.__start_thread(concrete.create_ffmpeg_record_process, [source_model, stream_model])
                self.__start_thread(concrete.create_ffmpeg_reader_process, [stream_model])
        else:
            self.publish_async(prev_stream_model)

    def __start_ffmpeg_process(self, request: StartStreamRequestEvent, stream_model: StreamModel):
        logger.info(f'starting stream at {datetime.now()}')
        if request.stream_type == StreamType.FLV:
            request.rtmp_server_address = stream_model.rtmp_address
            if request.jpeg_enabled and request.reader:  # both of them cannot be enabled since they use same 'read_service' pub_sub channel
                request.jpeg_enabled = False
                request.use_disk_image_reader_service = False
            self.source_repository.add(request)
        cmd_builder = CommandBuilder(request)
        args: List[str] = cmd_builder.build()

        p = None
        image_reader = None
        try:
            logger.info(f'stream subprocess has been opened at {datetime.now()}')
            p = subprocess.Popen(args)
            stream_model.pid = p.pid
            stream_model.args = ' '.join(args)
            self.stream_repository.add(stream_model)
            logger.info(f'the model has been saved by repository at {datetime.now()}')
            if stream_model.is_disk_image_reader_service_enabled():
                image_reader = self.__start_disk_image_reader(stream_model)
            self.publish_async(stream_model)
            p.wait()
        except BaseException as e:
            logger.error(f'an error occurred during FFmpeg sub-process, err: {e} at {datetime.now()}')
        finally:
            if p is not None:
                p.terminate()
            if image_reader is not None:
                image_reader.close()
            logger.info(f'stream subprocess has been terminated at {datetime.now()}')

    @staticmethod
    def __start_disk_image_reader(stream_model: StreamModel) -> DiskImageReader:
        options = DiskImageReaderOptions()
        options.id = stream_model.id
        options.name = stream_model.name
        options.frame_rate = stream_model.jpeg_frame_rate
        options.image_path = stream_model.read_jpeg_output_path
        image_reader = DiskImageReader(options)
        image_reader.read()
        return image_reader


class StartHlsStreamEventHandler:
    def __init__(self, proxy: StartStreamEventHandler):
        self.proxy = proxy

    def set_values(self, stream_model: StreamModel):
        self.proxy.delete_prev_stream_files(stream_model.id)
        stream_model.hls_output_path = get_hls_output_path(stream_model.id)

    @staticmethod
    def wait_for(stream_model: StreamModel):
        max_retry = config.ffmpeg.max_operation_retry_count
        retry_count = 0
        while retry_count < max_retry:
            if os.path.exists(stream_model.hls_output_path):
                logger.info(f'HLS stream file created at {datetime.now()}')
                break
            time.sleep(1.)
            retry_count += 1

    def create_ffmpeg_record_process(self, source_model: SourceModel, stream_model: StreamModel):
        pass  # HLS record handled without any problem.

    def create_ffmpeg_reader_process(self, stream_model: StreamModel):
        pass  # HLS does not have RTMP server


class StartFlvStreamHandler:
    def __init__(self, proxy: StartStreamEventHandler):
        self.proxy = proxy
        self.docker_manager = DockerManager(proxy.stream_repository.connection)
        self.rtmp_model = None

    def set_values(self, stream_model: StreamModel):
        self.rtmp_model, _ = self.docker_manager.run(stream_model.rtmp_server_type, stream_model.id)
        self.rtmp_model.map_to(stream_model)

    def wait_for(self, stream_model: StreamModel):
        self.rtmp_model.init_channel_key()

    @staticmethod
    def __get_rtmp_address(stream_model: StreamModel):
        if stream_model.rtmp_server_type == RmtpServerType.LIVEGO:
            local_rtmp_pipe_input_address = stream_model.rtmp_address.replace('livestream',
                                                                              'rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk')
        else:
            local_rtmp_pipe_input_address = stream_model.rtmp_address
        return local_rtmp_pipe_input_address

    def create_ffmpeg_record_process(self, source_model: SourceModel, stream_model: StreamModel):
        if not stream_model.is_flv_record_enabled():
            return

        local_rtmp_pipe_input_address = self.__get_rtmp_address(stream_model)
        args: List[str] = ['ffmpeg', '-re', '-i',
                           local_rtmp_pipe_input_address]  # this one have to be local address (Loopback). Otherwise, it costs double network usage!..
        cmd_builder = CommandBuilder(source_model)
        cmd_builder.extend_record(args)
        p = None
        try:
            logger.info(f'stream FLV Record subprocess has been opened at {datetime.now()}')
            p = subprocess.Popen(args)  # do not use PIPE, otherwise FFmpeg recording process will be stuck.
            stream_model.record_flv_pid = p.pid
            stream_model.record_flv_args = ' '.join(args)
            self.proxy.stream_repository.add(stream_model)
            logger.info(f'the model has been saved by repository at {datetime.now()}')
            p.wait()
        except BaseException as e:
            logger.error(f'an error occurred during FFmpeg FLV record subprocess, err: {e} at {datetime.now()}')
        finally:
            if p is not None:
                p.terminate()
            logger.info(f'stream FLV record subprocess has been terminated at {datetime.now()}')

    # always execute this by a different thread. Otherwise, it blocks the whole execution
    def create_ffmpeg_reader_process(self, stream_model: StreamModel):
        if not stream_model.is_reader_enabled():
            return
        local_rtmp_pipe_input_address = self.__get_rtmp_address(stream_model)
        ffmpeg_reader = None
        try:
            logger.info(f'starting FFmpeg read process at {datetime.now()}')
            options = FFmpegReaderOptions()
            options.id = stream_model.id
            options.name = stream_model.name
            options.rtsp_address = local_rtmp_pipe_input_address
            options.frame_rate = stream_model.reader_frame_rate
            options.width = stream_model.reader_width
            options.height = stream_model.reader_height
            ffmpeg_reader = FFmpegReader(options)
            stream_model.reader_pid = ffmpeg_reader.get_pid()
            self.proxy.stream_repository.add(stream_model)
            ffmpeg_reader.read()
        except BaseException as e:
            logger.error(f'an error occurred while starting FFmpeg direct read sub-process, err: {e} at {datetime.now()}')
        finally:
            if ffmpeg_reader is not None:
                ffmpeg_reader.close()
                logger.info(f'FFmpeg reader process has been terminated at {datetime.now()}')


class DirectReadHandler:
    def __init__(self, stream_model: StreamModel, proxy: StartStreamEventHandler):
        self.stream_model = stream_model
        self.proxy = proxy
        self.stream_repository = proxy.stream_repository
        self.options = FFmpegReaderOptions()
        self.options.id = stream_model.id
        self.options.name = stream_model.name
        self.options.rtsp_address = stream_model.rtsp_address
        self.options.frame_rate = stream_model.direct_read_frame_rate
        self.options.width = stream_model.direct_read_width
        self.options.height = stream_model.direct_read_height
        self.ffmpeg_reader = FFmpegReader(self.options)

    def start_ffmpeg_process(self):
        logger.info('starting FFmpeg direct read stream')
        try:
            logger.info(f'FFmpeg direct read stream subprocess has been opened at {datetime.now()}')
            self.stream_model.pid = self.ffmpeg_reader.get_pid()
            self.stream_repository.add(self.stream_model)
            logger.info(f'the model has been saved by repository at {datetime.now()}')
            self.proxy.publish_async(self.stream_model)
            self.ffmpeg_reader.read()
        except BaseException as e:
            logger.error(f'an error occurred while starting FFmpeg direct read sub-process, err: {e} at {datetime.now()}')
        finally:
            self.ffmpeg_reader.close()
            logger.info(f'FFmpeg direct read stream subprocess has been terminated at {datetime.now()}')
