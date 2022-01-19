import asyncio
import os.path
import time
from threading import Thread

from common.utilities import logger
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler
from streaming.hls_streaming import start_streaming, start_streaming_async


class StartStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'start_streaming_response')
        # todo: move to ml_config
        self.use_async = False
        logger.info('StartStreamingEventHandler initialized')

    def handle(self, dic: dict):
        logger.info('StartStreamingEventHandler handle called')
        is_valid_msg, prev, model, json_str = self.parse_message(dic)
        if not is_valid_msg:
            return
        if prev is None:
            self.start_streaming(model)
        self.event_bus.publish(json_str)

    def start_streaming(self, model: StreamingModel):
        th = Thread(target=self.__handle, args=[model])
        th.daemon = True
        th.start()
        # todo: move to ml-config
        while 1:
            if os.path.exists(model.output_file):
                logger.info('Streaming file created')
                break
            time.sleep(1)

    def __handle(self, model: StreamingModel):
        if self.use_async:
            asyncio.run(start_streaming_async(model, self.streaming_repository.get_connection()))
        else:
            start_streaming(model, self.streaming_repository.get_connection())
