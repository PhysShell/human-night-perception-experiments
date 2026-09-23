#!/usr/bin/env python3
"""M2: compare the same scene through no medium / clear / mild / moderate atmospheres.

Inputs per case (from m2/run_m2.sh):
  m2/out/scene_<case>.exr        Cycles render (179 lm/W convention: cd/m^2 = 179 * Y)
  m2/out/lc_<case>.exr           M1.1 pcond stage (display-linear Rec.709, unchanged pipeline)
  m2/out/results/<case>.png      M1.1 display for stills (PBR Neutral on out-of-gamut pixels)
Measured:
  * lamp transmittance vs distance: ribbon peak / no-medium peak per column, fitted to
    exp(-sigma d) and compared with the medium's input extinction (G channel);
  * lamp colour near (2-4 km) and far (10-14 km): CIE 1976 u'v' hue/chroma, scene and
    after pcond;
  * apparent ribbon width: vertical extent of the glow above display thresholds, arcmin;
  * silhouettes: Weber contrast of the poplars and of the horizon against the adjacent sky,
    in scene luminance and on the display.
"""
import math
import numpy as np
import OpenImageIO as oiio

D = "m2/out"
CASES = ["none", "clear", "mild", "moderate"]
Yw = np.array([0.2126, 0.7152, 0.0722])
HFOV, YAW = 60.0, 4.0                     # camera: 60 deg, yawed 4 deg towards +x (scene.py)
ROAD = ((-1500.0, 1800.0), (7500.0, 13500.0))


def load(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]


def srgb_decode(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def uv(rgb):
    X, Y, Z = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ rgb
    s = X + 15 * Y + 3 * Z
    du, dv = 4 * X / s - 0.1978, 9 * Y / s - 0.4683
    return math.degrees(math.atan2(dv, du)), math.hypot(du, dv)


def road_distance(W):
    """Horizontal distance to the road along each image column's viewing direction."""
    (x0, y0), (x1, y1) = ROAD
    out = np.full(W, np.nan)
    for c in range(W):
        t = ((c + 0.5) / W * 2 - 1) * math.tan(math.radians(HFOV / 2))
        phi = math.radians(YAW) + math.atan(t)
        d = np.array([math.sin(phi), math.cos(phi)])
        A = np.array([[d[0], x0 - x1], [d[1], y0 - y1]])
        try:
            s, u = np.linalg.solve(A, [x0, y0])
        except np.linalg.LinAlgError:
            continue
        if s > 0 and 0 <= u <= 1:
            out[c] = s
    return out


scene = {c: load(f"{D}/scene_{c}.exr") * 179 for c in CASES}
lc = {c: load(f"{D}/lc_{c}.exr") for c in CASES}
disp = {c: srgb_decode(load(f"{D}/results/{c}.png")) for c in CASES}
H, W = scene["none"].shape[:2]
arcmin = HFOV * 60 / W
Lnone = scene["none"] @ Yw
dist = road_distance(W)
band = slice(int(H * 0.40), int(H * 0.55))                   # rows around the horizon
row = np.argmax(Lnone[band], axis=0) + band.start             # ribbon row per column
has_lamp = Lnone[row, np.arange(W)] > 1.0
near = has_lamp & (dist >= 2000) & (dist < 4000)
far = has_lamp & (dist >= 10000) & (dist < 14000)
print(f"{W}x{H}, {arcmin:.2f} arcmin/px; lamp columns near (2-4 km) {near.sum()}, far (10-14 km) {far.sum()}")

# total input extinction at 550 nm (Koschmieder, m2/atmospheres.py)
coeff = {"clear": 3.912 / 40e3, "mild": 3.912 / 15e3, "moderate": 3.912 / 7e3}

print("\n== 1. lamp transmittance vs distance (ribbon peak / no-medium peak)")
for c in CASES[1:]:
    L = scene[c] @ Yw
    cols = np.flatnonzero(has_lamp & ~np.isnan(dist))
    ratio = L[row[cols], cols] / Lnone[row[cols], cols]
    ok = ratio > 0
    sig = -np.polyfit(dist[cols][ok], np.log(ratio[ok]), 1)[0]
    tn = np.median(ratio[near[cols]]) if near.any() else np.nan
    tf = np.median(ratio[far[cols]]) if far.any() else np.nan
    print(f"  {c:9s} T near {tn:.3f}  T far {tf:.4f}   fitted sigma {sig:.2e} 1/m  vs input {coeff[c]:.2e} (550 nm)")

print("\n== 2. lamp colour (u'v' hue deg / chroma): scene | after pcond (LC)")
for c in CASES:
    out = []
    for name, m in (("near", near), ("far", far)):
        cols = np.flatnonzero(m)
        if not len(cols):
            out.append(f"{name}: -"); continue
        s_rgb = np.array([scene[c][row[k] - 1:row[k] + 2, k].sum(0) for k in cols]).sum(0)
        l_rgb = np.array([lc[c][row[k] - 1:row[k] + 2, k].sum(0) for k in cols]).sum(0)
        (hs, cs), (hl, cl) = uv(s_rgb), uv(l_rgb)
        out.append(f"{name}: {hs:5.1f}/{cs:.3f} | {hl:5.1f}/{cl:.3f}")
    print(f"  {c:9s} " + "    ".join(out))

print("\n== 3. apparent ribbon width (vertical extent of glow on the display, arcmin)")
for c in CASES:
    Yd = disp[c] @ Yw
    res = []
    for name, m in (("near", near), ("far", far)):
        cols = np.flatnonzero(m)
        w = {t: np.mean([(Yd[band, k] >= t).sum() for k in cols]) * arcmin for t in (0.2, 0.02)}
        res.append(f"{name}: >0.2 {w[0.2]:5.1f}'  >0.02 {w[0.02]:6.1f}'")
    print(f"  {c:9s} " + "    ".join(res))

print("\n== 4. silhouette contrast (Weber, vs adjacent sky): scene | display")
sky_rows = slice(int(H * 0.25), int(H * 0.42))
tree = (Lnone[sky_rows] < 0.5 * np.median(Lnone[sky_rows]))              # poplars against sky
hz = int(np.median(row))
for c in CASES:
    L, Yd = scene[c] @ Yw, disp[c] @ Yw
    s_sky, d_sky = np.median(L[sky_rows][~tree]), np.median(Yd[sky_rows][~tree])
    ct = (s_sky - np.median(L[sky_rows][tree])) / s_sky
    cd = (d_sky - np.median(Yd[sky_rows][tree])) / max(d_sky, 1e-6)
    above, below = L[hz - 12:hz - 4], L[hz + 4:hz + 12]
    ch = (np.median(above) - np.median(below)) / np.median(above)
    dh = (np.median(Yd[hz - 12:hz - 4]) - np.median(Yd[hz + 4:hz + 12])) / max(np.median(Yd[hz - 12:hz - 4]), 1e-6)
    print(f"  {c:9s} poplars {ct:5.2f} | {cd:5.2f}    horizon (sky vs ground) {ch:5.2f} | {dh:5.2f}"
          f"    sky {s_sky:.2e} cd/m2 -> display {d_sky:.4f}")
