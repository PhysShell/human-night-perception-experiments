#!/usr/bin/env python3
"""N1.7 addendum 3: add the 12 stage-2 keyframes (K0125 ... K0975) to n1/views.json; existing entries unchanged (asserted)."""
import copy, json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
V = json.load(open("n1/views.json")); old = copy.deepcopy(V)
for t in (0.125, 0.175, 0.225, 0.350, 0.400, 0.450, 0.475, 0.525, 0.825, 0.850, 0.925, 0.975):
    name = f"K{round(t * 1000):04d}"; assert name not in old
    V[name] = {"what": f"N1.7 stage-2 keyframe t={t} on the B->C path", "t": t, "loc": [round(V["B"]["loc"][i] * (1 - t) + V["C"]["loc"][i] * t, 6) for i in range(3)],
               "yaw_deg": round(180.0 + 171.6 * t, 6), "pitch_deg": round(-3.0 * (1 - t), 6), "hfov_deg": 60.0, "res": [1920, 820], "crops": {}}
    print(name, V[name]["loc"], V[name]["yaw_deg"], V[name]["pitch_deg"])
assert all(V[k] == old[k] for k in old)
json.dump(V, open("n1/views.json", "w"), indent=1)
