import asyncio
import base64
import json
from datetime import datetime
from enum import IntEnum
from io import BytesIO
from threading import Thread
import requests

from common.event_bus.event_bus import EventBus
from common.utilities import logger


class PushMethod(IntEnum):
    REDIS_PUBSUB = 0
    REST_API = 1


class DiskImageReaderOptions:
    id: str = ''
    name: str = ''
    method: PushMethod = PushMethod.REST_API
    pubsub_channel: str = 'read_service'
    api_address: str = 'http://localhost:2072/ffmpegreader'
    frame_rate: int = 1
    image_path: str = ''


class DiskImageReader:
    def __init__(self, options: DiskImageReaderOptions):
        self.options = options
        self.closed = False
        self.event_bus = EventBus(options.pubsub_channel)

    def __send(self, dic: dict):
        # noinspection DuplicatedCode
        if self.options.method == PushMethod.REDIS_PUBSUB:
            def _pub():
                self.event_bus.publish(json.dumps(dic, ensure_ascii=False, indent=4))
                logger.info(
                    f'camera ({self.options.name}) -> an image has been send to broker by Redis PubSub at {datetime.now()}')

            fn = _pub
        else:
            def _post():
                data = json.dumps(dic).encode("utf-8")
                requests.post(self.options.api_address, data=data)
                logger.info(
                    f'camera ({self.options.name}) -> an image has been send to broker by rest api at {datetime.now()}')

            fn = _post
        th = Thread(target=fn)
        th.daemon = True
        th.start()

    async def __read(self):
        img_path, frame_rate = self.options.image_path, self.options.frame_rate
        self.closed = False
        while not self.closed:
            try:
                with open(img_path, 'rb') as fh:
                    buffered = BytesIO(fh.read())
                img_str = base64.b64encode(buffered.getvalue()).decode()
                dic = {'name': self.options.name, 'img': img_str, 'source': self.options.id}
                self.__send(dic)
                await asyncio.sleep(1. / frame_rate)
            except BaseException as e:
                logger.error(f'An error occurred during the reading image from disk, err: {e}')
                await asyncio.sleep(1)
        logger.info('Disk Image Service has been closed')

    def read_async(self):
        def fn():
            asyncio.run(self.__read())

        th = Thread(target=fn)
        th.daemon = True
        th.start()

    def close(self):
        self.closed = True
