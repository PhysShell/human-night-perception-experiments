#!/usr/bin/env python3
"""Luminance statistics of downloaded HDR files (format inspection only, no model).
Fairchild HDRPS: camera RGB (white-balanced D2x) -> Y via the D65-normalised matrix row
(0.1904, 0.7646, 0.0450) [D2xCharacterization.pdf p.1] times the per-scene luminance factor.
Radiance .hdr: Y = 179 * (0.2126 R + 0.7152 G + 0.0722 B) per Radiance convention (WHITE_EFFICACY 179),
and also reported without the 179 factor since MPI states its EXRs are in cd/m^2 directly."""
import sys, json, numpy as np, OpenImageIO as oiio
def load(p):
    b = oiio.ImageBuf(p); a = b.get_pixels(oiio.FLOAT); return a[..., :3]
def pct(Y):
    Yp = Y[Y > 0]
    return {k: float(v) for k, v in zip(["p0.1","p1","p50","p99","p99.9","p99.99","max"],
            np.percentile(Yp, [0.1,1,50,99,99.9,99.99,100]))} | {"min_pos": float(Yp.min()),
            "mean": float(Y.mean()), "frac_zero_or_neg": float((Y <= 0).mean())}
out = {}
for spec in sys.argv[1:]:
    path, kind, factor = spec.split("::"); factor = float(factor)
    a = load(path)
    if kind == "d2x":
        Y = (a @ np.array([0.1904, 0.7646, 0.0450])) * factor
    else:
        Y = (a @ np.array([0.2126, 0.7152, 0.0722])) * factor
    s = pct(Y); s["shape"] = list(a.shape); s["factor"] = factor; s["kind"] = kind
    s["DR_p0.1_to_p99.99"] = s["p99.99"] / s["p0.1"]
    out[path.split("/")[-1] + ("" if factor == 1 else f"@x{factor:g}")] = s
print(json.dumps(out, indent=1))
