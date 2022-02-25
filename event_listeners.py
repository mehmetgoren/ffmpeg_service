from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import crate_redis_connection, RedisDb
from editor.editor_event_handler import EditorEventHandler
from stream.restart_stream_event_handler import RestartStreamEventHandler
from stream.start_stream_event_handler import StartStreamEventHandler
from stream.stop_stream_event_handler import StopStreamEventHandler
from stream.stream_repository import StreamRepository

__connection_source = crate_redis_connection(RedisDb.MAIN)
__source_repository = SourceRepository(__connection_source)
__stream_repository = StreamRepository(__connection_source)


def listen_editor_event():
    handler = EditorEventHandler()
    event_bus = EventBus('editor_request')
    event_bus.subscribe_async(handler)


def listen_start_stream_event():
    handler = StartStreamEventHandler(__source_repository, __stream_repository)
    event_bus = EventBus('start_stream_request')
    event_bus.subscribe_async(handler)


def listen_stop_stream_event():
    handler = StopStreamEventHandler(__stream_repository)
    event_bus = EventBus('stop_stream_request')
    event_bus.subscribe_async(handler)


def listen_restart_stream_event():
    handler = RestartStreamEventHandler(__source_repository, __stream_repository)
    event_bus = EventBus('restart_stream_request')
    event_bus.subscribe_async(handler)
