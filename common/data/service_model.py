import multiprocessing
import os
import platform
import psutil
import re
import socket
import uuid

from common.utilities import datetime_now


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

    def map_from(self, dic: dict):
        self.__dict__.update(dic)
        return self
