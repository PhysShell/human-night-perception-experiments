#!/usr/bin/env python3
"""N1.6 RoadLine addendum 6 gates, written before the renders are evaluated.
  tracks/temporal-glare-2009/py.sh n1/roadline/a6_eval.py A   -> n1/roadline/a6_A.json,
                                                               n1/roadline/work/A6/rl6_cdm2.exr, rl6_rgb.exr (base + far pass)
Far pass: M2.5 resample (m25/resample.py, unchanged) of far_<seed>.exr (4x, box) to the output resolution.
Estimator: aperture r_ap = projected emitter radius (px) + 1.5 px (half of Cycles' 3-px Blackman-Harris window).
Base (50-400 m): background = median of r_ap+1 < r <= r_ap+3.5 px excluding pixels within r_ap of other emitter centres.
Far pass and reference: background identically zero."""
import json, math, os, subprocess, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
ST = sys.argv[1]; W_ = f"n1/roadline/work/{ST}6"; K, YW = 179.0, np.array([0.2126, 0.7152, 0.0722])
F = 960 / math.tan(math.radians(30)); RADIUS = 0.105
lampsj = json.load(open(f"n1/roadline/work/{ST}/lamps.json"))["lamps"]; lamps = [l for l in lampsj if l["in_frame"]]
diam = {l["d"]: 2 * RADIUS / l["r_m"] * F for l in lamps}
Yimg = lambda p: K * (oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3] @ YW)


def omega(xs, ys): return (F / np.sqrt(F ** 2 + (xs + 0.5 - 960) ** 2 + (ys + 0.5 - 410) ** 2)) ** 3 / F ** 2


def signal(img, l, d_px, others=None, zero_bg=False):
    cx, cy = l["px"]; r_ap = d_px / 2 + 1.5; R = int(np.ceil(r_ap + 4.5))
    x0, y0 = int(cx) - R, int(cy) - R; sub = img[y0:y0 + 2 * R + 1, x0:x0 + 2 * R + 1]
    ys, xs = np.mgrid[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]]; r = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
    if zero_bg: bg = 0.0
    else:
        excl = np.zeros_like(r, bool)
        for o in others: excl |= np.hypot(xs + 0.5 - o["px"][0], ys + 0.5 - o["px"][1]) <= diam[o["d"]] / 2 + 1.5
        bg = float(np.median(sub[(r > r_ap + 1) & (r <= r_ap + 3.5) & ~excl]))
    ap = r <= r_ap
    return float(((sub - bg) * omega(xs, ys))[ap].sum()), sub, (xs, ys), bg


res = {"stim": ST, "addendum": 6}
for s in (0, 1):
    subprocess.run([sys.executable, "m25/resample.py", "4", f"{W_}/far_{s}.exr", f"{W_}/far_{s}_out.exr"], check=True)
far = {s: Yimg(f"{W_}/far_{s}_out.exr") for s in (0, 1)}; ref = {s: Yimg(f"{W_}/ref_{s}.exr") for s in (0, 1)}
farinfo = {x["d"]: x for x in json.load(open(f"{W_}/far_0.json"))["lamps"]}
g = {}
for l in lamps:
    if l["d"] not in (800, 1600): continue
    d = l["d"]; Sf = [signal(far[s], l, farinfo[d]["diam_px"], zero_bg=True)[0] for s in (0, 1)]
    Sr = [signal(ref[s], l, diam[d], zero_bg=True)[0] for s in (0, 1)]
    conv = Sf[0] / Sf[1] - 1; spread = abs(Sr[0] / Sr[1] - 1); tol = max(0.02, 2 * spread)
    eq = np.mean(Sf) / np.mean(Sr) - 1
    cx, cy = int(l["px"][0]), int(l["px"][1])                           # 5x5 output-pixel stimulus around the centre pixel
    pf = sum(far[s][cy - 2:cy + 3, cx - 2:cx + 3] for s in (0, 1)); pr = sum(ref[s][cy - 2:cy + 3, cx - 2:cx + 3] for s in (0, 1))
    pf, pr = pf / pf.sum(), pr / pr.sum(); L1 = float(np.abs(pf - pr).sum())
    I = np.mean(Sf) * l["r_m"] ** 2
    g[d] = {"far_S_seed0_1": Sf, "conv_dev": conv, "conv_PASS": abs(conv) <= 0.02, "ref_S_seed0_1": Sr, "ref_seed_spread": spread,
            "equiv_dev": eq, "equiv_tol": tol, "equiv_PASS": abs(eq) <= tol, "stimulus_L1": L1, "stimulus_PASS": L1 <= 0.10,
            "peak_share_far": float(pf.max()), "peak_share_ref": float(pr.max()), "diam_px_natural": diam[d], "diam_px_far": farinfo[d]["diam_px"],
            "I_measured": I, "I_table": l["I_table_cd"], "R1_ratio": I / l["I_table_cd"], "R1_PASS": abs(I / l["I_table_cd"] - 1) <= 0.10}
res["far_pass"] = g
base = Yimg(f"{W_}/base.exr"); r1 = {}
near = [l for l in lamps if l["d"] not in (800, 1600)]
for l in near:
    S, _, _, bg = signal(base, l, diam[l["d"]], others=[o for o in lamps if o is not l]); I = S * l["r_m"] ** 2
    r1[l["d"]] = {"I_measured": I, "I_table": l["I_table_cd"], "ratio": I / l["I_table_cd"], "bg_cdm2": bg, "r_ap_px": diam[l["d"]] / 2 + 1.5,
                  "PASS": abs(I / l["I_table_cd"] - 1) <= 0.10}
for d, v in g.items(): r1[d] = {"I_measured": v["I_measured"], "I_table": v["I_table"], "ratio": v["R1_ratio"], "PASS": v["R1_PASS"], "source": "far pass"}
res["R1"] = {"lamps": r1, "PASS": all(v["PASS"] for v in r1.values())}; res["R2"] = "N/A (no denoiser; addendum 5)"
res["PASS"] = res["R1"]["PASS"] and all(v["conv_PASS"] and v["equiv_PASS"] and v["stimulus_PASS"] for v in g.values())
brgb = oiio.ImageBuf(f"{W_}/base.exr").get_pixels(oiio.FLOAT)[..., :3]; frgb = oiio.ImageBuf(f"{W_}/far_0_out.exr").get_pixels(oiio.FLOAT)[..., :3]
tot = brgb + frgb; H_, W2 = tot.shape[:2]
for name, arr in (("rl6_cdm2.exr", tot * K), ("rl6_rgb.exr", tot)):
    o = oiio.ImageBuf(oiio.ImageSpec(W2, H_, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, W2, 0, H_, 0, 1, 0, 3), np.ascontiguousarray(arr, np.float32)); o.write(f"{W_}/{name}")
json.dump(res, open(f"n1/roadline/a6_{ST}.json", "w"), indent=1, default=float)
for d, v in g.items(): print(f"far {d}: conv {v['conv_dev']:+.2%} | equiv {v['equiv_dev']:+.2%} (tol {v['equiv_tol']:.1%}) | stimulus L1 {v['stimulus_L1']:.3f} peak {v['peak_share_far']:.3f}/{v['peak_share_ref']:.3f} | diam {v['diam_px_natural']:.2f}->{v['diam_px_far']:.2f} px")
for d, v in sorted(r1.items()): print(f"R1 {d}: I {v['I_measured']:.2f} / {v['I_table']:.2f} = {v['ratio']:.3f} {'PASS' if v['PASS'] else 'FAIL'}")
print("ADDENDUM 6", "PASS" if res["PASS"] else "FAIL")
