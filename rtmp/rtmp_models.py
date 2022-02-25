import json
import time
from enum import Enum

import requests
from abc import ABC, abstractmethod
from redis.client import Redis

from common.data.source_model import FlvPlayerConnectionType
from common.utilities import logger, config
from stream.stream_model import StreamModel


class RtmpServerImages(Enum):
    OSSRS = 'ossrs/srs:4'
    LIVEGO = 'gwuhaolin/livego'
    NMS = 'illuspas/node-media-server'


class BaseRtmpModel(ABC):
    def __init__(self, container_name: str, connection: Redis):
        self.container_name = container_name
        self.connection: Redis = connection
        self.inc_namespace = 'rtmpports'
        self.inc_starting_port = 1023  # for more info: https://www.thegeekdiary.com/which-network-ports-are-reserved-by-the-linux-operating-system/
        self.increment_by = 1
        self.host = '127.0.0.1'
        self.protocol = 'http'
        self.port_dic = {}
        self.rtmp_port: int = 0
        self.flv_port: int = 0
        self.rtmp_server_wait: float = config.ffmpeg.rtmp_server_init_interval  # otherwise, RTMP read will not work

    def map_to(self, stream_model: StreamModel):
        stream_model.rtmp_container_ports = json.dumps(self.get_ports())
        stream_model.rtmp_image_name = self.get_image_name()
        stream_model.rtmp_container_name = self.get_container_name()
        stream_model.rtmp_address = self.get_rtmp_address()
        stream_model.rtmp_flv_address = self.get_flv_address(stream_model)
        stream_model.rtmp_container_commands = ','.join(self.get_commands())
        stream_model.rtmp_server_initialized = True

    def port_inc(self) -> int:
        max_port_num = 65535
        inc = self.connection.hincrby(self.inc_namespace, 'ports_count', self.increment_by)
        return (self.inc_starting_port + inc) % max_port_num

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
        super().__init__(f'srs_{unique_name}', connection)

    def get_image_name(self) -> str:
        return RtmpServerImages.OSSRS.value

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/docker.conf']

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


class LiveGoRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'livego_{unique_name}', connection)
        self.web_api_port: int = 0
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
        if not self.channel_key:
            max_retry = config.ffmpeg.max_operation_retry_count
            retry_count = 0
            while not self.channel_key and retry_count < max_retry:
                try:
                    resp = requests.get(
                        f'{self.protocol}://{self.host}:{self.web_api_port}/control/get?room=livestream')
                    resp.raise_for_status()
                    self.channel_key = resp.json()['data']
                except BaseException as e:
                    logger.error(e)
                    time.sleep(1)
                retry_count += 1
            if retry_count == max_retry:
                logger.error('init_channel_key max retry count has been exceeded.')
        time.sleep(self.rtmp_server_wait)
        return self.channel_key

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/livestream'

    def get_flv_address(self, stream_model: StreamModel) -> str:
        # livestream default channel key is rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk
        return f'{self.protocol}://{self.host}:{self.flv_port}/live/{("rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk" if not self.channel_key else self.channel_key)}.flv'


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
        protocol = 'http' if stream_model.flv_player_connection_type == FlvPlayerConnectionType.HTTP else 'ws'
        return f'{protocol}://{self.host}:{self.flv_port}/live/STREAM_NAME.flv'
