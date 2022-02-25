import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from threading import Thread
import requests

from common.event_bus.event_bus import EventBus
from common.utilities import logger
from utils.json_serializer import serialize_json_dic


class PushMethod(IntEnum):
    REDIS_PUBSUB = 0
    REST_API = 1


class BaseReaderOptions:
    id: str = ''
    name: str = ''
    method: PushMethod = PushMethod.REDIS_PUBSUB
    pubsub_channel: str = 'read_service'
    api_address: str = 'http://localhost:2072/ffmpegreader'
    frame_rate: int = 1


class BaseReader(ABC):
    def __init__(self, options: BaseReaderOptions):
        self.options = options
        self.event_bus = EventBus(options.pubsub_channel) if self.options.method == PushMethod.REDIS_PUBSUB else None

    def _send(self, img_data):
        img_str = self._create_base64_img(img_data)
        dic = {'name': self.options.name, 'img': img_str, 'source': self.options.id}
        if self.options.method == PushMethod.REDIS_PUBSUB:
            self.event_bus.publish_async(serialize_json_dic(dic))
            logger.info(
                f'camera ({self.options.name}) -> an image has been send to broker by Redis PubSub at {datetime.now()}')
        else:
            def _post():
                data = json.dumps(dic).encode("utf-8")
                requests.post(self.options.api_address, data=data)
                logger.info(
                    f'camera ({self.options.name}) -> an image has been send to broker by rest api at {datetime.now()}')

            th = Thread(target=_post)
            th.daemon = True
            th.start()

    @abstractmethod
    def close(self):
        raise NotImplementedError('BaseReader.close')

    @abstractmethod
    def read(self):
        raise NotImplementedError('BaseReader.read')

    @abstractmethod
    def _create_base64_img(self, img_data) -> str:
        raise NotImplementedError('BaseReader._create_base64_img')
