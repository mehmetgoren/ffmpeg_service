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
        self.name: str = name
        self.description: str = ''
        self.platform: str = ''
        self.platform_version: str = ''
        self.hostname: str = ''
        self.ip_address: str = ''
        self.mac_address: str = ''
        self.processor: str = ''
        self.cpu_count: str = ''
        self.ram: str = ''
        self.pid: str = ''
        self.created_at: str = ''
        self.heartbeat: str = ''

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
