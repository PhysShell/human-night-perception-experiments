#!/usr/bin/env python3
"""Temporal behaviour of pfstmo_mantiuk08's per-frame tone curves on S2 (48 frames): descriptive, no thresholds.
Reads the tool's own --output-tone-curve CSVs (frame, log10 input luminance, log10 display luminance, pixel value):
  video_whiteauto / video_whiteanchor               one 48-frame stream, tool's temporal IIR filter (--fps 25)
  video_unfiltered_whiteauto / _whiteanchor         each frame in its own process (no temporal filtering)
Per frame-to-frame step: max and mean |delta log10 L_display| over the nodes that the clip's content occupies
(log10 input luminance within the S2 frame-1 0.1..99.9 percentile span, from the manifest), and max |delta pixel value|.
  python3 d0/donors/mantiuk08/curve_smoothness.py  -> d0/results/curves/mantiuk08/video_smoothness.json
"""
import json, os
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
C = f"{ROOT}/d0/results/curves/mantiuk08"
S1 = json.load(open(f"{ROOT}/d0/work/inputs/manifest.json"))["scenes"]["S1"]["stats_Y_cdm2"]["S1.exr"]  # S2 frame 1 = S1
lo, hi = np.log10(S1["0.1"]), np.log10(S1["99.9"])


def load(p):
    a = np.loadtxt(p, delimiter=",")
    n = int(a[:, 0].max()) + 1
    a = a.reshape(n, -1, 4)
    return a[0, :, 1], a[:, :, 2], a[:, :, 3]


res = {"_what": __doc__, "content_log10_span": [round(lo, 3), round(hi, 3)]}
for lum in ["SDR100", "BRIGHT500"]:
    for w in ["whiteauto", "whiteanchor"]:
        for cfg in [f"video_{w}", f"video_unfiltered_{w}"]:
            p = f"{C}/{cfg}/S2__PHONE_{lum}_DARK.csv"
            if not os.path.exists(p):
                continue
            x, y, v = load(p)
            m = (x >= lo - 0.05) & (x <= hi + 0.05)
            dy = np.abs(np.diff(y[:, m], axis=0)); dv = np.abs(np.diff(v[:, m], axis=0))
            d2 = np.abs(np.diff(y[:, m], 2, axis=0))
            res[f"{cfg}/{lum}"] = {
                "frames": int(y.shape[0]),
                "max_step_dlog10L": float(dy.max()), "mean_step_dlog10L": float(dy.mean()),
                "p95_of_per_step_max_dlog10L": float(np.percentile(dy.max(1), 95)),
                "max_step_dpixel": float(dv.max()),
                "max_second_difference_dlog10L": float(d2.max()),
                "total_drift_frame1_to_48_max_dlog10L": float(np.abs(y[-1, m] - y[0, m]).max()),
                "per_step_max_dlog10L": [round(float(t), 4) for t in dy.max(1)]}
json.dump(res, open(f"{C}/video_smoothness.json", "w"), indent=1)
for k, r in res.items():
    if isinstance(r, dict):
        print(f"{k:45s} max step {r['max_step_dlog10L']:.4f}  mean {r['mean_step_dlog10L']:.5f}  max dpix {r['max_step_dpixel']:.4f}  "
              f"max 2nd diff {r['max_second_difference_dlog10L']:.4f}  drift {r['total_drift_frame1_to_48_max_dlog10L']:.3f}")
