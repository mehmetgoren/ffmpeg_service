from multiprocessing import Process
from threading import Thread

from common.config import EventListenerHandlerType
from common.event_bus.event_handler import EventHandler
from common.utilities import crate_redis_connection, RedisDb, config


class EventBus:
    def __init__(self, channel: str):
        self.connection = crate_redis_connection(RedisDb.EVENTBUS, True, 2)
        self.channel = channel
        self.mode = config.ffmpeg.event_listener_handler_type

    def publish(self, event):
        th = Thread(target=self.connection.publish, args=[self.channel, event])
        th.daemon = True
        th.start()

    def subscribe(self, event_handler: EventHandler):
        pub_sub = self.connection.pubsub()
        pub_sub.subscribe(self.channel)
        for event in pub_sub.listen():
            if self.mode == EventListenerHandlerType.THREAD:
                th = Thread(target=event_handler.handle, args=[event])
                th.daemon = True
                th.start()
            elif self.mode == EventListenerHandlerType.PROCESS:
                p = Process(target=event_handler.handle, args=(event,))
                p.daemon = True
                p.start()
            else:
                raise NotImplemented(self.mode)

    def unsubscribe(self):
        pub_sub = self.connection.pubsub()
        pub_sub.unsubscribe(self.channel)
