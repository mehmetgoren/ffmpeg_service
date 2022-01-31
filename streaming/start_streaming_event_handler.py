import os
import os.path
import time
import subprocess
from typing import List
from threading import Thread

from command_builder import CommandBuilder, get_hls_output_path
from common.data.source_repository import SourceRepository
from common.utilities import logger
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

    def handle(self, dic: dict):
        is_valid_msg, prev_streaming_model, source_model, _ = self.parse_message(dic)
        if not is_valid_msg:
            return
        logger.info('StartHlsStreamingEventHandler handle called')
        if prev_streaming_model is None:
            if source_model.stream_type == StreamType.HLS:
                concrete = StartHlsStreamingEventHandler(self)
            elif source_model.stream_type == StreamType.FLV:
                concrete = StartFlvStreamingHandler(self)
            else:
                raise NotImplementedError('fuck you bitchi this one hasnt been implemented yet')

            streaming_model = StreamingModel().map_from_source(source_model)
            concrete.set_values(streaming_model)
            th = Thread(target=self.__start_ffmpeg_process, args=[source_model, streaming_model])
            th.daemon = True
            th.start()
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
        try:
            logger.info('streaming subprocess has been opened')
            p = subprocess.Popen(args)
            streaming_model.pid = p.pid
            streaming_model.args = ' '.join(args)
            self.streaming_repository.update(streaming_model, ['pid', 'args'])
            logger.info('the model has been saved by repository')
            p.wait()
        except Exception as e:
            logger.error(f'an error occurred while starting FFmpeg sub-process, err: {e}')
        finally:
            if p is not None:
                p.terminate()
            logger.info('streaming subprocess has been terminated')


class StartHlsStreamingEventHandler:
    def __init__(self, proxy: StartStreamingEventHandler):
        self.proxy = proxy

    def set_values(self, streaming_model: StreamingModel):
        self.proxy.delete_pref_streaming_files(streaming_model.id)
        streaming_model.hls_output_path = get_hls_output_path(streaming_model.id)

    @staticmethod
    def wait_for(streaming_model: StreamingModel):
        # todo: need a timeout to cancel the infinite operation here.
        while 1:
            if os.path.exists(streaming_model.hls_output_path):
                logger.info('Streaming file created')
                break
            time.sleep(1)


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
