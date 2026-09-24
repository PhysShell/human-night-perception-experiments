#!/usr/bin/env python3
"""D0.1 iCAM06 absolute-level ladder (SENSITIVITY_RUN): the SAME S1 (and S3 pair) scaled by 10^k, k = 0 (the physical
night) .. 6 (sky ~290 cd/m^2, daylight), max_L = 0 (absolute input, Readme), p = 0.7, gamma 1.2 (dark surround).
Question: does iCAM06's absolute-luminance machinery (FL, rod term As/FLS, luminance-dependent IPT) make the physical
night look different from the same image at daylight level, and what survives the native display step?
Outputs: d0/work/out/icam06/ladder_x1e<k>/<scene>__PHONE_SDR100_DARK.png (native), XYZ_tm stats ->
d0/results/tables/icam06_ladder.json.  Needs the author code: d0/donors/icam06/setup.sh first.
  tracks/temporal-glare-2009/py.sh d0/donors/icam06/ladder.py
"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")); os.chdir(REPO)
W0 = "d0/work/donors/icam06"; TMP = os.path.abspath("d0/work/icam_ladder_tmp"); os.makedirs(TMP, exist_ok=True)
OCT = "tracks/hdrvdp3/octave.sh"
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
m = dict(np.load("d0/work/inputs/masks/S1.npz"))
res = {"what": __doc__.split("Outputs")[0].strip(), "params": {"max_L": 0, "p": 0.7, "gamma_value": 1.2}, "rows": []}


def uvdist(XYZ):
    X, Y, Z = XYZ[..., 0], XYZ[..., 1], XYZ[..., 2]; s = X + 15 * Y + 3 * Z + 1e-30
    return np.hypot(4 * X / s - 0.1978, 9 * Y / s - 0.4683)


for k in range(0, 7):
    for sc in ("S1", "S3_bar", "S3_nobar"):
        a = oiio.ImageBuf(f"d0/work/inputs/{sc}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float32) * np.float32(10.0 ** k)
        H, W = a.shape[:2]; fin, fo, fx = f"{TMP}/in.f32", f"{TMP}/out.u8", f"{TMP}/xyz.f32"
        a.tofile(fin)
        env = dict(os.environ, REPO=REPO, ICAM_IN=fin, ICAM_OUT=fo, ICAM_XYZ=fx, ICAM_H=str(H), ICAM_W=str(W), ICAM_P="0.7", ICAM_GAMMA="1.2",
                   ICAM_SRC=os.path.abspath(f"{W0}/src_pristine"), ICAM_SHIM=os.path.abspath(f"{W0}/shim"))
        r = subprocess.run([OCT, "d0/donors/icam06/icam06_ladder.m"], env=env, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stdout + r.stderr)
        u8 = np.fromfile(fo, np.uint8).reshape(H, W, 3); xyz = np.fromfile(fx, np.float32).reshape(H, W, 3).astype(np.float64)
        d = f"d0/work/out/icam06/ladder_x1e{k}"; os.makedirs(d, exist_ok=True)
        o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(), u8.astype(np.uint16) * 257); o.write(f"{d}/{sc}__PHONE_SDR100_DARK.png")
        if sc == "S1":
            Y = xyz[..., 1]; sky, tree, nl = m["sky"], m["tree"], ~m["near_lamp"]
            v = u8 / 255.0; lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); dXYZ = lin @ M709.T
            res["rows"].append({"k": k, "scene_sky_median_cd_m2": float(2.876e-4 * 10 ** k),
                "XYZ_tm_Y": {"sky_median": float(np.median(Y[sky])), "tree_median": float(np.median(Y[tree])), "max": float(Y.max()),
                             "sky_over_max": float(np.median(Y[sky]) / Y.max()), "sky_tree_weber": float(1 - np.median(Y[tree]) / np.median(Y[sky])),
                             "nonsource_chroma_uv_median": float(np.median(uvdist(xyz)[nl]))},
                "display_rel_Y": {"sky_median": float(np.median(dXYZ[..., 1][sky])), "tree_median": float(np.median(dXYZ[..., 1][tree])),
                                  "nonsource_chroma_uv_median": float(np.median(uvdist(dXYZ)[nl]))},
                "log": r.stdout.strip().splitlines()[-1:]})
            print(json.dumps(res["rows"][-1]), flush=True)
        for f in (fin, fo, fx):
            os.remove(f)
os.rmdir(TMP)
json.dump(res, open("d0/results/tables/icam06_ladder.json", "w"), indent=1)
