import os
import signal
from threading import Thread

import psutil

from common.data.heartbeat_repository import HeartbeatRepository
from common.data.service_repository import ServiceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb
from data.recording_repository import RecordingRepository
from recording.start_recording_event_handler import StartRecordingEventHandler
from utils.process_checker import ProcessChecker
from data.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler


def kill_all_ffmpeg_process():
    for proc in psutil.process_iter():
        if proc.name() == "ffmpeg":
            os.kill(proc.pid, signal.SIGKILL)


def register_ffmpeg_service():
    connection_service = crate_redis_connection(RedisDb.SERVICE, False)
    service_name = 'ffmpeg_service'
    heartbeat = HeartbeatRepository(connection_service, service_name)
    heartbeat.start()
    service_repository = ServiceRepository(connection_service)
    service_repository.add(service_name)


def start_listen_recording(recording_repository: RecordingRepository):
    def listen_recording(rep: RecordingRepository):
        handler = StartRecordingEventHandler(rep)
        event_bus = EventBus('start_recording_request')
        event_bus.subscribe(handler)

    th = Thread(target=listen_recording, args=[recording_repository])
    th.daemon = True
    th.start()


def listen_streaming(streaming_repository: StreamingRepository):
    handler = StartStreamingEventHandler(streaming_repository)
    event_bus = EventBus('start_streaming_request')
    event_bus.subscribe(handler)


def main():
    kill_all_ffmpeg_process()
    register_ffmpeg_service()

    connection_source = crate_redis_connection(RedisDb.SOURCES, False)
    streaming_repository = StreamingRepository(connection_source)
    streaming_repository.delete_by_namespace()
    recording_repository = RecordingRepository(connection_source)

    process_checker = ProcessChecker(streaming_repository, recording_repository)
    process_checker.start()

    start_listen_recording(recording_repository)

    logger.info('FFmpeg service has been started...')
    listen_streaming(streaming_repository)


if __name__ == '__main__':
    main()
