import os
import os.path
import time
import subprocess
from typing import List
from threading import Thread

from command_builder import CommandBuilder, get_hls_output_path
from common.data.source_repository import SourceRepository
from common.utilities import logger, config
from readers.disk_image_reader import DiskImageReader, DiskImageReaderOptions
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions
from rtmp.docker_manager import DockerManager
from streaming.req_resp import StartStreamingRequestEvent
from streaming.streaming_model import StreamingModel, StreamType
from streaming.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler
from utils.json_serializer import serialize_json


class StartStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, source_repository: SourceRepository, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'start_streaming_response')
        self.source_repository = source_repository
        logger.info('StartStreamingEventHandler initialized')

    @staticmethod
    def __start_thread(target, args):
        th = Thread(target=target, args=args)
        th.daemon = True
        th.start()

    def handle(self, dic: dict):
        is_valid_msg, prev_streaming_model, source_model, _ = self.parse_message(dic)
        if not is_valid_msg:
            return
        logger.info('StartHlsStreamingEventHandler handle called')
        if prev_streaming_model is None:
            streaming_model = StreamingModel().map_from_source(source_model)
            if source_model.stream_type == StreamType.DirectRead:
                direct = DirectReadHandler(streaming_model, self.streaming_repository)
                self.__start_thread(direct.start_ffmpeg_process, [])
            else:
                if source_model.stream_type == StreamType.HLS:
                    concrete = StartHlsStreamingEventHandler(self)
                elif source_model.stream_type == StreamType.FLV:
                    concrete = StartFlvStreamingHandler(self)
                else:
                    raise NotImplementedError(f'StreamType of {source_model.stream_type} is not supported')
                concrete.set_values(streaming_model)
                self.__start_thread(self.__start_ffmpeg_process, [source_model, streaming_model])
                concrete.wait_for(streaming_model)
            self.streaming_repository.add(streaming_model)
            prev_streaming_model = streaming_model

        streaming_model_json = serialize_json(prev_streaming_model)
        self.event_bus.publish(streaming_model_json)

    def __start_ffmpeg_process(self, request: StartStreamingRequestEvent, streaming_model: StreamingModel):
        logger.info('starting streaming')
        if request.stream_type == StreamType.FLV:
            request.rtmp_server_address = streaming_model.rtmp_address
            self.source_repository.update(request, ['rtmp_server_address'])
        cmd_builder = CommandBuilder(request)
        args: List[str] = cmd_builder.build()

        p = None
        image_reader = None
        try:
            logger.info('streaming subprocess has been opened')
            p = subprocess.Popen(args)
            streaming_model.pid = p.pid
            streaming_model.args = ' '.join(args)
            self.streaming_repository.update(streaming_model, ['pid', 'args'])
            logger.info('the model has been saved by repository')
            if streaming_model.jpeg_enabled and streaming_model.use_disk_image_reader_service:
                image_reader = self.__start_disk_image_reader(streaming_model)
            p.wait()
        except Exception as e:
            logger.error(f'an error occurred while starting FFmpeg sub-process, err: {e}')
        finally:
            if p is not None:
                p.terminate()
            if image_reader is not None:
                image_reader.close()
            logger.info('streaming subprocess has been terminated')

    @staticmethod
    def __start_disk_image_reader(streaming_model: StreamingModel) -> DiskImageReader:
        options = DiskImageReaderOptions()
        options.id = streaming_model.id
        options.name = streaming_model.name
        options.frame_rate = streaming_model.jpeg_frame_rate
        options.image_path = streaming_model.read_jpeg_output_path
        image_reader = DiskImageReader(options)
        image_reader.read_async()
        return image_reader


class StartHlsStreamingEventHandler:
    def __init__(self, proxy: StartStreamingEventHandler):
        self.proxy = proxy

    def set_values(self, streaming_model: StreamingModel):
        self.proxy.delete_pref_streaming_files(streaming_model.id)
        streaming_model.hls_output_path = get_hls_output_path(streaming_model.id)

    @staticmethod
    def wait_for(streaming_model: StreamingModel):
        max_retry = config.ffmpeg.max_operation_retry_count
        retry_count = 0
        while retry_count < max_retry:
            if os.path.exists(streaming_model.hls_output_path):
                logger.info('HLS streaming file created')
                break
            time.sleep(1)
            retry_count += 1


class StartFlvStreamingHandler:
    def __init__(self, proxy: StartStreamingEventHandler):
        self.proxy = proxy
        self.docker_manager = DockerManager(proxy.streaming_repository.connection)
        self.rtmp_model = None

    def set_values(self, streaming_model: StreamingModel):
        self.rtmp_model, _ = self.docker_manager.run(streaming_model.rtmp_server_type, streaming_model.id)
        self.rtmp_model.map_to(streaming_model)

    def wait_for(self, streaming_model: StreamingModel):
        self.rtmp_model.init_channel_key()


class DirectReadHandler:
    def __init__(self, streaming_model: StreamingModel, streaming_repository: StreamingRepository):
        self.streaming_model = streaming_model
        self.streaming_repository = streaming_repository
        self.options = FFmpegReaderOptions()
        self.options.id = streaming_model.id
        self.options.name = streaming_model.name
        self.options.rtsp_address = streaming_model.rtsp_address
        self.options.frame_rate = streaming_model.direct_read_frame_rate
        self.options.width = streaming_model.direct_read_width
        self.options.height = streaming_model.direct_read_height
        self.ffmpeg_reader = FFmpegReader(self.options)

    def start_ffmpeg_process(self):
        logger.info('starting FFmpeg direct read streaming')
        try:
            logger.info('FFmpeg direct read streaming subprocess has been opened')
            self.streaming_model.pid = self.ffmpeg_reader.get_pid()
            self.streaming_repository.update(self.streaming_model, ['pid'])
            logger.info('the model has been saved by repository')
            self.ffmpeg_reader.read()
        except Exception as e:
            logger.error(f'an error occurred while starting FFmpeg direct read sub-process, err: {e}')
        finally:
            self.ffmpeg_reader.close()
            logger.info('FFmpeg direct read streaming subprocess has been terminated')
