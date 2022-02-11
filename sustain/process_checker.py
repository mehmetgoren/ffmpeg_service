import json
import time
import psutil
import schedule

from common.data.source_model import StreamType
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb, config
from streaming.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler, StartFlvStreamingHandler

_connection_main = crate_redis_connection(RedisDb.MAIN)
_source_repository = SourceRepository(_connection_main)
_streaming_repository = StreamingRepository(_connection_main)

_interval_streaming = config.ffmpeg.check_ffmpeg_streaming_running_process_interval
_event_bus = EventBus('start_streaming_request')

_interval_recording = config.ffmpeg.check_ffmpeg_recording_running_process_interval
_start_streaming_event_handler = StartStreamingEventHandler(_source_repository, _streaming_repository)
_start_flv_streaming_handler = StartFlvStreamingHandler(_start_streaming_event_handler)


# containers are not to be checked since they are handled by Docker's unless-stop policy itself.
# todo: add max fail count
def __check_ffmpeg_streaming_running_process():
    logger.info('checking FFmpeg running streaming processes')
    streaming_models = _streaming_repository.get_all()
    for streaming_model in streaming_models:
        if not psutil.pid_exists(streaming_model.pid):
            # remove to make prev_streaming_model is None
            _streaming_repository.remove(streaming_model.id)
            logger.warn(
                f'a failed streaming FFmpeg process was detected for model {streaming_model.name} - {streaming_model.pid} and will be recovered in {_interval_streaming} seconds')
            source_model = _source_repository.get(streaming_model.id)
            # todo: need tobe tested carefully with fix_redis_pubsub_dict bytes data
            dic = source_model.__dict__
            _event_bus.publish(json.dumps(dic, ensure_ascii=False, indent=4))
            time.sleep(1)
        else:
            logger.info(f'FFmpeg streaming process {streaming_model.name} - {streaming_model.pid} is running')


# todo: test it
def __check_ffmpeg_recording_running_process():
    logger.info('checking FFmpeg running RTMP server recording processes')
    streaming_models = _streaming_repository.get_all()
    for streaming_model in streaming_models:
        pipe_recording_enabled = streaming_model.streaming_type == StreamType.FLV and streaming_model.recording
        if pipe_recording_enabled and not psutil.pid_exists(streaming_model.pid):
            streaming_model.record_flv_failed_count += 1
            _streaming_repository.update(streaming_model, ['record_flv_failed_count'])
            logger.warn(
                f'a failed streaming FFmpeg recording process was detected for model {streaming_model.name} - {streaming_model.pid} and will be recovered in {_interval_recording} seconds')
            source_model = _source_repository.get(streaming_model.id)
            # todo: need tobe tested carefully with fix_redis_pubsub_dict bytes data
            _start_flv_streaming_handler.create_piped_ffmpeg_process(source_model, streaming_model)
            time.sleep(1)
        else:
            logger.info(f'FFmpeg recording process {streaming_model.name} - {streaming_model.pid} is running')


def check_ffmpeg_streaming_running_process():
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(_interval_streaming).seconds.do(__check_ffmpeg_streaming_running_process)
    while True:
        scheduler_instance.run_pending()
        time.sleep(1)


def check_ffmpeg_recording_running_process():
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(_interval_recording).seconds.do(__check_ffmpeg_recording_running_process)
    while True:
        scheduler_instance.run_pending()
        time.sleep(1)
