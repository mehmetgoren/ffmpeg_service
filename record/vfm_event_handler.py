from datetime import datetime

from common.data.redis_mapper import RedisMapper
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from record.req_resp import VfmRequestEvent, VfmResponseEvent
from record.video_file_indexer import VideoFileIndexer
from record.video_file_merger import VideoFileMerger
from stream.stream_repository import StreamRepository
from utils.json_serializer import serialize_json


class VfmEventHandler(EventHandler):
    def __init__(self, stream_repository: StreamRepository):
        self.stream_repository = stream_repository
        self.event_bus = EventBus('vfm_response')
        logger.info(f'VideoFileMergerEventHandler: initialized at {datetime.now()}')

    def handle(self, dic: dict):
        if RedisMapper.is_pubsub_message_invalid(dic):
            return
        logger.info(f'VideoFileMergerEventHandler handle called at {datetime.now()}')

        mapper = RedisMapper(VfmRequestEvent())
        request: VfmRequestEvent = mapper.from_redis_pubsub(dic)
        vfm = VideoFileMerger(self.stream_repository)
        response = VfmResponseEvent()
        response.source_id = request.source_id
        response.output_file_name, response.merged_video_filenames = vfm.merge(request.source_id, request.date_str)
        prs = VideoFileIndexer.check_by_ffprobe([response.output_file_name])
        if len(prs) > 0:
            response.merged_video_file_duration = prs[0].duration

        self.event_bus.publish_async(serialize_json(response))
