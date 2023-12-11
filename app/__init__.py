import os
import multiprocessing
import logging
import time
import asyncio
from functools import wraps, partial
from typing import AsyncGenerator
from threading import get_ident

from quart import Quart, render_template, Response, websocket, make_response, session, request
from jwt import encode, decode, InvalidTokenError


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
        app.config.from_object(config)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    reset_hat()

    # Check that the session contains a valid token.
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    def check_session(fn, send_to_login=False):
        async def auth_failed(error):
            if send_to_login:
                return await render_template("login.html", error=error)
            else:
                return {}, 401

        @wraps(fn)
        async def wrapper(*args, **kwargs):
            if not "token" in session:
                return await auth_failed(None)
            else:
                try:
                    token = decode(session["token"], config.JWT_SECRET_KEY,
                                   algorithms=["HS512"])
                    if token["exp"] < time.time():
                        return await auth_failed("Session expired")
                except InvalidTokenError as e:
                    return await auth_failed(None)
            return await fn(*args, **kwargs)
        return wrapper
    
    # TODO: Is there a better way?
    check_session_index = partial(check_session, send_to_login=True)
    check_session_others = partial(check_session, send_to_login=False)
    
    # Index
    @app.route("/", methods=["POST"])
    async def login():
        form = await request.form
        password = form.get("password", None)
        if password == config.PASSWORD:
            session["token"] = encode({
                "exp": time.time() + 3600
            }, config.JWT_SECRET_KEY, algorithm="HS512")
            return await render_template("index.html")
        else:
            return await render_template("login.html", error="Incorrect password")

    @app.route('/', methods=["GET"])
    @check_session_index
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
    @check_session_others
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
    @check_session_others
    async def ws():
        try:
            task = asyncio.ensure_future(_receive())
            async for message in broker.subscribe():
                await websocket.send(message)
        finally:
            task.cancel()
            await task

    return app
