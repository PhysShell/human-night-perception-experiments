#!/usr/bin/env python3
"""N1.7 addendum 3: FLASH over the 17 states + contact sheet -> n1/n17/stage2_results.json, n1/n17/N17_stage2_sheet.png"""
import json, os
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
V = json.load(open("n1/views.json")); YW = np.array([0.2126, 0.7152, 0.0722])
keys = sorted(["B", "K070", "K080", "K0875", "C"] + [json.loads(l)["key"] for l in open("n1/n17/stage2.jsonl")], key=lambda k: {"B": 0.0, "C": 1.0}.get(k, V[k].get("t", 0)))
T = {k: {"B": 0.0, "C": 1.0}.get(k, V[k].get("t")) for k in keys}
def meanY(k):
    a = oiio.ImageBuf(f"n1/renders/final/cam_{k}.png").get_pixels(oiio.FLOAT)[..., :3].astype(float)
    return float((0.1 + 99.9 * (np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4) @ YW)).mean())
M = [meanY(k) for k in keys]; flashes = []
for i in range(1, len(M) - 1):
    a, b = M[i] - M[i - 1], M[i] - M[i + 1]
    if a * b > 0 and min(abs(a), abs(b)) / max(M[i], 0.5 * (M[i - 1] + M[i + 1])) > 0.2: flashes.append(keys[i])
S2 = [json.loads(l) for l in open("n1/n17/stage2.jsonl")]
res = {"states": [{"key": k, "t": T[k], "mean_Y_disp": m} for k, m in zip(keys, M)], "flashes": flashes, "FLASH_PASS": len(flashes) <= 1,
       "per_frame_fail": {r["key"]: [g for g in ("OIDN", "R3_PASS", "CF_PASS", "TRACE_PASS") if not r[g]] + (["SRC"] if r.get("SRC_PASS") is False else []) for r in S2}}
res["per_frame_fail"] = {k: v for k, v in res["per_frame_fail"].items() if v}
json.dump(res, open("n1/n17/stage2_results.json", "w"), indent=1); print(json.dumps(res, indent=1))
n = len(keys); cols = 2; rows = (n + 1) // 2; fig = plt.figure(figsize=(9.6, rows * 2.35 + 0.2), dpi=100, facecolor="black"); H = fig.get_figheight() * 100
for i, k in enumerate(keys):
    im = oiio.ImageBuf(f"n1/renders/final/cam_{k}.png").get_pixels(oiio.FLOAT)[..., :3]; r, c = divmod(i, cols)
    ax = fig.add_axes([(5 + c * 480) / 960, 1 - (10 + r * 235 + 25 + 200) / H, 470 / 960, 200 / H]); ax.imshow(np.clip(im, 0, 1), interpolation="lanczos"); ax.axis("off")
    ax.set_title(f"{i + 1}. {k}  t={T[k]}", color="w", fontsize=9)
fig.savefig("n1/n17/N17_stage2_sheet.png", facecolor="black")
