#!/usr/bin/env python3
"""D2-A2c blind sheet, exactly as d2/a2/PREREG_A2c.md (committed before this code). Seed-0 permutation of the three
existing RoadLine-A2 canonical D1 outputs; salted key -> A2c_blind_key.json (sha256 printed, committed before showing).
Per label: full frame (2x box-downsampled to 960 px) + road crop rows 410-820, cols 560-1360 at 1:1 (nearest)."""
import hashlib, json, os, secrets
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
SRC = {"frozen_D1": "n1/roadline/renders/A2_canonical_final.png", "oracle_A1a2": "d2/a1/renders/roadline_a1a.png", "Q999_A2b": "d2/a2/renders/roadline_A2b.png"}
names = list(SRC); perm = np.random.default_rng(0).permutation(3); key = {"XYZ"[i]: names[p] for i, p in enumerate(perm)}
key["salt"] = secrets.token_hex(16); kf = "d2/a2/A2c_blind_key.json"; open(kf, "w").write(json.dumps(key, indent=1))
print("key sha256", hashlib.sha256(open(kf, "rb").read()).hexdigest())
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(float) / 65535
Wc, pad, lab = 960, 10, 28; rows = []
for L in "XYZ":
    a = ld(SRC[key[L]]); full = a.reshape(410, 2, 960, 2, 3).mean((1, 3)); crop = a[410:820, 560:1360]
    blk = np.zeros((lab + 410 + pad + 410 + 2 * pad, Wc, 3)); blk[lab:lab + 410] = full
    blk[lab + 410 + pad:lab + 820 + pad, 80:880] = crop; rows.append((L, blk))
H = sum(b.shape[0] for _, b in rows); canvas = np.concatenate([b for _, b in rows]); fig = plt.figure(figsize=(Wc / 100, H / 100), dpi=100, facecolor="black")
fig.figimage(canvas, 0, 0, origin="upper"); y = 0
for L, b in rows:
    fig.text(0.01, 1 - (y + 20) / H, f"{L}: full frame (top), road crop 1:1 rows 410-820 cols 560-1360 (bottom)", color="w", fontsize=11); y += b.shape[0]
fig.savefig("d2/a2/renders/A2c_blind_sheet.png", dpi=100, facecolor="black")
