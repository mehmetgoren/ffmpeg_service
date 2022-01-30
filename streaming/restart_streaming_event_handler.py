from common.data.base_repository import is_message_invalid
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from streaming.start_streaming_event_handler import StartStreamingEventHandler
from streaming.stop_streaming_event_handler import StopStreamingEventHandler
from streaming.streaming_repository import StreamingRepository


class RestartStreamingEventHandler(EventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        self.stop_streaming_event_handler = StopStreamingEventHandler(streaming_repository)
        self.start_streaming_event_handler = StartStreamingEventHandler(streaming_repository)
        logger.info('RestartStreamingEventHandler initialized')

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        if is_message_invalid(dic):
            return
        logger.info('RestartStreamingEventHandler handle called')
        self.stop_streaming_event_handler.handle(dic)
        self.start_streaming_event_handler.handle(dic)
