#!/usr/bin/env python3
"""M1.1: which of Radiance's two scotopic approximations (pcond path A vs B) is closer to
CIE 1951 V'(lambda) for the colours we care about?

An RGB renderer has no spectra, so there is no single right answer; this script brackets
it with existing implementations only:
  * Radiance B: pcond rgblum(scotopic) weights (.062 .608 .330) on Radiance-standard RGB,
    the RGB coming from ra_xyze itself;
  * Radiance A: pcond cielum(scotopic) formula Y*(1.33*(1+(Y+Z)/X) - 1.68) on ra_xyze XYZE;
  * colour-science 0.4.7: five published RGB->spectrum recovery methods, integrated
    against CIE 1951 scotopic V'(lambda) and CIE 1924 photopic V(lambda).
Quantity: relative scotopic efficiency (S/P of the colour) / (S/P of white).
Run inside the uv venv (see m1/README.md).
"""
import os, subprocess, tempfile
import numpy as np
import colour
import OpenImageIO as oiio

COLOURS = {  # linear Rec.709
    "red probe": (1.0, 0.05, 0.03),
    "blue probe": (0.05, 0.12, 1.0),
    "sodium lamp": (1.0, 0.45, 0.08),
    "warm LED 3000K": (1.0, 0.72, 0.42),
    "white": (1.0, 1.0, 1.0),
}
names = list(COLOURS)
rgb = np.array([COLOURS[n] for n in names], np.float32)

# --- Radiance: let ra_xyze do the conversions ------------------------------------------
T = tempfile.mkdtemp()
oiio.ImageBuf(rgb[None]).write(f"{T}/c.hdr")
P = "0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
sh = lambda c: subprocess.run(c, shell=True, check=True, capture_output=True, text=True).stdout
sh(f"getinfo -a 'PRIMARIES= {P}' < {T}/c.hdr > {T}/c709.hdr")
std = np.array([l.split() for l in sh(f"ra_xyze -r -u {T}/c709.hdr | pvalue -h -H -o -d").split("\n") if l], float)
xyz = np.array([l.split() for l in sh(f"ra_xyze -u {T}/c709.hdr | pvalue -h -H -o -d").split("\n") if l], float)
Ystd = std @ [0.2651, 0.6701, 0.0648]     # Radiance-standard primaries luminance row
rad_B = (std @ [0.062, 0.608, 0.330]) / Ystd
X, Y, Z = xyz.T
rad_A = 1.33 * (1 + (Y + Z) / X) - 1.68


def spectral(method):
    out = []
    shape = colour.SpectralShape(380, 780, 5)
    V = colour.colorimetry.SDS_LEFS_PHOTOPIC["CIE 1924 Photopic Standard Observer"].copy().align(shape)
    Vs = colour.colorimetry.SDS_LEFS_SCOTOPIC["CIE 1951 Scotopic Standard Observer"].copy().align(shape)
    for c in rgb.astype(float):
        if method == "Mallett 2019":
            sd = colour.recovery.RGB_to_sd_Mallett2019(c)
        elif method == "Smits 1999":
            sd = colour.recovery.RGB_to_sd_Smits1999(c)
        else:
            XYZ = colour.RGB_to_XYZ(c, "sRGB")
            sd = colour.XYZ_to_sd(XYZ / XYZ[1] * 0.5, method=method)   # reflectance-like
        sd = sd.copy().align(shape)
        out.append(np.sum(sd.values * Vs.values) / np.sum(sd.values * V.values))
    return np.array(out)


rows = {"Radiance B (rgblum)": rad_B, "Radiance A (cielum)": rad_A}
for m in ("Jakob 2019", "Otsu 2018", "Meng 2015", "Mallett 2019", "Smits 1999"):
    try:
        rows[f"colour: {m}"] = spectral(m)
    except Exception as e:  # a method may not converge for extreme colours
        print(f"{m}: {type(e).__name__}: {e}")

w = names.index("white")
print("relative scotopic efficiency (S/P) / (S/P of white)")
print(f"{'':24s}" + "".join(f"{n:>16s}" for n in names[:-1]) + f"{'blue/red':>10s}")
for k, v in rows.items():
    r = v / v[w]
    print(f"{k:24s}" + "".join(f"{x:16.3f}" for x in r[:-1]) + f"{r[1] / r[0]:10.2f}")
