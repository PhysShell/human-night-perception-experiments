#!/usr/bin/env python3
"""B0 v2 continuous sweep of the source level (0.1x .. 100x, 31 log steps; E at the eye 8.9e-6 .. 8.9e-3 lx)
for every optics variant, using retinal(k, bar) = R(sky_bar) + k * R(src1) (exact, linear optics).
Per variant and k:
  * display step (frozen pcond, PHONE, Ldmax 100) -> WHITE-CLIPPED PLATEAU angular diameter under this
    display mapping (equivalent diameter of the clipped area; NOT a PSF size), peak;
  * trunk visibility, HDR-VDP-3 side-by-side P_det on the displayed images, two evaluators (stage ledger):
      EVAL_OFF    : evaluator optics OFF (mtf none) - isolates the donor chain;
      EVAL_VIEWER : evaluator = the viewer's real eye looking at the phone (HDR-VDP MTF) - physically
                    present, and NOT the same eye as the donor's (which models the eye in the scene)
    both with HDR-VDP's own local adaptation + CSF (evaluator stages, never in a donor);
  * Vangorp adaptation luminance at the trunk, on the DONOR retinal image (HDR-VDP local adapt).
REAL_SCENE_REFERENCE (reference observer models, NOT ground truth): the physical stimulus at 146 px/deg
(converged: 73/146/292 px/deg within 5 %), donor none, evaluator optics CIE99 or HDR-VDP MTF.
  nix develop -c python3 b0/sweep.py [variants...]
"""
import json, math, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import OpenImageIO as oiio

C, O = "b0/out/comp", "b0/out/sweep"
os.makedirs(O, exist_ok=True)
K = np.geomspace(0.1, 100, 31)
VAR = sys.argv[1:] or ["V0_none", "V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V4_spencer", "V5_temporal", "V5t_square", "V5t_norenorm"]
meta = json.load(open("b0/out/stim/meta.json"))
PPD = meta["px_per_deg"]; ARC = 60 / PPD
bx0, bx1, by0, by1 = meta["bar_px_x0x1y0y1"]; BAR_XY = ((bx0 + bx1) // 2, (by0 + by1) // 2)
Yw = np.array([0.2126, 0.7152, 0.0722])
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def save(p, a):
    b = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT))
    b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a, np.float32)); b.write(p)


def raw(p, a):
    with open(p, "wb") as f:
        np.array([a.shape[0], a.shape[1], 3, 3], "<i4").tofile(f); a.astype("<f4").tofile(f)


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pdet(run_json):
    try:
        t = open(run_json).read()
        return float(t.split('"side-by-side":{"P_det":')[1].split(",")[0])
    except Exception:
        return None


jobs_disp, jobs_vis, lla_list, rows = [], [], [], []
for v in VAR:
    Rsb, Rsn, Rs = ld(f"{C}/{v}_C_sky_bar.exr"), ld(f"{C}/{v}_C_sky_nobar.exr"), ld(f"{C}/{v}_C_src1.exr")
    for i, k in enumerate(K):
        tag = f"{O}/{v}_i{i:02d}"
        if not os.path.exists(f"{tag}_nobar_displayed_cdm2.exr"):
            for b, Rb in (("bar", Rsb), ("nobar", Rsn)):
                save(f"{tag}_{b}_retinal.exr", Rb + k * Rs)
                jobs_disp.append(f"b0/display.sh {tag}_{b}_retinal.exr {tag}_{b} 100")
            raw(f"{tag}_bar_retinal.raw", Rsb + k * Rs)
            lla_list.append(f"{tag}_bar_retinal.raw {tag}_lla.txt {BAR_XY[0]} {BAR_XY[1]}")
        for ev, mtf in (("EVAL_OFF", "none"), ("EVAL_VIEWER", "hdrvdp")):
            jobs_vis.append((f"tracks/hdrvdp3/run_hdrvdp.sh {tag}_bar_displayed_cdm2.exr {tag}_nobar_displayed_cdm2.exr PHONE "
                             f"{tag}_{ev} --display none --mtf {mtf} --tasks side-by-side", f"{tag}_{ev}/run.json"))
print(f"display jobs {len(jobs_disp)}, lla {len(lla_list)}, visibility jobs {len(jobs_vis)}", flush=True)
with ThreadPoolExecutor(4) as ex:
    list(ex.map(sh, jobs_disp))
if lla_list:
    open(f"{O}/lla_list.txt", "w").write("\n".join(lla_list) + "\n")
    sh(f"REPO=$PWD B0_LIST={O}/lla_list.txt B0_PPD={PPD} tracks/hdrvdp3/octave.sh b0/lla_batch.m")
    sh(f"rm -f {O}/*_retinal.raw {O}/*_retinal.exr")
with ThreadPoolExecutor(4) as ex:
    list(ex.map(lambda j: None if os.path.exists(j[1]) else sh(j[0]), jobs_vis))
for v in VAR:
    for i, k in enumerate(K):
        tag = f"{O}/{v}_i{i:02d}"
        img = ld(f"{tag}_nobar_displayed_cdm2.exr")
        dl = (img - 1.0) / 100.0
        white = (dl >= 0.98).any(-1)
        la = open(f"{tag}_lla.txt").read().split()
        rows.append({"variant": v, "k": float(k), "E_eye_lx": float(k * meta["source"]["E_eye_lx"]["1"]),
                     "peak_display_cdm2": float((img @ Yw).max()),
                     "white_plateau_equiv_diam_arcmin": float(2 * math.sqrt(white.sum() / math.pi) * ARC),
                     "P_det_trunk_EVAL_OFF": pdet(f"{tag}_EVAL_OFF/run.json"),
                     "P_det_trunk_EVAL_VIEWER": pdet(f"{tag}_EVAL_VIEWER/run.json"),
                     "Vangorp_Lla_trunk": float(la[0]), "Vangorp_Lla_far_sky": float(la[1])})
json.dump(rows, open("b0/results/sweep.json", "w"), indent=1)
print(f"{len(rows)} rows -> b0/results/sweep.json")
