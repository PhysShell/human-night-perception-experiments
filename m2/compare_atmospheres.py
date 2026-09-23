#!/usr/bin/env python3
"""M2: compare the same scene in vacuum and through clear / mild / moderate atmospheres.

Inputs per case (from m2/run_m2.sh):
  m2/out/scene_<case>.exr        Cycles render (179 lm/W convention: cd/m^2 = 179 * Y)
  m2/out/lc_<case>.exr           M1.1 pcond stage (display-linear Rec.709, unchanged pipeline)
  m2/out/results/<case>.png      M1.1 display for stills (PBR Neutral on out-of-gamut pixels)
Measured:
  * lamp transmittance vs distance: lamp ENERGY (sum over a window around the ribbon, minus
    the local glow background) per 20-column bin, medium / vacuum, fitted to exp(-sigma d)
    and compared with the input extinction. Single-pixel peaks are not photometry: a lamp
    covers ~2 % of a pixel and the pixel filter shares it differently between renders;
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
CASES = ["vacuum", "clear", "mild", "moderate"]
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
H, W = scene["vacuum"].shape[:2]
arcmin = HFOV * 60 / W
Lnone = scene["vacuum"] @ Yw
dist = road_distance(W)
band = slice(int(H * 0.40), int(H * 0.55))                   # rows around the horizon
row = np.argmax(Lnone[band], axis=0) + band.start             # ribbon row per column
has_lamp = Lnone[row, np.arange(W)] > 1.0
near = has_lamp & (dist >= 2000) & (dist < 4000)
far = has_lamp & (dist >= 10000) & (dist < 14000)
print(f"{W}x{H}, {arcmin:.2f} arcmin/px; lamp columns near (2-4 km) {near.sum()}, far (10-14 km) {far.sum()}")

# total input extinction at 550 nm (Koschmieder, m2/atmospheres.py)
coeff = {"clear": 3.912 / 40e3, "mild": 3.912 / 15e3, "moderate": 3.912 / 7e3}

BIN = 20


def lamp_energy(L, k0):
    """Energy of the lamps in columns k0..k0+BIN (window +-3 rows around the ribbon row),
    minus the glow background measured 6-10 rows above and below."""
    r = int(np.median(row[k0:k0 + BIN][has_lamp[k0:k0 + BIN]]))      # lamp columns only
    win = L[r - 3:r + 4, k0:k0 + BIN]
    bg = np.median(np.r_[L[r - 10:r - 6, k0:k0 + BIN].ravel(), L[r + 6:r + 10, k0:k0 + BIN].ravel()])
    return win.sum(axis=(0, 1)) - bg * win.shape[0] * win.shape[1]


bins = [k for k in range(0, W - BIN + 1, BIN) if has_lamp[k:k + BIN].sum() >= 3
        and not np.isnan(dist[k:k + BIN]).any()]
bd = np.array([np.nanmean(dist[k:k + BIN]) for k in bins])
E0 = {c: np.array([lamp_energy(scene[c] @ Yw, k) for k in bins]) for c in CASES}
# reference = "vacuum": same M2 lamps, no medium, no baked extinction
print(f"\n== 1. lamp transmittance vs distance: energy per {BIN}-column bin, medium / vacuum "
      f"({len(bins)} bins, {bd.min() / 1000:.1f}-{bd.max() / 1000:.1f} km)")
for c in CASES[1:]:
    T = E0[c] / E0["vacuum"]
    # fit only where the lamps are measurable above the Monte Carlo noise of the haze glow
    # (expected T > 20 %); farther, only a few samples reach a sub-pixel lamp per bin
    ok = (T > 1e-3) & (np.exp(-coeff[c] * bd) > 0.2)
    span = np.ptp(bd[ok]) if ok.any() else 0
    sig = -np.polyfit(bd[ok], np.log(T[ok]), 1)[0] if ok.sum() > 2 and span > 2500 else np.nan
    # ratio of summed energies (not a median of per-bin ratios): behind a few optical depths
    # only a handful of camera samples reach a sub-pixel lamp, so per-bin values are
    # unbiased but heavily skewed, and their median is biased low
    t3, t10 = (E0[c][(bd >= lo) & (bd < hi)].sum() / E0["vacuum"][(bd >= lo) & (bd < hi)].sum()
               for lo, hi in ((2000, 4000), (9000, 14000)))
    e3, e10 = math.exp(-coeff[c] * 3000), math.exp(-coeff[c] * 11500)
    print(f"  {c:9s} T(2-4 km) {t3:.3f} (Beer-Lambert @3 km {e3:.3f})   T(9-14 km) {t10:.4f} "
          f"(@11.5 km {e10:.4f})   fitted sigma {'n/a' if np.isnan(sig) else f'{sig:.2e}'} vs input {coeff[c]:.2e} 1/m "
          f"(fit over {ok.sum()} bins up to {bd[ok].max() / 1000:.1f} km)")

print("\n== 2. lamp colour (u'v' hue deg / chroma), background-subtracted lamp energy: scene | after pcond (LC)")
for c in CASES:
    out = []
    for name, lo, hi in (("near", 2000, 4000), ("far", 9000, 14000)):
        sel = [k for k, d in zip(bins, bd) if lo <= d < hi]
        if not sel:
            out.append(f"{name}: -"); continue
        s_rgb = sum(np.array([lamp_energy(scene[c][..., i], k) for i in range(3)]) for k in sel)
        l_rgb = sum(np.array([lamp_energy(lc[c][..., i], k) for i in range(3)]) for k in sel)
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
