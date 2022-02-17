# import asyncio
# import datetime
# import io
# import math
# import time
# import subprocess
# from threading import Thread
# 
# import numpy as np
#
# import ffmpeg
# import psutil
# from PIL import Image
#
# import cv2
# import json
# import subprocess
from enum import Enum

from common.config import Config
from common.data.rtsp_template_model import RtspTemplateModel
from common.data.rtsp_template_repository import RtspTemplateRepository
# from common.data.source_repository import SourceRepository
from common.utilities import crate_redis_connection, RedisDb, logger
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions, PushMethod, ImageConverterType
# from rtmp.rtmp_models import RtmpServerImages
#
# print(str(RtmpServerImages.OSSRS.value))
# print(RtmpServerImages.LIVEGO)
# print(RtmpServerImages.NMS)
from sustain.kill_prevs import remove_all_prev_rtmp_containers

remove_all_prev_rtmp_containers(crate_redis_connection(RedisDb.MAIN))

# import numpy as np

# args = 'ffmpeg -progress pipe:5 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -loglevel warning -i rtsp://admin:admin123456@192.168.0.19:8554/profile0 -strict -2 -c:a copy -c:v copy -tune zerolatency -g 1 -f hls -hls_time 2 -hls_list_size 3 -start_number 0 -hls_allow_cache 0 -hls_flags +delete_segments+omit_endlist /mnt/sde1/live/m7kdwupjdvw/stream.m3u8 -acodec copy -vcodec copy -strict -2 -movflags +faststart -f segment -segment_atclocktime 1 -reset_timestamps 1 -strftime 1 -segment_list pipe:8 -segment_time 60 /mnt/sde1/playback/m7kdwupjdvw/%Y-%m-%d-%H-%M-%S.mp4'
# # args = 'ffmpeg -progress pipe:5 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -loglevel warning -i rtsp://admin:admin123456@192.168.0.19:8554/profile0 -strict -2 -c:a copy -c:v copy -tune zerolatency -g 1 -f hls -hls_time 2 -hls_list_size 3 -start_number 0 -hls_allow_cache 0 -hls_flags +delete_segments+omit_endlist /mnt/sde1/live/m7kdwupjdvw/stream.m3u8'
# # args = 'ffprobe -i rtsp://admin:admin123456@192.168.0.19:8554/profile0'
# args = args.split(' ')
# p = subprocess.Popen(args, stderr=subprocess.PIPE)  # stdout=subprocess.PIPE
# p.wait()
# if p.stderr is not None:
#     try:
#         data: bytes = p.stderr.read()
#         msg: str = data.decode('utf-8')
#         print(msg)
#     except BaseException as e:
#         logger.error(f'an error occurred during the getting message from STDERR, err: {e}')
# code = p.returncode
# print(code)


def read_test():
    opts = FFmpegReaderOptions()
    opts.id = 'ayufisdvbuw'
    opts.name = 'eufy'
    opts.rtsp_address = 'rtsp://Admin1:Admin1@192.168.1.183/live0'
    opts.method = PushMethod.REDIS_PUBSUB
    opts.frame_rate = 1
    opts.width = 640
    opts.height = 360
    opts.pubsub_channel = 'read_service'
    opts.image_converter_type = ImageConverterType.PIL
    reader = FFmpegReader(opts)
    reader.read()


# class FFmpegRtspSource:
#     def __init__(self, name: str, rtsp_address: str):
#         self.name = name
#         self.rtsp_address = rtsp_address
#         self.target_fps = 1
#         probe = ffmpeg.probe(self.rtsp_address)
#         video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
#         self.width = 720  # int(video_stream['width'])
#         self.height = 480  # int(video_stream['height'])
#         self.stream_fps = video_stream['r_frame_rate'].split('/')
#         self.stream_fps = float(self.stream_fps[0]) / float(self.stream_fps[1])
#         logger.info(f'camera ({self.name}) stream fps: {self.stream_fps}')
#         self.period = int(self.stream_fps / self.target_fps)
#         logger.info(f'camera ({self.name}) period: {self.period}')
#
#         self.cl_channels = 3  # RGB
#         self.packet_size = self.width * self.height * self.cl_channels
#         # process is a Popen(subprocess) object
#         self.process = ffmpeg.input(rtsp_address).filter('fps', fps=1, round='up').filter('scale', self.width,
#                                                                                           self.height).output('pipe:',
#                                                                                                               format='rawvideo',
#                                                                                                               pix_fmt='rgb24').run_async(
#             pipe_stdout=True)
#
#         # cmd = 'ffmpeg -progress pipe:5 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -i rtsp://Admin1:Admin1@192.168.0.15:554/live0 -strict -2 -an -c:v copy -preset ultrafast -f flv pipe:1'
#         # cmd = 'ffmpeg -i rtsp://Admin1:Admin1@192.168.0.15/live0 -f rawvideo -pix_fmt rgb24 pipe:1'
#         # cmd = 'ffmpeg -progress pipe:5 -use_wallclock_as_timestamps 1 -analyzeduration 1000000 -probesize 1000000 -fflags +igndts -rtsp_transport tcp -loglevel warning -i rtsp://Admin1:Admin1@192.168.0.15:554/live0 -strict -2 -an -c:v copy -preset ultrafast -f flv pipe:'
#         # args = cmd.split(' ')
#         # self.process = subprocess.Popen(args,  stdout=subprocess.PIPE)
#
#     def recalculate_fixed_fps(self):
#         # calculate real fps
#         now = time.time()
#         count = 0
#         while 1:
#             self.process.stdout.read(self.packet_size)
#             count += 1
#             if count >= 300:
#                 break
#         end = time.time()
#         self.stream_fps = count / (end - now)
#         self.stream_fps = int(math.ceil(self.stream_fps))
#         logger.info(f'camera ({self.name}) fixed stream fps: {self.stream_fps}')
#         self.period = int(self.stream_fps / self.target_fps)
#         logger.info(f'camera ({self.name}) fixed period: {self.period}')
#
#     def set_fps(self, fps: int):
#         self.target_fps = fps
#
#     def get_img(self) -> np.array:
#         if self.process.poll() is not None:
#             logger.error(f'camera ({self.name}) could not capture any frame and is now being released')
#             return None
#         packet = self.process.stdout.read(self.packet_size)
#         # numpy_img = np.frombuffer(packet, np.uint8).reshape([self.height, self.width, self.cl_channels])
#         # To convert RGB to BGR
#         # numpy_img = numpy_img[:, :, ::-1]
#         # return numpy_img
#         return packet
#
#     def is_closed(self) -> bool:
#         return self.process.poll() is not None
#
#     def close(self):
#         self.process.terminate()
#
#
# def _read_ffmpeg():
#     name, rtsp_address = 'eufy', 'rtsp://Admin1:Admin1@192.168.0.15/live0'
#     source = FFmpegRtspSource(name, rtsp_address)
#     # source.recalculate_fixed_fps()
#     logger.info(f"ffmpeg capturing will be starting now, camera no:  {name}, url: {rtsp_address}")
#     while not source.is_closed():
#         img_bytes = source.get_img()
#         if img_bytes is None:
#             # _close_stream(source, name, 1)
#             break
#         try:
#             if len(img_bytes) < 10000:
#                 continue
#             numpy_img = np.frombuffer(img_bytes, np.uint8).reshape([source.height, source.width, source.cl_channels])
#             # numpy_img = numpy_img[:, :, ::-1]
#             # numpy_img = cv2.cvtColor(numpy_img, cv2.COLOR_RGB2BGR)
#             # cv2.imshow("image", numpy_img)
#             # cv2.waitKey(1)
#             image = Image.fromarray(numpy_img)
#             image.save('/mnt/sdc1/pics/' + str(datetime.datetime.now()) + ".jpg")
#             print('publish ', str(numpy_img.shape) + ' at: ' + str(datetime.datetime.now()))
#         except BaseException as e:
#             print(e)
# _publish(img, name, identifier)


# _read_ffmpeg()

def config_save():
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


# config_save()


def add_rtsp_templates():
    connection = crate_redis_connection(RedisDb.MAIN)
    rep = RtspTemplateRepository(connection)

    template = RtspTemplateModel()
    template.name = "Dahua DVR"
    template.brand = "Dahua"
    template.default_user = 'admin'
    template.default_port = '554'
    template.address = f'rtsp://{template.default_user}:' + '{password}@{ip}:{port}'
    template.route = '/cam/realmonitor?channel={camera_no}&subtype={subtype}'
    template.templates = '{password},{ip},{port},{camera_no},{subtype}'
    rep.add(template)

    template = RtspTemplateModel()
    template.name = 'ConcordIpc'
    template.brand = 'Concord'
    template.default_user = 'admin'
    template.default_password = 'admin123456'
    template.default_port = '8554'
    template.address = f'rtsp://{template.default_user}:{template.default_password}' + '@{ip}:' + f'{template.default_port}'
    template.route = '/profile0'
    template.templates = '{ip}'
    rep.add(template)

    template = RtspTemplateModel()
    template.name = 'Anker Eufy Security 2K'
    template.brand = 'Anker'
    template.address = 'rtsp://{user}:{password}@{ip}'
    template.route = '/live0'
    template.templates = '{user},{password},{ip}'
    rep.add(template)

    template = RtspTemplateModel()
    template.name = 'TP Link Tapo C200 1080P'
    template.brand = 'TP Link'
    template.default_port = '554'
    template.address = 'rtsp://{user}:{password}@{ip}:' + f'{template.default_port}'
    template.route = 'stream1'
    template.templates = '{user},{password},{ip}'
    rep.add(template)

# add_rtsp_templates()
