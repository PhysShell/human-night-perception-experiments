#!/usr/bin/env python3
"""Per-frame statistics of the authors' own demo video (gazehdr.mp4, NATIVE measurement).
Measures display code values only (8-bit Rec.709/sRGB-ish video as published); nothing is modelled.
Usage: frame_stats.py <video> <out.csv> [fps=30] [scale_w=341]
Columns: t_s, mean_Yp (Rec.709 luma of code values, 0..255), mean_Ylin (sRGB-decoded relative linear
luminance, 0..1, ASSUMING sRGB transfer), sat (mean HSV saturation over pixels with V>20),
dot_x, dot_y, dot_n (centroid/count of 'red gaze marker' pixels R>200,G<70,B<70; -1 if none)."""
import sys, subprocess, numpy as np
FF = "/nix/store/nm4ih3jrw0zma6qxhk5s2ks2r0gppzfl-ffmpeg-9.0.1-bin/bin/ffmpeg"
vid, out = sys.argv[1], sys.argv[2]
fps = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
W = int(sys.argv[4]) if len(sys.argv) > 4 else 341
H = int(round(W * 720 / 1366 / 2) * 2)
p = subprocess.Popen([FF, "-loglevel", "error", "-threads", "1", "-i", vid, "-vf",
                      f"fps={fps},scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     stdout=subprocess.PIPE)
n = W * H * 3
def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
with open(out, "w") as f:
    f.write("t_s,mean_Yp,mean_Ylin,sat,dot_x,dot_y,dot_n\n")
    i = 0
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        a = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        Yp = 0.2126 * R + 0.7152 * G + 0.0722 * B
        L = lin(a)
        Yl = 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
        mx = a.max(-1); mn = a.min(-1)
        m = mx > 20
        sat = float(((mx - mn)[m] / mx[m]).mean()) if m.any() else 0.0
        d = (R > 200) & (G < 70) & (B < 70)
        if d.sum() >= 2:
            ys, xs = np.nonzero(d); dx, dy, dn = xs.mean(), ys.mean(), int(d.sum())
        else:
            dx = dy = -1; dn = 0
        f.write(f"{i/fps:.4f},{Yp.mean():.4f},{Yl.mean():.6f},{sat:.4f},{dx:.2f},{dy:.2f},{dn}\n")
        i += 1
