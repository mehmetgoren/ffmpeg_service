import os
import shutil
from abc import ABC

from command_builder import get_hls_output_path
from common.data.source_model import SourceModel
from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from common.utilities import logger
from streaming.streaming_model import StreamingModel
from streaming.streaming_repository import StreamingRepository
from common.data.base_repository import is_message_invalid, fix_redis_pubsub_dict


class BaseStreamingEventHandler(EventHandler, ABC):
    def __init__(self, streaming_repository: StreamingRepository, response_channel_name: str):
        self.encoding = 'utf-8'
        self.event_bus = EventBus(response_channel_name)
        self.streaming_repository = streaming_repository

    def parse_message(self, dic: dict) -> (bool, StreamingModel, SourceModel, str):
        if is_message_invalid(dic):
            return False, None, None, ''

        fixed_dic, dic_json = fix_redis_pubsub_dict(dic, self.encoding)
        source_model = SourceModel().map_from(fixed_dic)
        prev_streaming_model = self.streaming_repository.get(source_model.id)

        return True, prev_streaming_model, source_model, dic_json

    @staticmethod
    def delete_pref_streaming_files(source_id: str):
        hls_output_file_path = get_hls_output_path(source_id)
        folder: str = os.path.dirname(hls_output_file_path)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')
