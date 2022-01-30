import base64
import json
from datetime import datetime
from enum import IntEnum

import ffmpeg
import numpy as np
import requests
from cv2 import cv2

from common.event_bus.event_bus import EventBus
from common.utilities import logger


class PushMethod(IntEnum):
    REDIS_PUBSUB = 0
    REST_API = 1


class PushMethodOptions:
    id: str = ''
    name: str = ''
    rtsp_address: str = ''
    frame_rate: int = 1
    method: PushMethod = PushMethod.REDIS_PUBSUB
    pubsub_channel: str = 'redis'
    api_address: str = 'localhost/ffmpegreader'
    width: int = -1
    height: int = -1


class FFmpegReader:
    def __init__(self, options: PushMethodOptions):
        self.options: PushMethodOptions = options
        self.event_bus = EventBus('read')
        has_external_scale = options.width > 0 or options.height > 0
        if has_external_scale:
            probe = ffmpeg.probe(options.rtsp_address)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            options.width = int(video_stream['width'])
            options.height = int(video_stream['height'])
            self.stream_fps = video_stream['r_frame_rate'].split('/')
        else:
            self.stream_fps = 0
        self.cl_channels = 3
        logger.info(f'camera ({options.id}) stream fps: {self.stream_fps}')

        self.packet_size = options.width * options.height * self.cl_channels
        stream = ffmpeg.input(options.rtsp_address)
        stream = ffmpeg.filter(stream, 'fps', fps=options.frame_rate, round='up')
        if has_external_scale:
            stream = ffmpeg.filter(stream, 'scale', options.width, options.height)
        stream = ffmpeg.output(stream, 'pipe:', format='rawvideo', pix_fmt='rgb24')
        self.process = ffmpeg.run_async(stream, pipe_stdout=True)

    def get_img(self) -> np.array:
        if self.process.poll() is not None:
            logger.error(f'camera ({self.options.name}) could not capture any frame and is now being released')
            return None
        packet = self.process.stdout.read(self.packet_size)
        numpy_img = np.frombuffer(packet, np.uint8).reshape([self.options.height, self.options.width, self.cl_channels])
        return numpy_img

    def is_closed(self) -> bool:
        return self.process.poll() is not None

    def close(self):
        self.process.terminate()

    def read(self):
        while not self.is_closed():
            np_img = self.get_img()
            if np_img is None:
                # _close_stream(source, name, 1)
                break
            dic = self.__create_model_dic(np_img)
            if self.options.method == PushMethod.REDIS_PUBSUB:
                self.event_bus.publish(json.dumps(dic, ensure_ascii=False, indent=4))
                logger.info(
                    f'camera ({self.options.name}) -> an image has been send to broker by Redis PubSub at {datetime.now()}')
            else:
                requests.post(self.options.api_address, data=dic)
                logger.info(
                    f'camera ({self.options.name}) -> an image has been send to broker by rest api at {datetime.now()}')

    def __create_model_dic(self, numpy_img: np.array):
        # To convert RGB to BGR
        # numpy_img = numpy_img[:, :, ::-1]
        img_str = base64.b64encode(cv2.imencode('.jpg', numpy_img)[1]).decode()
        return {'name': self.options.name, 'img': img_str, 'source': self.options.id}
