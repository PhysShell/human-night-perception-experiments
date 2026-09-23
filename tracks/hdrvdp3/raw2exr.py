#!/usr/bin/env python3
"""Format conversion only: write an Octave-produced float32 raw (see img2raw.py container) to EXR/PNG/PFM via OIIO."""
import sys, numpy as np, OpenImageIO as oiio
src, dst = sys.argv[1], sys.argv[2]
with open(src, "rb") as f:
    h, w, c, t = np.fromfile(f, dtype="<i4", count=4)
    dt = {1: np.uint8, 2: np.uint16, 3: np.float32}[int(t)]
    a = np.fromfile(f, dtype=np.dtype(dt).newbyteorder("<")).reshape(h, w, c)
out = oiio.ImageOutput.create(dst)
spec = oiio.ImageSpec(int(w), int(h), int(c), {1: oiio.UINT8, 2: oiio.UINT16, 3: oiio.FLOAT}[int(t)])
out.open(dst, spec); out.write_image(a); out.close()
