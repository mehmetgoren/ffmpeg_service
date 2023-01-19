from __future__ import annotations

import os
from pathlib import Path
import subprocess
from datetime import datetime
from os import path
from typing import List

from common.utilities import logger
from stream.stream_repository import StreamRepository


class ConcatDemuxer:
    def __init__(self, stream_repository: StreamRepository):
        self.stream_repository = stream_repository

    def concatenate(self, source_id: str, filenames: List[str], output_filename: str) -> subprocess.Popen | None:
        if len(filenames) == 0:
            return None

        p = Path(output_filename)
        output_dir = p.parent.absolute()
        list_txt_path = path.join(output_dir, 'list.txt')
        with open(list_txt_path, 'w') as f:
            for filename in filenames:
                f.write(f"file '{filename}'\n")

        proc = None
        try:
            args: List[str] = ['ffmpeg', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list_txt_path, '-c', 'copy', '-y', output_filename]
            proc = subprocess.Popen(args, stderr=subprocess.PIPE)
            logger.info(f'a concat demuxer subprocess has been opened at {datetime.now()}')
            stream_model = self.stream_repository.get(source_id)
            stream_model.concat_demuxer_args = ' '.join(args)
            stream_model.concat_demuxer_pid = proc.pid
            self.stream_repository.add(stream_model)
            proc.wait()
        finally:
            try:
                os.remove(list_txt_path)
            except BaseException as ex:
                logger.error(f'an error occurred while deleting list.txt, err: {ex}')
        return proc
