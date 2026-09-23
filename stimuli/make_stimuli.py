#!/usr/bin/env python3
"""Common, immutable stimulus pack for the donor bake-off (round 8). Deterministic; the images
are rebuilt from this script and the frozen M2.6 renders, and checked against manifest.json.

Conventions for EVERY stimulus (also written into stimuli/pack/<id>/meta.json):
  * linear Rec.709 / D65 RGB, float32 OpenEXR; luminance Y = 0.2126 R + 0.7152 G + 0.0722 B
    is in cd/m^2 (absolute, photopic). A luminance-only PFM (cd/m^2) is written next to it.
  * geometry: 32 px/deg at the image centre (M2.6: 32 and 64 px/deg converge; 16 does not).
  * unresolved sources carry the footprint of Cycles' own pixel filter (Blackman-Harris,
    3-px window = filter_width 1.5 doubled, film.cpp) normalised to unit energy, so a point's
    energy is exact at every sub-pixel phase; its luminance integral equals its illuminance
    at the eye: sum(L_px) * Omega_px = E = I / d^2.
  * night sky background 4e-4 cd/m^2 (the M1 scene's sky), unless stated.
S0 white point  S1 warm (sodium) point  S2 red/blue equal-luminance pair  S3 ribbon (lamps
only, clear air)  S4 ribbon + poplar silhouettes  S5 point next to a dark target on a mesopic
field  S6 S0 moving 1 px in 2 s (48 frames, 24 fps)  S7 canonical clear-haze scene frame
S7v the same, 48 frames walking (M2.6 32 px/deg, target-first)
  python3 stimuli/make_stimuli.py [outdir=stimuli/pack]
"""
import hashlib, json, math, os, sys
import numpy as np
import OpenImageIO as oiio

OUT = sys.argv[1] if len(sys.argv) > 1 else "stimuli/pack"
PPD = 32.0
SKY = 4e-4
OMEGA = (math.radians(1 / PPD)) ** 2                 # sr per pixel at the centre
I_LAMP, D_LAMP = 800.0, 3000.0                        # cd, m: the scene's road luminaire at 3 km
E_LAMP = I_LAMP / D_LAMP ** 2                          # lx at the eye (clear air ignored here)
SODIUM = np.array([1.0, 0.45, 0.08]); WHITE = np.ones(3)
Yw = np.array([0.2126, 0.7152, 0.0722])
M26 = "m26/out/p32_t"


def unit_lum(c):
    return c / (c @ Yw)


def bh(t):
    v = 2 * np.pi * (t + 0.5)
    return np.where(np.abs(t) <= 0.5, 0.35875 - 0.48829 * np.cos(v) + 0.14128 * np.cos(2 * v) - 0.01168 * np.cos(3 * v), 0)


def add_point(img, x, y, E, rgb):
    """Unresolved source of illuminance E (lx) at pixel coords (x, y) (pixel centres at +0.5)."""
    xs, ys = np.arange(int(x) - 3, int(x) + 4), np.arange(int(y) - 3, int(y) + 4)
    w = np.outer(bh((ys + 0.5 - y) / 3), bh((xs + 0.5 - x) / 3))
    w /= w.sum()
    img[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] += (w * E / OMEGA)[..., None] * unit_lum(rgb)


def field(w=1024, h=512, L=SKY):
    return np.full((h, w, 3), L, np.float32) * unit_lum(np.array([0.85, 0.9, 1.0]))


def write(sid, frames, meta):
    d = os.path.join(OUT, sid)
    os.makedirs(d, exist_ok=True)
    files = []
    for k, img in enumerate(frames):
        base = f"{sid}" if len(frames) == 1 else f"{sid}_{k + 1:04d}"
        h, w = img.shape[:2]
        b = oiio.ImageBuf(oiio.ImageSpec(w, h, 3, oiio.FLOAT))
        b.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, 3), np.ascontiguousarray(img, np.float32))
        b.write(f"{d}/{base}.exr")
        y = oiio.ImageBuf(oiio.ImageSpec(w, h, 1, oiio.FLOAT))
        y.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, 1), np.ascontiguousarray((img @ Yw)[..., None], np.float32))
        y.write(f"{d}/{base}_Y.pfm")
        files += [f"{base}.exr", f"{base}_Y.pfm"]
    Y = np.array([f @ Yw for f in frames])
    meta.update({"id": sid, "units": "cd/m^2 (Y of linear Rec.709/D65 RGB)", "px_per_deg": PPD,
                 "size_px": [int(frames[0].shape[1]), int(frames[0].shape[0])],
                 "fov_deg": [frames[0].shape[1] / PPD, frames[0].shape[0] / PPD],
                 "frames": len(frames), "L_min": float(Y.min()), "L_max": float(Y.max()),
                 "files": files})
    json.dump(meta, open(f"{d}/meta.json", "w"), indent=1)
    return meta


metas = []
c = (512.0, 256.0)                                     # a pixel corner: phase 0.5 in x and y
img = field(); add_point(img, *c, E_LAMP, WHITE)
metas.append(write("S0", [img], {"what": "isolated white (D65) unresolved source, 800 cd at 3 km, on night sky",
                                 "E_eye_lx": E_LAMP, "source_px": c}))
img = field(); add_point(img, *c, E_LAMP, SODIUM)
metas.append(write("S1", [img], {"what": "isolated warm (high-pressure-sodium-like Rec.709 1:0.45:0.08) source, same illuminance as S0",
                                 "E_eye_lx": E_LAMP, "source_px": c}))
img = field(); add_point(img, 448.0, 256.0, E_LAMP, np.array([1.0, 0, 0])); add_point(img, 576.0, 256.0, E_LAMP, np.array([0, 0, 1.0]))
metas.append(write("S2", [img], {"what": "Rec.709 red and blue unresolved sources of equal photopic illuminance, 4 deg apart (Purkinje/mesopic probe)",
                                 "E_eye_lx": E_LAMP, "source_px": [[448, 256], [576, 256]]}))
# S5: mesopic field 0.01 cd/m^2, dark bar 0.001 cd/m^2 (0.1 x 0.5 deg), source 0.25 deg from its edge
img = field(L=0.01)
bx0, bx1, by0, by1 = int(512 + 0.25 * PPD), int(512 + 0.35 * PPD), int(256 - 0.25 * PPD), int(256 + 0.25 * PPD)
img[by0:by1, bx0:bx1] = 0.001 * unit_lum(np.array([0.85, 0.9, 1.0]))
add_point(img, *c, E_LAMP, SODIUM)
metas.append(write("S5", [img], {"what": "local adaptation probe: warm source 0.25 deg left of a 0.1 x 0.5 deg dark bar (0.001 cd/m^2) on a 0.01 cd/m^2 mesopic field",
                                 "E_eye_lx": E_LAMP, "source_px": c, "bar_px": [bx0, bx1, by0, by1]}))
# S6: S0 moving 1.0 px to the right in 2 s (48 frames at 24 fps): sub-pixel motion only
frames = []
for k in range(48):
    img = field(); add_point(img, c[0] + k / 47.0, c[1], E_LAMP, WHITE); frames.append(img)
metas.append(write("S6", frames, {"what": "S0 moving 1.0 px (1.9 arcmin) to the right over 2 s, 48 frames at 24 fps; energy constant per frame",
                                  "fps": 24, "E_eye_lx": E_LAMP}))
# S3/S4/S7 from the frozen M2.6 32 px/deg renders (scene units x 179 = cd/m^2)
if os.path.isdir(M26):
    ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3] * 179.0
    lamps, haze = ld(f"{M26}/lamps_0001.exr"), ld(f"{M26}/haze_0001.exr")
    occ = oiio.ImageBuf("m26/out/occ/occ_0001.exr").get_pixels(oiio.FLOAT)[..., 1:2]
    sky = field(1920, 820)
    metas.append(write("S3", [lamps + sky], {"what": "the scene's road-light ribbon (492 lamps, 2.2-14 km, clear air V=40 km, lamps pass of M2.6 at 32 px/deg) on a uniform night sky; no ground, no trees",
                                             "source": "m26/out/p32_t/lamps_0001.exr x 179"}))
    metas.append(write("S4", [lamps + sky * (1 - occ)], {"what": "S3 with the poplar silhouettes (black) in front",
                                                         "source": "S3 + m26/out/occ/occ_0001.exr"}))
    metas.append(write("S7", [haze + lamps], {"what": "canonical scene frame: clear-haze rural night, poplars, ribbon; M2.6 32 px/deg, frame 1 of the walk",
                                              "source": "m26/out/p32_t/{haze,lamps}_0001.exr x 179"}))
    fr = [ld(f"{M26}/haze_{k:04d}.exr") + ld(f"{M26}/lamps_{k:04d}.exr") for k in range(1, 49)]
    metas.append(write("S7v", fr, {"what": "S7 as 2 s of walking sideways at 1 m/s (48 frames, 24 fps)", "fps": 24,
                                   "source": "m26/out/p32_t/{haze,lamps}_00NN.exr x 179"}))
man = {"generator": "stimuli/make_stimuli.py", "conventions": __doc__.split("Conventions")[1].split("S0 white")[0].strip(),
       "stimuli": metas, "sha256": {}}
for m in metas:
    for f in m["files"]:
        man["sha256"][f"{m['id']}/{f}"] = hashlib.sha256(open(os.path.join(OUT, m["id"], f), "rb").read()).hexdigest()
json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print(f"{len(metas)} stimuli in {OUT}")
for m in metas:
    print(f"  {m['id']:4s} {m['size_px']} x{m['frames']}  L {m['L_min']:.2e}..{m['L_max']:.2e} cd/m^2  {m['what'][:70]}")
