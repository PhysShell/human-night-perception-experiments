#!/usr/bin/env python3
"""B0 v2 sweep plots + smoothness checks (no winner is chosen): vs illuminance at the eye,
  white-clipped plateau diameter, trunk P_det (EVAL_OFF, EVAL_VIEWER; world reference points),
  Vangorp adaptation at the trunk. Checks per curve: monotonicity (plateau and Lla must not fall
  as the source brightens; P_det must not rise), largest step between neighbours (knees)."""
import glob, json, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = json.load(open("b0/results/sweep.json"))
E1 = 800 / 3000 ** 2
K = np.geomspace(0.1, 100, 31)
world = {}
for f in glob.glob("b0/out/sweep_world/w*_*/run.json"):
    m = re.search(r"w(\d+)_(cie|hdrvdp)", f); t = open(f).read()
    try: p = float(t.split('"side-by-side":{"P_det":')[1].split(",")[0])
    except Exception: continue
    world[(m.group(2), int(m.group(1)))] = p
VAR = sorted({r["variant"] for r in rows}, key=lambda v: (v[1], v))
series = {v: sorted([r for r in rows if r["variant"] == v], key=lambda r: r["k"]) for v in VAR}
checks = {}
for v, s in series.items():
    E = np.array([r["E_eye_lx"] for r in s])
    pl = np.array([r["white_plateau_equiv_diam_arcmin"] for r in s])
    la = np.array([r["Vangorp_Lla_trunk"] for r in s])
    po = np.array([r["P_det_trunk_EVAL_OFF"] for r in s], float); pv = np.array([r["P_det_trunk_EVAL_VIEWER"] for r in s], float)
    checks[v] = {"plateau_monotone_nondecreasing": bool((np.diff(pl) >= -1e-9).all()),
                 "plateau_max_step_arcmin": float(np.abs(np.diff(pl)).max()),
                 "Lla_monotone_nondecreasing": bool((np.diff(la) >= -1e-12).all()),
                 "Pdet_OFF_monotone_nonincreasing(tol 0.02)": bool((np.diff(po) <= 0.02).all()),
                 "Pdet_VIEWER_monotone_nonincreasing(tol 0.02)": bool((np.diff(pv) <= 0.02).all()),
                 "Pdet_OFF_max_step": float(np.abs(np.diff(po)).max()), "Pdet_VIEWER_max_step": float(np.abs(np.diff(pv)).max())}
json.dump({"checks": checks, "world_reference": {f"{m}_k{K[i]:.3g}": p for (m, i), p in sorted(world.items())}},
          open("b0/results/sweep_checks.json", "w"), indent=1)
fig, ax = plt.subplots(2, 2, figsize=(12, 9))
for v, s in series.items():
    E = [r["E_eye_lx"] for r in s]
    ls = "--" if v.startswith("V5t") else "-"
    ax[0, 0].semilogx(E, [r["white_plateau_equiv_diam_arcmin"] for r in s], ls, label=v)
    ax[0, 1].semilogx(E, [r["P_det_trunk_EVAL_OFF"] for r in s], ls, label=v)
    ax[1, 0].semilogx(E, [r["P_det_trunk_EVAL_VIEWER"] for r in s], ls, label=v)
    ax[1, 1].loglog(E, [r["Vangorp_Lla_trunk"] for r in s], ls, label=v)
for m, mk in (("cie", "ko"), ("hdrvdp", "k^")):
    pts = sorted((K[i] * E1, p) for (mm, i), p in world.items() if mm == m)
    for a in (ax[0, 1], ax[1, 0]):
        a.semilogx([p[0] for p in pts], [p[1] for p in pts], mk, label=f"reference observer: {m} (world, 146 px/deg)")
ax[0, 0].set_title("white-clipped plateau diameter under this display mapping [arcmin]")
ax[0, 1].set_title("trunk P_det, evaluator optics OFF (donor chain only)")
ax[1, 0].set_title("trunk P_det, evaluator = viewer's eye at the phone (HDR-VDP MTF)")
ax[1, 1].set_title("Vangorp/HDR-VDP adaptation luminance at the trunk [cd/m²]\n(fitted 1-5000 cd/m²: extrapolated here)")
for a in ax.ravel():
    a.set_xlabel("illuminance at the eye from the lamp [lx]  (x1 = 800 cd at 3 km = 8.9e-5 lx)"); a.grid(True, which="both", lw=0.3)
ax[0, 1].legend(fontsize=7)
plt.tight_layout(); plt.savefig("b0/results/sweep_curves.png", dpi=100)
print(json.dumps(checks, indent=1)); print("world:", {f"{m}_{i}": round(p, 4) for (m, i), p in sorted(world.items())})
