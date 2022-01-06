import io
import ffmpeg
import PIL.Image as Image


# that is the reason why I chose python over golang for this microservice: https://github.com/kkroening/ffmpeg-python

# for more information: https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md
class RtspVideoEditor:
    def __init__(self, rtsp_address: str):
        self.rtsp_address = rtsp_address

    def generate_thumbnail(self) -> bytes:
        probe = ffmpeg.probe(self.rtsp_address)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        channels = 3
        packet_size = width * height * channels
        process = ffmpeg.input(self.rtsp_address).output('pipe:', format='rawvideo', pix_fmt='rgb24').run_async(
            pipe_stdout=True)
        packet = process.stdout.read(packet_size)
        image = Image.open(io.BytesIO(packet))
        size = (int(width / 4), int(height / 4))
        image.thumbnail(size, Image.ANTIALIAS)
        bytes = io.BytesIO()
        image.save(bytes, format='JPEG')
        return bytes.getvalue()
