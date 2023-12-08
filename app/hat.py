import pantilthat

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
