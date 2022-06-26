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

    @staticmethod
    def __get_ip_addr() -> str:
        ret = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [
            [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + [
                   "no IP found"])[0]
        return ret if len(ret) > 0 and ret != "no IP found" else socket.gethostbyname_ex(socket.gethostname())

    def detect_values(self):
        self.platform = platform.system()
        self.platform_version = platform.version()
        self.hostname = socket.gethostname()
        self.ip_address = self.__get_ip_addr()
        self.mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        self.processor = platform.processor()
        self.cpu_count = multiprocessing.cpu_count()
        self.ram = str(round(psutil.virtual_memory().total / (1024.0 ** 3)) + 1) + " GB"
        self.pid = os.getpid()
        self.created_at = datetime_now()
        self.heartbeat = datetime_now()
