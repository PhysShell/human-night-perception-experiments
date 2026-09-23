#!/usr/bin/env python3
"""Sky noise and lamp statistics of a Cycles EXR (179 lm/W convention -> cd/m^2)."""
import sys
import numpy as np
import OpenImageIO as oiio

for f in sys.argv[1:]:
    Y = oiio.ImageBuf(f).get_pixels(oiio.FLOAT)[..., :3] @ [0.2126, 0.7152, 0.0722] * 179
    h = Y.shape[0]
    sky = Y[int(h * .06):int(h * .30)]           # well above the horizon
    print(f"{f.split('/')[-1]:34s} sky median {np.median(sky):.2e}  p99 {np.percentile(sky, 99):.2e}  "
          f"p99.9 {np.percentile(sky, 99.9):.2e}  max {sky.max():.2e}  | lamps max {Y.max():.0f} cd/m2")
