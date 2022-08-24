import re
import time
from datetime import datetime
from subprocess import Popen, PIPE
from getmac import get_mac_address

from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger
from utils.json_serializer import serialize_json_dic


class MacIpMatching:
    def __init__(self, source_repository: SourceRepository):
        self.source_repository: SourceRepository = source_repository
        self.restart_stream_event_bus = EventBus('restart_stream_request')
        self.ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        self.last_check = datetime.now()

    def __parse_ip_address(self, url: str):
        result = self.ip_pattern.search(url)
        return result[0]

    # noinspection DuplicatedCode
    @staticmethod
    def __run_mac_address(ip_address) -> str:
        ret = ''
        max_retry = 5
        index = 0
        while index <= max_retry:
            ip_mac = get_mac_address(ip=ip_address, network_request=True)
            if ip_mac is not None and ip_mac != '00:00:00:00:00:00':
                ret = ip_mac
                break
            index += 1
            time.sleep(.2)
        return ret.upper() if len(ret) > 0 else ret

    # this function can use more advanced technique
    # noinspection DuplicatedCode
    @staticmethod
    def __run_ip_address(mac_addr: str) -> str:
        proc = None
        try:
            args = ['ip', 'neighbor']
            proc = Popen(args, stdout=PIPE, stderr=PIPE)
            proc.wait()
            output, error_output = proc.communicate()
            if len(error_output) == 0 and len(output) > 0:
                result = output.decode('utf-8')
                splits = result.split('\n')
                reverse_index = len(splits) - 1
                # we need to reverse loop to prevent cached ip neighbor misleading
                while reverse_index >= 0:
                    split = splits[reverse_index]
                    sp = split.split(' ')
                    if len(sp) == 6:
                        ip_val = sp[0]
                        mac_val = sp[4]
                        if mac_val.upper() == mac_addr:
                            return ip_val
                    reverse_index -= 1
            else:
                logger.warning(f'an IP address was not found from this mac address: {mac_addr}')
        except BaseException as ex:
            logger.error(f'an error occurred while getting the ip address by a mac address, ex: {ex}')
        finally:
            if proc is not None:
                try:
                    proc.terminate()
                except BaseException as ex:
                    logger.error(f'an error occurred while terminating the get ip address by mac address process, ex: {ex}')
        return ''

    def check(self):
        now = datetime.now()
        check_diff = now - self.last_check
        if check_diff.seconds < 2:
            return
        self.last_check = now
        source_models = self.source_repository.get_all()
        for source_model in source_models:

            if len(source_model.address) == 0:
                continue

            ip_addr = self.__parse_ip_address(source_model.address)
            if len(ip_addr) == 0:
                logger.warning(f'could not grab an ip address from the source address, source name: {source_model.name}, address: {source_model.address}')
                continue
            if len(source_model.ip_address) == 0:
                source_model.ip_address = ip_addr
                self.source_repository.add(source_model)

            if len(source_model.mac_address) == 0:
                mac_addr = self.__run_mac_address(ip_addr)
                if len(mac_addr) == 0:
                    logger.warning(f'could not grabbed an mac address for source name: {source_model.name}, ip: {source_model.ip_address}')
                    continue
                source_model.mac_address = mac_addr
                self.source_repository.add(source_model)

            # the __get_ip_address function cost too much cpu time.
            check_ip_addr = self.__run_ip_address(source_model.mac_address)
            if len(check_ip_addr) == 0:
                logger.warning(f'ip address could not be grabbed by mac address for source name: {source_model.name}, mac: {source_model.mac_address}')
                continue
            if check_ip_addr != ip_addr:
                logger.error(f'a changed ip address has ben detected for source name: {source_model.name}, it will be restart')
                logger.error(f'mac: {source_model.mac_address}, ip: {source_model.ip_address}, new ip: {check_ip_addr}')
                source_model.address = source_model.address.replace(source_model.ip_address, check_ip_addr)
                # reset for the new job
                source_model.ip_address = ''
                source_model.mac_address = ''
                self.source_repository.add(source_model)
                self.__publish_restart(self.source_repository.get(source_model.id))
                time.sleep(1.)

    def __publish_restart(self, source_model):
        dic = source_model.__dict__
        self.restart_stream_event_bus.publish_async(serialize_json_dic(dic))
