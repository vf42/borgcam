import os
import io
import multiprocessing
import logging
import time
from threading import Condition

from flask import Flask, render_template, Response

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

from base_camera import BaseCamera


class StreamingOutput(io.BufferedIOBase):
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
            camera.configure(camera.create_video_configuration())
                # TODO: Move size values to configuration
                # main={"size": (640, 480)}))
            output = StreamingOutput()
            camera.start_recording(JpegEncoder(), FileOutput(output))

            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                yield frame


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # TODO: Add config here once I have it
        pass
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Index
    @app.route('/')
    def index():
        return render_template("index.html")

    # Camera stream
    def gen(camera):
        """Video streaming generator function."""
        yield b'--frame\r\n'
        while True:
            frame = camera.get_frame()
            yield b'Content-Type: image/jpeg\r\n\r\n' + frame\
                + b'\r\n--frame\r\n'

    @app.route('/stream.mjpg')
    def stream():
        return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'})

    return app
