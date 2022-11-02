import time

from common.data.source_model import SourceModel
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import config, logger
from editor.rtsp_video_editor import RtspVideoEditor
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from sustain.failed_stream.failed_stream_model import WatchDogOperations
from sustain.failed_stream.notify_failed_stream_model import NotifyFailedStreamModel
from utils.json_serializer import serialize_json_dic


class BlackScreenMonitor:
    def __init__(self, source_repository: SourceRepository, stream_repository: StreamRepository):
        self.source_repository = source_repository
        self.stream_repository = stream_repository
        self.interval = float(max(config.jobs.black_screen_monitor_interval, 10))
        self.restart_stream_event_bus = EventBus('restart_stream_request')
        self.notify_failed_event_bus = EventBus('notify_failed')

    def __publish_restart(self, source_model: SourceModel):
        logger.warning(f'BlackScreenMonitor: a broken stream({source_model.id}/{source_model.name}) has been found and restart event will be triggered')
        self.restart_stream_event_bus.publish(serialize_json_dic(source_model.__dict__))

    def __publish_failed_notification(self, stream_model: StreamModel):
        model = NotifyFailedStreamModel().map_from(WatchDogOperations.check_rtmp_feeder_process, stream_model)
        self.notify_failed_event_bus.publish_async(serialize_json_dic(model.__dict__))
        logger.warning(f'BlackScreenMonitor: a failed source ({model.name}) has been notified at {model.created_at}')

    def run(self):
        time.sleep(self.interval)
        logger.info(f'BlackScreenMonitor is now starting')
        while 1:
            stream_models = self.stream_repository.get_all()
            for stream_model in stream_models:
                source_id = stream_model.id
                source_model = self.source_repository.get(source_id)
                if source_model is None:
                    logger.error(f'BlackScreenMonitor: a orphan stream({source_id}) has been found and leaved Watchdog to prevent remove it')
                    continue
                if not source_model.black_screen_check_enabled:
                    continue

                editor = RtspVideoEditor(stream_model.address)  # can't use rtmp_address since it causes timeout.
                logger.info(f'BlackScreenMonitor: ({source_id}/{stream_model.name}) is now probing')
                try:
                    editor.probe()
                    logger.info(f'BlackScreenMonitor: ({source_id}/{stream_model.name}) has been probed successfully')
                except BaseException as ex:
                    logger.error(f'BlackScreenMonitor: an error occurred while probing for source ({source_id}/{stream_model.name}), ex: {ex}')
                    self.__publish_restart(source_model)
                    time.sleep(1.)
                    self.__publish_failed_notification(stream_model)
                time.sleep(1.)
            time.sleep(self.interval)
