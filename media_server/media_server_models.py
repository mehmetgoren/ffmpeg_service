import json
import os
import time
from enum import Enum
import requests
from abc import ABC, abstractmethod
from redis.client import Redis

from common.data.source_repository import SourceRepository
from common.utilities import logger, config
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository

inc_namespace = 'media_server_ports'
ports_count = 'ports_count'


class MediaServerImages(Enum):
    GO_RTC = 'alexxit/go2rtc:1.8.5'
    SRS = 'ossrs/srs:5'
    LIVE_GO = 'gokalpgoren/livego_local'  # original one is 'gwuhaolin/livego'
    NMS = 'illuspas/node-media-server'


class BaseMediaServerModel(ABC):
    def __init__(self, container_name: str, main_connection: Redis):
        self.container_name = container_name
        self.connection: Redis = main_connection
        self.inc_starting_port: int = 0
        self.max_port_num: int = 0
        self.__set_ports_values(main_connection)
        self.increment_by = 1
        self.host = '127.0.0.1'
        self.protocol = 'http'
        self.port_dic = {}
        self.media_server_port: int = 0
        self.stream_port: int = 0
        self.media_server_wait: float = config.ffmpeg.ms_init_interval  # otherwise, Media Server read will not work
        self.stream_repository = StreamRepository(main_connection)

    def __set_ports_values(self, main_connection: Redis):
        f = config.ffmpeg
        mp = 65535
        self.inc_starting_port: int = f.ms_port_start - 1 if f.ms_port_start - 1 > 1 else 1024
        self.max_port_num: int = (f.ms_port_end if f.ms_port_end > f.ms_port_start else mp) - self.inc_starting_port
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
        stream_model.ms_container_ports = json.dumps(self.get_ports())
        stream_model.ms_image_name = self.get_image_name()
        stream_model.ms_container_name = self.get_container_name()
        stream_model.ms_address = self.get_ms_address()
        stream_model.ms_stream_address = self.get_stream_address(stream_model)
        stream_model.ms_container_commands = ','.join(self.get_commands())
        stream_model.ms_initialized = True

    def __port_inc(self, ports: set) -> int:
        inc = self.connection.hincrby(inc_namespace, ports_count, self.increment_by)
        ret = self.inc_starting_port + (inc % self.max_port_num)
        if ret in ports:
            logger.warning(f'port ({ret}) is being used by another container, now trying another one')
            return self.__port_inc(ports)
        return ret

    def port_inc(self) -> int:
        ports = set()
        stream_models = self.stream_repository.get_all()
        for stream_model in stream_models:
            if len(stream_model.ms_container_ports) == 0:
                continue
            dic = json.loads(stream_model.ms_container_ports)
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
    def on_media_server_initialized(self) -> str:
        raise NotImplementedError('on_media_server_initialized() must be implemented')

    @abstractmethod
    def get_ms_address(self) -> str:
        raise NotImplementedError('get_ms_address() must be implemented')

    @abstractmethod
    def get_stream_address(self, stream_model: StreamModel) -> str:
        raise NotImplementedError('get_stream_address() must be implemented')


class SrsMediaServerModel(BaseMediaServerModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'{self._get_prefix()}_{unique_name}', connection)

    @staticmethod
    def _get_prefix():
        return 'srs'

    def get_image_name(self) -> str:
        return MediaServerImages.SRS.value

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/http.flv.live.conf']

    def int_ports(self):
        if not self.port_dic:
            self.media_server_port = self.port_inc()
            other_port = self.port_inc()
            self.stream_port = self.port_inc()
            self.port_dic = {'1935': str(self.media_server_port), '1985': str(other_port), '8080': str(self.stream_port)}

    def on_media_server_initialized(self) -> str:
        time.sleep(self.media_server_wait)
        return ''

    def get_ms_address(self) -> str:
        return f'rtmp://{self.host}:{self.media_server_port}/live/livestream'

    def get_stream_address(self, stream_model: StreamModel) -> str:
        return f'{self.protocol}://{self.host}:{self.stream_port}/live/livestream.flv'


class SrsRealtimeMediaServerModel(SrsMediaServerModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(unique_name, connection)

    @staticmethod
    def _get_prefix():
        return 'srsrt'

    def get_commands(self) -> list:
        return ['./objs/srs', '-c', 'conf/realtime.flv.conf']


class LiveGoMediaServerModel(BaseMediaServerModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'livego_{unique_name}', connection)
        self.web_api_port: int = 0
        self.predefined_channel_key = 'rfBd56ti2SMtYvSgD5xAV0YU99zampta7Z7S575KLkIZ9PYk'
        self.channel_key: str = ''

    def get_image_name(self) -> str:
        return MediaServerImages.LIVE_GO.value

    def get_commands(self) -> list:
        return []

    def int_ports(self):
        if not self.port_dic:
            self.media_server_port = self.port_inc()
            self.stream_port = self.port_inc()
            other_port = self.port_inc()
            self.web_api_port = self.port_inc()
            self.port_dic = {'1935': str(self.media_server_port), '7001': str(self.stream_port), '7002': str(other_port),
                             '8090': str(self.web_api_port)}

    def on_media_server_initialized(self) -> str:
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
                logger.error('on_media_server_initialized max retry count has been exceeded for livego.')
                self.channel_key = self.predefined_channel_key
        time.sleep(self.media_server_wait)
        return self.channel_key

    def get_ms_address(self) -> str:
        return f'rtmp://{self.host}:{self.media_server_port}/live/{self.channel_key}'

    def get_stream_address(self, stream_model: StreamModel) -> str:
        return f'{self.protocol}://{self.host}:{self.stream_port}/live/{self.channel_key}.flv'


class NodeMediaServerModel(BaseMediaServerModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'nms_{unique_name}', connection)

    def get_image_name(self) -> str:
        return MediaServerImages.NMS.value

    def get_commands(self) -> list:
        return []

    def int_ports(self):
        if not self.port_dic:
            self.media_server_port = self.port_inc()
            self.stream_port = self.port_inc()
            other_port = self.port_inc()
            self.port_dic = {'1935': str(self.media_server_port), '8000': str(self.stream_port), '8443': str(other_port)}

    def on_media_server_initialized(self) -> str:
        time.sleep(self.media_server_wait)
        return ''

    def get_ms_address(self) -> str:
        return f'rtmp://{self.host}:{self.media_server_port}/live/STREAM_NAME'

    def get_stream_address(self, stream_model: StreamModel) -> str:
        protocol = 'http'  # or https?
        return f'{protocol}://{self.host}:{self.stream_port}/live/STREAM_NAME.flv'


class Go2RtcMediaServerModel(BaseMediaServerModel):
    def __init__(self, unique_name: str, connection: Redis):
        super().__init__(f'go2rtc_{unique_name}', connection)
        self.webrtc_port: int = 0

    def get_image_name(self) -> str:
        return MediaServerImages.GO_RTC.value

    def get_commands(self) -> list:
        return []

    def int_ports(self):
        if not self.port_dic:
            """
            INF [api] listen addr=:1984
            INF [rtsp] listen addr=:8554
            INF [webrtc] listen addr=:8555/tcp
            """
            self.stream_port = self.port_inc()  # api  http://127.0.0.1:1985/api/ws?src=camera1
            self.media_server_port = self.port_inc()  # rtsp ffmpeg -f rtsp rtsp://127.0.0.1:8564/camera1
            self.webrtc_port = self.port_inc()  # webrtc  it is not used now
            self.port_dic = {'1984': str(self.stream_port), '8554': str(self.media_server_port),
                             '8555': str(self.webrtc_port)}

    def on_media_server_initialized(self) -> str:
        config_url = f'{self.protocol}://{self.host}:{self.stream_port}/api/config'
        restart_url = f'{self.protocol}://{self.host}:{self.stream_port}/api/restart'
        exit_url = f'{self.protocol}://{self.host}:{self.stream_port}/api/exit'
        yml = f'streams:{os.linesep}    camera1:{os.linesep}api:{os.linesep}    origin: "*"'
        try:
            result = requests.post(config_url, data=yml)
            if result.status_code == 200:
                time.sleep(self.media_server_wait)

                try:
                    requests.post(restart_url)
                except BaseException as e:
                    logger.error(e)

                time.sleep(self.media_server_wait)
                try:
                    requests.post(exit_url)
                except BaseException as e:
                    logger.error(e)

                time.sleep(self.media_server_wait)
        except BaseException as e:
            logger.error(e)
            time.sleep(1)
        return ''

    def get_ms_address(self) -> str:
        return f'rtsp://{self.host}:{self.media_server_port}/camera1'

    def get_stream_address(self, stream_model: StreamModel) -> str:
        return f'{self.protocol}://{self.host}:{self.stream_port}/api/ws?src=camera1'
