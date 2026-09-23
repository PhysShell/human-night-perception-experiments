#!/usr/bin/env python3
"""M2.5 hard invariants of a rendered clip (after m25/render_clip.sh + m25/display_clip.sh).

  finite      every haze / lamps / pcond-stage frame is finite;
  adaptation  pcond stays in its linear mode on every frame (an EXPOSURE is recorded) and
              that exposure varies by < 1 % over the clip: pcond adapts per frame, so a
              larger change would be a global brightness flicker that no eye makes;
  lamp energy the lamps pass's total energy changes by < 1 % between consecutive frames
              (the camera moves slowly; one lamp is ~0.2 % of the total, so a lamp going
              behind a poplar is a small legitimate step);
  no flashes  no single-frame spike: in 5x5-pixel windows around lamps, frame t may not
              stand out from BOTH neighbours in the same direction (a blink) by more than
              20 % of the local level, in pcond-stage and displayed luminance, nor by more
              than 0.004 u'v' (about one JND) in chromaticity. A step (an occlusion, a lamp
              entering a pixel) is not a flash; comparing with the neighbours' mean would
              count every step as a spike. Windows touching a poplar edge (occ_####.exr, in
              any of the three frames) are excluded and counted: a lamp seen through a
              moving gap between trees does blink, physically;
  display     the displayed PNGs contain no NaN-like codes (checked by decoding) and the
              ribbon band's displayed luminance changes by < 2 % per frame.
  python3 m25/check_clip.py CLIPDIR [png|png_pbr]   (which display to check; default png)
"""
import glob, os, sys
import numpy as np
import OpenImageIO as oiio

D = sys.argv[1]
Yw = np.array([0.2126, 0.7152, 0.0722])
M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])


def load(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]


def box5(a):
    c = np.cumsum(np.cumsum(np.pad(a, ((3, 2), (3, 2)) + ((0, 0),) * (a.ndim - 2)), 0), 1)
    return c[5:, 5:] - c[:-5, 5:] - c[5:, :-5] + c[:-5, :-5]


frames = sorted(os.path.basename(p)[5:9] for p in glob.glob(f"{D}/haze_*.exr"))
res, ok = [], True
haze = [load(f"{D}/haze_{f}.exr") for f in frames]
lamps = [load(f"{D}/lamps_{f}.exr") for f in frames]
lc = [load(f"{D}/lc/{f}.exr") for f in frames]
PNG = sys.argv[2] if len(sys.argv) > 2 else "png"
png = [load(f"{D}/{PNG}/{f}.png") for f in frames]
occ = [load(f"{D}/occ_{f}.exr")[..., 1] if os.path.exists(f"{D}/occ_{f}.exr") else None for f in frames]
fin = all(np.isfinite(x).all() for x in haze + lamps + lc + png)
res.append(("finite", fin, f"{len(frames)} frames"))

expo = {}
for line in open(f"{D}/exposure.txt"):
    parts = line.split()
    expo[parts[0]] = float(parts[1]) if len(parts) > 1 else None
lin = all(expo.get(f) for f in frames)
e = np.array([expo[f] for f in frames]) if lin else np.array([np.nan])
var = e.max() / e.min() - 1 if lin else np.inf
res.append(("adaptation", lin and var < 0.01,
            f"linear mode on all frames: {lin}; EXPOSURE {e.min():.6g}..{e.max():.6g} ({var * 100:.3f} %)"))

if len(frames) < 3:
    res.append(("temporal", True, "static clip: one rendered frame, repeated (nothing temporal to check)"))
else:
    El = np.array([(x @ Yw).sum() for x in lamps])
    dE = np.abs(np.diff(El) / El[:-1]).max()
    res.append(("lamp energy", dE < 0.01, f"max frame-to-frame change {dE * 100:.3f} %"))

    L0 = lamps[0] @ Yw
    rows = np.flatnonzero((L0 > 0).any(1))
    band = slice(rows.min() - 3, rows.max() + 4)
    worst = {}
    for name, seq in (("pcond stage", lc), ("display", [p ** 2.2 for p in png])):
        Y = [box5(x @ Yw)[band] for x in seq]
        XYZ = [box5(x @ M.T)[band] for x in seq]
        lampwin = box5((np.maximum.reduce([l @ Yw for l in lamps]) > 0).astype(float))[band] > 0
        edge = [np.zeros_like(Y[0], bool) if o is None else
                box5(((o > 0.02) & (o < 0.98)).astype(float) + box5((o > 0.5).astype(float)) * box5((o <= 0.5).astype(float)))[band] > 0
                for o in occ]
        spike, cspike, n_edge = 0.0, 0.0, 0
        for t in range(1, len(seq) - 1):
            ref = 0.5 * (Y[t - 1] + Y[t + 1])
            near_tree = edge[t - 1] | edge[t] | edge[t + 1]
            m0 = lampwin & (ref > 1e-3 * ref.max())
            a0, b0 = Y[t] - Y[t - 1], Y[t] - Y[t + 1]
            bl0 = np.where(a0 * b0 > 0, np.minimum(np.abs(a0), np.abs(b0)), 0.0) / np.maximum(np.maximum(Y[t], ref), 1e-30)
            n_edge += int(((bl0 > 0.20) & m0 & near_tree).any())
            m = m0 & ~near_tree
            a, b = Y[t] - Y[t - 1], Y[t] - Y[t + 1]
            blink = np.where(a * b > 0, np.minimum(np.abs(a), np.abs(b)), 0.0)
            spike = max(spike, (blink[m] / np.maximum(Y[t], ref)[m]).max())
            uv = []
            for k in (t - 1, t, t + 1):
                X, Yy, Z = (XYZ[k][..., i][m] for i in range(3))
                s = X + 15 * Yy + 3 * Z + 1e-12
                uv.append(np.stack([4 * X / s, 9 * Yy / s], -1))
            da, db = uv[1] - uv[0], uv[1] - uv[2]
            same = (da * db).sum(-1) > 0                        # away from both neighbours
            cb = np.minimum(np.linalg.norm(da, axis=-1), np.linalg.norm(db, axis=-1))
            cspike = max(cspike, np.where(same, cb, 0.0).max())
        worst[name] = (spike, cspike)
        res.append((f"no flashes ({name})", spike < 0.20 and cspike < 0.004,
                    f"max single-frame luminance spike {spike * 100:.2f} %, chromaticity spike {cspike:.5f} u'v'; "
                    f"frames with a > 20 % blink at a poplar edge (allowed): {n_edge}"))
    Yb = np.array([(p ** 2.2 @ Yw)[band].sum() for p in png])
    dB = np.abs(np.diff(Yb) / Yb[:-1]).max()
    res.append(("display ribbon", dB < 0.02, f"max frame-to-frame change of displayed ribbon band {dB * 100:.3f} %"))

for name, good, msg in res:
    ok &= bool(good)
    print(f"{name:26s} {'ok  ' if good else 'FAIL'} {msg}")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
