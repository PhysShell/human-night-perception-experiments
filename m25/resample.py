#!/usr/bin/env python3
"""Resample a supersampled lamps pass (M25_SS x, 1-px box filter) to the output resolution
with the pixel filter Cycles itself uses by default: Blackman-Harris, "filter_width" 1.5 px,
which Cycles doubles for this filter (intern/cycles/scene/film.cpp, filter_table), i.e. a
window 3 output pixels wide. OIIO's filter width is in output pixels. Checked against Cycles'
own filtering of the true-radius lamps (golden view): peak-row energy 0.756 vs 0.798, total
2.741 vs 2.732; a 1.5-px window gives 0.957 and 3.034 (too sharp, and not energy-conserving).
  python3 m25/resample.py SS in.exr out.exr [in2.exr out2.exr ...]
"""
import sys
import OpenImageIO as oiio

ss = int(sys.argv[1])
for src, dst in zip(sys.argv[2::2], sys.argv[3::2]):
    b = oiio.ImageBuf(src)
    s = b.spec()
    roi = oiio.ROI(0, s.width // ss, 0, s.height // ss, 0, 1, 0, s.nchannels)
    out = oiio.ImageBufAlgo.resize(b, filtername="blackman-harris", filterwidth=3.0, roi=roi)
    out.write(dst, "float")
