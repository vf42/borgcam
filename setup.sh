#!/bin/bash

# Picamera2 without GUI dependencies
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y libcap-dev

# Pantilthat
sudo apt install -y python3-dev python3-smbus python3-pantilthat

# Flask and other app dependencies
sudo apt install -y python3-flask python3-dotenv python3-mypy

# Enable i2c
sudo raspi-config nonint do_i2c 0
