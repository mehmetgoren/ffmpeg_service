import json

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from data.models import EditorEventType, EditorRequestModel, EditorImageResponseModel
from common.data.source_repository import SourceRepository
from editor.rtsp_video_editor import RtspVideoEditor
from utils.json_serializer import serialize_json
from utils.redis import is_message_invalid, fix_redis_pubsub_dict


class EditorEventHandler(EventHandler):
    def __init__(self, source_repository: SourceRepository):
        self.encoding = 'utf-8'
        self.event_bus = EventBus('editor_response')
        self.source_repository = source_repository
        logger.info('EditorEventHandler: initialized')

    def handle(self, dic: dict):
        if is_message_invalid(dic):
            logger.info('EditorEventHandler: message is invalid')
            return
        logger.info('EditorEventHandler handle called')
        fixed_dic, _ = fix_redis_pubsub_dict(dic, self.encoding)
        model = EditorRequestModel().map_from(fixed_dic)
        if model.event_type == EditorEventType.NONE:
            logger.info('EditorEventHandler: NONE, EditorEventHAndler is not handling this event')
            return
        source = self.source_repository.get(model.source.id)
        if source is None:
            logger.info('EditorEventHandler: source is None, EditorEventHAndler is not handling this event')
            return
        model.source = source
        if model.event_type < 3:
            response_model = EditorImageResponseModel()
            if model.event_type == EditorEventType.TAKE_SCREENSHOT:
                response_model.image_base64 = RtspVideoEditor(source.rtsp_address).take_screenshot()
            elif model.event_type == EditorEventType.GENERATE_THUMBNAIL:
                response_model.image_base64 = RtspVideoEditor(source.rtsp_address).generate_thumbnail()

            model.response_json = json.dumps(response_model.__dict__)
            self.event_bus.publish(serialize_json(model))
        else:
            raise NotImplementedError('EditorEventHandler: event_type is not implemented')
