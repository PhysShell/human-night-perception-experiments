#!/usr/bin/env python3
"""D1-B scene-domain measurements for the Kirk 2011 plug-in runs (no display step).

    tracks/temporal-glare-2009/py.sh d1/kirk2011/measure.py

Every run is measured against ITS OWN input on the D0 masks (d0/work/inputs/masks/<scene>.npz):
  lum_ratio      median(Y_out) / median(Y_in) over the region (Y = Rec.709 luminance of the linear RGB)
  chroma_in/out  u'v' distance from D65 (0.1978, 0.4683) of the region's mean XYZ
  hue_in/out     angle of the u'v' vector about D65 (deg); hue_shift = out - in wrapped to (-180, 180]
  lamp_uv        u'v' of the mean XYZ in the lamp mask, in and out
  detail_ratio   band-pass contrast energy out/in: C = (G_2 - G_8) / G_8 on Y (Gaussians sigma 2 and 8 px),
                 energy = mean(C^2) over the region (ground, sky)
Pairs measured:
  NATIVE_DEFAULT final    : decoded sRGB final PNG   vs decoded sRGB 8-bit input (the plug-in's own input)
  NATIVE_DEFAULT core     : lms2display output       vs the 8-bit codes as the plug-in reads them (linear x64)
  DOCUMENTED_TARGET_CONFIG, SENSITIVITY_RUN core : lms2display output vs the absolute input (cd/m^2)
The core's RGB is the plug-in's (Apple Cinema HD) monitor RGB; it is read here as linear Rec.709 without
conversion, as the plug-in sends it to the screen. Luminance ratios therefore include the donor's arbitrary
units (input x scale -> H -> M^-1); only ratios between regions/levels and colour measures are comparable.
"""
import json, os
import numpy as np
import OpenImageIO as oiio
from scipy.ndimage import gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
C = os.path.join(HERE, ".cache")
INP = os.path.join(REPO, "d0/work/inputs")
M709 = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
UVW = np.array([0.1978, 0.4683])
REGIONS = ["sky", "tree", "ground", "lamp", "near_lamp"]


def rd(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def uv(XYZ):
    X, Y, Z = XYZ
    d = X + 15 * Y + 3 * Z
    return np.array([4 * X / d, 9 * Y / d]) if d > 0 else np.array([np.nan, np.nan])


def colour(rgb, m):
    XYZ = (rgb[m] @ M709.T).mean(0)
    u = uv(XYZ); dv = u - UVW
    return u, float(np.hypot(*dv)), float(np.degrees(np.arctan2(dv[1], dv[0])))


def bandpass_energy(Y, m):
    g2 = gaussian_filter(Y, 2); g8 = gaussian_filter(Y, 8)
    Cc = (g2 - g8) / np.maximum(g8, 1e-30)
    return float(np.mean(Cc[m] ** 2))


def measure(rgb_in, rgb_out, masks):
    # the donor can emit NaN (negative S-cone value from its RGB->LMSR matrix on saturated red -> pow(<0, 0.5));
    # such pixels are counted and excluded from every region
    finite = np.isfinite(rgb_out).all(-1)
    Yi = rgb_in @ M709[1]; Yo = rgb_out @ M709[1]
    res = {"_n_nonfinite_px": int((~finite).sum())}
    for r in REGIONS:
        m = masks.get(r)
        if m is None or m.sum() == 0:
            continue
        m = m & finite
        ui, ci, hi = colour(rgb_in, m); uo, co, ho = colour(rgb_out, m)
        d = dict(n_px=int(m.sum()), Y_in_median=float(np.median(Yi[m])), Y_out_median=float(np.median(Yo[m])),
                 lum_ratio=float(np.median(Yo[m]) / max(np.median(Yi[m]), 1e-30)),
                 chroma_in=ci, chroma_out=co, hue_in=hi, hue_out=ho,
                 hue_shift=float((ho - hi + 180) % 360 - 180), uv_in=ui.tolist(), uv_out=uo.tolist())
        if r in ("ground", "sky"):
            ei = bandpass_energy(Yi, m); eo = bandpass_energy(Yo, m)
            d.update(detail_energy_in=ei, detail_energy_out=eo, detail_ratio=eo / max(ei, 1e-30))
        res[r] = d
    return res


def main():
    runs = json.load(open(os.path.join(HERE, "runs.json")))["runs"]
    out = []
    for r in runs:
        cfg, s, name = r["config"], r["scene"], r["name"]
        masks = dict(np.load(os.path.join(INP, "masks", s.split("_")[0] + ".npz")))
        D = os.path.join(C, "out", cfg)
        if cfg == "NATIVE_DEFAULT":
            i8 = rd(os.path.join(D, name + "_input8_linear.exr"))
            out.append(dict(config=cfg, stage="final", scene=s, name=name,
                            regions=measure(i8, rd(os.path.join(D, name + ".exr")), masks)))
            codes = oiio.ImageBuf(os.path.join(D, name + "_input8.png")).get_pixels(oiio.FLOAT)[..., :3] * 255 * 64
            out.append(dict(config=cfg, stage="core", scene=s, name=name,
                            regions=measure(codes.astype(np.float64), rd(os.path.join(D, name + "_core.exr")), masks)))
        else:
            rgb = rd(os.path.join(INP, s + ".exr")) * r["level_multiplier"]
            out.append(dict(config=cfg, stage="core", scene=s, name=name, level_multiplier=r["level_multiplier"],
                            regions=measure(rgb, rd(os.path.join(D, name + ".exr")), masks)))
        print(cfg, out[-1]["stage"], name, {k: (round(v["lum_ratio"], 4) if isinstance(v, dict) else v) for k, v in out[-1]["regions"].items()})
    json.dump(dict(doc=__doc__, results=out), open(os.path.join(HERE, "results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
