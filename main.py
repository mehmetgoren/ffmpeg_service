import asyncio

from common.event_bus.event_bus import EventBus
from common.utilities import logger
from streaming.hls_streaming import start_streaming, start_streaming_async
from streaming.streaming_event_handler import StreamingEventHandler


def start():
    start_streaming('rtsp://Admin1:Admin1@192.168.0.15/live0',
                    '/mnt/super/ionix/node/mngr/static/live/stream.m3u8')


def start_async():
    asyncio.ensure_future(start_streaming_async('rtsp://Admin1:Admin1@192.168.0.15/live0',
                                                '/mnt/super/ionix/node/mngr/static/live/stream.m3u8'))


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()

    # start()
    # start_async()
    logger.info('FFmpeg service has been started...')
    handler = StreamingEventHandler()
    event_bus = EventBus('streaming_request')
    event_bus.subscribe(handler)

    # loop.run_forever()
    # loop.close()
