import json
import os
from types import SimpleNamespace
from typing import List
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


class HeartbeatConfig:
    def __init__(self):
        self.interval: int = 5


class ConfigRedis:
    def __init__(self):
        self.host: str = os.getenv('REDIS_HOST', '127.0.0.1')
        redis_port_str: str = os.getenv('REDIS_PORT', '6379')
        self.port: int = int(redis_port_str) if redis_port_str.isdigit() else 6379


class JetsonConfig:
    def __init__(self):
        self.model_name: str = 'ssd-mobilenet-v2'
        self.threshold: float = .1
        self.white_list: List[int] = [j for j in range(91)]


class TorchConfig:
    def __init__(self):
        self.model_name = 'ultralytics/yolov5'
        self.model_name_specific = 'yolov5x6'
        self.threshold: float = .1
        self.white_list: List[int] = [j for j in range(80)]


class OnceDetectorConfig:
    def __init__(self):
        self.imagehash_threshold: int = 3
        self.psnr_threshold: float = .2
        self.ssim_threshold: float = .2


class HandlerConfig:
    def __init__(self):
        self.save_image_folder_path: str = '/mnt/sde1'
        self.save_image_extension: str = 'jpg'
        self.show_image_wait_key: int = 1
        self.show_image_caption: bool = False
        self.show_image_fullscreen: bool = False
        self.read_service_overlay: bool = True


class SourceReaderConfig:
    def __init__(self):
        self.fps: int = 1
        self.buffer_size: int = 2
        self.max_retry: int = 150
        self.max_retry_in: int = 6  # hours
        # todo: remove it.
        self.kill_starter_proc: bool = True


class PathConfig:
    def __init__(self):
        self.streaming: str = '/mnt/sde1/live'
        self.recording: str = '/mnt/sde1/playback'
        self.reading: str = '/mnt/sde1/read'


class FFmpegConfig:
    def __init__(self):
        self.use_double_quotes_for_path: bool = False
        self.max_operation_retry_count: int = 20


class Config:
    def __init__(self):
        self.device: DeviceConfig = DeviceConfig()
        self.heartbeat: HeartbeatConfig = HeartbeatConfig()
        self.redis: ConfigRedis = ConfigRedis()
        self.jetson: JetsonConfig = JetsonConfig()
        self.torch: TorchConfig = TorchConfig()
        self.once_detector: OnceDetectorConfig = OnceDetectorConfig()
        self.handler: HandlerConfig = HandlerConfig()
        self.source_reader: SourceReaderConfig = SourceReaderConfig()
        self.path: PathConfig = PathConfig()
        self.ffmpeg: FFmpegConfig = FFmpegConfig()
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
