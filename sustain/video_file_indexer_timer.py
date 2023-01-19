from common.utilities import crate_redis_connection, RedisDb, config
from record.video_file_indexer import VideoFileIndexer
from stream.stream_repository import StreamRepository
from sustain.scheduler import setup_scheduler

__connection_main = crate_redis_connection(RedisDb.MAIN)
__stream_repository = StreamRepository(__connection_main)
__vfi = VideoFileIndexer(__stream_repository)
__interval = config.ffmpeg.record_video_file_indexer_interval


def schedule_video_file_indexer():
    setup_scheduler(__interval, __check, True)


def __check():
    stream_models = __stream_repository.get_all()
    for stream_model in stream_models:
        if stream_model.is_record_enabled():
            __vfi.move(stream_model)
