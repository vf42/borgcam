#!/bin/bash

# Check that we are running as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Configure the systemd service
./scripts/configure-systemd
