import time
from datetime import datetime

from common.data.source_repository import SourceRepository
from common.event_bus.event_bus import EventBus
from common.utilities import crate_redis_connection, RedisDb, logger, config
from editor.editor_event_handler import EditorEventHandler
from record.vfm_event_handler import VfmEventHandler
from stream.restart_stream_event_handler import RestartStreamEventHandler
from stream.start_stream_event_handler import StartStreamEventHandler
from stream.stop_stream_event_handler import StopStreamEventHandler
from stream.stream_repository import StreamRepository
from sustain.recurrent_jobs.black_screen_monitor import BlackScreenMonitor
from sustain.recurrent_jobs.mac_ip_matching import MacIpMatching
from sustain.scheduler import setup_scheduler
from utils.utils import start_thread
from various.probe_event_handler import ProbeEventHandler

__connection_source = crate_redis_connection(RedisDb.MAIN)
__source_repository = SourceRepository(__connection_source)
__stream_repository = StreamRepository(__connection_source)


def listen_editor_event():
    handler = EditorEventHandler()
    event_bus = EventBus('editor_request')
    event_bus.subscribe_async(handler)


def listen_start_stream_event():
    handler = StartStreamEventHandler(__source_repository, __stream_repository)
    event_bus = EventBus('start_stream_request')
    event_bus.subscribe_async(handler)


def listen_stop_stream_event():
    handler = StopStreamEventHandler(__source_repository, __stream_repository)
    event_bus = EventBus('stop_stream_request')
    event_bus.subscribe_async(handler)


def listen_restart_stream_event():
    handler = RestartStreamEventHandler(__source_repository, __stream_repository)
    event_bus = EventBus('restart_stream_request')
    event_bus.subscribe_async(handler)


def listen_various_events():
    def listen_probe_event():
        while 1:
            try:
                probe_handler = ProbeEventHandler()
                event_bus = EventBus('probe_request')
                event_bus.subscribe_async(probe_handler)
            except BaseException as ex:
                logger.error(f'an error occurred on ProbeEventHandler at {datetime.now()}, err: {ex}')
            time.sleep(1.)

    start_thread(listen_probe_event, [])

    def fn_listen_vfm():
        while 1:
            try:
                vfm_handler = VfmEventHandler(__stream_repository)
                event_bus = EventBus('vfm_request')
                event_bus.subscribe_async(vfm_handler)
            except BaseException as ex:
                logger.error(f'an error occurred on VideoFileMergerEventHandler at {datetime.now()}, err: {ex}')
            time.sleep(1.)

    fn_listen_vfm()


def execute_various_jobs():
    def fn_check_mac_and_ip_mathing():
        mim = MacIpMatching(__source_repository)
        while 1:
            try:
                setup_scheduler(max(config.jobs.mac_ip_matching_interval, 10), mim.check, True)
            except BaseException as ex:
                logger.error(f'an error occurred on VideoFileMergerEventHandler at {datetime.now()}, err: {ex}')
            time.sleep(1.)

    if config.jobs.mac_ip_matching_enabled:
        start_thread(fn_check_mac_and_ip_mathing, [])
    else:
        logger.warning('IP match making is not enabled')

    if config.jobs.black_screen_monitor_enabled:
        logger.info(f'BlackScreenMonitor.start will be executed at {datetime.now()}')
        bsm = BlackScreenMonitor(__source_repository, __stream_repository)
        bsm.run()
    else:
        logger.warning('BlackScreenMonitor is not enabled')
