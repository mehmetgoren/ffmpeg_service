import threading
from redis import Redis

from common.data.base_repository import BaseRepository
from common.utilities import logger, config, datetime_now


class HeartbeatRepository(BaseRepository):
    def __init__(self, connection: Redis, service_name: str):
        super().__init__(connection, 'services:')
        self.service_name = service_name
        self.interval = config.heartbeat.interval

    def start(self):
        stopped = threading.Event()

        def loop():
            while not stopped.wait(self.interval):  # until stopped
                self._tick()

        t = threading.Thread(target=loop)
        t.daemon = True  # stop if the program exits
        t.start()

    def _tick(self):
        try:
            self.connection.hset(self.namespace + self.service_name, 'heartbeat', datetime_now())
        except Exception as e:
            logger.error('Heartbeat failed: ' + str(e))
