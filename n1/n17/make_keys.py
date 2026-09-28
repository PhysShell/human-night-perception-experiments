#!/usr/bin/env python3
"""N1.7 (n1/n17/PREREG_N17.md + amendment 1): add the keyframes K070/K080/K0875 to n1/views.json. Path: position linear
in t, yaw 180 + 171.6 t (shortest signed path), pitch -3 (1 - t). OIDN uses fixed image-space windows (n1/n17/gate.py),
so crops are empty. The B and C entries are left unchanged (asserted)."""
import copy, json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
V = json.load(open("n1/views.json")); B0, C0 = copy.deepcopy(V["B"]), copy.deepcopy(V["C"])
for name, t in (("K070", 0.70), ("K080", 0.80), ("K0875", 0.875)):
    loc = [round(V["B"]["loc"][i] * (1 - t) + V["C"]["loc"][i] * t, 6) for i in range(3)]
    V[name] = {"what": f"N1.7 keyframe t={t} on the B->C path", "t": t, "loc": loc, "yaw_deg": round(180.0 + 171.6 * t, 6),
               "pitch_deg": round(-3.0 * (1 - t), 6), "hfov_deg": 60.0, "res": [1920, 820], "crops": {}}
    print(name, V[name])
assert V["B"] == B0 and V["C"] == C0
json.dump(V, open("n1/views.json", "w"), indent=1)
