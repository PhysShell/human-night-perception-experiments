#!/usr/bin/env python3
"""D1-A0 (axis separation) and D1-A1 synthetic kill tests K0-K3, exactly as d1/axis_a/PREREG.md.
  tracks/temporal-glare-2009/py.sh d1/axis_a/kill_tests.py -> kill_tests.json, kill_curves.png"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d1/axis_a")
from wanat_global import tone_curve, Gt
R = {}
# ---------------- A0 on patches (B4 functions) and S1
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])
import OpenImageIO as oiio
t = lambda L: L / (L + 0.108)
worst = {"dchroma": 0.0, "dhue": 0.0, "dY": 0.0}
def a0_check(phys):
    Lp = phys @ M709[1]; f = filament(phys); b = stage(f, Lp, t(Lp), "uv"); Yb = b @ M709[1]
    x = b * (Lp / np.where(Yb > 0, Yb, 1))[:, None]; k = Yb > 0
    dc = np.abs(chroma(x) - chroma(b))[k]; cb = chroma(b)
    dh = np.abs((hue(x) - hue(b) + 180) % 360 - 180)[k & (cb >= 0.002)]
    dY = np.abs((x @ M709[1])[k] / Lp[k] - 1)
    for key, v in (("dchroma", dc), ("dhue", dh), ("dY", dY)):
        if v.size: worst[key] = max(worst[key], float(v.max()))
for c in PATCH.values():
    c = np.array(c, float); a0_check(np.array([c / (M709 @ c)[1] * L for L in LS]))
img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64).reshape(-1, 3)
a0_check(img)
R["A0"] = worst | {"pass": worst["dchroma"] <= 1e-9 and worst["dhue"] <= 1e-6 and worst["dY"] <= 1e-9}
# ---------------- A1 K0-K3
def slope(l, T, a, b):
    k = (l >= np.log10(a) - 1e-9) & (l <= np.log10(b) + 1e-9); return float((np.interp(np.log10(b), l, T) - np.interp(np.log10(a), l, T)) / (np.log10(b) - np.log10(a)))
curves = {}
l, T, r = tone_curve(-3, 2, -3, 2); curves["K0a 100->100"] = (l, T)
R["K0a"] = {"max_abs_T_minus_l": float(np.max(np.abs(T - l))), "solver": r.message}; R["K0a"]["pass"] = R["K0a"]["max_abs_T_minus_l"] <= 0.05
l, T, r = tone_curve(-3, 2, -5, 0); curves["K0b 100->1"] = (l, T)
sb, sd = slope(l, T, 10, 100), slope(l, T, 1e-3, 1e-2)
R["K0b"] = {"slope_bright_10_100": sb, "slope_dark_1e-3_1e-2": sd, "solver": r.message, "pass": sb < 1 and sb < sd}
l, T, r = tone_curve(-3, 2, -2, 3); curves["K0c 100->1000"] = (l, T)
sl = np.diff(T) / np.diff(l); lm = 0.5 * (l[1:] + l[:-1]); mid = (lm >= -2) & (lm <= 1)
R["K0c"] = {"slope_min": float(sl[mid].min()), "slope_max": float(sl[mid].max()), "solver": r.message}; R["K0c"]["pass"] = 0.85 <= R["K0c"]["slope_min"] and R["K0c"]["slope_max"] <= 1.15
l, T, r = tone_curve(-4, 2, -1, 2); curves["K1-3 night 1e-4..1e2 -> SDR100"] = (l, T)
R["K1"] = {"monotone": bool(np.all(np.diff(T) >= -1e-9)), "T_lmin": float(T[0]), "T_lmax": float(T[-1]), "solver": r.message}
R["K1"]["pass"] = R["K1"]["monotone"] and T[0] >= -1 - 1e-6 and T[-1] <= 2 + 1e-6
dec = {f"1e{a}..1e{a+1}": slope(l, T, 10.0 ** a, 10.0 ** (a + 1)) for a in range(-3, 2)}
R["K2"] = {"decade_mean_slopes": dec, "pass": all(v >= 0.1 for v in dec.values())}
R["K3"] = {"slope_1e-3_1e-2": slope(l, T, 1e-3, 1e-2), "slope_1_100": slope(l, T, 1, 100)}; R["K3"]["pass"] = R["K3"]["slope_1e-3_1e-2"] < R["K3"]["slope_1_100"]
for _k in ("A0", "K0a", "K0b", "K0c", "K1", "K2", "K3"): R[_k]["pass"] = bool(R[_k]["pass"])
R["A1_synthetic_pass"] = all(R[k]["pass"] for k in ("K0a", "K0b", "K0c", "K1", "K2", "K3"))
R["curves"] = {k: {"l": v[0].tolist(), "T": v[1].tolist()} for k, v in curves.items()}
json.dump(R, open("d1/axis_a/kill_tests.json", "w"), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for k, (l, T) in curves.items(): ax[0].plot(l, T, "o-", ms=3, label=k)
ax[0].plot([-4, 3], [-4, 3], "k:", lw=0.8); ax[0].set(xlabel="log10 source Y [cd/m^2]", ylabel="log10 display Y [cd/m^2]", title="Wanat 2014 global tone curves (our implementation)"); ax[0].legend(fontsize=7)
lg = np.linspace(-5, 3, 200); ax[1].plot(lg, Gt(lg)); ax[1].axhline(0.4, color="k", ls=":"); ax[1].set(xlabel="log10 L [cd/m^2]", ylabel="Gt (threshold, log contrast)", title="Gt(L) at 2 cpd, S = 8.6 (dotted: G = 0.4)")
plt.tight_layout(); plt.savefig("d1/axis_a/kill_curves.png", dpi=100)
for k in ("A0", "K0a", "K0b", "K0c", "K1", "K2", "K3"):
    print(k, json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in R[k].items() if a != "solver"}))
print("A1 synthetic pass:", R["A1_synthetic_pass"])
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
