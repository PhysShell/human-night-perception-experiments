#!/usr/bin/env python3
"""Format conversion only: Octave raw container (tracks/hdrvdp3/img2raw.py layout) -> float EXR.
(tracks/hdrvdp3/raw2exr.py's ImageOutput.write_image path wrote headers without pixels here.)"""
import sys, numpy as np, OpenImageIO as oiio
with open(sys.argv[1], "rb") as f:
    h, w, c, t = (int(v) for v in np.fromfile(f, "<i4", 4))
    a = np.fromfile(f, {1: "u1", 2: "<u2", 3: "<f4"}[t]).reshape(h, w, c).astype(np.float32)
b = oiio.ImageBuf(oiio.ImageSpec(w, h, c, oiio.FLOAT))
b.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(a))
if not b.write(sys.argv[2]):
    sys.exit(b.geterror())
