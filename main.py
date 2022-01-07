import asyncio

from common.data.heartbeat_repository import HeartbeatRepository
from common.data.service_repository import ServiceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb
# from streaming.hls_streaming import start_streaming, start_streaming_async
from streaming.start_streaming_event_handler import StartStreamingEventHandler

# def start():
#     start_streaming('rtsp://Admin1:Admin1@192.168.0.15/live0',
#                     '/mnt/super/ionix/node/mngr/static/live/stream.m3u8')
#
#
# def start_async():
#     asyncio.ensure_future(start_streaming_async('rtsp://Admin1:Admin1@192.168.0.15/live0',
#                                                 '/mnt/super/ionix/node/mngr/static/live/stream.m3u8'))


if __name__ == '__main__':
    connectionService = crate_redis_connection(RedisDb.SERVICE, False)
    service_name = 'ffmpeg_service'
    heartbeat = HeartbeatRepository(connectionService, service_name)
    heartbeat.start()
    service_repository = ServiceRepository(connectionService)
    service_repository.add(service_name)

    # start()
    # start_async()

    connectionSource = crate_redis_connection(RedisDb.SOURCES, False)
    handler = StartStreamingEventHandler(connectionSource)
    event_bus = EventBus('start_streaming_request')
    logger.info('FFmpeg service has been started...')
    event_bus.subscribe(handler)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
