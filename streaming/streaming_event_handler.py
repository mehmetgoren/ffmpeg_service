import json
import time
from threading import Thread

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
# from data.events import StreamingStartedEvent
from streaming.hls_streaming import start_streaming


class StreamingEventHandler(EventHandler):
    def __init__(self):
        self.encoding = 'utf-8'
        # this one is for response to the mngr
        self.event_bus = EventBus('streaming_response')

    def handle(self, dic: dict):
        if dic is None or dic['type'] != 'message':
            return

        th = Thread(target=self.__handle, args=[dic])
        th.daemon = True
        th.start()
        time.sleep(10)

        data: bytes = dic['data']
        self.event_bus.publish(data.decode(self.encoding))

    def __handle(self, dic: dict):
        data: bytes = dic['data']
        dic = json.loads(data.decode(self.encoding))
        start_streaming(dic['rtsp_address'], dic['folder_path'])
