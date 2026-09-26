#!/usr/bin/env python3
"""POST-HOC boundary refinement (not part of the pre-registered grid): the same G1 and G2 definitions as
PREREG.md, evaluated on a fine kappa grid (0.5..20, 81 log steps) to locate the admissible interval's ends.
Only G1 and G2 bind at the ends (G3-G5 passed on the whole 0.3..100 grid); G5 is re-checked at the ends.
  tracks/temporal-glare-2009/py.sh d1/filament_b3/boundary.py -> boundary.json
"""
import json, os, sys
import numpy as np
sys.argv = [sys.argv[0]]
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
src = open("d1/filament_b3/sweep.py").read().split("res = {")[0]      # helpers only (kern, uvY, crossing, ...)
exec(src)
out = []
for k in np.logspace(np.log10(0.5), np.log10(20), 81):
    r1 = []
    for name, c in PATCH.items():
        c = np.array(c, float); ins = np.array([c / (M709 @ c)[1] * L for L in (0.005, 5)])
        o = kern(ins * k) / k; E = np.hypot(*(uvY(o)[0] - uvY(ins)[0]).T); r1.append(E[1] / E[0])
    ins = np.array([np.ones(3) * L for L in LS]); o = kern(ins * k) / k; En = np.hypot(*(uvY(o)[0] - uvY(ins)[0]).T)
    L50, L10, L90 = crossing(LS, En, .5, En[0]), crossing(LS, En, .1, En[0]), crossing(LS, En, .9, En[0])
    out.append({"kappa": float(k), "G1_worst": float(max(r1)), "G1_pass": bool(max(r1) <= 0.10), "L50": L50,
                "width": float(np.log10(L10 / L90)) if L10 and L90 else None,
                "G2_pass": bool(L50 is not None and 0.005 <= L50 <= 5 and L10 and L90 and np.log10(L10 / L90) >= 1)})
ok = [r["kappa"] for r in out if r["G1_pass"] and r["G2_pass"]]
rep = {"note": "POST-HOC boundary refinement of the pre-registered admissible interval (G1, G2 only)", "kappa_min": min(ok) if ok else None,
       "kappa_max": max(ok) if ok else None, "grid": out}
json.dump(rep, open("d1/filament_b3/boundary.json", "w"), indent=1)
print("admissible (G1&G2) kappa range on fine grid:", rep["kappa_min"], "-", rep["kappa_max"])
for f in ("i.f32", "o.f32"):
    p = f"d1/filament_b3/.cache/{f}"
    if os.path.exists(p): os.remove(p)
