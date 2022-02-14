import json
import time
import psutil
import schedule

from common.data.source_model import StreamType
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb, config
from stream.stream_repository import StreamRepository
from stream.start_stream_event_handler import StartStreamEventHandler, StartFlvStreamHandler

__connection_main = crate_redis_connection(RedisDb.MAIN)
__source_repository = SourceRepository(__connection_main)
__stream_repository = StreamRepository(__connection_main)

__interval_stream = config.ffmpeg.check_ffmpeg_stream_running_process_interval
__event_bus = EventBus('start_stream_request')

__interval_record = config.ffmpeg.check_ffmpeg_record_running_process_interval
__start_stream_event_handler = StartStreamEventHandler(__source_repository, __stream_repository)
__start_flv_stream_handler = StartFlvStreamHandler(__start_stream_event_handler)


# containers are not to be checked since they are handled by Docker's unless-stop policy itself.
# todo: add max fail count
def __check_ffmpeg_stream_running_process():
    logger.info('checking FFmpeg running stream processes')
    stream_models = __stream_repository.get_all()
    for stream_model in stream_models:
        if not psutil.pid_exists(stream_model.pid):
            __stream_repository.remove(stream_model.id)  # remove to make prev_stream_model is None
            logger.warn(
                f'a failed stream FFmpeg process was detected for model {stream_model.name} - {stream_model.pid} and will be recovered in {__interval_stream} seconds')
            source_model = __source_repository.get(stream_model.id)
            dic = source_model.__dict__
            __event_bus.publish(json.dumps(dic, ensure_ascii=False, indent=4))
            time.sleep(1)
        else:
            logger.info(f'FFmpeg stream process {stream_model.name} - {stream_model.pid} is running')


def __check_ffmpeg_record_running_process():
    logger.info('checking FFmpeg running RTMP server record processes')
    stream_models = __stream_repository.get_all()
    for stream_model in stream_models:
        pipe_record_enabled = stream_model.stream_type == StreamType.FLV and stream_model.record
        if pipe_record_enabled and not psutil.pid_exists(stream_model.record_flv_pid):
            stream_model.record_flv_failed_count += 1
            __stream_repository.update(stream_model, ['record_flv_failed_count'])
            logger.warn(
                f'a failed stream FFmpeg record process was detected for model {stream_model.name} - {stream_model.pid} and will be recovered in {__interval_record} seconds')
            source_model = __source_repository.get(stream_model.id)
            __start_flv_stream_handler.create_piped_ffmpeg_process(source_model, stream_model)
            time.sleep(1)
        else:
            logger.info(f'FFmpeg record process {stream_model.name} - {stream_model.pid} is running')


def check_ffmpeg_stream_running_process():
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(__interval_stream).seconds.do(__check_ffmpeg_stream_running_process)
    while True:
        scheduler_instance.run_pending()
        time.sleep(1)


def check_ffmpeg_record_running_process():
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(__interval_record).seconds.do(__check_ffmpeg_record_running_process)
    while True:
        scheduler_instance.run_pending()
        time.sleep(1)
