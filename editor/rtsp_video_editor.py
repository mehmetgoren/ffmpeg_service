import base64
import io

import ffmpeg
import PIL.Image as Image


# that is the reason why I chose python over golang for this microservice: https://github.com/kkroening/ffmpeg-python

# for more information: https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md
class RtspVideoEditor:
    def __init__(self, rtsp_address: str):
        self.rtsp_address = rtsp_address

    def __take_screenshot(self) -> Image:
        x = ffmpeg.input(self.rtsp_address)
        x = ffmpeg.output(x, 'pipe:', vframes=1, format='image2')
        # args = x.get_args()
        out, _ = x.run(capture_stdout=True)
        img = Image.open(io.BytesIO(out))
        return img

    def take_screenshot(self) -> str:
        image = self.__take_screenshot()
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        img_str = base64.b64encode(image_bytes.getvalue())
        return img_str.decode('utf-8')

    def generate_thumbnail(self) -> str:
        image = self.__take_screenshot()
        image.thumbnail((300, 300), Image.ANTIALIAS)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        img_str = base64.b64encode(image_bytes.getvalue())
        return img_str.decode('utf-8')
