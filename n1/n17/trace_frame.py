#!/usr/bin/env python3
"""N1.7 addendum 2, per trace frame: after the render, write the x179 Combined pass as cd/m^2 EXR (then the raw EXR is
deleted), or, with 'stats', extract the numbers from the frozen A caches and append to n1/n17/trace.jsonl.
  tracks/temporal-glare-2009/py.sh n1/n17/trace_frame.py convert WDIR
  tracks/temporal-glare-2009/py.sh n1/n17/trace_frame.py stats WDIR AXNAME T X Y Z YAW PITCH"""
import json, math, os, re, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
YW = np.array([0.2126, 0.7152, 0.0722]); STEP, W = sys.argv[1], sys.argv[2]
if STEP == "convert":
    src = f"{W}/hero_b.exr"; P = {}
    for si in range(oiio.ImageBuf(src).nsubimages):
        b = oiio.ImageBuf(src, si, 0); a = b.get_pixels(oiio.FLOAT); assert not b.has_error, b.geterror()
        for i, c in enumerate(b.spec().channelnames):
            parts = c.split("."); P.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
    rgb = np.stack([P["Combined"][c] for c in "RGB"], -1) * 179.0; assert np.isfinite(rgb).all()
    H, Wd = rgb.shape[:2]; o = oiio.ImageBuf(oiio.ImageSpec(Wd, H, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, Wd, 0, H, 0, 1, 0, 3), np.ascontiguousarray(rgb, np.float32))
    assert o.write(f"{W}/cdm2.exr"), o.geterror(); os.remove(src)
else:
    from cam import project_view
    AX, T, X, Y, Z, YAW, PITCH = sys.argv[3], *map(float, sys.argv[4:10])
    L = oiio.ImageBuf(f"{W}/cdm2.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64) @ YW
    hdr = open(f"d1/a_extract/.cache/{AX}/out.header").read(); m = re.search(r"EXPOSURE=([0-9.eE+-]+)", hdr)
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; g = {"__name__": "trace", "__file__": f"{REPO}/d1/display_r/run.py"}
    exec(compile(src, "d1/display_r/run.py[trace]", "exec"), g)
    r_ax, v = g["extract"](AX); Ya = v["Ynew"]
    lx, ly = project_view((4.5, 45.0, 5.92), (X, Y, Z), YAW, PITCH); sy, cy = math.sin(math.radians(YAW)), math.cos(math.radians(YAW))
    front = (4.5 - X) * (-sy) + (45.0 - Y) * cy > 0
    row = {"t": T, "EXPOSURE": float(m.group(1)) if m else None, "branch": r_ax["tone_map"]["mode"], "C0": r_ax["C0_bit_identical"],
           "Y_A_median": float(np.median(Ya)), "Y_disp_median_pred": float(0.1 + 99.9 * np.median(np.clip(Ya, 0, 1))),
           "scene_logmean": float(np.exp(np.log(np.maximum(L, 1e-7)).mean())), "scene_median": float(np.median(L)), "scene_Q999": float(np.percentile(L, 99.9)),
           "lamp_in_frame": bool(front and 0 <= lx < 1920 and 0 <= ly < 820), "lamp_px": [lx, ly] if front else None}
    open("n1/n17/trace.jsonl", "a").write(json.dumps(row) + "\n"); print(row)
