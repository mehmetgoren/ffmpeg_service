from common.data.base_repository import is_message_invalid
from common.data.source_repository import SourceRepository
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from stream.start_stream_event_handler import StartStreamEventHandler
from stream.stop_stream_event_handler import StopStreamEventHandler
from stream.stream_repository import StreamRepository


class RestartStreamEventHandler(EventHandler):
    def __init__(self, source_repository: SourceRepository, stream_repository: StreamRepository):
        self.stop_stream_event_handler = StopStreamEventHandler(stream_repository)
        self.start_stream_event_handler = StartStreamEventHandler(source_repository, stream_repository)
        logger.info('RestartStreamEventHandler initialized')

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        if is_message_invalid(dic):
            return
        logger.info('RestartStreamEventHandler handle called')
        self.stop_stream_event_handler.handle(dic)
        self.start_stream_event_handler.handle(dic)
