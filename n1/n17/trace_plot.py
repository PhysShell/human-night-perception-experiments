#!/usr/bin/env python3
"""N1.7 addendum 2: stage-1 trace plot + controls -> n1/n17/trace_results.json, n1/n17/N17_trace.png"""
import json, math, os
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = sorted((json.loads(l) for l in open("n1/n17/trace.jsonl")), key=lambda r: r["t"]); t = np.array([r["t"] for r in R])
E = np.array([r["EXPOSURE"] for r in R]); LM = np.array([r["scene_logmean"] for r in R]); lamp = np.array([r["lamp_in_frame"] for r in R])
ACC = {0.0: 453.5, 0.7: 869.49, 0.8: 865.23, 0.875: 868.78, 1.0: 982.64}
ctrl = {str(k): {"trace": float(E[np.isclose(t, k)][0]), "accepted": v, "rel": float(E[np.isclose(t, k)][0] / v - 1)} for k, v in ACC.items()}
dE, dL = np.diff(np.log2(E)), np.diff(np.log2(LM))
res = {"n": len(R), "controls": ctrl, "controls_PASS": all(abs(c["rel"]) <= 0.05 for c in ctrl.values()), "branches": sorted({r["branch"] for r in R}),
       "C0_all": all(r["C0"] for r in R), "max_abs_step_log2E": float(np.abs(dE).max()), "argmax_step_t": [float(t[np.abs(dE).argmax()]), float(t[np.abs(dE).argmax() + 1])],
       "corr_step_log2E_vs_log2logmean": float(np.corrcoef(dE, dL)[0, 1]), "lamp_enters_between": [float(t[np.flatnonzero(lamp)[0] - 1]), float(t[np.flatnonzero(lamp)[0]])],
       "auto_KILL_branch_change": len({r["branch"] for r in R}) > 1}
json.dump(res, open("n1/n17/trace_results.json", "w"), indent=1); print(json.dumps(res, indent=1))
f, ax = plt.subplots(3, 1, figsize=(9.6, 10), facecolor="white", sharex=True)
ax[0].plot(t, E, "o-", ms=3); ax[0].scatter(list(ACC), list(ACC.values()), marker="x", c="r", s=60, label="accepted 4096 spp keyframes")
ax[0].set_ylabel("pcond EXPOSURE"); ax[0].legend(); ax[0].set_title("N1.7 stage-1 trace (128 spp raw, full res), B (t=0) -> C (t=1)")
ax[1].plot(t, LM, "o-", ms=3, c="g"); ax[1].set_ylabel("scene log-mean L (cd/m2)")
ax[2].bar(t[1:] - 0.0125, dE, width=0.02, label="step log2 EXPOSURE"); ax[2].plot(t[1:] - 0.0125, dL, "k.", label="step log2 scene log-mean")
ax[2].axhline(0, c="gray", lw=0.5); ax[2].set_ylabel("per-step change (log2)"); ax[2].set_xlabel("t"); ax[2].legend()
for a in ax: a.axvspan(t[lamp][0] - 0.0125, 1.0, color="orange", alpha=0.12)
ax[0].text(t[lamp][0], E.min(), " lamp head in frame", color="darkorange")
f.tight_layout(); f.savefig("n1/n17/N17_trace.png", dpi=100)
