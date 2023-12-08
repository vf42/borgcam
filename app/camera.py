import io
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

from .base_camera import BaseCamera
from .config import CAMERA_SENSOR_MODE

class StreamingOutput(io.BufferedIOBase):
    """
    Camera stream buffer.
    """

    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class Camera(BaseCamera):
    @staticmethod
    def frames():
        with Picamera2() as camera:
            mode = camera.sensor_modes[CAMERA_SENSOR_MODE]
            camera.configure(camera.create_video_configuration(
                sensor={
                    "output_size": mode["size"],
                    "bit_depth": mode["bit_depth"]
                }))
            output = StreamingOutput()
            camera.start_recording(JpegEncoder(), FileOutput(output))

            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                yield frame
