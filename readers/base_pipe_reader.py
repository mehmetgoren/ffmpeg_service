import base64
import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from io import BytesIO

import ffmpeg
import numpy as np
import requests
from PIL import Image

from common.event_bus.event_bus import EventBus
from common.utilities import logger
from utils.json_serializer import serialize_json_dic
from utils.utils import start_thread


class PushMethod(IntEnum):
    REDIS_PUBSUB = 0
    REST_API = 1


class PipeReaderOptions:
    id: str = ''
    name: str = ''
    method: PushMethod = PushMethod.REDIS_PUBSUB
    pubsub_channel: str = 'read_service'
    api_address: str = 'http://localhost:2072/ffmpegreader'
    frame_rate: int = 1
    address: str = ''
    width: int = 0
    height: int = 0
    ai_clip_enabled: bool = False


class BasePipeReader(ABC):
    def __init__(self, options: PipeReaderOptions):
        self.options: PipeReaderOptions = options
        self.event_bus = EventBus(options.pubsub_channel) if self.options.method == PushMethod.REDIS_PUBSUB else None
        self.has_external_scale = options.width > 0 and options.height > 0
        if not self.has_external_scale:
            probe = ffmpeg.probe(options.address)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            options.width = int(video_stream['width'])
            options.height = int(video_stream['height'])
            self.stream_fps = video_stream['r_frame_rate'].split('/')
        else:
            self.stream_fps = 0
        self.cl_channels = 3
        logger.info(f'camera ({options.id}) stream fps: {self.stream_fps}')

        self.packet_size = options.width * options.height * self.cl_channels
        self.process = self._create_process(options)

    @abstractmethod
    def _create_process(self, options: PipeReaderOptions) -> any:
        raise NotImplementedError('BaseReader._create_process() must be implemented')

    @abstractmethod
    def is_closed(self) -> any:
        raise NotImplementedError('BaseReader.is_closed() must be implemented')

    @abstractmethod
    def close(self) -> any:
        raise NotImplementedError('BaseReader.close() must be implemented')

    @abstractmethod
    def read(self) -> any:
        raise NotImplementedError('BaseReader.read() must be implemented')

    @abstractmethod
    def get_img(self) -> np.array:
        raise NotImplementedError('BaseReader.get_img() must be implemented')

    @staticmethod
    def __create_base64_img(numpy_img: np.array) -> str:
        img = Image.fromarray(numpy_img)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def send(self, img_data):
        img_str = self.__create_base64_img(img_data)
        dic = {'name': self.options.name, 'img': img_str, 'source': self.options.id, 'ai_clip_enabled': self.options.ai_clip_enabled}
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

            start_thread(_post, [])
