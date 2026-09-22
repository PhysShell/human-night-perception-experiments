#!/usr/bin/env python3
"""Synthetic, luminance-calibrated night test image for M0.

This is TEST DATA, not a vision model: a deliberately crude stand-in for the
target scene with every pixel in absolute units (linear Rec.709/sRGB primaries,
D65 white, Y channel == luminance in cd/m^2), so that operators which need
calibrated input (pcond -h, pfstmo_pattanaik00) receive meaningful numbers.

Luminance levels are order-of-magnitude choices, documented in m0/README.md.
Writes m0/data/synthetic_night.exr (float32) and prints the view angles.
"""
import sys
import numpy as np
import OpenImageIO as oiio

W, H = 1920, 820
HFOV_DEG = 60.0                      # horizontal field of view -> 32 px/deg
rng = np.random.default_rng(1)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
img = np.zeros((H, W, 3), np.float32)

def rgb_for(Y, rgb):
    """Scale a linear-sRGB chromaticity so its luminance equals Y (cd/m^2)."""
    rgb = np.asarray(rgb, np.float32)
    return Y[..., None] * rgb / (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2])

NEUTRAL = (1.0, 1.0, 1.0)
SODIUM = (1.0, 0.45, 0.08)          # HPS-ish warm
WARM_LED = (1.0, 0.72, 0.42)        # ~3000 K
COOL_LED = (0.85, 0.92, 1.0)        # ~5000 K

horizon = 0.46 * H
# Sky: rural moonless sky with a little settlement skyglow near the horizon.
t = np.clip((horizon - yy) / horizon, 0, 1)
sky_Y = 3e-4 + 1.2e-3 * np.exp(-t / 0.15)
img[:] = rgb_for(sky_Y, (0.85, 0.85, 1.0))
glow = 1.5e-3 * np.exp(-((xx - 0.7 * W) / (0.12 * W)) ** 2) * np.exp(-t / 0.08)
img += rgb_for(glow, WARM_LED)

# Distant hills: barely darker than the sky.
hill = horizon - 18 - 22 * np.sin(xx / W * 5.0 + 1.0) - 10 * np.sin(xx / W * 13.0)
mask = yy > hill
img[mask] = rgb_for(np.full(mask.sum(), 2.0e-4, np.float32), NEUTRAL)

# Fields: dark, with fine furrow texture (tests acuity loss) and low-freq variation.
field = yy > horizon + 6
furrows = 1.0 + 0.35 * np.sin(xx * 0.9 + 40 * np.log1p((yy - horizon).clip(0))) 
lowf = 1.0 + 0.3 * np.sin(xx / 170.0) * np.cos(yy / 90.0)
field_Y = (1.5e-4 + 4e-4 * ((yy - horizon) / (H - horizon)).clip(0, 1)) * furrows * lowf
img[field] = rgb_for(field_Y[field], (0.9, 0.95, 0.85))

# Poplar-like silhouettes: tall ellipses with ragged edges, near-black.
for cx, base, h, w in [(160, 0.80, 430, 38), (215, 0.81, 470, 44), (270, 0.79, 400, 34),
                       (1450, 0.62, 170, 16), (1478, 0.62, 185, 18), (1506, 0.625, 160, 15),
                       (1534, 0.63, 175, 17), (1780, 0.70, 300, 30)]:
    by = base * H
    cy = by - h / 2
    rag = 1.0 + 0.18 * rng.standard_normal((H, W)).astype(np.float32)
    r = ((xx - cx) / (w * rag)) ** 2 + ((yy - cy) / (h / 2)) ** 2
    tree = (r < 1.0) & (yy < by + 4)
    img[tree] = rgb_for(np.full(tree.sum(), 3e-5, np.float32), NEUTRAL)

# Mesopic Purkinje probe: two equal-photopic-luminance patches (red, blue) at 0.03 cd/m^2.
for x0, col in [(560, (1.0, 0.05, 0.03)), (640, (0.05, 0.12, 1.0))]:
    sl = np.s_[700:760, x0:x0 + 60]
    img[sl] = rgb_for(np.full((60, 60), 0.03, np.float32), col)

# Distant road: a dense chain of lamps crossing the view almost perpendicularly.
# Each lamp is sub-pixel; its luminous intensity is spread into one pixel
# (pixel-averaged luminance). Spacing shrinks with distance -> near-continuous ribbon.
def lamp(x, y, Y, col):
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < W and 0 <= yi < H:
        img[yi, xi] += rgb_for(np.array(Y, np.float32), col)

x = 0.12 * W
while x < 0.95 * W:
    u = (x - 0.12 * W) / (0.83 * W)              # 0 near, 1 far
    y = horizon + 30 - 22 * u                    # slight diagonal toward horizon
    spacing = 9.0 - 6.5 * u                      # px between lamps
    trans = np.exp(-(0.4 + 1.6 * u))             # crude haze extinction, 0.67 .. 0.13
    lamp(x, y, 4000.0 * trans * (0.8 + 0.4 * rng.random()), SODIUM)
    x += spacing * (0.85 + 0.3 * rng.random())

# Sparse village lights.
for _ in range(70):
    cx = rng.choice([0.33, 0.68, 0.72, 0.9]) * W + rng.normal(0, 30)
    cy = horizon - 2 + rng.normal(0, 3)
    lamp(cx, cy, float(rng.uniform(200, 2500)), WARM_LED if rng.random() < 0.7 else COOL_LED)

out = sys.argv[1] if len(sys.argv) > 1 else "m0/data/synthetic_night.exr"
spec = oiio.ImageSpec(W, H, 3, oiio.FLOAT)
spec.attribute("oiio:ColorSpace", "lin_rec709")
spec.attribute("ImageDescription",
               "Synthetic night test image; linear Rec.709 primaries; Y = luminance in cd/m^2; "
               f"HFOV {HFOV_DEG} deg")
o = oiio.ImageOutput.create(out)
o.open(out, spec)
o.write_image(img)
o.close()
vfov = 2 * np.degrees(np.arctan(np.tan(np.radians(HFOV_DEG / 2)) * H / W))
Y = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
print(f"wrote {out}  {W}x{H}  hfov={HFOV_DEG:.2f} vfov={vfov:.2f}")
print(f"Y min={Y.min():.2e} median={np.median(Y):.2e} logmean={np.exp(np.log(Y + 1e-9).mean()):.2e} max={Y.max():.2e} cd/m^2")
