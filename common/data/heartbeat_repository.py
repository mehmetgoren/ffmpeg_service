import threading
from datetime import datetime

from common.utilities import logger, crate_redis_connection, RedisDb, config


class HeartbeatRepository:
    def __init__(self, service_name: str):
        self.service_name = service_name if service_name is not None else 'heartbeat'
        self.dic = {self.service_name: ''}
        self.key = 'heartbeat'
        self.interval = config.heartbeat.interval
        self.connection = crate_redis_connection(RedisDb.MAIN, True)

    @staticmethod
    def _to_my_format():
        now = datetime.now()
        sep = '-'
        strings = [''] * 13
        for j in [1, 3, 5, 7, 9, 11]:
            strings[j] = sep
        strings[0] = str(now.year)
        strings[2] = str(now.month)
        strings[4] = str(now.day)
        strings[6] = str(now.hour)
        strings[8] = str(now.minute)
        strings[10] = str(now.second)
        strings[12] = str(now.microsecond)

        return ''.join(strings)

    def start(self):
        stopped = threading.Event()

        def loop():
            while not stopped.wait(self.interval):  # until stopped
                self._tick()

        t = threading.Thread(target=loop)
        t.daemon = True  # stop if the program exits
        t.start()

    def _tick(self):
        self.dic[self.service_name] = self._to_my_format()
        self.connection.hset(self.key, mapping=self.dic)
        logger.info('Heartbeat was beaten at ' + datetime.now().strftime("%Y-%m-%d %H:%M:%MS"))
