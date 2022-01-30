import os
import os.path
import time
import subprocess
from typing import List
from threading import Thread

from command_builder import CommandBuilder, get_hls_output_path
from common.utilities import logger
from streaming.req_resp import StartStreamingRequestEvent
from streaming.streaming_model import StreamingModel
from streaming.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler
from utils.json_serializer import serialize_json


class StartStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'start_streaming_response')
        logger.info('StartStreamingEventHandler initialized')

    def handle(self, dic: dict):
        logger.info('StartStreamingEventHandler handle called')
        is_valid_msg, prev_streaming_model, source_model, _ = self.parse_message(dic)
        if not is_valid_msg:
            return
        if prev_streaming_model is None:
            self._delete_pref_streaming_files(source_model.id)
            self._start_streaming(source_model)
            prev_streaming_model = self.streaming_repository.get(source_model.id)
        streaming_model_json = serialize_json(prev_streaming_model)
        self.event_bus.publish(streaming_model_json)

    def _start_streaming(self, request: StartStreamingRequestEvent):
        th = Thread(target=self._start_process, args=[request])
        th.daemon = True
        th.start()
        hls_output_file_path = get_hls_output_path(request.id)
        # todo: need a timeout to cancel  the infinite operation here.
        while 1:
            if os.path.exists(hls_output_file_path):
                logger.info('Streaming file created')
                break
            time.sleep(1)

    def _start_process(self, request: StartStreamingRequestEvent):
        logger.info('starting streaming')
        cmd_builder = CommandBuilder(request)
        args: List[str] = cmd_builder.build()

        p = subprocess.Popen(args)
        streaming_model = None
        try:
            streaming_model = StreamingModel().map_from_source(request)
            streaming_model.pid = p.pid
            streaming_model.args = ' '.join(args)
            streaming_model.hls_output_path = get_hls_output_path(streaming_model.id)
            self.streaming_repository.add(streaming_model)
            logger.info('the model has been saved by repository')
            logger.info('streaming subprocess has been opened')
            p.wait()
        except Exception as e:
            # if streaming_model is not None:
            #     self.streaming_repository.remove(streaming_model.id)
            logger.error(f'an error occurred while starting FFmpeg sub-process, err: {e}')
        finally:
            p.terminate()
            logger.info('streaming subprocess has been terminated')
