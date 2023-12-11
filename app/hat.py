import pantilthat

from . import config

def reset_hat():
    """
    Reset pan/tilt position
    """
    pantilthat.pan(0)
    pantilthat.tilt(0)

# Pan/Tilt controls.
def pan(offset):
    current = pantilthat.get_pan()
    new = current + offset
    if new < config.MIN_PAN:
        new = config.MIN_PAN
    elif new > config.MAX_PAN:
        new = config.MAX_PAN
    pantilthat.pan(new)

def tilt(offset):
    current = pantilthat.get_tilt()
    new = current + offset
    if new < config.MIN_TILT:
        new = config.MIN_TILT
    elif new > config.MAX_TILT:
        new = config.MAX_TILT
    pantilthat.tilt(new)

def move_camera(direction):
    """
    Move camera in specified direction.
    """
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
