import os
import multiprocessing

from dotenv import load_dotenv

load_dotenv(override=True)

APP_HOME = os.getenv(
    "APP_HOME") or "/home/vadim/borgcam"

PASSWORD = os.getenv("PASSWORD") or "1701"  # Configure me!
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "dev"  # Configure me!
JWT_EXPIRATION = os.getenv("JWT_EXPIRATION") or 60

LOG_PATH = os.getenv("LOG_PATH") or "/var/log/borgcam.log"
LOG_LEVEL = os.getenv("LOG_LEVEL") or "INFO"

# Uvicorn settings.
# Note: currently, using more than 1 workers causes issues with camera access.
SERVER_WORKERS = os.getenv("SERVER_WORKERS") or 1
SERVER_HOST = os.getenv("SERVER_HOST") or "0.0.0.0"
SERVER_PORT = os.getenv("SERVER_PORT") or 8000
SERVER_PID = os.getenv("SERVER_PID") or os.path.join(
    "/tmp", "borgcam.pid")
SERVER_USE_SSL = ((os.getenv("SERVER_USE_SSL") or "true").lower() != "false")

SSL_PATH = os.getenv("SSL_PATH") or os.path.join(APP_HOME, "ssl")
SSL_CERT = os.getenv("SSL_CERT") or os.path.join(SSL_PATH, "cert.pem")
SSL_KEY = os.getenv("SSL_KEY") or os.path.join(SSL_PATH, "key.pem")
SSL_PASSWORD = os.getenv("SSL_PASSWORD") or "1234"

# Systemd service settings.
SERVICE_NAME = os.getenv("SERVICE_NAME") or "borgcam"
SERVICE_USER = os.getenv("SERVICE_USER") or "root"

# Camera settings.
CAMERA_SENSOR_MODE = 1

# Pan/tilt hat settings.
MIN_PAN = int(os.getenv("MIN_PAN") or -90)
MAX_PAN = int(os.getenv("MAX_PAN") or 90)
MIN_TILT = int(os.getenv("MIN_TILT") or -90)
MAX_TILT = int(os.getenv("MAX_TILT") or 90)
