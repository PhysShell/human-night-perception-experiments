#!/usr/bin/env python3
"""M2.6: build one full frame at W x H px from the 16 px/deg clip (m25 B_walk, 960 x 410)
and a high-resolution render of the crop region (haze and lamps passes rendered with
M26_CROP): outside the crop, the 16 px/deg frame upsampled; inside, the new render.
The crop holds the near half of the ribbon (where lamps are measured); outside it the frame
is mostly sky and ground below pcond's display black, and it keeps pcond's adaptation
histogram the same (checked: exposure logged per frame).
  python3 m26/composite.py W H CROP(x0,x1,y0,y1; y up) haze16 lamps16 hazeHR lampsHR out_haze out_lamps
"""
import sys
import numpy as np
import OpenImageIO as oiio

W, H = int(sys.argv[1]), int(sys.argv[2])
x0, x1, y0, y1 = (float(v) for v in sys.argv[3].split(","))
h16, l16, hHR, lHR, out_haze, out_lamps = sys.argv[4:10]
roi = oiio.ROI(0, W, 0, H, 0, 1, 0, 3)


def up(p):  # energy-preserving upsample of a 16 px/deg frame (radiance per pixel unchanged)
    b = oiio.ImageBufAlgo.channels(oiio.ImageBuf(p), (0, 1, 2))
    return oiio.ImageBufAlgo.resize(b, filtername="triangle", roi=roi).get_pixels(oiio.FLOAT)


get = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
haze, lamps = up(h16), up(l16)
c0, c1 = int(round(x0 * W)), int(round(x1 * W))
r0, r1 = int(round((1 - y1) * H)), int(round((1 - y0) * H))
haze[r0:r1, c0:c1] = get(hHR)[r0:r1, c0:c1]
lamps[r0:r1, c0:c1] = get(lHR)[r0:r1, c0:c1]
for arr, p in ((haze, out_haze), (lamps, out_lamps)):
    o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.FLOAT))
    o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(arr, np.float32))
    o.write(p)
