import asyncio
import datetime
import io
import math
import time
import subprocess
import numpy as np

import ffmpeg
from PIL import Image

import cv2

from common.config import Config
from common.data.source_model import AudioQuality
from common.utilities import logger


class FFmpegRtspSource:
    def __init__(self, name: str, rtsp_address: str):
        self.name = name
        self.rtsp_address = rtsp_address
        self.target_fps = 1
        probe = ffmpeg.probe(self.rtsp_address)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        self.width = 720  # int(video_stream['width'])
        self.height = 480  # int(video_stream['height'])
        self.stream_fps = video_stream['r_frame_rate'].split('/')
        self.stream_fps = float(self.stream_fps[0]) / float(self.stream_fps[1])
        logger.info(f'camera ({self.name}) stream fps: {self.stream_fps}')
        self.period = int(self.stream_fps / self.target_fps)
        logger.info(f'camera ({self.name}) period: {self.period}')

        self.cl_channels = 3  # RGB
        self.packet_size = self.width * self.height * self.cl_channels
        # process is a Popen(subprocess) object
        self.process = ffmpeg.input(rtsp_address).filter('fps', fps=1, round='up').filter('scale', self.width,
                                                                                          self.height).output('pipe:',
                                                                                                              format='rawvideo',
                                                                                                              pix_fmt='rgb24').run_async(
            pipe_stdout=True)

        # cmd = 'ffmpeg -progress pipe:5 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -i rtsp://Admin1:Admin1@192.168.0.15:554/live0 -strict -2 -an -c:v copy -preset ultrafast -f flv pipe:1'
        # cmd = 'ffmpeg -i rtsp://Admin1:Admin1@192.168.0.15/live0 -f rawvideo -pix_fmt rgb24 pipe:1'
        # cmd = 'ffmpeg -progress pipe:5 -use_wallclock_as_timestamps 1 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -rtsp_transport tcp -loglevel warning -i rtsp://Admin1:Admin1@192.168.0.15:554/live0 -strict -2 -an -c:v copy -preset ultrafast -f flv pipe:'
        # args = cmd.split(' ')
        # self.process = subprocess.Popen(args,  stdout=subprocess.PIPE)

    def recalculate_fixed_fps(self):
        # calculate real fps
        now = time.time()
        count = 0
        while 1:
            self.process.stdout.read(self.packet_size)
            count += 1
            if count >= 300:
                break
        end = time.time()
        self.stream_fps = count / (end - now)
        self.stream_fps = int(math.ceil(self.stream_fps))
        logger.info(f'camera ({self.name}) fixed stream fps: {self.stream_fps}')
        self.period = int(self.stream_fps / self.target_fps)
        logger.info(f'camera ({self.name}) fixed period: {self.period}')

    def set_fps(self, fps: int):
        self.target_fps = fps

    def get_img(self) -> np.array:
        if self.process.poll() is not None:
            logger.error(f'camera ({self.name}) could not capture any frame and is now being released')
            return None
        packet = self.process.stdout.read(self.packet_size)
        # numpy_img = np.frombuffer(packet, np.uint8).reshape([self.height, self.width, self.cl_channels])
        # To convert RGB to BGR
        # numpy_img = numpy_img[:, :, ::-1]
        # return numpy_img
        return packet

    def is_closed(self) -> bool:
        return self.process.poll() is not None

    def close(self):
        self.process.terminate()


def _read_ffmpeg():
    name, rtsp_address = 'eufy', 'rtsp://Admin1:Admin1@192.168.0.15/live0'
    source = FFmpegRtspSource(name, rtsp_address)
    # source.recalculate_fixed_fps()
    logger.info(f"ffmpeg capturing will be starting now, camera no:  {name}, url: {rtsp_address}")
    while not source.is_closed():
        img_bytes = source.get_img()
        if img_bytes is None:
            # _close_stream(source, name, 1)
            break
        try:
            if len(img_bytes) < 10000:
                continue
            numpy_img = np.frombuffer(img_bytes, np.uint8).reshape([source.height, source.width, source.cl_channels])
            # numpy_img = numpy_img[:, :, ::-1]
            # numpy_img = cv2.cvtColor(numpy_img, cv2.COLOR_RGB2BGR)
            # cv2.imshow("image", numpy_img)
            # cv2.waitKey(1)
            image = Image.fromarray(numpy_img)
            image.save('/mnt/sdc1/pics/' + str(datetime.datetime.now()) + ".jpg")
            print('publish ', str(numpy_img.shape) + ' at: ' + str(datetime.datetime.now()))
        except BaseException as e:
            print(e)
        # _publish(img, name, identifier)


# _read_ffmpeg()

# x = AudioQuality.Auto
# b = False
# print(isinstance(b, bool))
# print(isinstance(b, int))
# print(isinstance(x, int))

config = Config.create()
# config.handler.read_service_overlay = True
# config.handler.show_image_caption = True
# config.handler.show_image_fullscreen = True
# config.handler.show_image_wait_key = -1000000
# config.heartbeat.interval = -100000
# config.redis.host = 'fcuk'
# config.redis.port = -100000
# config.jetson.model_name = 'fcuk'
# config.jetson.threshold = -100000
# config.jetson.white_list = [-100000]
# config.torch.model_repo_name = 'fcuk'
# config.torch.model_name = 'fcuk'
# config.torch.threshold = -100000
# config.torch.white_list = [-100000]
# config.once_detector.imagehash_threshold = -100000
# config.once_detector.psnr_threshold = -100000
# config.once_detector.ssim_threshold = -100000
# config.source_hub.fps = -100000
# config.source_hub.source_hub_buffer_size = -100000
# config.source_hub.max_retry = -100000
# config.source_hub.max_retry_in = -100000
# config.source_hub.kill_starter_proc = True

config.save()

print(config.to_json())
