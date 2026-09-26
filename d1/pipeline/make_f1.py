#!/usr/bin/env python3
"""F1 synthetic patch fixture (d1/pipeline/PREREG.md): 7 colours x 13 levels (1e-4..1e2 cd/m^2, half decades),
32x32 px patches on a 1e-5 cd/m^2 background, 8 px gaps. -> d1/pipeline/.cache/F1.exr, F1_layout.json"""
import json, os
import numpy as np, OpenImageIO as oiio
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
COL = {"neutral": [1, 1, 1], "red": [1, 0, 0], "green": [0, 1, 0], "blue": [0, 0, 1], "cyan": [0, 1, 1], "warm_lamp": [1, 0.55, 0.2], "yellow": [1, 1, 0]}
LEV = [10 ** (-4 + 0.5 * i) for i in range(13)]; P, G = 32, 8
H, W = G + len(COL) * (P + G), G + len(LEV) * (P + G)
img = np.full((H, W, 3), 1e-5, np.float32); lay = []
for r, (n, c) in enumerate(COL.items()):
    c = np.array(c, float); c = c / (M709 @ c)[1]
    for k, L in enumerate(LEV):
        y0, x0 = G + r * (P + G), G + k * (P + G); img[y0:y0 + P, x0:x0 + P] = c * L; lay.append({"colour": n, "L": L, "y0": y0, "x0": x0, "size": P})
os.makedirs("d1/pipeline/.cache", exist_ok=True)
sp = oiio.ImageSpec(W, H, 3, oiio.FLOAT); b = oiio.ImageBuf(sp); b.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), img); b.write("d1/pipeline/.cache/F1.exr")
json.dump(lay, open("d1/pipeline/.cache/F1_layout.json", "w")); print("F1", W, H)
