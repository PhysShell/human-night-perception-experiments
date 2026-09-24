#!/usr/bin/env python3
"""B0 blind presentation. The six variants at the nominal point (source x1, phone Ldmax 100, no
silhouette), shuffled with an OS-random permutation and labelled only A-F. The key is written to
b0/results/BLIND_KEY_open_after_viewing.json.
Each still is the 876 x 438 displayed image placed 1:1 (no scaling) in the centre of a black
1920 x 820 frame, i.e. exactly PHONE_TARGET (73 px/deg) when shown full screen on a 1920-px-wide
phone in landscape. Each video is 6 s at 24 fps: static variants repeat their frame; the temporal
glare variant plays its sequence, so it can only be recognised by eye.
  nix develop -c python3 b0/blind.py
"""
import json, os, random, subprocess
import numpy as np
import OpenImageIO as oiio

D, R = "b0/out", "b0/results/blind"
os.makedirs(R, exist_ok=True)
VAR = ["V0_none", "V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V4_spencer", "V5_temporal"]
perm = VAR[:]
random.SystemRandom().shuffle(perm)
key = {chr(65 + i): v for i, v in enumerate(perm)}
json.dump({"key": key, "nominal": "source x1 (800 cd at 3 km), Ldmax 100, no silhouette, PHONE 73 px/deg"},
          open("b0/results/BLIND_KEY_open_after_viewing.json", "w"), indent=1)


def canvas(png):
    a = oiio.ImageBuf(png).get_pixels(oiio.UINT8)[..., :3]
    c = np.zeros((820, 1920, 3), np.uint8)
    y0, x0 = (820 - a.shape[0]) // 2, (1920 - a.shape[1]) // 2
    c[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    return c


def save(path, a):
    b = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.UINT8))
    b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a)); b.write(path)


tmp = f"{R}/_frames"; os.makedirs(tmp, exist_ok=True)
crops = []
for letter, v in key.items():
    still = f"{D}/display/{v}_k1_nobar_LD100.png"
    save(f"{R}/{letter}.png", canvas(still))
    a = oiio.ImageBuf(still).get_pixels(oiio.UINT8)[..., :3]
    crops.append(a[219 - 73:219 + 73, 438 - 146:438 + 146])      # 4 x 2 deg around the source, 1:1
    for i in range(144):
        src = f"{D}/seq/V5_k1_{i + 1:04d}_LD100.png" if v == "V5_temporal" else still
        save(f"{tmp}/{i:04d}.png", canvas(src))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "24", "-i", f"{tmp}/%04d.png", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "10", "-movflags", "+faststart", f"{R}/{letter}.mp4"], check=True)
grid = np.concatenate([np.concatenate(crops[:3], 1), np.concatenate(crops[3:], 1)], 0)
save(f"{R}/overview_ABC_top_DEF_bottom_4x2deg_1to1.png", grid)
subprocess.run(["rm", "-rf", tmp])
print("blind set:", sorted(os.listdir(R)))
