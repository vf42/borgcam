import os
import io
import multiprocessing
import logging
import time
from threading import Condition
import asyncio
from typing import AsyncGenerator

from quart import Quart, render_template, Response, websocket

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

import pantilthat

from base_camera import BaseCamera


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


class Broker:
    """
    In-memory message broker.
    https://quart.palletsprojects.com/en/latest/tutorials/chat_tutorial.html
    """

    def __init__(self) -> None:
        self.connections = set()

    async def publish(self, message: str) -> None:
        for connection in self.connections:
            await connection.put(message)

    async def subscribe(self) -> AsyncGenerator[str, None]:
        connection = asyncio.Queue()
        self.connections.add(connection)
        try:
            while True:
                yield await connection.get()
        finally:
            self.connections.remove(connection)


def create_app(test_config=None):
    app = Quart(__name__, instance_relative_config=True)
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

    # Reset pan/tilt position
    pantilthat.pan(0)
    pantilthat.tilt(0)

    # Index
    @app.route('/')
    async def index():
        return await render_template("index.html")

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

    # Pan/Tilt controls.
    def pan(offset):
        current = pantilthat.get_pan()
        new = current + offset
        if new < -90:
            new = -90
        elif new > 90:
            new = 90
        pantilthat.pan(new)

    def tilt(offset):
        current = pantilthat.get_tilt()
        new = current + offset
        if new < -90:
            new = -90
        elif new > 90:
            new = 90
        pantilthat.tilt(new)

    def move_camera(direction):
        if direction == "up":
            tilt(-1)
        elif direction == "down":
            tilt(1)
        elif direction == "left":
            pan(1)
        elif direction == "right":
            pan(-1)
        else:
            raise ValueError(f"Invalid direction: {direction}")

    # Websocket
    broker = Broker()

    async def _receive() -> None:
        while True:
            message = await websocket.receive()
            if message.startswith("move:"):
                try:
                    logging.info(message)
                    move_camera(message.split(":")[1])
                except Exception as e:
                    logging.error(e)
                    await websocket.send(f"error:{e}")

    @app.websocket('/ws')
    async def ws():
        try:
            task = asyncio.ensure_future(_receive())
            async for message in broker.subscribe():
                await websocket.send(message)
        finally:
            task.cancel()
            await task

    return app
