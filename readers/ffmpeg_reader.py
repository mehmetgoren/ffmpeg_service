import base64
from io import BytesIO
import ffmpeg
import numpy as np
from PIL import Image

from common.utilities import logger
from readers.base_reader import BaseReaderOptions, BaseReader


class FFmpegReaderOptions(BaseReaderOptions):
    address: str = ''
    width: int = 0
    height: int = 0


class FFmpegReader(BaseReader):
    def __init__(self, options: FFmpegReaderOptions):
        super().__init__(options)
        self.options: FFmpegReaderOptions = options
        has_external_scale = options.width > 0 and options.height > 0
        if not has_external_scale:
            probe = ffmpeg.probe(options.address)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            options.width = int(video_stream['width'])
            options.height = int(video_stream['height'])
            self.stream_fps = video_stream['r_frame_rate'].split('/')
        else:
            self.stream_fps = 0
        self.cl_channels = 3
        logger.info(f'camera ({options.id}) stream fps: {self.stream_fps}')

        self.packet_size = options.width * options.height * self.cl_channels
        stream = ffmpeg.input(options.address)
        stream = ffmpeg.filter(stream, 'fps', fps=options.frame_rate, round='up')
        if has_external_scale:
            stream = ffmpeg.filter(stream, 'scale', options.width, options.height)
        stream = ffmpeg.output(stream, 'pipe:', format='rawvideo', pix_fmt='rgb24')
        self.process = ffmpeg.run_async(stream, pipe_stdout=True)

    def get_img(self) -> np.array:
        packet = self.process.stdout.read(self.packet_size)
        numpy_img = np.frombuffer(packet, np.uint8).reshape([self.options.height, self.options.width, self.cl_channels])
        return numpy_img

    def is_closed(self) -> bool:
        return self.process.poll() is not None

    # todo: move to stable version powered by Redis-RQ
    def close(self):
        self.process.terminate()

    def get_pid(self) -> int:
        return self.process.pid

    # todo: move to stable version powered by Redis-RQ
    def read(self):
        while not self.is_closed():
            np_img = self.get_img()
            if np_img is None:
                # _close_stream(source, name, 1)
                break
            self._send(np_img)
        logger.error(f'camera ({self.options.name}) could not capture any frame and is now being released')

    def _create_base64_img(self, numpy_img: np.array) -> str:
        img = Image.fromarray(numpy_img)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
