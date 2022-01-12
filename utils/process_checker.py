import sys
import time
from threading import Thread

import psutil
import schedule

from common.utilities import logger
from data.streaming_repository import StreamingRepository
from streaming.start_streaming_event_handler import StartStreamingEventHandler


class ProcessChecker:
    def __init__(self, streaming_repository: StreamingRepository):
        self.streaming_repository = streaming_repository
        self.start_streaming_event_handler = StartStreamingEventHandler(streaming_repository)
        # todo: move to ml_config
        self.interval = 10
        self.leaky_ffmpeg_checker_interval = 300

    def __check_running_process(self):
        logger.info('checking running processes')
        models = self.streaming_repository.get_all()
        for model in models:
            if not psutil.pid_exists(model.pid):
                model.failed_count += 1
                self.streaming_repository.update(model, 'failed_count')
                logger.warn(
                    f'a failed FFmpeg process was detected for model {model.name} - {model.pid} and will be recovered in {self.interval} seconds')
                self.start_streaming_event_handler.start_streaming(model)
            else:
                logger.info(f'process {model.name} - {model.pid} is running')

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
