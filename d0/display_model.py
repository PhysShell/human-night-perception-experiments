#!/usr/bin/env python3
"""D0 common display model: donor CODE VALUES -> light the display emits (+ reflected ambient), in cd/m^2.
Every donor is decoded by THIS model with the scenario from d0/display-scenarios.json, so no donor is judged by its
own display model. Parametric scenarios, not measured hardware.

  SDR (srgb | gamma2.2):  L_c = black + (peak - black) * EOTF(V_c)          per channel, Rec.709 primaries
  HDR (pq):               L_c = black + PQ^-1(V_c) * (peak - black) / peak, PQ^-1 clipped to [0, peak], Rec.2020 primaries
  ambient:                + E_ambient * reflectivity / pi, neutral (D65), on every channel
Returned: XYZ (cd/m^2) and linear Rec.709 RGB (cd/m^2; out-of-709 negatives kept in XYZ, clipped to 0 in RGB).
  python3 d0/display_model.py CODE.png LUM AMB OUT.exr      (writes linear Rec.709 cd/m^2 for HDR-VDP etc.)
"""
import json, os, sys
import numpy as np
import OpenImageIO as oiio

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = json.load(open(os.path.join(HERE, "display-scenarios.json")))
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M2020 = np.array([[0.6369580, 0.1446169, 0.1688810], [0.2627002, 0.6779981, 0.0593017], [0.0000000, 0.0280727, 1.0609851]])
XYZ2709 = np.linalg.inv(M709)


def eotf(v, transfer):
    v = np.clip(v, 0, 1)
    if transfer == "srgb":
        return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    if transfer == "gamma2.2":
        return v ** 2.2
    if transfer == "pq":                                   # SMPTE ST 2084, returns cd/m^2
        m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
        p = v ** (1 / m2)
        return 10000 * (np.maximum(p - c1, 0) / (c2 - c3 * p)) ** (1 / m1)
    raise ValueError(transfer)


def read_code(path):
    b = oiio.ImageBuf(path)
    a = b.get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)   # OIIO normalises integer formats to [0, 1]
    return a


def decode(code, lum, amb="DARK"):
    s = SCEN["luminance"][lum]; a = SCEN["ambient"][amb]
    pk, bk = s["peak_cd_m2"], s["black_cd_m2"]
    if s["transfer"] == "pq":
        lin = bk + np.clip(eotf(code, "pq"), 0, pk) * (pk - bk) / pk
        M = M2020
    else:
        lin = bk + (pk - bk) * eotf(code, s["transfer"])
        M = M709
    lin = lin + a["E_ambient_lux"] * a["reflectivity"] / np.pi
    XYZ = lin @ M.T
    return XYZ, np.maximum(XYZ @ XYZ2709.T, 0)


def save_exr(path, a):
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT); spec.attribute("compression", "zip")
    b = oiio.ImageBuf(spec); b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a, np.float32)); b.write(path)


if __name__ == "__main__":
    XYZ, rgb = decode(read_code(sys.argv[1]), sys.argv[2], sys.argv[3])
    save_exr(sys.argv[4], rgb)
