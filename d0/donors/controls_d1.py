#!/usr/bin/env python3
"""D0 control D1: pure exposure + clamp + the scenario's display encoding. No curve, no adaptation, no tuning.
  d1a_photometric : exposure 1 on ABSOLUTE luminance: the display is asked to emit the scene's own cd/m^2,
                    clamped per channel to [black, peak]  (the literal 'show the physical scene' control)
  d1b_key018      : exposure k = 0.18 * peak / Lavg, Lavg = exp(mean(log(Y + 1e-9))) of the frame (the classic
                    log-average key, Reinhard et al. 2002 eq. 1-2 WITHOUT their curve), then the same clamp;
                    per frame for the clip (no temporal smoothing: a naive auto-exposure)
Encoding (d0/display-scenarios.json): SDR  code = OETF((L - black) / (peak - black)), sRGB or gamma 2.2;
HDR1000 code = PQ(L) with Rec.709 -> Rec.2020 primaries (absolute).  16-bit PNG, d0 output contract.
  nix develop -c python3 d0/donors/controls_d1.py
"""
import glob, json, os, sys
import numpy as np
import OpenImageIO as oiio
sys.path.insert(0, "d0")
from display_model import SCEN, M709, M2020

I, O = "d0/work/inputs", "d0/work/out/controls"
Yw = np.array([0.2126, 0.7152, 0.0722])
R709_2020 = np.linalg.inv(M2020) @ M709


def ld(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def oetf(x, tr):
    x = np.clip(x, 0, 1)
    if tr == "srgb":
        return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)
    return x ** (1 / 2.2)


def pq(L):
    m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
    y = np.clip(L / 10000, 0, 1) ** m1
    return ((c1 + c2 * y) / (1 + c3 * y)) ** m2


def encode(L, lum):
    s = SCEN["luminance"][lum]; pk, bk = s["peak_cd_m2"], s["black_cd_m2"]
    if s["transfer"] == "pq":
        return pq(np.clip(L @ R709_2020.T, 0, pk))
    return oetf((np.clip(L, bk, pk) - bk) / (pk - bk), s["transfer"])


def write(path, code):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    spec = oiio.ImageSpec(code.shape[1], code.shape[0], 3, oiio.UINT16)
    b = oiio.ImageBuf(spec); b.set_pixels(oiio.ROI(0, code.shape[1], 0, code.shape[0], 0, 1, 0, 3), np.ascontiguousarray(code, np.float32)); b.write(path)


LUMS = ["SDR100", "SDR200", "BRIGHT500", "HDR1000"]
runs = {"d1a_photometric": {"label": "DOCUMENTED_TARGET_CONFIG", "exposure": 1.0},
        "d1b_key018": {"label": "DOCUMENTED_TARGET_CONFIG", "exposure": "0.18 * peak / log-average(Y), per frame"}}
log = {}


def render(L, lum, cfg):
    if cfg == "d1a_photometric":
        k = 1.0
    else:
        Y = L @ Yw; k = 0.18 * SCEN["luminance"][lum]["peak_cd_m2"] / np.exp(np.mean(np.log(Y + 1e-9)))
    return encode(L * k, lum), k


for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    L = ld(f"{I}/{s}.exr")
    for cfg in runs:
        for lum in LUMS:
            code, k = render(L, lum, cfg)
            write(f"{O}/{cfg}/{s}__PHONE_{lum}_DARK.png", code); log[f"{cfg}/{s}/{lum}"] = k
for f in sorted(glob.glob(f"{I}/S2/frame_*.exr")):
    L = ld(f); n = os.path.basename(f).replace(".exr", ".png")
    for cfg in runs:
        for lum in ("SDR100", "BRIGHT500"):
            code, k = render(L, lum, cfg)
            write(f"{O}/{cfg}/S2__PHONE_{lum}_DARK/{n}", code); log[f"{cfg}/S2/{lum}/{n}"] = k
json.dump({"donor": "controls D1 (exposure + clamp)", "configs": runs, "exposures": log}, open(f"{O}/runs.json", "w"), indent=1)
print("D1 done", {k: v for k, v in log.items() if "/S1/" in k})
