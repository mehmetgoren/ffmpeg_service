import time

import requests
from abc import ABC, abstractmethod

from redis.client import Redis


class BaseRtmpModel(ABC):
    def __init__(self, container_name: str, connection: Redis):
        self.container_name = container_name
        self.connection: Redis = connection
        self.inc_namespace = 'rtmpmodels:'
        self.inc_starting_port = 8999
        self.increment_by = 1
        self.host = '127.0.0.1'
        self.http_protocol = 'http'
        self.port_dic = {}
        self.rtmp_port: int = 0
        self.flv_port: int = 0

    def port_inc(self) -> int:
        return self.inc_starting_port + self.connection.hincrby(self.inc_namespace, 'ports_count', self.increment_by)

    def get_container_name(self) -> str:
        return self.container_name

    @abstractmethod
    def get_image_name(self) -> str:
        raise NotImplementedError('get_image_name() must be implemented')

    @abstractmethod
    def get_commands(self) -> list:
        raise NotImplementedError('get_commands() must be implemented')

    @abstractmethod
    def int_ports(self) -> dict:
        raise NotImplementedError('get_ports() must be implemented')

    @abstractmethod
    def init_channel_key(self) -> str:
        raise NotImplementedError('get_channel_key() must be implemented')

    @abstractmethod
    def get_rtmp_address(self) -> str:
        raise NotImplementedError('get_rtmp_address() must be implemented')

    @abstractmethod
    def get_flv_address(self) -> str:
        raise NotImplementedError('get_flv_address() must be implemented')


class SrsRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'srs_{unique_name}', connection)

    def get_image_name(self) -> str:
        return 'ossrs/srs:4'

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/docker.conf']

    def int_ports(self) -> dict:
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            other_port = self.port_inc()
            self.flv_port = self.port_inc()
            self.port_dic = {str(self.rtmp_port): '1935', str(other_port): '1985', str(self.flv_port): '8080'}
        return self.port_dic

    def init_channel_key(self) -> str:
        return ''

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/livestream'

    def get_flv_address(self) -> str:
        return f'{self.http_protocol}://{self.host}:{self.flv_port}/live/livestream.flv'


class LiveGoRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'livego_{unique_name}', connection)
        self.web_api_port: int = 0
        self.channel_key: str = ''

    def get_image_name(self) -> str:
        return 'gwuhaolin/livego'

    def get_commands(self) -> list:
        return []

    def int_ports(self) -> dict:
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            self.flv_port = self.port_inc()
            other_port = self.port_inc()
            self.web_api_port = self.port_inc()
            self.port_dic = {str(self.rtmp_port): '1935', str(self.flv_port): '7001', str(other_port): '7002',
                             str(self.web_api_port): '8090'}
        return self.port_dic

    def init_channel_key(self) -> str:
        if not self.channel_key:
            time.sleep(5)  # give the container a time to initialized web api on even an IoT device.
            if not self.channel_key:
                self.channel_key = requests.get(
                    f'{self.http_protocol}://{self.host}:{self.web_api_port}/control/get?room=livestream').json()[
                    'data'].decode('utf-8')
        return self.channel_key

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/livestream'

    def get_flv_address(self) -> str:
        return f'{self.http_protocol}://{self.host}:{self.flv_port}/live/{self.channel_key}.flv'


class NodeMediaServerRtmpModel(BaseRtmpModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'nms_{unique_name}', connection)

    def get_image_name(self) -> str:
        return 'illuspas/node-media-server'

    def get_commands(self) -> list:
        return []

    def int_ports(self) -> dict:
        if not self.port_dic:
            self.rtmp_port = self.port_inc()
            self.flv_port = self.port_inc()
            other_port = self.port_inc()
            self.port_dic = {str(self.rtmp_port): '1935', str(self.flv_port): '8000', str(other_port): '8443'}
        return self.port_dic

    def init_channel_key(self) -> str:
        return ''

    def get_rtmp_address(self) -> str:
        return f'rtmp://{self.host}:{self.rtmp_port}/live/STREAM_NAME'

    def get_flv_address(self) -> str:
        return f'{self.http_protocol}://{self.host}:{self.flv_port}/live/STREAM_NAME.flv'
