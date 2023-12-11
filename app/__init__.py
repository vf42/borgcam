import os
import multiprocessing
import logging
import time
import asyncio
from typing import AsyncGenerator
from threading import get_ident

from quart import Quart, render_template, Response, websocket, make_response

from .camera import Camera
from .hat import reset_hat, move_camera


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

    reset_hat()

    # Index
    @app.route('/')
    async def index():
        return await render_template("index.html")

    # Camera stream
    def gen_stream(camera):
        """Video streaming generator function."""
        yield b'--frame\r\n'
        my_ident = get_ident()
        while True:
            frame = camera.get_frame(my_ident)
            yield b'Content-Type: image/jpeg\r\n\r\n' + frame\
                + b'\r\n--frame\r\n'

    @app.route('/stream.mjpg')
    async def stream():
        response = await make_response(gen_stream(Camera()), 200, {
            "Content-Type": "multipart/x-mixed-replace; boundary=frame",
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        response.timeout = None # Required to avoid disconnection after 1 min.
        return response

    # Websocket
    broker = Broker()

    async def _receive() -> None:
        while True:
            message = await websocket.receive()
            if message.startswith("move:"):
                try:
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
