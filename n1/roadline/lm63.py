#!/usr/bin/env python3
"""LM-63 type C reader + the RoadLine-B0 checks (n1/roadline/PREREG_B0.md).
  python3 n1/roadline/lm63.py FILE.ies   -> header, flux (integrated vs stated), I along the road towards the eye"""
import math, sys
import numpy as np


def read(path):
    t = open(path, errors="replace").read().replace("\r", "").split("\n")
    i = [k for k, l in enumerate(t) if l.startswith("TILT")][0]
    hdr = [l for l in t[:i] if l.startswith("[")]
    f = list(map(float, " ".join(t[i + 1:]).split()))
    nl, lm, mult, nv, nh, ptype, units = f[:7]; nv, nh = int(nv), int(nh); p = 13
    V = np.array(f[p:p + nv]); p += nv; H = np.array(f[p:p + nh]); p += nh
    C = np.array(f[p:p + nv * nh]).reshape(nh, nv) * mult
    return dict(hdr=hdr, n_lamps=nl, lm_per_lamp=lm, mult=mult, ptype=int(ptype), V=V, H=H, C=C)


def intensity(d, v, h):
    """I(V, H) with the type-C horizontal symmetry implied by the H range (0-90 quadrant, 0-180 half, 0-360 full)."""
    H, V, C = d["H"], d["V"], d["C"]; h = h % 360
    if H[-1] <= 90: h = abs(((h + 180) % 360) - 180); h = 180 - h if h > 90 else h
    elif H[-1] <= 180: h = abs(((h + 180) % 360) - 180)
    j = np.interp(h, H, np.arange(len(H))); j0 = int(np.floor(j)); j1 = min(j0 + 1, len(H) - 1); a = j - j0
    return float((1 - a) * np.interp(v, V, C[j0]) + a * np.interp(v, V, C[j1]))


def flux(d):
    th = np.radians(np.linspace(0, 180, 721)); ph = np.radians(np.linspace(0, 360, 721))
    I = np.array([[intensity(d, math.degrees(t), math.degrees(p)) if math.degrees(t) <= d["V"][-1] else 0.0 for t in th] for p in ph])
    return float(np.trapezoid(np.trapezoid(I * np.sin(th)[None, :], th, axis=1), ph))


if __name__ == "__main__":
    d = read(sys.argv[1]); print("\n".join(d["hdr"]))
    stated = d["lm_per_lamp"] * d["n_lamps"] if d["lm_per_lamp"] > 0 else None
    Fi = flux(d); print(f"ptype {d['ptype']}  V {d['V'][0]}..{d['V'][-1]}  H {d['H'][0]}..{d['H'][-1]} ({len(d['H'])})  max {d['C'].max():.1f} cd")
    print(f"flux integrated {Fi:.1f} lm | stated lamp lumens {stated} (relative photometry if > 0: luminaire flux = integrated)")
    print("along-road plane H=90:", {v: round(intensity(d, v, 90), 1) for v in (82.5, 85, 87.5, 90)}, "| H=270:", {v: round(intensity(d, v, 270), 1) for v in (87.5, 90)})
    for dist in (50, 100, 200, 400, 800, 1600):
        v = 90 - math.degrees(math.atan((8.0 - 1.7) / dist)); print(f"  eye at {dist:5d} m: V {v:6.2f}  I {intensity(d, v, 90):8.1f} cd")
    B0 = intensity(d, 87.5, 90) >= 255 and intensity(d, 90, 90) > 0
    print("B0 PASS" if B0 else "B0 FAIL", "(I(87.5) >= 255 cd and I(90) > 0, along-road plane)")
