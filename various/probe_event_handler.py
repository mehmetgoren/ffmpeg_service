import base64
import json
import ffmpeg
from datetime import datetime

from common.data.redis_mapper import RedisMapper
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from utils.json_serializer import serialize_json


class ProbeRequestEvent:
    def __init__(self):
        self.address: str = ''


class ProbeResponseEvent:
    def __init__(self):
        self.address: str = ''
        self.result_b64: str = ''


class ProbeEventHandler(EventHandler):
    def __init__(self):
        self.event_bus = EventBus('probe_response')
        logger.info(f'ProbeEventHandler: initialized at {datetime.now()}')

    def handle(self, dic: dict):
        if RedisMapper.is_pubsub_message_invalid(dic):
            return
        logger.info(f'ProbeEventHandler handle called at {datetime.now()}')

        mapper = RedisMapper(ProbeRequestEvent())
        request: ProbeRequestEvent = mapper.from_redis_pubsub(dic)
        probe: dict = ffmpeg.probe(request.address)
        js = json.dumps(probe)
        barr = js.encode('utf-8')

        pre = ProbeResponseEvent()
        pre.address = request.address
        pre.result_b64 = base64.b64encode(barr).decode('utf-8')
        self.event_bus.publish_async(serialize_json(pre))
