import asyncio
import json
import time
from threading import Thread

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository
from streaming.hls_streaming import start_streaming, start_streaming_async


class StartStreamingEventHandler(EventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        self.encoding = 'utf-8'
        self.event_bus = EventBus('start_streaming_response')
        self.streaming_repository = streaming_repository
        # todo: move to ml_config
        self.use_async = False

    def handle(self, dic: dict):
        if dic is None or dic['type'] != 'message':
            return

        data: bytes = dic['data']
        json_str = data.decode(self.encoding)
        fixed_dic = json.loads(json_str)
        model = StreamingModel().map_from(fixed_dic)
        prev = self.streaming_repository.get(model.id)

        if prev is None:
            self.start_streaming(model)

        self.event_bus.publish(json_str)

    def start_streaming(self, model: StreamingModel):
        th = Thread(target=self.__handle, args=[model])
        th.daemon = True
        th.start()
        # todo: move to ml-config
        time.sleep(10)

    def __handle(self, model: StreamingModel):
        if self.use_async:
            asyncio.run(start_streaming_async(model, self.streaming_repository.get_connection()))
        else:
            start_streaming(model, self.streaming_repository.get_connection())
