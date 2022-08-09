import asyncio

from common.config import Config
from common.data.heartbeat_repository import HeartbeatRepository
from common.data.service_repository import ServiceRepository
from common.utilities import logger, crate_redis_connection, RedisDb
from sustain.task_manager import add_tasks, start_tasks, clean_others_previous, clean_my_previous


def register_ffmpeg_service():
    connection_service = crate_redis_connection(RedisDb.MAIN)
    service_name = 'ffmpeg_service'
    heartbeat = HeartbeatRepository(connection_service, service_name)
    heartbeat.start()
    service_repository = ServiceRepository(connection_service)
    service_repository.add(service_name, 'ffmpeg_service-instance', 'The FFmpeg Service®')


def main():
    register_ffmpeg_service()

    clean_my_previous()
    clean_others_previous()

    config = Config.create()
    config.save()

    add_tasks()
    logger.info('The FFmpeg Service® has been started...')
    start_tasks()

    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    finally:
        clean_my_previous()
        clean_others_previous()


if __name__ == '__main__':
    main()
