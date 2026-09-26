#!/usr/bin/env python3
"""D1-B1: Filament scotopicAdaptation() (verbatim) on S0, S1, S4; nightAdaptation a in {0, 0.25, 0.5, 1}; input
scale s = 1 (linear Rec.709 read as cd/m^2; Filament defines no absolute anchor - see gates.py). Scene-domain
measurements against the donor's own input (no display): per region (d0 masks) Y out/in, chroma and hue angle
(u'v' about D65), lamp chroma/hue, band-pass detail energy out/in. Sheet: ONE viewing aid for all panels - the
INPUT's log-average key 0.18 applied to input and outputs alike, clip, sRGB - so the luminance change is visible.
Outputs: .cache/out/a<a>/<scene>.exr (not committed), scenes.json, sheet_S1.png.
  d1/filament/setup.sh; tracks/temporal-glare-2009/py.sh d1/filament/run_scenes.py
"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import gaussian_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
D = "d1/filament"; C = f"{D}/.cache"; BIN = f"{C}/scotopic"
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WU = np.array([0.1978, 0.4683]); AS = [0.0, 0.25, 0.5, 1.0]


def ld(p): return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float32)


def run(img, a):
    H, W = img.shape[:2]; np.ascontiguousarray(img).tofile(f"{C}/s_in.f32")
    subprocess.run([BIN, f"{C}/s_in.f32", f"{C}/s_out.f32", str(H * W), repr(a)], check=True)
    o = np.fromfile(f"{C}/s_out.f32", np.float32).reshape(H, W, 3); os.remove(f"{C}/s_in.f32"); os.remove(f"{C}/s_out.f32"); return o


def save(p, a):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    sp = oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT); sp.attribute("compression", "zip"); b = oiio.ImageBuf(sp)
    b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a)); b.write(p)


def stats(rgb, m):
    X = np.maximum(rgb.astype(np.float64), 0) @ M709.T; Y = X[..., 1]; s = X[..., 0] + 15 * Y + 3 * X[..., 2] + 1e-30
    du, dv = 4 * X[..., 0] / s - WU[0], 9 * Y / s - WU[1]; o = {}
    for r in ("sky", "tree", "ground", "lamp"):
        if r in m and m[r].any():
            k = m[r]; o[r] = {"Y_median": float(np.median(Y[k])), "chroma_uv": float(np.median(np.hypot(du[k], dv[k]))),
                              "hue_deg": float(np.degrees(np.arctan2(np.median(dv[k]), np.median(du[k]))))}
    if "sky" in o and "tree" in o: o["sky_tree_weber"] = float(1 - o["tree"]["Y_median"] / o["sky"]["Y_median"])
    return o, Y


def dogv(Y, k):
    L = np.log10(np.maximum(Y, 1e-12)); return float(np.var((gaussian_filter(L, 1) - gaussian_filter(L, 4))[k]))


res = {"donor": "Filament scotopicAdaptation() (google/filament ef1a133d, Apache-2.0), verbatim", "input_scale_s": 1.0, "label": "SENSITIVITY_RUN over nightAdaptation", "scenes": {}}
keep = {}
for sc in ("S0", "S1", "S4"):
    img = ld(f"d0/work/inputs/{sc}.exr"); m = dict(np.load(f"d0/work/inputs/masks/{sc}.npz"))
    sin, Yin = stats(img, m); e = {"in": sin}
    for a in AS:
        o = run(img, a); save(f"{C}/out/a{a:g}/{sc}.exr", o)
        so, Yo = stats(o, m); so["finite"] = bool(np.isfinite(o).all()); so["neg_frac"] = float((o < 0).any(-1).mean())
        so["detail_out_over_in"] = {r: dogv(Yo, m[r]) / max(dogv(Yin, m[r]), 1e-30) for r in ("sky", "ground") if r in m and m[r].any()}
        e[f"a{a:g}"] = so
        if sc == "S1": keep[a] = o
    res["scenes"][sc] = e; print(sc, json.dumps({k: (v.get("sky"), v.get("lamp")) for k, v in e.items()})[:600], flush=True)
json.dump(res, open(f"{D}/scenes.json", "w"), indent=1)
# sheet: one viewing aid for all panels
img = ld("d0/work/inputs/S1.exr"); Yin = img @ M709[1]; k = 0.18 / np.exp(np.mean(np.log(Yin + 1e-9)))
def aid(x):
    v = np.clip(x * k, 0, 1); v = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)
    h, w = v.shape[:2]; return v[: h // 2 * 2, : w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean((1, 3))
fig, axs = plt.subplots(len(AS) + 1, 1, figsize=(10, 2.4 * (len(AS) + 1)))
axs[0].imshow(aid(img)); axs[0].set_title("S1 input (abs. cd/m^2) [aid]", fontsize=8, loc="left")
for ax, a in zip(axs[1:], AS):
    s = res["scenes"]["S1"][f"a{a:g}"]
    ax.imshow(aid(keep[a])); ax.set_title(f"Filament scotopicAdaptation, nightAdaptation = {a:g}, s = 1 [aid]: sky Y x{s['sky']['Y_median'] / res['scenes']['S1']['in']['sky']['Y_median']:.2f}, "
                                          f"sky chroma {s['sky']['chroma_uv']:.3f}, lamp chroma {s['lamp']['chroma_uv']:.3f}", fontsize=8, loc="left")
for ax in axs: ax.axis("off")
fig.suptitle("[aid] = VIEWING AID, not part of the donor: the INPUT's log-average key 0.18 applied to every panel, clip, sRGB", fontsize=9)
plt.tight_layout(rect=[0, 0, 1, 0.98]); plt.savefig(f"{D}/sheet_S1.png", dpi=100)
