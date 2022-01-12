import os
import signal
import psutil

from common.data.heartbeat_repository import HeartbeatRepository
from common.data.service_repository import ServiceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb
from utils.process_checker import ProcessChecker
from data.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler


def kill_all_ffmpeg_process():
    for proc in psutil.process_iter():
        if proc.name() == "ffmpeg":
            os.kill(proc.pid, signal.SIGKILL)


def main():
    kill_all_ffmpeg_process()

    connection_service = crate_redis_connection(RedisDb.SERVICE, False)
    service_name = 'ffmpeg_service'
    heartbeat = HeartbeatRepository(connection_service, service_name)
    heartbeat.start()
    service_repository = ServiceRepository(connection_service)
    service_repository.add(service_name)

    connection_source = crate_redis_connection(RedisDb.SOURCES, False)
    streaming_repository = StreamingRepository(connection_source)
    streaming_repository.delete_by_namespace()

    process_checker = ProcessChecker(streaming_repository)
    process_checker.start()

    handler = StartStreamingEventHandler(streaming_repository)
    event_bus = EventBus('start_streaming_request')
    logger.info('FFmpeg service has been started...')
    event_bus.subscribe(handler)


if __name__ == '__main__':
    main()
