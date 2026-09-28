#!/usr/bin/env python3
"""D2-A1b V7 blind sheet, exactly as d2/a1/PREREG_A1b_V7.md (committed before this code). Same layout as the A2 blind
sheet (full frame + far-lamp crop rows 330-440 cols 900-1180, nearest; 8-bit as A2); seed-1 permutation; salted key in
the git-ignored d2/a1/work/ until the reveal.   -> d2/a1/renders/V7_blind_sheet.png"""
import hashlib, json, os, secrets
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
SRC = {"A1b": "d2/a1/renders/roadline_A1b.png", "V0": "n1/roadline/renders/A2_v0.png", "Blender_AgX_+7": "n1/roadline/renders/A2_comparator.png"}
names = list(SRC); perm = np.random.default_rng(1).permutation(3); key = {"XYZ"[i]: names[p] for i, p in enumerate(perm)}
key["salt"] = secrets.token_hex(16); os.makedirs("d2/a1/work", exist_ok=True); kf = "d2/a1/work/V7_blind_key.json"; open(kf, "w").write(json.dumps(key, indent=1))
print("key sha256", hashlib.sha256(open(kf, "rb").read()).hexdigest())
imgs = {L: (np.clip(oiio.ImageBuf(SRC[key[L]]).get_pixels(oiio.FLOAT)[..., :3], 0, 1) * 255).astype(np.uint8) for L in "XYZ"}
f, ax = plt.subplots(6, 1, figsize=(16, 30), facecolor="black")
for i, L in enumerate("XYZ"):
    ax[2 * i].imshow(imgs[L], interpolation="none"); ax[2 * i].set_title(L, color="w", fontsize=18); ax[2 * i].axis("off")
    ax[2 * i + 1].imshow(imgs[L][330:440, 900:1180], interpolation="nearest"); ax[2 * i + 1].set_title(f"{L}: crop of the far lamps (200-1600 m)", color="w", fontsize=12); ax[2 * i + 1].axis("off")
f.savefig("d2/a1/renders/V7_blind_sheet.png", dpi=55, facecolor="black", bbox_inches="tight")
