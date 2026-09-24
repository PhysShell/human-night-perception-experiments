#!/usr/bin/env python3
"""D0 common input set (frozen; FORMAT CONVERSION ONLY: no tone mapping, no eye model).
All scenes: linear Rec.709/D65 RGB float32 EXR, Y = 0.2126 R + 0.7152 G + 0.0722 B in absolute cd/m^2.
UNITS: Cycles/M2.6 frames follow Radiance's 179 lm/W convention (m1/README.md section 1: luminance = 179 * Y), so
S0-S2 are multiplied by K179 = 179 here; B0 (S3) and the Fairchild conversions (S4, S5) are already cd/m^2.
  S0  dark rural still: M2.6 frame 1 'haze' pass only (sky, ground, poplars, lamp-lit ground and haze; no lamp
      spheres), at the PHONE target (1920 x 820), m26/out/p32_t/haze_0001.exr as is
  S1  same frame with the distant lamp ribbon: haze_0001 + lamps_0001 (M2.6 target-first order)
  S2  the 2 s M2.6 walking clip, 48 frames at 24 fps: haze_#### + lamps_####
  S3  B0 point source + dark bar 0.3 deg away (warm source x10 = 8.9e-4 lx at the eye), bar and no-bar pair,
      b0/out/stim/B0_k10_{bar,nobar}.exr (73 px/deg, 12 x 6 deg)
  S4  real calibrated night photograph: Fairchild HDR Photographic Survey "Golden Gate (2)", the S8 conversion
      (research-cache/datasets/S8/S8.exr; tracks/datasets/make_s8.py)
  S5  calibrated mixed-luminance control: Fairchild "McKees Pub" (lit interior at night) x 6.25 (tracks/datasets
      README), converted exactly as S8 (D2x camera RGB -> XYZ -> linear Rec.709, negatives clipped), area-
      averaged to 1024 px wide. A DAYTIME scene was intended; markfairchild.org now answers every new download
      with a JavaScript bot check, so none could be fetched in this round.
Fairchild-derived files are licensed for non-commercial research only: kept in d0/work (gitignored), never
committed. Masks (npz) per scene for d0/metrics.py.
  nix develop -c python3 d0/make_inputs.py   -> d0/work/inputs/{S0,S1,S3_bar,S3_nobar,S4,S5}.exr, S2/frame_####.exr,
                                               masks/*.npz, manifest.json
"""
import hashlib, json, os
import numpy as np
import OpenImageIO as oiio

O = "d0/work/inputs"; os.makedirs(f"{O}/S2", exist_ok=True); os.makedirs(f"{O}/masks", exist_ok=True)
Yw = np.array([0.2126, 0.7152, 0.0722])
M26 = "m26/out/p32_t"
K179 = 179.0                                   # Cycles scene-linear -> cd/m^2 (m1/README.md section 1)


def ld(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def save(p, a):
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT); spec.attribute("compression", "zip")
    b = oiio.ImageBuf(spec); b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a, np.float32))
    b.write(p)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


man = {"convention": "linear Rec.709/D65 RGB float32 EXR; Y (0.2126,0.7152,0.0722) in absolute cd/m^2", "scenes": {}}
# ---- S0, S1 (+ masks from the M2.6 poplar pass and the lamps pass)
haze, lamps = K179 * ld(f"{M26}/haze_0001.exr"), K179 * ld(f"{M26}/lamps_0001.exr")
occ = ld("m26/out/occ/occ_0001.exr")[..., 1]
save(f"{O}/S0.exr", haze); save(f"{O}/S1.exr", haze + lamps)
YL = lamps @ Yw; lamp = YL > 1e-3 * YL.max()
H, W = YL.shape
rows = np.flatnonzero(lamp.any(1)); horizon = int(rows.max()) + 2 if rows.size else H // 2
from scipy.ndimage import binary_dilation
near_lamp = binary_dilation(lamp, iterations=6)
sky = (occ < 0.02) & ~near_lamp; sky[horizon - 30:, :] = False
tree = (occ > 0.98) & ~near_lamp
ground = np.zeros_like(lamp); ground[horizon + 10:, :] = True; ground &= ~near_lamp & (occ < 0.02)
np.savez_compressed(f"{O}/masks/S1.npz", lamp=lamp, near_lamp=near_lamp, sky=sky, tree=tree, ground=ground)
np.savez_compressed(f"{O}/masks/S0.npz", lamp=np.zeros_like(lamp), near_lamp=near_lamp, sky=sky, tree=tree, ground=ground)
geo = {"scene_px_per_deg": 32.0, "scene_hfov_deg": 60.0, "display_geometry": "PHONE (73 px/deg): the 60 deg render shown on ~26 deg"}
man["scenes"]["S0"] = {"file": "S0.exr", "what": "dark rural still, no lamp spheres (M2.6 frame 1 haze pass)", **geo, "size": [W, H], "sha": sha(f"{O}/S0.exr")}
man["scenes"]["S1"] = {"file": "S1.exr", "what": "S0 + distant lamp ribbon (haze + lamps, M2.6 frame 1)", **geo, "size": [W, H], "sha": sha(f"{O}/S1.exr")}
# ---- S2 clip
for f in range(1, 49):
    save(f"{O}/S2/frame_{f:04d}.exr", K179 * (ld(f"{M26}/haze_{f:04d}.exr") + ld(f"{M26}/lamps_{f:04d}.exr")))
lampmax = np.zeros((H, W))
for f in range(1, 49):                      # running max: no 48-frame stack in memory
    lampmax = np.maximum(lampmax, ld(f"{M26}/lamps_{f:04d}.exr") @ Yw)
np.savez_compressed(f"{O}/masks/S2.npz", lamp_any=lampmax > 1e-3 * lampmax.max(), sky=sky, tree=tree, ground=ground)
man["scenes"]["S2"] = {"dir": "S2", "frames": 48, "fps": 24, "what": "2 s walking clip (M2.5 clip B, 1 m/s), M2.6 target-first frames", **geo, "size": [W, H]}
# ---- S3 pair
m = json.load(open("b0/out/stim/meta.json"))
for b in ("bar", "nobar"):
    save(f"{O}/S3_{b}.exr", ld(f"b0/out/stim/B0_k10_{b}.exr"))
h3, w3 = m["size_px"][1], m["size_px"][0]; sx, sy = m["source_px"]; x0, x1, y0, y1 = m["bar_px_x0x1y0y1"]
yy, xx = np.mgrid[0:h3, 0:w3]; r = np.hypot(yy - sy, xx - sx) / m["px_per_deg"]
bar = np.zeros((h3, w3), bool); bar[y0:y1, x0:x1] = True
beside = np.zeros_like(bar); beside[y0:y1, x1 + 3:x1 + 3 + (x1 - x0)] = True
np.savez_compressed(f"{O}/masks/S3.npz", lamp=r < 1 / 60, near_lamp=r < 0.25, bar=bar, beside_bar=beside, sky=(r > 1.5) & ~bar)
man["scenes"]["S3"] = {"files": ["S3_bar.exr", "S3_nobar.exr"], "what": "B0 warm point source x10 (8.9e-4 lx at the eye) on a 4e-4 cd/m^2 sky, dark bar 0.15 x 3 deg at 0.3 deg; bar/no-bar pair",
                       "scene_px_per_deg": 73.0, "display_geometry": "PHONE (73 px/deg): 1:1 visual angle", "size": [w3, h3], "E_eye_lx": 10 * m["source"]["E_eye_lx"]["1"]}
# ---- S4 Golden Gate (S8)
s8 = ld("research-cache/datasets/S8/S8.exr"); save(f"{O}/S4.exr", s8)
clip = ld("research-cache/datasets/S8/S8_clipmask.exr")[..., 0] > 0.5
Y8 = s8 @ Yw; sky8 = np.zeros_like(clip); sky8[: Y8.shape[0] // 4, :] = True
np.savez_compressed(f"{O}/masks/S4.npz", lamp=clip | (Y8 > np.percentile(Y8, 99.9)), sky=sky8 & ~clip)
man["scenes"]["S4"] = {"file": "S4.exr", "what": "Fairchild HDRPS Golden Gate (2), real calibrated night photo (S8 conversion; lamp cores clipped by the HDR merge)",
                       "scene_px_per_deg": 32.0, "display_geometry": "PHONE (73 px/deg): 1024 px shown 1:1 (~14 deg)", "size": list(Y8.shape[::-1]), "licence": "Fairchild HDRPS: non-commercial research; do not commit"}
# ---- S5 McKees Pub, converted as S8
M_CAM2XYZ = np.array([[0.4024, 0.4610, 0.0871], [0.1904, 0.7646, 0.0450], [-0.0249, 0.1264, 0.9873]])
M_XYZ2709 = np.array([[3.2404542, -1.5371385, -0.4985314], [-0.9692660, 1.8760108, 0.0415560], [0.0556434, -0.2040259, 1.0572252]])
cam = oiio.ImageBuf("research-cache/datasets/fairchild/EXRs/McKeesPub.exr").get_pixels(oiio.FLOAT)[..., :3]
Hn, Wn = cam.shape[:2]; f = Wn // 1024
cam = cam[: (Hn // f) * f, : 1024 * f].reshape(Hn // f, f, 1024, f, 3).mean((1, 3), dtype=np.float64)   # area average first (linear)
rgb = np.maximum((cam @ M_CAM2XYZ.T * 6.25) @ M_XYZ2709.T, 0)
save(f"{O}/S5.exr", rgb)
Y5 = rgb @ Yw
np.savez_compressed(f"{O}/masks/S5.npz", lamp=Y5 > np.percentile(Y5, 99.9))
man["scenes"]["S5"] = {"file": "S5.exr", "what": "Fairchild HDRPS McKees Pub x6.25, lit interior at night: mixed-luminance control (daytime unavailable, see docstring)",
                       "scene_px_per_deg": round(56.85 / f, 2), "display_geometry": "PHONE (73 px/deg): 1024 px shown 1:1", "size": list(Y5.shape[::-1]),
                       "conversion": "as tracks/datasets/make_s8.py: D2x camera RGB x D65 matrix -> XYZ x 6.25 -> linear Rec.709, negatives clipped; area average by %d" % f,
                       "licence": "Fairchild HDRPS: non-commercial research; do not commit"}
man["scenes"]["S3"]["sha"] = {b: sha(f"{O}/S3_{b}.exr") for b in ("bar", "nobar")}
for k in ("S4", "S5"):
    man["scenes"][k]["sha"] = sha(f"{O}/{k}.exr")
for k, v in man["scenes"].items():
    for fn in ([v["file"]] if "file" in v else v.get("files", [])):
        a = ld(f"{O}/{fn}") @ Yw
        v.setdefault("stats_Y_cdm2", {})[fn] = {q: float(np.percentile(a, q)) for q in (0.1, 1, 50, 99, 99.9)} | {"max": float(a.max())}
json.dump(man, open(f"{O}/manifest.json", "w"), indent=1)
print(json.dumps({k: v.get("stats_Y_cdm2") for k, v in man["scenes"].items()}, indent=1))
