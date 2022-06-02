import base64
from datetime import datetime
import glob
import os
import subprocess
from io import BytesIO
import os.path as path
import docker
import ffmpeg
import numpy as np
from PIL import Image

from common.config import Config
from common.data.rtsp_template_model import RtspTemplateModel
from common.data.rtsp_template_repository import RtspTemplateRepository
from common.data.source_model import RecordFileTypes
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import crate_redis_connection, RedisDb, logger
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions, PushMethod
from record.concat_demuxer import ConcatDemuxer
from record.video_file_indexer import VideoFileIndexer
from record.video_file_merger import VideoFileMerger
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from utils.dir import get_record_dir_by, get_sorted_valid_files
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
        print(numpy_img.shape, ' at ', str(datetime.now()))
    # p.wait()


# pipe_test()

def redis_bench():
    conn = crate_redis_connection(RedisDb.MAIN)
    rep = SourceRepository(conn)
    start = datetime.now()
    length = 10000
    for j in range(length):
        _ = rep.get('3xzdeqtd3p6')
        # print(source.name)
    end = datetime.now()
    print(f'result: {(end - start).microseconds}')


# redis_bench()


def set_test():
    arr = [j for j in range(1000)]

    start = datetime.now()
    length = 1000000
    for j in range(length):
        _ = j in arr
        # print(source.name)
    end = datetime.now()
    print(f'arr result: {(end - start).microseconds}')

    sett = {j for j in range(1000)}
    start = datetime.now()
    for j in range(length):
        _ = j in sett
        # print(source.name)
    end = datetime.now()
    print(f'set result: {(end - start).microseconds}')

    dic = {j: True for j in range(1000)}
    start = datetime.now()
    for j in range(length):
        _ = j in dic
        # print(source.name)
    end = datetime.now()
    print(f'dict result: {(end - start).microseconds}')


# set_test()


def rc_test():
    conn = crate_redis_connection(RedisDb.MAIN)
    rep = StreamRepository(conn)
    streams = rep.get_all()
    for stream in streams:
        if stream.record_enabled:
            dir_path = get_record_dir_by(stream.id)
            list_of_files = glob.glob(f'{dir_path}/*')  # * means all if it needs specific format then *.csv
            latest_file = max(list_of_files, key=os.path.getctime)
            size = os.path.getsize(latest_file)
            print(f'{latest_file} - {size}')
            # print(os.stat(dir_path))


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


# docker_tests()


def config_save():
    config = Config.create()

    config.save()

    print(config.to_json())


config_save()


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


def probe_bench():
    filename = '/home/gokalp/Documents/sill/temp/2022_04_14_18_55_30.mp4'
    # filename = '/home/gokalp/Documents/sill/temp/corrupted/2022_04_14_00_10_10.mp4'
    start = datetime.now()
    length = 100
    for j in range(length):
        try:
            _ = ffmpeg.probe(filename)
        except BaseException as ex:
            logger.error(f'{ex}')
    end = datetime.now()
    print(f'probe_bench result s: {(end - start).seconds}')
    print(f'probe_bench result ms: {(end - start).microseconds}')


# probe_bench()

def test_video_file_indexer():
    conn_main = crate_redis_connection(RedisDb.MAIN)
    stream_repository = StreamRepository(conn_main)
    source_id = 'e5dbkevdg6l'
    stream_model = StreamModel()
    stream_model.id = source_id
    stream_model.record_file_type = RecordFileTypes.MP4
    stream_repository.add(stream_model)
    vfi = VideoFileIndexer(stream_repository)
    vfi.move(source_id)


# test_video_file_indexer()


def test_concat_demuxer():
    conn_main = crate_redis_connection(RedisDb.MAIN)
    stream_repository = StreamRepository(conn_main)
    source_id = 'e5dbkevdg6l'
    stream_model = StreamModel()
    stream_model.id = source_id
    stream_repository.add(stream_model)
    cd = ConcatDemuxer(stream_repository)
    root_path = path.join(get_record_dir_by(source_id), '2022', '04', '18', '19')
    lds = os.listdir(root_path)
    filenames = []
    for ld in lds:
        filenames.append(path.join(root_path, ld))
    output = path.join(root_path, 'output.mp4')
    proc = cd.concatenate(source_id, filenames, output)
    proc.terminate()


# test_concat_demuxer()


def test_video_file_merger():
    conn_main = crate_redis_connection(RedisDb.MAIN)
    stream_repository = StreamRepository(conn_main)
    source_id = 'e5dbkevdg6l'
    vfm = VideoFileMerger(stream_repository)
    vfm.merge(source_id, '2022_04_18_19')


# test_video_file_merger()

# def concat_demuxer_test():
#     conn_main = crate_redis_connection(RedisDb.MAIN)
#     source_repository = SourceRepository(conn_main)
#     stream_repository = StreamRepository(conn_main)
#     cd = ConcatDemuxer(source_repository, stream_repository)
#     source_id = 'e5dbkevdg6l'
#     for j in range(1):
#         cd.concatenate(source_id)
#     # start = datetime.now()
#     # cd.concatenate()
#     # end = datetime.now()
#     # print(f'concat_demuxer_test result in sec      : {(end - start).seconds}')
#     # print(f'concat_demuxer_test result in micro-sec: {(end - start).microseconds}')


# #
# concat_demuxer_test()

def test_openalpr_local():
    client = docker.from_env()
    filters: dict = {'name': 'openalpr_local'}
    container = client.containers.list(filters)[0]
    res = None
    start = datetime.now()
    for j in range(25):
        res = container.exec_run('alpr -c eu tr4.jpg -j')
    end = datetime.now()
    diff = end - start
    print(f'{diff.seconds}:{diff.microseconds}')
    print(res.output.decode('utf-8'))


# test_openalpr_local()

def restuck_test():
    first = ''
    record_output_dir = '/mnt/sde1/record/qhfv46ocpha/2022/4/22/21'
    ext = '.' + RecordFileTypes.str(RecordFileTypes.MP4)
    files = get_sorted_valid_files(record_output_dir, ext)
    if len(files) > 0:
        first = files[0]
    print(first)


# restuck_test()
