#!/usr/bin/env python3
"""D1-P4v2 + R3, exactly as d1/p4v2/PREREG.md (committed before this code). Frozen pipeline: A (d1/a_extract),
B (chroma_b4), display Y-priority (d1/display_r v2). Y_out from the float code (before 16-bit quantisation).
  tracks/temporal-glare-2009/py.sh d1/p4v2/run.py -> results.json"""
import json, os
import numpy as np
from scipy.stats import spearmanr
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
a = 'return g, dict(H=H, W=W,'; assert a in src
src = src.replace(a, 'return g, dict(LEFF=v["Leff"], YMAP=v["Ymap"], YA=Ya, H=H, W=W,')      # also hand back the extraction's L_eff, F, Y_A
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
TOL = 1e-6


def p4(srcimg, axname):
    g, v = run_image(srcimg, axname, "yprio", None)
    Yo, L, F, YA = v["Yo"], v["LEFF"], v["YMAP"], v["YA"]
    Yexp = np.clip(LO + (HI - LO) * YA, LO, HI); dev = np.abs(Yo - Yexp) / Yexp
    r = {"colour_active": open(f"{AXC}/{axname}/colour_active").read().strip() == "1", "G1_max_rel_dev": float(dev.max())}
    r["P4-G1"] = bool(r["G1_max_rel_dev"] <= TOL)
    rng = np.random.default_rng(0); idx = rng.choice(len(L), min(20000, len(L)), replace=False)
    Ls, Fs, As, Os = L[idx], F[idx], YA[idx], Yo[idx]; n_res = n_inv = n_raw = n_rawinv = 0
    for s0 in range(0, len(idx), 500):
        sl = slice(s0, s0 + 500)
        res = (Fs[sl, None] < Fs[None, :]) & (As[None, :] > As[sl, None] * (1 + TOL))          # resolvable: F ratio beats the pair's k ratio
        inv = Os[sl, None] > Os[None, :] * (1 + TOL)
        raw = Ls[None, :] > Ls[sl, None] * (1 + TOL)                                           # diagnostic: bare L_eff order
        n_res += int(res.sum()); n_inv += int((res & inv).sum()); n_raw += int(raw.sum()); n_rawinv += int((raw & inv).sum())
    r.update({"resolvable_pairs": n_res, "inversions": n_inv, "inversion_rate": (n_inv / n_res) if n_res else None,
              "raw_Leff_pairs": n_raw, "raw_Leff_inversion_rate_diag": (n_rawinv / n_raw) if n_raw else None,
              "k_p1_p99": np.percentile((YA / np.where(F > 0, F, np.nan))[F > 0], [1, 99]).tolist() if (F > 0).any() else None,
              "oldP4_spearman_photopic_diag": float(spearmanr(v["Y"][idx], Os).statistic)})
    if n_res == 0:
        r["P4"] = "N/A"; vals, cnt = np.unique(Ls, return_counts=True); lv = vals[np.argmax(cnt)]; m = L == lv
        r["R3_subsample_distinct_Leff"] = int(len(vals)); r["R3_flat_px"] = int(m.sum())
        r["R3_flat_rel_range"] = float(Yo[m].max() / Yo[m].min() - 1)
        r["R3-flat"] = bool(r["R3_flat_rel_range"] <= TOL and r["P4-G1"])
    else:
        r["P4-G2"] = bool(n_inv == 0); r["P4"] = "PASS" if (r["P4-G1"] and r["P4-G2"]) else "FAIL"
    return r


res = {"prereg": "d1/p4v2/PREREG.md", "images": {}}
for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    res["images"][s] = p4(f"d0/work/inputs/{s}.exr", s); print(s, res["images"][s], flush=True)
res["images"]["F1"] = p4("d1/pipeline/.cache/F1.exr", "F1"); print("F1", res["images"]["F1"], flush=True)
s2 = {}
for f in range(1, 49):
    n = f"frame_{f:04d}"; s2[n] = p4(f"d0/work/inputs/S2/{n}.exr", f"S2/{n}")
res["S2_frames"] = s2
res["S2_summary"] = {"all_P4": sorted(set(x["P4"] for x in s2.values())), "max_G1_dev": max(x["G1_max_rel_dev"] for x in s2.values()),
                     "total_inversions": sum(x["inversions"] for x in s2.values()), "min_resolvable_pairs": min(x["resolvable_pairs"] for x in s2.values())}
print("S2", res["S2_summary"], flush=True)
I = res["images"]
res["verdict"] = {k: (v["P4"] if v["P4"] != "N/A" else ("N/A+R3-flat PASS" if v["R3-flat"] else "N/A+R3-flat FAIL")) for k, v in I.items()}
res["verdict"]["S2"] = "PASS" if res["S2_summary"]["all_P4"] == ["PASS"] else str(res["S2_summary"]["all_P4"])
res["verdict"]["ALL"] = all(v in ("PASS", "N/A+R3-flat PASS") for v in res["verdict"].values())
print(res["verdict"])
json.dump(res, open("d1/p4v2/results.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
