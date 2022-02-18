from common.config import Config
from common.data.rtsp_template_model import RtspTemplateModel
from common.data.rtsp_template_repository import RtspTemplateRepository
from common.utilities import crate_redis_connection, RedisDb
from readers.base_reader import PushMethod
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions


# def bench_PIL_vs_cv2():
#     img_path = '/home/gokalp/Downloads/download (43)'
#     image = Image.open(img_path)
#     numpy_img = asarray(image)
#     # To convert RGB to BGR
#     # numpy_img = numpy_img[:, :, ::-1]
#
#     img_str = ''
#     length = 100
#     start = datetime.now()
#     for j in range(length):
#         buff = cv2.imencode('.jpg', numpy_img)[1]
#         img_str = base64.b64encode(buff).decode()
#         # print(len(img_str))
#     end = datetime.now()
#     print(f'cv2 length: {len(img_str)}')
#     print(f'cv2: {(end - start).microseconds}')
#
#     start = datetime.now()
#     for j in range(length):
#         img = Image.fromarray(numpy_img)
#         buffered = BytesIO()
#         img.save(buffered, format="JPEG")
#         img_str = base64.b64encode(buffered.getvalue()).decode()
#         # print(len(img_str))
#     end = datetime.now()
#     print(f'PIL length: {len(img_str)}')
#     print(f'PIL: {(end - start).microseconds}')
#     # result:
#     # cv2 length: 322456
#     # cv2: 962414
#     # PIL length: 187792
#     # PIL: 637581
#
#
# bench_PIL_vs_cv2()


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
