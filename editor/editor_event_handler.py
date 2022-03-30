from common.data.redis_mapper import RedisMapper
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from editor.req_resp import EditorRequestEvent, EditorEventType, EditorResponseEvent
from editor.rtsp_video_editor import RtspVideoEditor
from utils.json_serializer import serialize_json


class EditorEventHandler(EventHandler):
    def __init__(self):
        self.event_bus = EventBus('editor_response')
        logger.info('EditorEventHandler: initialized')

    def handle(self, dic: dict):
        if RedisMapper.is_pubsub_message_invalid(dic):
            logger.info('EditorEventHandler: message is invalid')
            return
        logger.info('EditorEventHandler handle called')
        mapper = RedisMapper(EditorRequestEvent())
        request: EditorRequestEvent = mapper.from_redis_pubsub(dic)
        if request.event_type == EditorEventType.NONE:
            logger.info('EditorEventHandler: NONE, EditorEventHAndler is not handling this event')
            return
        if request.event_type < 4:
            response = EditorResponseEvent().map_from_super(request)
            if request.event_type == EditorEventType.TAKE_SCREENSHOT or request.event_type == EditorEventType.MASK_SCREENSHOT:
                response.image_base64 = RtspVideoEditor(request.address).take_screenshot()
            elif request.event_type == EditorEventType.GENERATE_THUMBNAIL:
                response.image_base64 = RtspVideoEditor(request.address).generate_thumbnail()

            self.event_bus.publish_async(serialize_json(response))
        else:
            raise NotImplementedError(f'EditorEventHandler: event_type({request.event_type}) is not implemented')
