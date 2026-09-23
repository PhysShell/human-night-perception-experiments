#!/usr/bin/env python3
"""NATIVE measurement of the authors' demo video (gazehdr.mp4): patch statistics over time for one
segment. Frames decoded by ffmpeg at 683x360 (half of 1366x720), 30 fps. Values are DISPLAY CODE
VALUES of the published H.264 video, converted to relative linear light ASSUMING an sRGB transfer
(the video is untagged; the paper's gamma is 0.455, Appendix A). Nothing about the model is simulated.
Usage: segment_patches.py <video> <scene: lamp|sunset> <t0> <t1> <out.csv>"""
import sys, subprocess, numpy as np
FF = "/nix/store/nm4ih3jrw0zma6qxhk5s2ks2r0gppzfl-ffmpeg-9.0.1-bin/bin/ffmpeg"
vid, scene, t0, t1, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
W, H, FPS = 683, 360, 30
# patches: name -> (x0, x1, y0, y1) in 683x360 frame coordinates (chosen by inspecting stills)
P = {
 "lamp": {"bg_dark": (40, 200, 20, 100), "leftchk_neutral": (40, 190, 232, 252),
          "leftchk_colour": (40, 190, 145, 220), "rightchk_neutral": (500, 620, 215, 235),
          "lamp_face": (476, 486, 172, 186)},
 "sunset": {"sky_upper_right": (450, 650, 20, 80), "grass": (100, 600, 300, 350),
            "water_left": (20, 200, 250, 280), "sun_disk": (334, 342, 204, 212)},
}[scene]
def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
p = subprocess.Popen([FF, "-loglevel", "error", "-threads", "1", "-ss", str(t0), "-i", vid, "-t", str(t1 - t0),
                      "-vf", f"fps={FPS},scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     stdout=subprocess.PIPE)
n = W * H * 3
yy, xx = np.mgrid[0:H, 0:W]
cols = ["t_s", "dot_x", "dot_y"]
for k in P: cols += [f"{k}_Ylin", f"{k}_Ymax_code", f"{k}_sat"]
cols += ["leftchk_edge_rel"] if scene == "lamp" else []
with open(out, "w") as f:
    f.write(",".join(cols) + "\n")
    i = 0
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        a = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        dot = (R > 200) & (G < 70) & (B < 70)
        if dot.sum() >= 3:
            ys, xs = np.nonzero(dot); dx, dy = xs.mean(), ys.mean()
            keep = np.hypot(xx - dx, yy - dy) > 14
        else:
            dx = dy = -1; keep = np.ones((H, W), bool)
        L = lin(a); Y = 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
        Yc = 0.2126 * R + 0.7152 * G + 0.0722 * B
        mx = a.max(-1); mn = a.min(-1); S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
        row = [f"{t0 + i / FPS:.4f}", f"{dx:.1f}", f"{dy:.1f}"]
        for k, (x0, x1, y0, y1) in P.items():
            m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = True; m &= keep
            if m.sum() < 4: row += ["nan", "nan", "nan"]; continue
            row += [f"{Y[m].mean():.6f}", f"{Yc[m].max():.1f}", f"{S[m].mean():.4f}"]
        if scene == "lamp":
            x0, x1, y0, y1 = P["leftchk_colour"]
            reg = Y[y0 - 10:y1 + 30, x0:x1]
            lap = np.abs(4 * reg[1:-1, 1:-1] - reg[:-2, 1:-1] - reg[2:, 1:-1] - reg[1:-1, :-2] - reg[1:-1, 2:])
            row += [f"{lap.mean() / max(reg.mean(), 1e-6):.5f}"]
        f.write(",".join(row) + "\n"); i += 1
