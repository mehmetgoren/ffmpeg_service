import time
import ffmpeg
import numpy as np

from common.utilities import logger
from readers.base_pipe_reader import BasePipeReader, PipeReaderOptions


class FFmpegPipeReader(BasePipeReader):
    def __init__(self, options: PipeReaderOptions):
        super().__init__(options)

    def _create_process(self, options: PipeReaderOptions) -> any:
        stream = ffmpeg.input(options.address)
        stream = ffmpeg.filter(stream, 'fps', fps=options.frame_rate, round='up')
        if self.has_external_scale:
            stream = ffmpeg.filter(stream, 'scale', options.width, options.height)
        stream = ffmpeg.output(stream, 'pipe:', format='rawvideo', pix_fmt='rgb24')
        return ffmpeg.run_async(stream, pipe_stdout=True)

    def is_closed(self) -> bool:
        return self.process.poll() is not None

    def close(self):
        self.process.terminate()

    def get_pid(self) -> int:
        return self.process.pid

    def get_img(self) -> np.array:
        packet = self.process.stdout.read(self.packet_size)
        if len(packet) == 0:
            return None
        numpy_img = np.frombuffer(packet, np.uint8).reshape([self.options.height, self.options.width, self.cl_channels])
        return numpy_img

    def read(self):
        while not self.is_closed():
            np_img = self.get_img()
            if np_img is None:
                # # _close_stream(source, name, 1)
                # break
                logger.error(f'camera ({self.options.name}) could not capture any frame')
                time.sleep(1.)
                continue
            self.send(np_img)
        logger.error(f'camera ({self.options.name}) is now being released')
