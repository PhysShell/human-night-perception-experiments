#!/usr/bin/env python3
"""M2.6: resample a frame to the common target display (1920 x 820 by default) with a proper
reconstruction filter, never nearest-neighbour: Blackman-Harris, 3 target pixels wide when
downsampling (Cycles' own pixel filter), 3 SOURCE pixels wide when upsampling. OIIO's filter
width is in destination pixels.
  python3 m26/to_target.py W H in.exr out.exr [in2 out2 ...]
"""
import sys
import OpenImageIO as oiio

W, H = int(sys.argv[1]), int(sys.argv[2])
for src, dst in zip(sys.argv[3::2], sys.argv[4::2]):
    b = oiio.ImageBuf(src)
    b = oiio.ImageBufAlgo.channels(b, (0, 1, 2))
    fw = 3.0 * max(1.0, W / b.spec().width)
    if b.spec().width == W:
        b.write(dst, "float"); continue
    oiio.ImageBufAlgo.resize(b, filtername="blackman-harris", filterwidth=fw,
                             roi=oiio.ROI(0, W, 0, H, 0, 1, 0, 3)).write(dst, "float")
