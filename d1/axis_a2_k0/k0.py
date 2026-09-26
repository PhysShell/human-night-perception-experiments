#!/usr/bin/env python3
"""D1-A2-K0, exactly as d1/axis_a2_k0/PREREG.md. -> results.json
  tracks/temporal-glare-2009/py.sh d1/axis_a2_k0/k0.py"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import gaussian_filter, label, binary_dilation
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d1/axis_a")
from wanat_global import Gt as _Gt_rho2, csf, S_ABS, MT_CAP
def Gt(L, rho):
    Mt = np.minimum(1.0 / (S_ABS * csf(rho, np.asarray(L, float))), MT_CAP); return 0.5 * np.log10((1 + Mt) / (1 - Mt))
Yw = np.array([0.2126, 0.7152, 0.0722])
Y = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(float) @ Yw
m = dict(np.load("d0/work/inputs/masks/S1.npz")); L_sky = float(np.median(Y[m["sky"]]))
hor = int(np.flatnonzero(m["ground"].any(1)).min())
dark = Y < 0.5 * L_sky; dark[hor - 12:, :] = False
lab, n = label(dark); sizes = np.bincount(lab.ravel()); sizes[0] = 0
big = np.argsort(sizes)[::-1][:2]; trees = np.isin(lab, big)
L_tree = float(np.median(Y[trees])); G_src = 0.5 * np.log10(L_sky / L_tree)
roi = binary_dilation(trees, iterations=60); roi[hor - 12:, :] = False
l = np.log10(np.maximum(Y, 1e-12)); res = {"L_sky": L_sky, "L_tree": L_tree, "G_src": G_src, "weber_src": 1 - L_tree / L_sky,
                                          "tree_px": int(trees.sum()), "roi_px": int(roi.sum())}
def census(rppd):
    N = next(k for k in range(1, 20) if 2.0 ** -(k + 1) * rppd <= 2.0)
    lows = [l] + [gaussian_filter(l, 2.0 ** (k - 1)) for k in range(1, N + 1)]
    tot = float(np.sum((l[roi] - l[roi].mean()) ** 2)); out = {"N": N, "bands": []}
    f = np.linspace(1e-4, 0.5, 5000)
    for k in range(1, N + 1):
        b = lows[k - 1] - lows[k]; sa = 0 if k == 1 else 2.0 ** (k - 2); sb = 2.0 ** (k - 1)
        H = np.exp(-2 * np.pi ** 2 * sa ** 2 * f ** 2) - np.exp(-2 * np.pi ** 2 * sb ** 2 * f ** 2)
        out["bands"].append({"k": k, "rho_eq15_cpd": 2.0 ** -(k + 1) * rppd, "rho_measured_peak_cpd": float(f[np.argmax(H)] * rppd),
                             "energy_fraction": float(np.sum(b[roi] ** 2) / tot)})
    base = lows[N]; out["base_energy_fraction"] = float(np.sum((base[roi] - base[roi].mean()) ** 2) / tot)
    out["bands_energy_total"] = float(sum(b["energy_fraction"] for b in out["bands"])); return out
res["census_73"] = census(73.0); res["census_32_sensitivity"] = census(32.0)
L_tgt = 0.1   # A1 base band at the silhouette (d1/axis_a/scene.json: sky 0.10004, poplars 0.1000)
sc = json.load(open("d1/axis_a/scene.json")); res["A1_display_sky_tree"] = [sc["sky_median_display"], sc["tree_median_display"]]
rhos = [0.25, 0.5, 1.0, 2.0 ** -6 * 73, 2.0, 2.0 ** -5 * 73]
def pred(Ls):
    o = {}
    for r in rhos:
        g = G_src - Gt(Ls, r) + Gt(L_tgt, r); o[f"{r:.3g}"] = {"Gt_src": float(Gt(Ls, r)), "Gt_tgt": float(Gt(L_tgt, r)), "G_tilde": float(g), "weber_display": float(1 - 10 ** (-2 * max(g, 0)))}
    return o
res["eq17_ideal"] = {"L_src_geomean": pred(np.sqrt(L_sky * L_tree)), "L_src_sky": pred(L_sky), "L_src_tree": pred(L_tree)}
rhoN = 2.0 ** -6 * 73; key = f"{rhoN:.3g}"; P = res["eq17_ideal"]["L_src_geomean"]
k1 = res["census_73"]["base_energy_fraction"] >= 0.5
k2 = P[key]["weber_display"] < 0.1
k3 = (not any(v["weber_display"] >= 0.1 for r, v in zip(rhos, P.values()) if r >= rhoN - 1e-9)) and any(v["weber_display"] >= 0.1 for r, v in zip(rhos, P.values()) if r < rhoN - 1e-9)
res["kill"] = {"K0-1_base_energy>=0.5": bool(k1), "K0-2_ideal_weber_at_rhoN<0.1": bool(k2), "K0-3_only_below_rhoN": bool(k3)}
res["verdict"] = "KILL published A2 for S1" if (k1 or k2 or k3) else "PASS: full A2 allowed"
json.dump(res, open("d1/axis_a2_k0/results.json", "w"), indent=1)
print(f"L_sky {L_sky:.3g}  L_tree {L_tree:.3g}  G_src {G_src:.3f}  Weber_src {res['weber_src']:.3f}  ROI {res['roi_px']} px")
for name in ("census_73", "census_32_sensitivity"):
    c = res[name]; print(f"{name}: N={c['N']}  base fraction {c['base_energy_fraction']:.3f}  bands total {c['bands_energy_total']:.3f}")
    for b in c["bands"]: print(f"   k{b['k']}: rho eq15 {b['rho_eq15_cpd']:.2f} cpd (DoG peak {b['rho_measured_peak_cpd']:.2f})  energy {b['energy_fraction']:.3f}")
for s, P2 in res["eq17_ideal"].items():
    print(s, " | ".join(f"rho {r}: G~ {v['G_tilde']:+.3f} W {v['weber_display']:.3f}" for r, v in P2.items()))
print(res["kill"], "->", res["verdict"])
