import json
import time
from threading import Thread

from redis.client import Redis

from common.data.service_repository import ServiceRepository
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
# from data.events import StreamingStartedEvent
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository
from streaming.hls_streaming import start_streaming


class StartStreamingEventHandler(EventHandler):
    def __init__(self, connection: Redis):
        self.encoding = 'utf-8'
        # this one is for response to the mngr
        # source ve streming leri gelen parametreye göre sorgulamak ve eşleştirip start veya stop yapmak için kullanmamzı gerek
        self.event_bus = EventBus('start_streaming_response')
        self.connection = connection
        self.streaming_repository = StreamingRepository(connection)

    def handle(self, dic: dict):
        if dic is None or dic['type'] != 'message':
            return

        # ffmepg pid' e göre yaşayıp yaşamadığını kontyrol et.
        data: bytes = dic['data']
        json_str = data.decode(self.encoding)
        fixed_dic = json.loads(json_str)
        prev = self.streaming_repository.get(fixed_dic['name'])

        if prev is None:
            th = Thread(target=self.__handle, args=[dic])
            th.daemon = True
            th.start()
            time.sleep(10)

        self.event_bus.publish(json_str)

    def __handle(self, dic: dict):
        data: bytes = dic['data']
        dic = json.loads(data.decode(self.encoding))
        model = StreamingModel().map_from(dic)
        start_streaming(model, self.connection)
