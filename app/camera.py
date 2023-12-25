import io
import logging
import sys
import os
from threading import Condition
import traceback

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

from .base_camera import BaseCamera
from .config import CAMERA_SENSOR_MODE, CAMERA_CONTROLS_DAY, CAMERA_CONTROLS_NIGHT


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
    night_mode = False
    mode_toggle_requested = False

    @staticmethod
    def frames():
        try:
            with Picamera2() as camera:
                mode = camera.sensor_modes[CAMERA_SENSOR_MODE]
                camera.configure(camera.create_video_configuration(
                    sensor={
                        "output_size": mode["size"],
                        "bit_depth": mode["bit_depth"]
                    },
                ))
                camera.set_controls(CAMERA_CONTROLS_NIGHT if Camera.night_mode
                                    else CAMERA_CONTROLS_DAY)
                output = StreamingOutput()
                camera.start_recording(JpegEncoder(), FileOutput(output))
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    yield frame
                    if Camera.mode_toggle_requested:
                        Camera.mode_toggle_requested = False
                        if Camera.night_mode:
                            camera.set_controls(CAMERA_CONTROLS_NIGHT)
                        else:
                            camera.set_controls(CAMERA_CONTROLS_DAY)
        except OSError as e:
            # We are getting "Cannot allocate memory" errors from the camera
            # from time to time.
            # https://github.com/raspberrypi/picamera2/issues/887
            # Workaround: die and let systemd restart the service.
            logging.error(f"Camera error: {e}\n{traceback.format_exc()}")
            logging.error("Terminating the service")
            os._exit(1)

    @staticmethod
    def toggle_mode():
        print("Night mode toggle requested")
        Camera.mode_toggle_requested = True
        Camera.night_mode = not Camera.night_mode
