#!/usr/bin/env python3
"""D1 donor iCAM06_APPEARANCE: iCAM06 V1.3's image-appearance output XYZ_tm (the model output BEFORE its display
step iCAM06_disp), absolute input (max_L = 0), p 0.7, gamma 1.2 (dark surround, Readme). Uses the D0.1 driver
d0/donors/icam06/icam06_ladder.m, which calls the original sub-functions in the order of iCAM06_HDR.m.
XYZ_tm is in the model's own response units, NOT cd/m^2: only ratios within an image and chromaticities are read.
Scene-domain measurements against the model's own input (no display): per region (d0 masks)
  Y ratio to the image's own p99.9 (in / out), region-to-region Weber (sky -> tree), chroma = u'v' distance from
  D65 white (in / out), hue angle of the u'v' vector about D65 (in / out), lamp chromaticity, band-pass detail
  energy (DoG sigma 1 vs 4 px, log domain) out/in on sky and ground.
Outputs: .cache/<scene>_XYZ_tm.exr (not committed: S4/S5 are Fairchild-derived), results.json.
  d0/donors/icam06/setup.sh; tracks/temporal-glare-2009/py.sh d1/icam06_appearance/run.py
"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import gaussian_filter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
C = os.path.abspath("d1/icam06_appearance/.cache"); os.makedirs(C, exist_ok=True)
W0 = os.path.abspath("d0/work/donors/icam06")
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WU = np.array([0.1978, 0.4683])


def uv(X):
    s = X[..., 0] + 15 * X[..., 1] + 3 * X[..., 2] + 1e-30
    return np.stack([4 * X[..., 0] / s, 9 * X[..., 1] / s], -1)


def dog(Y):
    L = np.log10(np.maximum(Y, 1e-12)); return gaussian_filter(L, 1) - gaussian_filter(L, 4)


def region_stats(X, m, name):
    Y = X[..., 1]; u = uv(X) - WU; ref = np.percentile(Y, 99.9)
    out = {}
    for r in ("sky", "tree", "ground", "lamp", "bar", "beside_bar"):
        if r in m and m[r].any():
            k = m[r]
            out[r] = {"Y_over_p99.9": float(np.median(Y[k]) / ref), "chroma_uv": float(np.median(np.hypot(*u[k].T))),
                      "hue_deg": float(np.degrees(np.arctan2(np.median(u[k][:, 1]), np.median(u[k][:, 0]))))}
    if "sky" in out and "tree" in out:
        out["sky_tree_weber"] = float(1 - np.median(Y[m["tree"]]) / np.median(Y[m["sky"]]))
    return out


res = {"donor": "iCAM06_APPEARANCE (iCAM06 V1.3 XYZ_tm, before iCAM06_disp)", "params": {"max_L": 0, "p": 0.7, "gamma_value": 1.2},
       "label": "DOCUMENTED_TARGET_CONFIG", "scenes": {}}
for sc in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    a = oiio.ImageBuf(f"d0/work/inputs/{sc}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float32)
    H, W = a.shape[:2]; fin, fo, fx = f"{C}/in.f32", f"{C}/out.u8", f"{C}/xyz.f32"
    a.tofile(fin)
    env = dict(os.environ, REPO=REPO, ICAM_IN=fin, ICAM_OUT=fo, ICAM_XYZ=fx, ICAM_H=str(H), ICAM_W=str(W), ICAM_P="0.7", ICAM_GAMMA="1.2",
               ICAM_SRC=f"{W0}/src_pristine", ICAM_SHIM=f"{W0}/shim")
    r = subprocess.run(["tracks/hdrvdp3/octave.sh", "d0/donors/icam06/icam06_ladder.m"], env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout + r.stderr)
    xyz = np.fromfile(fx, np.float32).reshape(H, W, 3)
    spec = oiio.ImageSpec(W, H, 3, oiio.FLOAT); spec.attribute("compression", "zip"); b = oiio.ImageBuf(spec)
    b.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(xyz)); b.write(f"{C}/{sc}_XYZ_tm.exr")
    for f in (fin, fo, fx):
        os.remove(f)
    m = dict(np.load(f"d0/work/inputs/masks/{sc.split('_')[0]}.npz"))
    Xin = a.astype(np.float64) @ M709.T; Xout = xyz.astype(np.float64)
    e = {"in": region_stats(Xin, m, "in"), "out": region_stats(Xout, m, "out")}
    for rg in ("sky", "ground"):
        if rg in m and m[rg].any():
            e.setdefault("detail_energy_out_over_in", {})[rg] = float(np.var(dog(Xout[..., 1])[m[rg]]) / max(np.var(dog(Xin[..., 1])[m[rg]]), 1e-30))
    res["scenes"][sc] = e; print(sc, json.dumps(e)[:400], flush=True)
json.dump(res, open("d1/icam06_appearance/results.json", "w"), indent=1)
