from __future__ import annotations

import argparse
import json
import os
from types import SimpleNamespace
from typing import List
from redis import Redis
from enum import IntEnum
import platform


# it is readonly, but it is shown on redis as information
class ConfigRedis:
    def __init__(self):
        self.host: str = '127.0.0.1'
        self.port: int = 6379
        self.__init_values()

    def __init_values(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--redis-host')
        parser.add_argument('--redis-port')
        args = parser.parse_args()

        self.host: str = ''
        self.port: int = 0

        eh = os.getenv('REDIS_HOST', '')
        if len(eh) > 0:
            self.host = eh
        elif args.redis_host is not None and len(args.redis_host) > 0:
            self.host = args.redis_host
        else:
            self.host = '127.0.0.1'
        print(f'Redis host: {self.host}')

        ep = os.getenv('REDIS_PORT', '')
        if len(ep) > 0:
            self.port = int(ep)
        elif args.redis_port is not None and len(args.redis_port) > 0:
            self.port = int(args.redis_port)
        else:
            self.port = 6379
        print(f'Redis port: {self.port}')


config_redis = ConfigRedis()


class DbType(IntEnum):
    SQLite = 0
    MongoDB = 1


class DeviceArch(IntEnum):
    X86 = 0
    ARM = 1


class ArchiveActionType(IntEnum):
    Delete = 0
    MoveToNewLocation = 1


class SenseAiImage(IntEnum):
    CPU = 0
    GPU_CUDA_11_7 = 1
    GPU_CUDA_12_2 = 2
    ARM64 = 3
    RPI64 = 4


class DeviceConfig:
    def __init__(self):
        self.device_name = platform.node()
        _, _, _, _, machine, _ = platform.uname()
        self.device_arch = DeviceArch.X86 if 'x86' in machine else DeviceArch.ARM


class GeneralConfig:
    def __init__(self):
        self.dir_paths: List[str] = []


class DbConfig:
    def __init__(self):
        self.type: DbType = DbType.MongoDB
        self.connection_string = 'mongodb://localhost:27017'


class FFmpegConfig:
    def __init__(self):
        self.use_double_quotes_for_path: bool = False
        self.max_operation_retry_count: int = 10000000
        self.ms_init_interval: float = 3.  # ms prefix is for media server.
        self.watch_dog_interval: int = 23
        self.watch_dog_failed_wait_interval: float = 3.
        self.start_task_wait_for_interval: float = 1.
        self.record_concat_limit: int = 1
        self.record_video_file_indexer_interval: int = 60
        # 1024 - 65535
        self.ms_port_start: int = 7000  # for more info: https://www.thegeekdiary.com/which-network-ports-are-reserved-by-the-linux-operating-system/
        self.ms_port_end: int = 8000  # should be greater than total camera count


class AiConfig:
    def __init__(self):
        self.video_clip_duration: int = 10


class SenseAIConfig:
    def __init__(self):
        self.image: SenseAiImage = SenseAiImage.GPU_CUDA_12_2
        self.host: str = '127.0.0.1'
        self.port: int = 32168


class JobsConfig:
    def __init__(self):
        self.mac_ip_matching_enabled: bool = False
        self.mac_ip_matching_interval: int = 120
        self.black_screen_monitor_enabled: bool = False
        self.black_screen_monitor_interval: int = 600


class ArchiveConfig:
    def __init__(self):
        self.limit_percent: int = 95
        self.action_type: ArchiveActionType = ArchiveActionType.Delete
        self.move_location: str = ''


class SnapshotConfig:
    def __init__(self):
        self.process_count: int = 1
        self.overlay: bool = True


class DesimaConfig:
    def __init__(self):
        self.enabled: bool = False
        self.address: str = 'http://localhost:5268'
        self.token: str = ''
        self.web_app_address: str = 'http://localhost:8080'
        self.max_retry: int = 100


class Config:
    def __init__(self):
        self.device: DeviceConfig = DeviceConfig()
        self.general: GeneralConfig = GeneralConfig()
        self.db: DbConfig = DbConfig()
        self.ffmpeg: FFmpegConfig = FFmpegConfig()
        self.ai: AiConfig = AiConfig()
        self.sense_ai: SenseAIConfig = SenseAIConfig()
        self.jobs: JobsConfig = JobsConfig()
        self.archive: ArchiveConfig = ArchiveConfig()
        self.snapshot: SnapshotConfig = SnapshotConfig()
        self.desima: DesimaConfig = DesimaConfig()
        self.__connection: Redis | None = None

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
            self.__connection = Redis(host=config_redis.host, port=config_redis.port, charset='utf-8', db=0,
                                      decode_responses=True)
        return self.__connection

    def save(self):
        self.__get_connection().set(self.__get_redis_key(), self.to_json())
