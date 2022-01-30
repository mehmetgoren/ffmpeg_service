import asyncio
import os
import signal
from threading import Thread

import psutil

from common.data.heartbeat_repository import HeartbeatRepository
from common.data.service_repository import ServiceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb
from editor.editor_event_handler import EditorEventHandler
from streaming.restart_streaming_event_handler import RestartStreamingEventHandler
from streaming.stop_streaming_event_handler import StopStreamingEventHandler
# from utils.process_checker import ProcessChecker
from streaming.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler


def kill_all_ffmpeg_process():
    for proc in psutil.process_iter():
        if proc.name() == "ffmpeg":
            os.kill(proc.pid, signal.SIGKILL)


def register_ffmpeg_service():
    connection_service = crate_redis_connection(RedisDb.SERVICE)
    service_name = 'ffmpeg_service'
    heartbeat = HeartbeatRepository(connection_service, service_name)
    heartbeat.start()
    service_repository = ServiceRepository(connection_service)
    service_repository.add(service_name)


# todo: move to stable version powered by Redis-RQ
def listen_editor():
    def start_editor_event():
        handler = EditorEventHandler()
        event_bus = EventBus('editor_request')
        try:
            event_bus.subscribe(handler)
        except BaseException as e:
            logger.error(f'Error while starting editor event handler: {e}')
        finally:
            listen_editor()  # start again, otherwise event-listening will stop

    th = Thread(target=start_editor_event)
    th.daemon = True
    th.start()


# todo: move to stable version powered by Redis-RQ
def listen_start_streaming(streaming_repository: StreamingRepository):
    def start_streaming(rep: StreamingRepository):
        handler = StartStreamingEventHandler(rep)
        event_bus = EventBus('start_streaming_request')
        event_bus.subscribe(handler)

    th = Thread(target=start_streaming, args=[streaming_repository])
    th.daemon = True
    th.start()


# todo: move to stable version powered by Redis-RQ
def listen_stop_streaming(streaming_repository: StreamingRepository):
    def stop_streaming(rep: StreamingRepository):
        handler = StopStreamingEventHandler(rep)
        event_bus = EventBus('stop_streaming_request')
        event_bus.subscribe(handler)

    th = Thread(target=stop_streaming, args=[streaming_repository])
    th.daemon = True
    th.start()


# todo: move to stable version powered by Redis-RQ
def listen_restart_streaming(streaming_repository: StreamingRepository):
    def restart_streaming(rep: StreamingRepository):
        handler = RestartStreamingEventHandler(rep)
        event_bus = EventBus('restart_streaming_request')
        event_bus.subscribe(handler)

    th = Thread(target=restart_streaming, args=[streaming_repository])
    th.daemon = True
    th.start()


def main():
    # kill_all_ffmpeg_process()
    register_ffmpeg_service()

    connection_source = crate_redis_connection(RedisDb.SOURCES)
    streaming_repository = StreamingRepository(connection_source)
    # streaming_repository.delete_by_namespace()
    # source_repository = SourceRepository(connection_source)

    # process_checker = ProcessChecker(streaming_repository)
    # process_checker.start()

    listen_editor()
    listen_start_streaming(streaming_repository)
    listen_stop_streaming(streaming_repository)
    listen_restart_streaming(streaming_repository)

    logger.info('FFmpeg service has been started...')
    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == '__main__':
    main()
