import json
import os
from types import SimpleNamespace
from redis import Redis
from enum import IntEnum
import platform


class DeviceType(IntEnum):
    PC = 0
    IOT = 1


class DeviceServices(IntEnum):
    NONE = 0
    READ = 1
    DETECTION = 2
    CLOUD_INTEGRATION = 4
    FFMPEG = 8
    MNGR = 16
    ALL = READ | DETECTION | CLOUD_INTEGRATION | FFMPEG | MNGR


# todo: mngr should auto-decide config fields. Implement it later by heartbeat infos.
class DeviceConfig:
    def __init__(self):
        self.device_name = platform.node()
        _, _, _, _, machine, _ = platform.uname()
        self.device_type = DeviceType.PC if 'x86' in machine else DeviceType.IOT
        self.device_services = [DeviceServices.READ, DeviceServices.DETECTION, DeviceServices.CLOUD_INTEGRATION,
                                DeviceServices.FFMPEG, DeviceServices.MNGR]


class ConfigRedis:
    def __init__(self):
        self.host: str = os.getenv('REDIS_HOST', '127.0.0.1')
        redis_port_str: str = os.getenv('REDIS_PORT', '6379')
        self.port: int = int(redis_port_str) if redis_port_str.isdigit() else 6379


class JetsonConfig:
    def __init__(self):
        self.model_name: str = 'ssd-mobilenet-v2'


class TorchConfig:
    def __init__(self):
        self.model_name = 'ultralytics/yolov5'
        self.model_name_specific = 'yolov5x6'


class TensorflowConfig:
    def __init__(self):
        self.model_name = 'efficientdet/lite4/detection'
        self.cache_folder: str = '/mnt/sdc1/test_projects/tf_cache'


class OnceDetectorConfig:
    def __init__(self):
        self.imagehash_threshold: int = 3
        self.psnr_threshold: float = .2
        self.ssim_threshold: float = .2


class SourceReaderConfig:
    def __init__(self):
        self.fps: int = 1
        self.buffer_size: int = 2
        self.max_retry: int = 150
        self.max_retry_in: int = 6  # hours


class GeneralConfig:
    def __init__(self):
        self.root_folder_path: str = '/mnt/sde1'
        self.heartbeat_interval: int = 30


class FFmpegConfig:
    def __init__(self):
        self.use_double_quotes_for_path: bool = False
        self.max_operation_retry_count: int = 10000000
        self.rtmp_server_init_interval: float = 3.
        self.watch_dog_interval: int = 23
        self.watch_dog_failed_wait_interval: float = 3.
        self.start_task_wait_for_interval: float = 1.
        self.record_concat_limit: int = 1
        self.record_video_file_indexer_interval: int = 60


class AiConfig:
    def __init__(self):
        self.overlay: bool = True
        self.video_clip_duration: int = 10
        self.face_recog_mtcnn_threshold: float = .86
        self.face_recog_prob_threshold: float = .95
        self.plate_recog_instance_count: int = 2


class UiConfig:
    def __init__(self):
        self.gs_width: int = 4
        self.gs_height: int = 3
        self.booster_interval: float = .3
        self.seek_to_live_edge_internal: int = 30


class Config:
    def __init__(self):
        self.device: DeviceConfig = DeviceConfig()
        self.redis: ConfigRedis = ConfigRedis()
        self.jetson: JetsonConfig = JetsonConfig()
        self.torch: TorchConfig = TorchConfig()
        self.tensorflow: TensorflowConfig = TensorflowConfig()
        self.once_detector: OnceDetectorConfig = OnceDetectorConfig()
        self.source_reader: SourceReaderConfig = SourceReaderConfig()
        self.general: GeneralConfig = GeneralConfig()
        self.ffmpeg: FFmpegConfig = FFmpegConfig()
        self.ai: AiConfig = AiConfig()
        self.ui: UiConfig = UiConfig()
        self.__connection: Redis = None

    @staticmethod
    def __get_redis_key():
        return 'config'

    @staticmethod
    def create():
        obj = Config()
        config_json = obj.__get_connection().get(obj.__get_redis_key())
        if config_json is not None:
            simple_namespace = json.loads(config_json, object_hook=lambda d: SimpleNamespace(**d))
            obj.__dict__.update(simple_namespace.__dict__)
        return obj

    def to_json(self):
        dic = {}
        dic.update(self.__dict__)
        del dic['_Config__connection']
        return json.dumps(dic, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def __get_connection(self) -> Redis:
        if self.__connection is None:
            self.__connection = Redis(host=self.redis.host, port=self.redis.port, charset='utf-8', db=0,
                                      decode_responses=True)
        return self.__connection

    def save(self):
        self.__get_connection().set(self.__get_redis_key(), self.to_json())
