from threading import Thread

from common.event_bus.event_handler import EventHandler
from common.utilities import crate_redis_connection, RedisDb


class EventBus:
    def __init__(self, channel: str):
        self.connection = crate_redis_connection(RedisDb.EVENTBUS, True, 2)
        self.channel = channel

    def publish(self, event):  # added for AI service
        self.connection.publish(self.channel, event)

    def publish_async(self, event):
        th = Thread(target=self.connection.publish, args=[self.channel, event])
        th.daemon = True
        th.start()

    def subscribe_async(self, event_handler: EventHandler):
        pub_sub = self.connection.pubsub()
        pub_sub.subscribe(self.channel)
        for event in pub_sub.listen():
            th = Thread(target=event_handler.handle, args=[event])
            th.daemon = True
            th.start()

    def unsubscribe(self):
        pub_sub = self.connection.pubsub()
        pub_sub.unsubscribe(self.channel)
