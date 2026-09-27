"""Hero camera projection, matching n1/scene/scene.py (checked against Blender's own projection in n1/noise.py)."""
import math
W_, H_, HFOV, PITCH, YAW, EYE = 1920, 820, 60.0, -3.0, 10.0, 1.7


def project(p):
    """Pinhole projection matching scene.py's hero camera (checked below against Blender's own projection)."""
    x, y, z = p[0], p[1], p[2] - EYE
    cy, sy = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
    fwd0 = (-sy, cy, 0.0); right0 = (cy, sy, 0.0)                     # yaw > 0 turns the view towards -x
    cp, sp = math.cos(math.radians(PITCH)), math.sin(math.radians(PITCH))
    fwd = (fwd0[0] * cp, fwd0[1] * cp, sp); up = (-fwd0[0] * sp, -fwd0[1] * sp, cp)
    d = (x, y, z); f = sum(a * b for a, b in zip(d, fwd)); r = sum(a * b for a, b in zip(d, right0)); u = sum(a * b for a, b in zip(d, up))
    s = (W_ / 2) / math.tan(math.radians(HFOV / 2))
    return W_ / 2 + s * r / f, H_ / 2 - s * u / f


def project_view(p, loc, yaw, pitch, hfov=60.0, W=1920, H=820):
    """Same pinhole model for any N1.5 view (n1/views.json)."""
    x, y, z = p[0] - loc[0], p[1] - loc[1], p[2] - loc[2]
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    fwd0, right0 = (-sy, cy, 0.0), (cy, sy, 0.0)
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    fwd = (fwd0[0] * cp, fwd0[1] * cp, sp); up = (-fwd0[0] * sp, -fwd0[1] * sp, cp)
    d = (x, y, z); f = sum(a * b for a, b in zip(d, fwd)); r = sum(a * b for a, b in zip(d, right0)); u = sum(a * b for a, b in zip(d, up))
    s = (W / 2) / math.tan(math.radians(hfov / 2))
    return W / 2 + s * r / f, H / 2 - s * u / f
