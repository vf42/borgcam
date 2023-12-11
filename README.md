## About

A Raspberry Pi camera project, using:
* Pimoroni PanTilt HAT: http://pimoroni.com/pantilthat
* ZeroCam NightVision: https://thepihut.com/products/zerocam-nightvision-for-pizero-raspberry-pi-3

## Usage

Run `setup.sh` to install the dependencies and prepare the working environment.

Run `install.sh` to configure for production use: systemd service for auto-startup etc.

During development, use quart server which can be started like this:
```bash
quart --app app run
```

Uvicorn is used to serve the content for the practical use, see `bin/server`. It may be replaced by any other ASGI server of your choice.

## Configuration

All configuration is done through environment variables. It's best done through .env file.

See `app/config.py` for the list of available configuration params.

Important things to configure:
* By default, uvicorn server is started with SSL enabled, you should provide the ssl certificate or set SERVER_USE_SSL env variable to false.
* Provide your own JWT_SECRET_KEY and PASSWORD values - there's no user-based authentication, just a single password for all.

## Dependencies

See `setup.sh` to see what has to be installed on top of default Raspberry Pi OS package, and execute it, respectively.

Note: not using venv and pip since got to use the packages provided by the distro.

## References

* Thanks [@miguelgrinberg](https://blog.miguelgrinberg.com/) for the [Flask Video Streaming example repo](https://github.com/miguelgrinberg/flask-video-streaming/)
* [Picamera2 Manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
* [Pan-Tilt HAT Python library](https://github.com/pimoroni/pantilt-hat)
* [Interface Icons](https://www.svgrepo.com/collection/super-basic-interface-icons/)
