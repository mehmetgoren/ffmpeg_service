import glob
import os

from common.config import Config
from common.data.rtsp_template_model import RtspTemplateModel
from common.data.rtsp_template_repository import RtspTemplateRepository
from common.utilities import crate_redis_connection, RedisDb
from readers.base_reader import PushMethod
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions
from stream.stream_repository import StreamRepository


def rc_test():
    conn = crate_redis_connection(RedisDb.MAIN)
    rep = StreamRepository(conn)
    streams = rep.get_all()
    for stream in streams:
        if stream.record:
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
    opts.rtsp_address = 'rtsp://Admin1:Admin1@192.168.1.183/live0'
    opts.method = PushMethod.REDIS_PUBSUB
    opts.frame_rate = 1
    opts.width = 640
    opts.height = 360
    opts.pubsub_channel = 'read_service'
    reader = FFmpegReader(opts)
    reader.read()


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
