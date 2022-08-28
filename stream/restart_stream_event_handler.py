import time

from common.data.redis_mapper import RedisMapper
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

    def handle(self, dic: dict):
        if RedisMapper.is_pubsub_message_invalid(dic):
            return
        logger.info('RestartStreamEventHandler handle called')

        try:
            self.stop_stream_event_handler.handle(dic)
        except BaseException as ex:
            logger.error(f'an error occurred while stopping a stream bu restart stream event handler, ex: {ex}')
        finally:
            time.sleep(3.)
            try:
                self.start_stream_event_handler.handle(dic)
            except BaseException as ex:
                logger.error(f'an error occurred while starting a stream bu restart stream event handler, ex: {ex}')
