from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import crate_redis_connection, RedisDb
from editor.editor_event_handler import EditorEventHandler
from streaming.restart_streaming_event_handler import RestartStreamingEventHandler
from streaming.start_streaming_event_handler import StartStreamingEventHandler
from streaming.stop_streaming_event_handler import StopStreamingEventHandler
from streaming.streaming_repository import StreamingRepository

__connection_source = crate_redis_connection(RedisDb.MAIN)
__source_repository = SourceRepository(__connection_source)
__streaming_repository = StreamingRepository(__connection_source)


def listen_editor_event():
    handler = EditorEventHandler()
    event_bus = EventBus('editor_request')
    event_bus.subscribe(handler)


def listen_start_streaming_event():
    handler = StartStreamingEventHandler(__source_repository, __streaming_repository)
    event_bus = EventBus('start_streaming_request')
    event_bus.subscribe(handler)


def listen_stop_streaming_event():
    handler = StopStreamingEventHandler(__streaming_repository)
    event_bus = EventBus('stop_streaming_request')
    event_bus.subscribe(handler)


def listen_restart_streaming_event():
    handler = RestartStreamingEventHandler(__source_repository, __streaming_repository)
    event_bus = EventBus('restart_streaming_request')
    event_bus.subscribe(handler)
