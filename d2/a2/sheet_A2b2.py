#!/usr/bin/env python3
"""D2-A2b stage-2 visual sheets (PREREG_A2b_stage2.md §5 V): frozen D1 vs Q99.9 guard for every active natural scene
(hero, C, S1, S2). S2 frames 1 and 48 are recomputed through the identical code path (policy sha256 asserted), and
their s_hist is asserted equal to the value recorded in results_A2b2.json. Not blind: a degradation check.
  tracks/temporal-glare-2009/py.sh d2/a2/sheet_A2b2.py   -> d2/a2/renders/A2b2_sheet_{hero,C,S1,S2}.png"""
import ast, hashlib, json, os, subprocess
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
S_HIST_SHA = "7f7b37537f27425b8d8c2e96169d364730ac5eae5b6cc96e8395b3c6a7449edf"
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"; NEW_LINE = "S_H = s_hist(Ya, axname); Yreq = LO + (HI - LO) * S_H * Ya"; GUARD = {}
a2b = subprocess.run(["git", "show", "bacfd86:d2/a2/run_A2b.py"], capture_output=True, text=True, check=True).stdout
fn = [n for n in ast.parse(a2b).body if isinstance(n, ast.FunctionDef) and n.name == "s_hist"][0]; seg = ast.get_source_segment(a2b, fn)
assert hashlib.sha256(seg.encode()).hexdigest() == S_HIST_SHA; exec(seg)
res = json.load(open("d2/a2/results_A2b2.json")); WK = "d2/a2/work"; FRZ = "d0/work/out/d1_pipeline/final"
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, NEW_LINE); a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(S_H=S_H, H=H, W=W,')
gv = {"__name__": "sheet", "__file__": f"{REPO}/d1/display_r/run.py", "s_hist": s_hist}; exec(compile(src, "d1/display_r/run.py[A2b2 sheet]", "exec"), gv)
for f in (1, 48):
    n = f"frame_{f:04d}"; out = f"{WK}/s2_{n}.png"; g, v = gv["run_image"](f"d0/work/inputs/S2/{n}.exr", f"S2/{n}", "yprio", out)
    assert v["S_H"] == res["S2_per_frame"][n]["s_hist"], (n, v["S_H"])
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(float) / 65535
os.makedirs("d2/a2/renders", exist_ok=True)


def sheet(name, pairs):
    """pairs: list of (caption, frozen_png, guard_png); frozen on the left, guard on the right."""
    ims = [(c, ld(fz), ld(gd)) for c, fz, gd in pairs]; h, w = ims[0][1].shape[:2]; pw = 470; ph = pw * h / w
    fig = plt.figure(figsize=(9.6, (ph + 40) * len(ims) / 100 + 0.2), dpi=100, facecolor="black"); H = fig.get_figheight() * 100
    for i, (c, fz, gd) in enumerate(ims):
        top = 20 + i * (ph + 40) + 20
        for j, (lab, im) in enumerate((("frozen D1", fz), ("Q99.9 guard", gd))):
            ax = fig.add_axes([(10 + j * (pw + 10)) / 960, 1 - (top + ph) / H, pw / 960, ph / H]); ax.imshow(im, interpolation="lanczos"); ax.axis("off")
            ax.set_title(f"{c}: {lab}", color="w", fontsize=9)
    fig.savefig(f"d2/a2/renders/A2b2_sheet_{name}.png", facecolor="black")


sheet("hero", [("hero", "n1/renders/final/hero.png", f"{WK}/views/hero.png")])
sheet("C", [("Camera C", "n1/renders/final/cam_C.png", f"{WK}/views/C.png")])


def band_sheet(name, pairs):
    """S1-type panoramas: per image, full frame (960 wide) + the sky/poplar/lamp band rows 100-420 at 1:1 (left, right half)."""
    blocks = []
    for c, fz, gd in pairs:
        for lab, p in (("frozen D1", fz), ("Q99.9 guard", gd)):
            im = ld(p); full = im.reshape(410, 2, 960, 2, 3).mean((1, 3)); bl, br = im[100:420, :960], im[100:420, 960:]
            blocks.append((f"{c}: {lab}: full frame | band rows 100-420 1:1, left half | right half", np.concatenate([full, np.zeros((6, 960, 3)), bl, np.zeros((6, 960, 3)), br])))
    lab_h = 26; H = sum(b.shape[0] + lab_h for _, b in blocks); canvas = np.zeros((H, 960, 3)); y = 0; ys = []
    for c, b in blocks:
        ys.append(y); canvas[y + lab_h:y + lab_h + b.shape[0]] = b; y += lab_h + b.shape[0]
    fig = plt.figure(figsize=(9.6, H / 100), dpi=100, facecolor="black"); fig.figimage(canvas, 0, 0, origin="upper")
    for (c, _), y0 in zip(blocks, ys): fig.text(0.01, 1 - (y0 + 18) / H, c, color="w", fontsize=10)
    fig.savefig(f"d2/a2/renders/A2b2_sheet_{name}.png", dpi=100, facecolor="black")


band_sheet("S1", [("S1", f"{FRZ}/S1__PHONE_SDR100_DARK.png", f"{WK}/final/S1__PHONE_SDR100_DARK.png")])
band_sheet("S2", [(f"S2 frame {f}", f"{FRZ}/S2__PHONE_SDR100_DARK/frame_{f:04d}.png", f"{WK}/s2_frame_{f:04d}.png") for f in (1, 48)])
print("ok")
