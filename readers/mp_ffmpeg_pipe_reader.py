import os
import time
from multiprocessing import Process
from typing import List
import subprocess as sp
import numpy as np
import psutil

from common.data.source_model import Preset
from common.utilities import logger, crate_redis_connection, RedisDb
from readers.base_pipe_reader import BasePipeReader, PipeReaderOptions
from stream.stream_repository import StreamRepository


class MpFFmpegPipeReader(BasePipeReader):
    def __init__(self, options: PipeReaderOptions, args: List[str]):
        self.args: List[str] = args
        self.use_filter = True
        self.owner_proc = None
        self.proc_info = None
        super().__init__(options)

    def _create_process(self, options: PipeReaderOptions) -> any:
        self.args.extend(['-tune', 'zerolatency'])
        # if f.preset != Preset.Auto:
        self.args.extend(['-preset', Preset.str(Preset.Ultrafast)])

        o = self.options
        if self.use_filter:
            self.args.append('-filter_complex')
            self.args.append(f'[0]fps=fps={o.frame_rate}:round=up[s0];[s0]scale={o.width}:{o.height}[s1]')
            self.args.extend(['-map', '[s1]', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'])
        else:
            self.args.extend(['-vf', f'fps={o.frame_rate},scale={o.width}:{o.height}'])
            self.args.extend(['-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'])

        return sp.Popen(self.args, stdout=sp.PIPE, stderr=sp.DEVNULL, stdin=sp.PIPE)

    def create_process_proxy(self) -> any:
        return ProcessProxy(self)

    def get_img(self) -> np.array:
        packet = self.process.stdout.read(self.packet_size)
        if len(packet) != self.packet_size:
            msg = f'camera ({self.options.name}) could not capture any frame, packet size: {len(packet)} is not equal to packet size: {self.packet_size}.'
            logger.warning(msg)
            return None
        numpy_img = np.frombuffer(packet, np.uint8).reshape([self.options.height, self.options.width, self.cl_channels])
        return numpy_img

    def is_closed(self) -> bool:  # 100000 calls cost approximately close to 1 seconds for Ryzen 3000 CPU
        try:
            return self.proc_info.status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            logger.error('Multi Processing FFMpeg Reader process is not running anymore')
            return True

    def close(self):
        self.process.terminate()
        if self.owner_proc is not None:
            self.owner_proc.kill()

    def get_pid(self) -> int:
        return self.process.pid

    def read(self):
        self.proc_info = psutil.Process(self.process.pid)

        def do_read(me):
            time.sleep(7.)  # otherwise mp_ffmpeg_reader_owner_pid won't be set due to the delay of the process creation by start stream handler
            main_conn = crate_redis_connection(RedisDb.MAIN)
            rep = StreamRepository(main_conn)
            stream_model = rep.get(self.options.id)
            if stream_model is None:
                logger.error(f'camera ({self.options.id}/{self.options.name}) could not be found in the database, MultiProcessFFmpegPipeReader is now exiting')
                return
            stream_model.mp_ffmpeg_reader_owner_pid = os.getppid()
            rep.add(stream_model)
            while not me.is_closed():
                np_img = me.get_img()
                if np_img is None:
                    time.sleep(1.)
                    continue
                me.send(np_img)

        self.owner_proc = Process(target=do_read, args=(self,))
        self.owner_proc.daemon = True  # ????
        self.owner_proc.start()
        self.owner_proc.join()
        logger.warning(f"FFmpeg Reader owner process has been joined, pid: {self.owner_proc.pid}")
        logger.error(f'camera ({self.options.name}) could not capture any frame and is now being released')


class ProcessProxy:
    def __init__(self, mp_ffmpeg_pipe_reader: MpFFmpegPipeReader):
        self.mp_ffmpeg_pipe_reader = mp_ffmpeg_pipe_reader

    def wait(self):
        self.mp_ffmpeg_pipe_reader.read()

    def terminate(self):
        self.mp_ffmpeg_pipe_reader.close()
