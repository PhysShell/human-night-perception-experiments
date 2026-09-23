#!/usr/bin/env python3
"""M1.1: existing ways to bring pcond's over-range lamp pixels into the display gamut.

Input: display-linear Rec.709 image from m1/pcond_colorimetric.sh (1 = display max). Most
pixels are inside [0,1]; lamp pixels have Y <= 1 but a channel > 1 (warm colour kept).
Every method below is an existing transform (Blender 5.2.2 OCIO config, OCIO builtins,
Radiance clipgamut); this script only chains them and measures:
  * in-gamut fidelity: how much a method changes pixels that were already displayable
    (pcond's darkness lives there -- it must not move);
  * lamps: hue error vs. the input hue, saturation, display luminance.

usage: gamut_compare.py in_display_linear.exr radiance_clipgamut.exr outdir
"""
import colorsys, glob, os, shutil, sys
import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as ocio

src, cg_path, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
cfg = ocio.Config.CreateFromFile(glob.glob(os.path.dirname(os.path.realpath(shutil.which("blender")))
                                           + "/../share/blender/*/datafiles/colormanagement/config.ocio")[0])


def load(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].copy()


def apply(proc, img):
    out = np.ascontiguousarray(img, np.float32).copy()
    proc.getDefaultCPUProcessor().applyRGB(out)
    return out


def cs(a, b):
    return cfg.getProcessor(a, b)


def srgb_decode(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


x = load(src)
oog = x.max(-1) > 1.0

to_srgb = cs("Linear Rec.709", "sRGB")                      # Standard view: per-channel clip
pbr = cfg.getProcessor("Linear Rec.709", "sRGB", "Khronos PBR Neutral", ocio.TRANSFORM_DIR_FORWARD)
aces_view = cfg.getProcessor("Linear Rec.709", "sRGB", "ACES 2.0", ocio.TRANSFORM_DIR_FORWARD)
rgc = ocio.BuiltinTransform("ACES-LMT - ACES 1.3 Reference Gamut Compression")
out_t = ocio.BuiltinTransform("ACES-OUTPUT - ACES2065-1_to_CIE-XYZ-D65 - SDR-100nit-REC709_2.0")


def aces2_roundtrip(img):
    """Treat the pcond result as the display image of ACES 2.0, invert the output transform
    and run it forward again: in-gamut pixels should come back unchanged, over-range ones
    go through ACES 2.0's hue-preserving (JMh) gamut compression."""
    xyz = apply(cs("Linear Rec.709", "Linear CIE-XYZ D65"), img)
    g = ocio.GroupTransform()
    g.appendTransform(ocio.BuiltinTransform(out_t.getStyle(), ocio.TRANSFORM_DIR_INVERSE))
    g.appendTransform(out_t)
    xyz2 = apply(cfg.getProcessor(g), xyz)
    return apply(to_srgb, apply(cs("Linear CIE-XYZ D65", "Linear Rec.709"), xyz2))


methods = {
    "clip_standard": apply(to_srgb, x),
    "radiance_clipgamut": apply(to_srgb, load(cg_path)),
    "pbr_neutral_oog_only": np.where(oog[..., None], apply(pbr, x), apply(to_srgb, x)),
    "aces13_rgc_lmt": apply(to_srgb, apply(cs("ACES2065-1", "Linear Rec.709"),
                                           apply(cfg.getProcessor(rgc), apply(cs("Linear Rec.709", "ACES2065-1"), x)))),
    "aces20_roundtrip": aces2_roundtrip(x),
    "pbr_neutral_whole_image": apply(pbr, x),
    "aces20_view_whole_image": apply(aces_view, x),
}


def hs(rgb):
    h, s, v = colorsys.rgb_to_hsv(*np.clip(rgb, 1e-9, None) / max(rgb.max(), 1e-9))
    return h * 360, s


in_h = np.array([hs(p)[0] for p in x[oog]])
Yw = np.array([0.2126, 0.7152, 0.0722])
print(f"{int(oog.sum())} over-range (lamp) pixels; in-gamut pixels: {int((~oog).sum())}")
print(f"{'method':26s} {'in-gamut max|d|':>16s} {'p99.9|d|':>9s} {'lamp hue err':>13s} {'lamp sat':>9s} {'lamp Y':>7s}")
for name, enc in methods.items():
    lin = srgb_decode(enc)
    d = np.abs(lin[~oog] - np.clip(x[~oog], 0, 1))
    out_hs = np.array([hs(p) for p in lin[oog]])
    herr = np.abs((out_hs[:, 0] - in_h + 180) % 360 - 180)
    print(f"{name:26s} {d.max():16.5f} {np.percentile(d, 99.9):9.5f} {np.median(herr):11.1f}deg"
          f" {np.median(out_hs[:, 1]):9.2f} {np.median(lin[oog] @ Yw):7.3f}")
    oiio.ImageBuf(np.ascontiguousarray(enc)).write(f"{outdir}/{name}.png", "uint8")
print(f"input lamp saturation (median): {np.median([hs(p)[1] for p in x[oog]]):.2f}")
