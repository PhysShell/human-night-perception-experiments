#!/usr/bin/env python3
"""NATIVE measurement: the lamp demo in gazehdr.mp4 plays the SAME scripted gaze sequence three times
(pass 1 'Global adaptation' starts 28.77 s, pass 2 'Adding afterimages' 61.83 s, pass 3 'Adding
low-light effects' 80.30 s; start = first gaze jump detected by frame_stats.py). Aligning the passes
on that jump isolates what each added effect does to the displayed frame.
Outputs CSV of aligned time series + a few stills (PNG) + difference maps. Code values -> relative
linear via sRGB decode (assumption). Usage: compare_passes.py <video> <outdir>"""
import sys, subprocess, numpy as np
from PIL import Image
FF = "/nix/store/nm4ih3jrw0zma6qxhk5s2ks2r0gppzfl-ffmpeg-9.0.1-bin/bin/ffmpeg"
vid, od = sys.argv[1], sys.argv[2]
W, H, FPS = 683, 360, 30
starts = {"P1_global": 28.77, "P2_afterimages": 61.83, "P3_lowlight": 80.30}
DUR = 11.5   # pass 3 is cut at ~92.3 s
def grab(t0):
    p = subprocess.run([FF, "-loglevel", "error", "-threads", "1", "-ss", f"{t0 - 0.5:.3f}", "-i", vid,
                        "-t", f"{DUR + 0.5:.3f}", "-vf", f"fps={FPS},scale={W}:{H}:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8); n = a.size // (W * H * 3)
    return a[: n * W * H * 3].reshape(n, H, W, 3)
def lin(c):
    c = c.astype(np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
V = {k: grab(t) for k, t in starts.items()}
n = min(v.shape[0] for v in V.values())
LEFT = (40, 190, 145, 252)   # left (dark) colour checker incl. neutral row, 683x360 coords
yy, xx = np.mgrid[0:H, 0:W]
rows = []
for i in range(n):
    t = i / FPS - 0.5
    r = [f"{t:.3f}"]
    for k in starts:
        a = V[k][i].astype(np.float32); L = lin(V[k][i])
        dot = (a[..., 0] > 200) & (a[..., 1] < 70) & (a[..., 2] < 70)
        if dot.sum() >= 3:
            ys, xs = np.nonzero(dot); dx, dy = xs.mean(), ys.mean()
            ring = (np.hypot(xx - dx, yy - dy) > 14) & (np.hypot(xx - dx, yy - dy) < 40)
            keep = np.hypot(xx - dx, yy - dy) > 14
        else:
            dx = dy = -1; ring = np.zeros((H, W), bool); keep = np.ones((H, W), bool)
        x0, x1, y0, y1 = LEFT
        reg = np.zeros((H, W), bool); reg[y0:y1, x0:x1] = True; reg &= keep
        mx = a.max(-1); mn = a.min(-1); S = (mx - mn) / np.maximum(mx, 1)
        Y = 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
        sub = Y[y0:y1, x0:x1]
        lap = np.abs(4 * sub[1:-1, 1:-1] - sub[:-2, 1:-1] - sub[2:, 1:-1] - sub[1:-1, :-2] - sub[1:-1, 2:])
        ringRGB = L[ring].mean(0) if ring.any() else np.array([np.nan] * 3)
        r += [f"{dx:.1f}", f"{dy:.1f}", f"{Y[reg].mean():.6f}", f"{S[reg].mean():.4f}",
              f"{lap.mean() / max(sub.mean(), 1e-6):.5f}",
              f"{ringRGB[0]:.6f}", f"{ringRGB[1]:.6f}", f"{ringRGB[2]:.6f}"]
    rows.append(",".join(r))
hdr = ["t_rel_s"]
for k in starts:
    hdr += [f"{k}_{c}" for c in ["dot_x", "dot_y", "leftchk_Ylin", "leftchk_sat", "leftchk_edge_rel",
                                  "gazering_R", "gazering_G", "gazering_B"]]
open(f"{od}/NATIVE_lamp_passes_aligned.csv", "w").write(",".join(hdr) + "\n" + "\n".join(rows) + "\n")
# stills at aligned times: pass rows, time columns; plus |P2-P1| and |P3-P1| difference maps (x4 gain)
ts = [0.3, 2.0, 5.0, 8.4, 9.0, 11.0]
idx = [int(round((t + 0.5) * FPS)) for t in ts if (t + 0.5) * FPS < n]
tiles = []
for k in starts:
    tiles.append(np.concatenate([V[k][i][::2, ::2] for i in idx], 1))
for k in ["P2_afterimages", "P3_lowlight"]:
    d = [np.clip(np.abs(V[k][i].astype(np.int16) - V["P1_global"][i].astype(np.int16)) * 4, 0, 255).astype(np.uint8)[::2, ::2] for i in idx]
    tiles.append(np.concatenate(d, 1))
Image.fromarray(np.concatenate(tiles, 0)).save(f"{od}/NATIVE_lamp_passes_stills.png")
print("frames", n, "stills at t_rel", ts[: len(idx)])
