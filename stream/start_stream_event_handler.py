import os
import os.path
import time
import subprocess
from typing import List
from threading import Thread

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
        logger.info('StartStreamEventHandler initialized')

    @staticmethod
    def __start_thread(target, args):
        th = Thread(target=target, args=args)
        th.daemon = True
        th.start()

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        is_valid_msg, prev_stream_model, source_model = self.parse_message(dic)
        if not is_valid_msg:
            return
        logger.info('StartStreamEventHandler handle called')
        if prev_stream_model is None:
            stream_model = StreamModel().map_from_source(source_model)
            if source_model.stream_type == StreamType.DirectRead:
                direct = DirectReadHandler(stream_model, self.stream_repository)
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
                self.__start_thread(concrete.create_piped_ffmpeg_process, [source_model, stream_model])
            self.stream_repository.add(stream_model)
            prev_stream_model = stream_model

        stream_model_json = serialize_json(prev_stream_model)
        self.event_bus.publish(stream_model_json)

    def __start_ffmpeg_process(self, request: StartStreamRequestEvent, stream_model: StreamModel):
        logger.info('starting stream')
        if request.stream_type == StreamType.FLV:
            request.rtmp_server_address = stream_model.rtmp_address
            self.source_repository.update(request, ['rtmp_server_address'])
        cmd_builder = CommandBuilder(request)
        args: List[str] = cmd_builder.build()

        p = None
        image_reader = None
        try:
            logger.info('stream subprocess has been opened')
            p = subprocess.Popen(args)
            stream_model.pid = p.pid
            stream_model.args = ' '.join(args)
            self.stream_repository.update(stream_model, ['pid', 'args'])
            logger.info('the model has been saved by repository')
            if stream_model.jpeg_enabled and stream_model.use_disk_image_reader_service:
                image_reader = self.__start_disk_image_reader(stream_model)
            p.wait()
        except Exception as e:
            logger.error(f'an error occurred during FFmpeg sub-process, err: {e}')
        finally:
            if p is not None:
                p.terminate()
            if image_reader is not None:
                image_reader.close()
            logger.info('stream subprocess has been terminated')

    @staticmethod
    def __start_disk_image_reader(stream_model: StreamModel) -> DiskImageReader:
        options = DiskImageReaderOptions()
        options.id = stream_model.id
        options.name = stream_model.name
        options.frame_rate = stream_model.jpeg_frame_rate
        options.image_path = stream_model.read_jpeg_output_path
        image_reader = DiskImageReader(options)
        image_reader.read_async()
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
                logger.info('HLS stream file created')
                break
            time.sleep(1)
            retry_count += 1

    def create_piped_ffmpeg_process(self, source_model: SourceModel, stream_model: StreamModel):
        pass  # HLS record handled without any problem.


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

    def create_piped_ffmpeg_process(self, source_model: SourceModel, stream_model: StreamModel):
        if stream_model.stream_type != StreamType.FLV or not stream_model.record:
            return

        if stream_model.rtmp_server_type == RmtpServerType.LIVEGO:
            local_rtmp_pipe_input_address = stream_model.rtmp_address.replace('livestream',
                                                                              'rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk')
        else:
            local_rtmp_pipe_input_address = stream_model.rtmp_address
        args: List[str] = ['ffmpeg', '-i',
                           local_rtmp_pipe_input_address]  # this one have to be local address (Loopback). Otherwise, it costs double network usage!..
        # container = self.docker_manager.get_container(stream_model)
        # while 1:
        #     if container.status == 'running':
        #         break
        # todo:move it to config
        time.sleep(3)
        cmd_builder = CommandBuilder(source_model)
        cmd_builder.extend_record(args)
        p = None
        try:
            logger.info('stream FLV Record subprocess has been opened')
            p = subprocess.Popen(args)
            stream_model.record_flv_pid = p.pid
            stream_model.record_flv_args = ' '.join(args)
            self.proxy.stream_repository.update(stream_model, ['record_flv_pid', 'record_flv_args'])
            logger.info('the model has been saved by repository')
            p.wait()
        except Exception as e:
            logger.error(f'an error occurred during FFmpeg FLV record subprocess, err: {e}')
        finally:
            if p is not None:
                p.terminate()
            logger.info('stream FLV record subprocess has been terminated')


class DirectReadHandler:
    def __init__(self, stream_model: StreamModel, stream_repository: StreamRepository):
        self.stream_model = stream_model
        self.stream_repository = stream_repository
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
            logger.info('FFmpeg direct read stream subprocess has been opened')
            self.stream_model.pid = self.ffmpeg_reader.get_pid()
            self.stream_repository.update(self.stream_model, ['pid'])
            logger.info('the model has been saved by repository')
            self.ffmpeg_reader.read()
        except Exception as e:
            logger.error(f'an error occurred while starting FFmpeg direct read sub-process, err: {e}')
        finally:
            self.ffmpeg_reader.close()
            logger.info('FFmpeg direct read stream subprocess has been terminated')
