import json

from common.data.base_repository import is_message_invalid, fix_redis_pubsub_dict
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from editor.req_resp import EditorRequestEvent, EditorEventType, EditorResponseEvent
from editor.rtsp_video_editor import RtspVideoEditor
from utils.json_serializer import serialize_json


class EditorEventHandler(EventHandler):
    def __init__(self):
        self.encoding = 'utf-8'
        self.event_bus = EventBus('editor_response')
        logger.info('EditorEventHandler: initialized')

    def handle(self, dic: dict):
        if is_message_invalid(dic):
            logger.info('EditorEventHandler: message is invalid')
            return
        logger.info('EditorEventHandler handle called')
        fixed_dic, _ = fix_redis_pubsub_dict(dic, self.encoding)
        request: EditorRequestEvent = EditorRequestEvent().map_from(fixed_dic)
        if request.event_type == EditorEventType.NONE:
            logger.info('EditorEventHandler: NONE, EditorEventHAndler is not handling this event')
            return
        if request.event_type < 3:
            response = EditorResponseEvent().map_from_super(request)
            if request.event_type == EditorEventType.TAKE_SCREENSHOT:
                response.image_base64 = RtspVideoEditor(request.rtsp_address).take_screenshot()
            elif request.event_type == EditorEventType.GENERATE_THUMBNAIL:
                response.image_base64 = RtspVideoEditor(request.rtsp_address).generate_thumbnail()

            self.event_bus.publish(serialize_json(response))
        else:
            raise NotImplementedError('EditorEventHandler: event_type is not implemented')
