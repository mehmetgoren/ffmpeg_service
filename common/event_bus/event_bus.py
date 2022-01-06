from common.event_bus.event_handler import EventHandler
from common.utilities import crate_redis_connection, RedisDb


class EventBus:
    def __init__(self, channel: str):
        self.connection = crate_redis_connection(RedisDb.EVENTBUS, False)
        self.channel = channel

    def publish(self, event):
        self.connection.publish(self.channel, event)

    def subscribe(self, event_handler: EventHandler):
        pub_sub = self.connection.pubsub()
        pub_sub.subscribe(self.channel)
        for event in pub_sub.listen():
            event_handler.handle(event)

    def unsubscribe(self):
        pub_sub = self.connection.pubsub()
        pub_sub.unsubscribe(self.channel)
