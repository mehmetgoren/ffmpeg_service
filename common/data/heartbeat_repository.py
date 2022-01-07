import threading
from datetime import datetime
from redis import Redis

from common.utilities import logger, crate_redis_connection, RedisDb, config, datetime_now


class HeartbeatRepository:
    def __init__(self, connection: Redis, service_name: str):
        self.connection: Redis = connection
        self.service_name = service_name
        self.namespace = 'services:'
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
            logger.info(f'Heartbeat({self.service_name}) was beaten at ' + datetime.now().strftime("%Y-%m-%d %H:%M:%MS"))
        except Exception as e:
            logger.error('Heartbeat failed: ' + str(e))
