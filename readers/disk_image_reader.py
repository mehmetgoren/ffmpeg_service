import asyncio
import base64
from io import BytesIO
from threading import Thread

from common.utilities import logger
from readers.base_reader import BaseReaderOptions, BaseReader


class DiskImageReaderOptions(BaseReaderOptions):
    image_path: str = ''


class DiskImageReader(BaseReader):
    def __init__(self, options: DiskImageReaderOptions):
        super().__init__(options)
        self.options = options
        self.closed = False

    def close(self):
        self.closed = True

    async def __read(self):
        img_path, frame_rate = self.options.image_path, self.options.frame_rate
        self.closed = False
        while not self.closed:
            try:
                with open(img_path, 'rb') as fh:
                    buffered = BytesIO(fh.read())
                self._send(buffered)
                await asyncio.sleep(1. / frame_rate)
            except BaseException as e:
                logger.error(f'An error occurred during the reading image from disk, err: {e}')
                await asyncio.sleep(1)
        logger.info('Disk Image Service has been closed')

    def read(self):
        def fn():
            asyncio.run(self.__read())

        th = Thread(target=fn)
        th.daemon = True
        th.start()

    def _create_base64_img(self, buffered):
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
