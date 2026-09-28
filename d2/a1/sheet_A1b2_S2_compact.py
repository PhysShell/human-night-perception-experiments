#!/usr/bin/env python3
"""Compact re-issue of the A1b stage-2 S2 sheet (layout only; the same PNGs as renders/A1b2_sheet_S2.png)."""
import os
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
FRZ = "d0/work/out/d1_pipeline/final/S2__PHONE_SDR100_DARK"; SH = "d2/a1/work/A1b2/s2keep"
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(float) / 65535
rows = []
for f in (1, 48):
    a, b = ld(f"{FRZ}/frame_{f:04d}.png"), ld(f"{SH}/frame_{f:04d}.png")
    full = lambda im: im.reshape(205, 4, 480, 4, 3).mean((1, 3))[:, 5:475]
    rows.append((f"S2 frame {f}: full frame  (left frozen D1 | right shoulder)", np.concatenate([full(a), np.zeros((205, 20, 3)), full(b)], 1)))
    rows.append((f"S2 frame {f}: band rows 100-420, cols 0-470 at 1:1  (left frozen D1 | right shoulder)",
                 np.concatenate([a[100:420, :470], np.zeros((320, 20, 3)), b[100:420, :470]], 1)))
lab = 26; H = sum(r.shape[0] + lab for _, r in rows); canvas = np.zeros((H, 960, 3)); y = 0; ys = []
for c, r in rows:
    ys.append(y); canvas[y + lab:y + lab + r.shape[0], :r.shape[1]] = r; y += lab + r.shape[0]
fig = plt.figure(figsize=(9.6, H / 100), dpi=100, facecolor="black"); fig.figimage(canvas, 0, 0, origin="upper")
for (c, _), y0 in zip(rows, ys): fig.text(0.01, 1 - (y0 + 18) / H, c, color="w", fontsize=10)
fig.savefig("d2/a1/renders/A1b2_sheet_S2_compact.png", dpi=100, facecolor="black")
