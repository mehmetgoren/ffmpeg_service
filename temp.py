import base64
import datetime
import glob
import os
import subprocess
from io import BytesIO

import docker
import numpy as np
from PIL import Image

from common.config import Config
from common.data.rtsp_template_model import RtspTemplateModel
from common.data.rtsp_template_repository import RtspTemplateRepository
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import crate_redis_connection, RedisDb
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions, PushMethod
from stream.stream_repository import StreamRepository
from utils.json_serializer import serialize_json_dic

__event_bus = EventBus('read_service')


def _create_base64_img(numpy_img: np.array) -> str:
    img = Image.fromarray(numpy_img)
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def _send(img_data):
    img_str = _create_base64_img(img_data)
    dic = {'name': 'eufy', 'img': img_str, 'source': 'xxx_test'}
    __event_bus.publish_async(serialize_json_dic(dic))


def pipe_test():
    args = 'ffmpeg -i rtmp://127.0.0.1:9010/live/rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk -filter_complex [0]fps=fps=1:round=up[s0];[s0]scale=1280:720[s1] -map [s1] -f rawvideo -pix_fmt rgb24 pipe:'
    args = args.split(' ')
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    width, height, cl_channels = 1280, 720, 3
    packet_size = width * height * cl_channels
    while True:
        # line = proc.stdout.readline()
        packet = proc.stdout.read(packet_size)
        numpy_img = np.frombuffer(packet, np.uint8).reshape([height, width, cl_channels])
        _send(numpy_img)
        print(numpy_img.shape, ' at ', str(datetime.datetime.now()))
    # p.wait()


# pipe_test()

def redis_bench():
    conn = crate_redis_connection(RedisDb.MAIN)
    rep = SourceRepository(conn)
    start = datetime.datetime.now()
    length = 10000
    for j in range(length):
        _ = rep.get('3xzdeqtd3p6')
        # print(source.name)
    end = datetime.datetime.now()
    print(f'result: {(end - start).microseconds}')


# redis_bench()


def set_test():
    arr = [j for j in range(1000)]

    start = datetime.datetime.now()
    length = 1000000
    for j in range(length):
        _ = j in arr
        # print(source.name)
    end = datetime.datetime.now()
    print(f'arr result: {(end - start).microseconds}')

    sett = {j for j in range(1000)}
    start = datetime.datetime.now()
    for j in range(length):
        _ = j in sett
        # print(source.name)
    end = datetime.datetime.now()
    print(f'set result: {(end - start).microseconds}')

    dic = {j: True for j in range(1000)}
    start = datetime.datetime.now()
    for j in range(length):
        _ = j in dic
        # print(source.name)
    end = datetime.datetime.now()
    print(f'dict result: {(end - start).microseconds}')


# set_test()


def rc_test():
    conn = crate_redis_connection(RedisDb.MAIN)
    rep = StreamRepository(conn)
    streams = rep.get_all()
    for stream in streams:
        if stream.record_enabled:
            list_of_files = glob.glob(f'{stream.record_output_folder_path}/*')  # * means all if it needs specific format then *.csv
            latest_file = max(list_of_files, key=os.path.getctime)
            size = os.path.getsize(latest_file)
            print(f'{latest_file} - {size}')
            # print(os.stat(stream.record_output_folder_path))


# rc_test()


def read_test():
    opts = FFmpegReaderOptions()
    opts.id = 'ayufisdvbuw'
    opts.name = 'eufy'
    opts.address = 'rtsp://Admin1:Admin1@192.168.1.183/live0'
    opts.method = PushMethod.REDIS_PUBSUB
    opts.frame_rate = 1
    opts.width = 640
    opts.height = 360
    opts.pubsub_channel = 'read_service'
    reader = FFmpegReader(opts)
    reader.read()


def docker_tests():
    client = docker.from_env()
    filters: dict = {'name': 'livego_gokalp222'}
    container = client.containers.list(filters=filters)
    print(container[0].name)


docker_tests()


def config_save():
    config = Config.create()

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
