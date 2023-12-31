#!/bin/bash

# Picamera2 without GUI dependencies
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y libcap-dev

# Pantilthat
sudo apt install -y python3-dev python3-smbus python3-pantilthat

# Quart and other app dependencies
sudo apt install -y python3-quart python3-dotenv python3-mypy python3-jwt

# Uvicorn server
sudo apt install -y uvicorn python3-uvicorn

# Enable i2c
sudo raspi-config nonint do_i2c 0