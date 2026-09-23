#!/usr/bin/env python3
"""Regression test for our reading of Radiance pcond (m1/pcond_colorimetric.sh):
 1. histogram mode: stored display value == (Ld - Ldmin)/(Ldmax - Ldmin) with Ld from -x;
 2. linear mode (-l): the -x table overstates display luminance by exactly 179/Ldmax
    (pcond putmapping() quirk) -- if upstream fixes it, this test tells us;
 3. pcond_colorimetric.sh B/AB: equal pcond's own output (B: its Radiance-standard-RGB run,
    AB: its XYZE run) on every pixel pcond did not clip, keep the input chromaticity on
    clipped photopic pixels, and never exceed display luminance 1 (both pcond modes).
Input: a log ramp 1e-3..1e3 cd/m^2 in grey, warm (1,.72,.42) and blue (.3,.5,1) rows."""
import os, subprocess, sys, tempfile
import numpy as np
import OpenImageIO as oiio

HERE = os.path.dirname(os.path.abspath(__file__))
P = "0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290".split()
Yw = np.array([0.2126, 0.7152, 0.0722])
T = tempfile.mkdtemp()
fails = []


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, **kw).stdout


L = np.logspace(-3, 3, 600)
cols = np.array([[1, 1, 1], [1, .72, .42], [.3, .5, 1]], np.float32)
cols /= (cols @ Yw)[:, None]
img = np.concatenate([np.repeat((L[None, :, None] * c)[None], 40, 0)[0] for c in cols]).astype(np.float32)
img = np.repeat(img[:, None], 1, 1).reshape(3, 600, 3).repeat(40, 0).reshape(120, 600, 3)
oiio.ImageBuf(img).write(f"{T}/ramp.exr")                                   # cd/m^2, Rec.709
oiio.ImageBuf(img / 179).write(f"{T}/ramp_rad.hdr")
sh(f"getinfo -a 'VIEW= -vtv -vh 60 -vv 12' 'PRIMARIES= {' '.join(P)}' < {T}/ramp_rad.hdr > {T}/in709.hdr")


def stored(path):
    return oiio.ImageBuf(path).get_pixels(oiio.FLOAT)[..., :3]


# 1 + 2: -x table vs actual output, grey row
for flags, expect in (("-s", 1.0), ("-l", 100 / 179)):
    sh(f"pcond {flags} -p {' '.join(P)} -x {T}/m {T}/in709.hdr > {T}/o.hdr")
    m = np.loadtxt(f"{T}/m")
    Ld = np.interp(np.log(L), np.log(m[:, 0]), m[:, 1])
    Y = stored(f"{T}/o.hdr")[20] @ Yw
    sel = (Ld > 1.5) & (Ld < 99)
    ratio = np.median(Y[sel] * 100 / Ld[sel]) if flags == "-l" else np.median(Y[sel] / ((Ld[sel] - 1) / 99))
    ok = abs(ratio / expect - 1) < 0.01
    print(f"pcond {flags}: output / (-x table) = {ratio:.4f}, expected {expect:.4f}  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(f"pcond {flags} mapping ratio {ratio:.4f}")

# 3: pcond_colorimetric.sh B / AB vs pcond's own runs, both pcond modes
sh(f"ra_xyze -r {T}/in709.hdr > {T}/instd.hdr")           # oracle input for B (std RGB, honest)
for mode in ("B", "AB"):
    for extra in ("", "-l"):
        out = f"{T}/r_{mode}{extra}.hdr"
        sh(f"{HERE}/pcond_colorimetric.sh {T}/ramp.exr 60 {mode} {out} 0.00558659 {extra}")
        rec = stored(out)
        if mode == "B":   # oracle: pcond on the same Radiance-standard RGB data, -p Rec.709
            sh(f"pcond -s -c {extra} -p {' '.join(P)} {T}/instd.hdr > {T}/pcB.hdr")
            pc = stored(f"{T}/pcB.hdr")
        else:             # oracle: pcond on XYZE (the .pcond.hdr written next to the output)
            pc = stored(out.replace(".hdr", ".pcond.hdr"))
        Lw = img @ Yw
        sel = (pc.max(-1) < 0.98) & (pc.min(-1) > 1e-3)
        err = np.median(np.abs(rec[sel] - pc[sel]) / pc[sel]) if sel.any() else 0.0
        clipped = (Lw >= 5.62) & (pc.max(-1) >= 0.999)
        chroma = rec[clipped] / (rec[clipped] @ Yw)[:, None]
        want = img[clipped] / (img[clipped] @ Yw)[:, None]
        # RGBE stores a shared exponent + 8-bit mantissas: absolute step <= max component / 128;
        # the chain quantises twice (in709.hdr, pcomb output) -> bound 2/128
        cerr = (np.abs(chroma - want) / want.max(-1, keepdims=True)).max() if clipped.any() else 0.0
        ymax = (rec @ Yw).max()
        ok = err < 0.01 and cerr <= 2 / 128 and ymax <= 1 + 2 / 128
        print(f"path {mode:2s} {extra or '(histogram)':12s}: {int(sel.sum()):5d} unclipped px, median err {err:.4f}; "
              f"max Y {ymax:.3f}; {int(clipped.sum()):5d} clipped px, chroma err {cerr:.4f} "
              f"(bound 2 RGBE steps {2/128:.4f})  {'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"pcond_colorimetric {mode}{extra}")

if fails:
    sys.exit("PCOND MAPPING REGRESSION FAILED: " + "; ".join(fails))
print("PASS")
