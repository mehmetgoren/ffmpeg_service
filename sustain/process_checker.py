import time
from datetime import datetime

import psutil
import schedule

from common.data.source_model import StreamType
from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import logger, crate_redis_connection, RedisDb, config
from stream.stream_repository import StreamRepository
from stream.start_stream_event_handler import StartStreamEventHandler, StartFlvStreamHandler
from sustain.rec_stuck.rec_stuck_model import RecStuckModel
from sustain.rec_stuck.rec_stuck_repository import RecStuckRepository
from utils.json_serializer import serialize_json_dic

__connection_main = crate_redis_connection(RedisDb.MAIN)
__source_repository = SourceRepository(__connection_main)
__stream_repository = StreamRepository(__connection_main)
__rec_stuck_repository = RecStuckRepository(__connection_main)

__interval_stream = config.ffmpeg.check_ffmpeg_stream_running_process_interval
__start_stream_event_bus = EventBus('start_stream_request')

__interval_record = config.ffmpeg.check_ffmpeg_record_running_process_interval
__start_stream_event_handler = StartStreamEventHandler(__source_repository, __stream_repository)
__start_flv_stream_handler = StartFlvStreamHandler(__start_stream_event_handler)

__interval_stuck = config.ffmpeg.check_ffmpeg_record_stuck_process_interval
__restart_stream_event_bus = EventBus('restart_stream_request')


# containers are not to be checked since they are handled by Docker's unless-stop policy itself.
# todo: add max fail count
def __check_ffmpeg_stream_running_process():
    logger.info('checking FFmpeg running stream processes')
    stream_models = __stream_repository.get_all()
    for stream_model in stream_models:
        if not psutil.pid_exists(stream_model.pid):
            logger.warn(
                f'a failed stream FFmpeg process was detected for model {stream_model.name} - {stream_model.pid} and will be recovered in {__interval_stream} seconds')
            source_model = __source_repository.get(stream_model.id)
            dic = source_model.__dict__
            __start_stream_event_bus.publish(serialize_json_dic(dic))
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


def __check_ffmpeg_record_stuck_process():
    logger.info('checking FFmpeg running recording stuck processes')
    stream_models = __stream_repository.get_all()
    if len(stream_models) == 0:
        logger.info(f'no stream operation exists, checking stuck recording process operation is now exiting at {datetime.now()}')
        return
    streams_dic = {stream_model.id: stream_model for stream_model in stream_models}
    rec_stuck_models = __rec_stuck_repository.get_all()
    # let's check zombie record first.
    for rec_stuck_model in rec_stuck_models:
        if rec_stuck_model.id not in streams_dic:
            __rec_stuck_repository.remove(rec_stuck_model)
            logger.warn('a zombie recording stuck model found on recstucks and removed')

    def refresh(old: RecStuckModel, curr: RecStuckModel):
        old.last_modified_file = curr.last_modified_file
        old.last_modified_size = curr.last_modified_size
        __rec_stuck_repository.add(old)

    stream_models = __stream_repository.get_all()
    for stream_model in stream_models:
        if stream_model.record:
            db_model = __rec_stuck_repository.get(stream_model.id)
            if db_model is None:
                db_model = RecStuckModel().from_stream(stream_model)
                __rec_stuck_repository.add(db_model)
            else:
                current = RecStuckModel().from_stream(stream_model)
                if db_model.last_modified_file != current.last_modified_file:  # means file has been already changed
                    refresh(db_model, current)
                    continue
                if db_model.last_modified_size < current.last_modified_size:  # means everything works as expected
                    refresh(db_model, current)
                    continue
                # let' s relive the zombie
                db_model.failed_count += 1
                db_model.failed_modified_file = db_model.last_modified_file
                __rec_stuck_repository.add(db_model)
                source_model = __source_repository.get(stream_model.id)
                dic = source_model.__dict__
                __restart_stream_event_bus.publish(serialize_json_dic(dic))
                time.sleep(1)


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


def check_ffmpeg_record_stuck_process():
    scheduler_instance = schedule.Scheduler()
    scheduler_instance.every(__interval_stuck).seconds.do(__check_ffmpeg_record_stuck_process)
    while True:
        scheduler_instance.run_pending()
        time.sleep(1)
