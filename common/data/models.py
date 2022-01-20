import multiprocessing
import os
import platform
import psutil
import re
import socket
import uuid
import shortuuid

from common.utilities import datetime_now


class RtspTemplate:
    def __init__(self):
        self.id = shortuuid.uuid()[:11]
        self.name = ''
        self.description = ''
        self.brand = ''
        self.default_user = ''
        self.default_password = ''
        self.default_port = ''
        self.address = ''
        self.route = ''
        self.templates = '{user},{password},{ip},{port},{route}'


class Source:
    def __init__(self, identifier: str = '', brand: str = '', name: str = '', rtsp_address: str = ''):
        self.id = identifier
        self.brand = brand
        self.name = name
        self.rtsp_address = rtsp_address
        self.description = ''

    def get_id(self):
        return self.id

    def get_brand(self):
        return self.brand

    def get_name(self):
        return self.name

    def get_rtsp_address(self):
        return self.rtsp_address


class ServiceModel:
    def __init__(self, name: str):
        self.name = name
        self.platform = ''
        self.platform_version = ''
        self.hostname = ''
        self.ip_address = ''
        self.mac_address = ''
        self.processor = ''
        self.cpu_count = ''
        self.ram = ''
        self.pid = ''
        self.created_at = ''
        self.heartbeat = ''

    def detect_values(self):
        self.platform = platform.system()
        self.platform_version = platform.version()
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(socket.gethostname())
        self.mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        self.processor = platform.processor()
        self.cpu_count = multiprocessing.cpu_count()
        self.ram = str(round(psutil.virtual_memory().total / (1024.0 ** 3)) + 1) + " GB"
        self.pid = os.getpid()
        self.created_at = datetime_now()
        self.heartbeat = datetime_now()
