import pybase64
import io
import ffmpeg
import PIL.Image as Image


# that is the reason why I chose python over golang for this microservice: https://github.com/kkroening/ffmpeg-python

# for more information: https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md
class RtspVideoEditor:
    def __init__(self, address: str):
        self.address = address

    def __take_screenshot(self) -> Image:
        x = ffmpeg.input(self.address)
        x = ffmpeg.output(x, 'pipe:', vframes=1, format='image2')
        # args = x.get_args()
        out, _ = x.run(capture_stdout=True)
        img = Image.open(io.BytesIO(out))
        return img

    def take_screenshot(self) -> str:
        image = self.__take_screenshot()
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        img_str = pybase64.b64encode(image_bytes.getvalue())
        return img_str.decode('utf-8')

    def generate_thumbnail(self) -> str:
        image = self.__take_screenshot()
        image.thumbnail((300, 300), Image.LANCZOS)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        img_str = pybase64.b64encode(image_bytes.getvalue())
        return img_str.decode('utf-8')

    def probe(self) -> dict:
        probe_result = ffmpeg.probe(self.address)
        return probe_result
