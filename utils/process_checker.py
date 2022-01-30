import sys
import time
from threading import Thread

import psutil
import schedule

from common.utilities import logger
from streaming.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler


# todo: activate leaky FFmpeg process checker
class ProcessChecker:
    def __init__(self, streaming_repository: StreamingRepository):
        self.streaming_repository = streaming_repository
        self.start_streaming_event_handler = StartStreamingEventHandler(streaming_repository)
        # todo: move to ml_config
        self.interval = 10
        self.leaky_ffmpeg_checker_interval = 300

    def __check_running_process(self):
        logger.info('checking running processes')
        streaming_models = self.streaming_repository.get_all()
        for streaming_model in streaming_models:
            if not psutil.pid_exists(streaming_model.pid):
                streaming_model.failed_count += 1
                self.streaming_repository.update(streaming_model, 'failed_count')
                logger.warn(
                    f'a failed streaming FFmpeg process was detected for model {streaming_model.name} - {streaming_model.pid} and will be recovered in {self.interval} seconds')
                self.start_streaming_event_handler.start_streaming(streaming_model)
                time.sleep(1)
            else:
                logger.info(f'streaming process {streaming_model.name} - {streaming_model.pid} is running')

    # def __check_leaky_ffmpeg_process(self):
    #     logger.info('checking leaking ffmpeg processes')
    #     models = self.streaming_repository.get_all()
    #     ffmpeg_processes = []
    #     for proc in psutil.process_iter():
    #         if proc.name() == "ffmpeg":
    #             ffmpeg_processes.append(proc)
    #     if len(ffmpeg_processes) > len(models):
    #         models_pid_dic = {proc.pid: 'ffmpeg' for proc in models}
    #         del models_pid_dic[-1]
    #         for ffmpeg_process in ffmpeg_processes:
    #             if ffmpeg_process.pid not in models_pid_dic:
    #                 try:
    #                     os.kill(ffmpeg_process.pid, signal.SIGKILL)
    #                     logger.warn(f'a leaked FFmpeg process was detected and killed - {ffmpeg_process.pid}')
    #                 except BaseException as e:
    #                     logger.error(f'an error occurred during killing a leaked FFmpeg process - {e}')

    def start(self):
        th = Thread(target=self.__run)
        th.daemon = True
        th.start()

        # th = Thread(target=self.__run_leaky_ffmpeg_processes)
        # th.daemon = True
        # th.start()

    def __run(self):
        schedule.every(self.interval).seconds.do(self.__check_running_process)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except BaseException as e:
            logger.error('An error occurred during the process checker: {}'.format(e))
        finally:
            sys.exit()  # docker restart the container in production environment

    # def __run_leaky_ffmpeg_processes(self):
    #     schedule.every(self.leaky_ffmpeg_checker_interval).seconds.do(self.__check_leaky_ffmpeg_process)
    #     try:
    #         while True:
    #             schedule.run_pending()
    #             time.sleep(1)
    #     except BaseException as e:
    #         logger.error('An error occurred during the process checker: {}'.format(e))
    #     finally:
    #         sys.exit()
