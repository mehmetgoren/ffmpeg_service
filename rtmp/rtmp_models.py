import json
import time
from enum import Enum
import requests
from abc import ABC, abstractmethod
from redis.client import Redis

from common.data.source_repository import SourceRepository
from common.utilities import logger, config
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository


class RtmpServerImages(Enum):
    OSSRS = 'ossrs/srs:4'
    LIVEGO = 'livego_local'  # original one is 'gwuhaolin/livego'
    NMS = 'illuspas/node-media-server'


class BaseRtmpModel(ABC):
    def __init__(self, container_name: str, main_connection: Redis):
        self.container_name = container_name
        self.connection: Redis = main_connection
        self.inc_namespace = 'rtmpports'
        self.inc_starting_port: int = 0
        self.max_port_num: int = 0
        self.__set_ports_values(main_connection)
        self.increment_by = 1
        self.host = '127.0.0.1'
        self.protocol = 'http'
        self.port_dic = {}
        self.rtmp_port: int = 0
        self.flv_port: int = 0
        self.rtmp_server_wait: float = config.ffmpeg.rtmp_server_init_interval  # otherwise, RTMP read will not work
        self.stream_repository = StreamRepository(main_connection)

    def __set_ports_values(self, main_connection: Redis):
        f = config.ffmpeg
        mp = 65535
        self.inc_starting_port: int = f.rtmp_server_port_start - 1 if f.rtmp_server_port_start - 1 > 1 else 1024
        self.max_port_num: int = (f.rtmp_server_port_end if f.rtmp_server_port_end > f.rtmp_server_port_start else mp) - self.inc_starting_port
        self.max_port_num = max(self.max_port_num, 16)
        if self.max_port_num > mp:
            self.max_port_num = mp
        source_repository = SourceRepository(main_connection)
        source_models = source_repository.get_all()
        min_port_value = len(source_models) * 5
        if self.max_port_num < min_port_value:
            logger.error(f'max port number is lower then source count * 5, the min_port_num is not set to {min_port_value}')
            self.max_port_num = min_port_value

    def map_to(self, stream_model: StreamModel):
        stream_model.rtmp_container_ports = json.dumps(self.get_ports())
        stream_model.rtmp_image_name = self.get_image_name()
        stream_model.rtmp_container_name = self.get_container_name()
        stream_model.rtmp_address = self.get_rtmp_address()
        stream_model.rtmp_flv_address = self.get_flv_address(stream_model)
        stream_model.rtmp_container_commands = ','.join(self.get_commands())
        stream_model.rtmp_server_initialized = True

    def __port_inc(self, ports: set) -> int:
        inc = self.connection.hincrby(self.inc_namespace, 'ports_count', self.increment_by)
        ret = self.inc_starting_port + (inc % self.max_port_num)
        if ret in ports:
            logger.warning(f'port ({ret}) is being used by another container, now trying another one')
            return self.__port_inc(ports)
        return ret

    def port_inc(self) -> int:
        ports = set()
        stream_models = self.stream_repository.get_all()
        for stream_model in stream_models:
            if len(stream_model.rtmp_container_ports) == 0:
                continue
            dic = json.loads(stream_model.rtmp_container_ports)
            for field in dic:
                ports.add(int(dic[field]))
        return self.__port_inc(ports)

    def get_container_name(self) -> str:
        return self.container_name

    @abstractmethod
    def get_image_name(self) -> str:
        raise NotImplementedError('get_image_name() must be implemented')

    @abstractmethod
    def get_commands(self) -> list:
        raise NotImplementedError('get_commands() must be implemented')

    @abstractmethod
    def int_ports(self):
        raise NotImplementedError('get_ports() must be implemented')

    def get_ports(self) -> dict:
        return self.port_dic

    @abstractmethod
    def init_channel_key(self) -> str:
        raise NotImplementedError('get_channel_key() must be implemented')

    @abstractmethod
    def get_rtmp_address(self) -> str:
        raise NotImplementedError('get_rtmp_address() must be implemented')

    @abstractmethod
    def get_flv_address(self, stream_model: StreamModel) -> str:
        raise NotImplementedError('get_flv_address() must be implemented')


class SrsRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'{self._get_prefix()}_{unique_name}', connection)

    @staticmethod
    def _get_prefix():
        return 'srs'

    def get_image_name(self) -> str:
        return RtmpServerImages.OSSRS.value

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/http.flv.live.conf']

    def int_ports(self):
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            other_port = self.port_inc()
            self.flv_port = self.port_inc()
            self.port_dic = {'1935': str(self.rtmp_port), '1985': str(other_port), '8080': str(self.flv_port)}

    def init_channel_key(self) -> str:
        time.sleep(self.rtmp_server_wait)
        return ''

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/livestream'

    def get_flv_address(self, stream_model: StreamModel) -> str:
        return f'{self.protocol}://{self.host}:{self.flv_port}/live/livestream.flv'


class SrsRealtimeRtmpServer(SrsRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(unique_name, connection)

    @staticmethod
    def _get_prefix():
        return 'srsrt'

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/realtime.flv.conf']


class LiveGoRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'livego_{unique_name}', connection)
        self.web_api_port: int = 0
        self.predefined_channel_key = 'rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk'
        self.channel_key: str = ''

    def get_image_name(self) -> str:
        return RtmpServerImages.LIVEGO.value

    def get_commands(self) -> list:
        return []

    def int_ports(self):
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            self.flv_port = self.port_inc()
            other_port = self.port_inc()
            self.web_api_port = self.port_inc()
            self.port_dic = {'1935': str(self.rtmp_port), '7001': str(self.flv_port), '7002': str(other_port),
                             '8090': str(self.web_api_port)}

    def init_channel_key(self) -> str:
        if len(self.channel_key) == 0:
            max_retry = config.ffmpeg.max_operation_retry_count
            retry_count = 0
            while not self.channel_key and retry_count < max_retry:
                try:
                    resp = requests.get(
                        f'{self.protocol}://{self.host}:{self.web_api_port}/control/get?room={self.predefined_channel_key}')
                    resp.raise_for_status()
                    self.channel_key = self.predefined_channel_key
                except BaseException as e:
                    logger.error(e)
                    time.sleep(1)
                retry_count += 1
            if retry_count == max_retry:
                logger.error('init_channel_key max retry count has been exceeded.')
                self.channel_key = self.predefined_channel_key
        time.sleep(self.rtmp_server_wait)
        return self.channel_key

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/{self.channel_key}'

    def get_flv_address(self, stream_model: StreamModel) -> str:
        return f'{self.protocol}://{self.host}:{self.flv_port}/live/{self.channel_key}.flv'


class NodeMediaServerRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'nms_{unique_name}', connection)

    def get_image_name(self) -> str:
        return RtmpServerImages.NMS.value

    def get_commands(self) -> list:
        return []

    def int_ports(self):
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            self.flv_port = self.port_inc()
            other_port = self.port_inc()
            self.port_dic = {'1935': str(self.rtmp_port), '8000': str(self.flv_port), '8443': str(other_port)}

    def init_channel_key(self) -> str:
        time.sleep(self.rtmp_server_wait)
        return ''

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/STREAM_NAME'

    def get_flv_address(self, stream_model: StreamModel) -> str:
        protocol = 'http'  # or https?
        return f'{protocol}://{self.host}:{self.flv_port}/live/STREAM_NAME.flv'
