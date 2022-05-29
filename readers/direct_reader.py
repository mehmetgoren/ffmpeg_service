from typing import List
import subprocess as sp

from common.data.source_model import Preset
from readers.ffmpeg_reader import FFmpegReader, FFmpegReaderOptions


class DirectReader(FFmpegReader):
    def __init__(self, options: FFmpegReaderOptions, args: List[str]):
        self.args: List[str] = args
        self.use_filter = True
        super().__init__(options)

    def _create_process(self, options: FFmpegReaderOptions) -> any:
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

        return sp.Popen(self.args, stdout=sp.PIPE, stderr=sp.DEVNULL, stdin=sp.PIPE, start_new_session=True)

    def create_process_proxy(self) -> any:
        return ProcessProxy(self)


class ProcessProxy:
    def __init__(self, direct_reader: DirectReader):
        self.direct_reader = direct_reader

    def wait(self):
        self.direct_reader.read()

    def terminate(self):
        self.direct_reader.close()
