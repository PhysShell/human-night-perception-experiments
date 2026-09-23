#!/usr/bin/env python3
"""Format conversion only (tracks/hdrvdp3): read an image with OpenImageIO (EXR, PNG 8/16-bit,
PFM, HDR) and write a trivial raw container Octave can fread:
  int32 height, width, channels, dtype (1=uint8, 2=uint16, 3=float32), then row-major H x W x C data.
Pixel values are passed through unchanged (no scaling, no colour conversion)."""
import sys, numpy as np, OpenImageIO as oiio
src, dst = sys.argv[1], sys.argv[2]
inp = oiio.ImageInput.open(src)
if inp is None:
    sys.exit("cannot open " + src + ": " + oiio.geterror())
spec = inp.spec()
fmt = {"uint8": (oiio.UINT8, np.uint8, 1), "uint16": (oiio.UINT16, np.uint16, 2)}.get(str(spec.format), (oiio.FLOAT, np.float32, 3))
a = inp.read_image(0, 0, 0, spec.nchannels, fmt[0]); inp.close()
a = np.ascontiguousarray(np.asarray(a, dtype=fmt[1]).reshape(spec.height, spec.width, spec.nchannels))
with open(dst, "wb") as f:
    np.array([spec.height, spec.width, spec.nchannels, fmt[2]], dtype="<i4").tofile(f)
    a.astype(a.dtype.newbyteorder("<")).tofile(f)
