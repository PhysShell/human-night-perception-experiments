"""Format-conversion wrapper (not a model): VSS `render` (wgpu branch 22055373) writes its display pass into an
Rgba8UnormSrgb target (vss-desktop/src/cmd/render.rs l.222) although inputs are uploaded as Rgba8Unorm
(vss/src/node/rgb_buffer/upload.rs l.223) without sRGB decoding, so every output = sRGB_OETF(expected).
This script inverts that one extra encode (IEC 61966-2-1 EOTF on the 8-bit code values) and reports the
difference to a reference image. Usage: python undo_extra_srgb.py in.png out.png [reference.png]"""
import sys, numpy as np, OpenImageIO as oiio
def rd(p):
    b = oiio.ImageBuf(p); return b.get_pixels(oiio.FLOAT)[..., :3]
def eotf(v): return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
x = rd(sys.argv[1]); y = eotf(x)
out = oiio.ImageBuf(oiio.ImageSpec(y.shape[1], y.shape[0], 3, oiio.UINT8))
out.set_pixels(oiio.ROI(), np.clip(np.round(y * 255), 0, 255).astype(np.uint8)); out.write(sys.argv[2])
if len(sys.argv) > 3:
    r = rd(sys.argv[3]); q = np.round(y * 255) / 255
    d = np.abs(q - r) * 255
    print(f"{sys.argv[2]} vs {sys.argv[3]}: max |diff| = {d.max():.0f} codes, mean = {d.mean():.3f} codes, "
          f"pixels differing by >=1 code = {(d.max(axis=2) > 0.5).mean()*100:.3f} %")
