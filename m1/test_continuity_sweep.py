#!/usr/bin/env python3
"""Temporal continuity sweep for pcond_colorimetric.sh (and the display gamut step).

A 4x4-pixel coloured source sits in the dark sky of the M1 scene; its luminance ramps
geometrically 0.03 .. 30 cd/m^2 over 61 frames (~12 %/frame), crossing pcond's clip point
(mesopic in this scene) into the photopic range. The source is small enough not to move
pcond's adaptation (checked: one EXPOSURE value for all frames). Every frame goes through
the unchanged route; measured on the source pixel, per stage:
  linear      pcond_colorimetric.sh output (display-linear Rec.709, before gamut handling)
  pbr_oog     + Khronos PBR Neutral on pixels outside the display cube, Standard elsewhere
  clipgamut   + Radiance clipgamut (pcond -l -e 1 with a Rec.709 PRIMARIES header)
Reference = pcond as shipped (path A). The test asks whether our composition ADDS temporal
artefacts that pcond itself does not have (pcond's own hard knee at display max is not ours).
  colour seam  = CIE 1976 u'v' step between frames that is > 3x the mean of the two steps on
                 each side AND > 0.002 (half a colour JND of ~0.004). Hue is reported as the
                 u'v' arc (chroma x angle): for these mesopic, near-grey colours (chroma
                 0.005-0.04) a 1 deg hue step is only ~0.0007 u'v', below RGBE quantisation.
  luminance    = pop if |dlog Y_stage - dlog Y_pcond| > log 1.05 between two frames;
                 "added fall" if Y_stage falls relative to pcond's own step by more than
                 3 RGBE quantisation steps (2.4 %; the LC chain quantises three times).
Gate: only the pcond stage ("linear") decides the exit code; the two display gamut stages
are reported (their known defects are documented in m1/README.md, section 4).
usage: test_continuity_sweep.py scene.exr|synthetic [outdir] [mode AB|LC]
  "synthetic" = uniform moonless sky (4e-4 cd/m^2), self-contained for nix flake check.
"""
import concurrent.futures as cf, glob, os, shutil, subprocess, sys, tempfile
import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as ocio

HERE = os.path.dirname(os.path.abspath(__file__))
scene = sys.argv[1] if len(sys.argv) > 1 else "m1/out/scene.exr"
out = sys.argv[2] if len(sys.argv) > 2 else "m1/out/ab_sweep"
MODE = sys.argv[3] if len(sys.argv) > 3 else "LC"
os.makedirs(out, exist_ok=True)
K = 179.0
REC709 = "0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
Yw = np.array([0.2126, 0.7152, 0.0722])
COLS = {"sodium": (1.0, 0.45, 0.08), "warm LED": (1.0, 0.72, 0.42),
        "red": (1.0, 0.05, 0.03), "blue": (0.05, 0.12, 1.0)}
L = np.geomspace(0.03, 30.0, 61)
Y0, X0 = 200, 1500                                         # dark sky
if scene == "synthetic":
    base = np.full((820, 1920, 3), 4e-4 / 179.0, np.float32)
else:
    base = oiio.ImageBuf(scene).get_pixels(oiio.FLOAT)[..., :3]
cfg = ocio.Config.CreateFromFile(glob.glob(os.path.dirname(os.path.realpath(shutil.which("blender")))
                                           + "/../share/blender/*/datafiles/colormanagement/config.ocio")[0])
pbr = cfg.getProcessor("Linear Rec.709", "sRGB", "Khronos PBR Neutral", ocio.TRANSFORM_DIR_FORWARD).getDefaultCPUProcessor()
std = cfg.getProcessor("Linear Rec.709", "sRGB", "Standard", ocio.TRANSFORM_DIR_FORWARD).getDefaultCPUProcessor()


def frame(args):
    name, i = args
    c = np.array(COLS[name], np.float32)
    c = c / (c @ Yw)
    img = base.copy()
    img[Y0:Y0 + 4, X0:X0 + 4] = c * L[i] / K               # radiance units, K = 179 convention
    d = tempfile.mkdtemp(dir=out)
    oiio.ImageBuf(img).write(f"{d}/in.exr")
    subprocess.run(f"{HERE}/pcond_colorimetric.sh {d}/in.exr 60 {MODE} {d}/ab.hdr 1", shell=True, check=True)
    ab = oiio.ImageBuf(f"{d}/ab.hdr").get_pixels(oiio.FLOAT)[Y0 + 1:Y0 + 3, X0 + 1:X0 + 3].reshape(-1, 3).mean(0)
    a = oiio.ImageBuf(f"{d}/ab.pcond.hdr").get_pixels(oiio.FLOAT)[Y0 + 1:Y0 + 3, X0 + 1:X0 + 3].reshape(-1, 3).mean(0)
    expo = subprocess.run(f"getinfo < {d}/ab.pcond.hdr | grep EXPOSURE", shell=True,
                          capture_output=True, text=True).stdout.split("=")[-1].strip()
    subprocess.run(f"cd {d} && getinfo -a 'PRIMARIES= {REC709}' < ab.hdr > abp.hdr && "
                   f"pcond -l -e 1 -p {REC709} abp.hdr > cg.hdr", shell=True, check=True)
    cg = oiio.ImageBuf(f"{d}/cg.hdr").get_pixels(oiio.FLOAT)[Y0 + 1:Y0 + 3, X0 + 1:X0 + 3].reshape(-1, 3).mean(0)
    shutil.rmtree(d)
    return name, i, ab, a, expo, cg


def uv_hue_chroma(rgb):
    X, Y, Z = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ rgb
    s = X + 15 * Y + 3 * Z
    u, v = 4 * X / s, 9 * Y / s
    du, dv = u - 0.1978, v - 0.4683                        # D65
    return np.degrees(np.arctan2(dv, du)), np.hypot(du, dv), Y


def through(proc, rgb):
    px = np.ascontiguousarray(rgb[None, None], np.float32).copy()
    proc.applyRGB(px)
    v = np.clip(px[0, 0], 0, 1)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)   # back to linear


def pbr_oog(rgb):
    """run_m1.sh gamut step: PBR Neutral only outside the display cube, Standard elsewhere."""
    return through(pbr if rgb.max() > 1 else std, rgb)


jobs = [(n, i) for n in COLS for i in range(len(L))]
with cf.ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
    res = list(ex.map(frame, jobs))

fails = []
print(f"mode {MODE}: {len(L)} frames per colour, luminance step {L[1] / L[0] - 1:.1%}; "
      f"pcond EXPOSURE values seen: {sorted({r[4] for r in res})}")
for name in COLS:
    rows = sorted([r for r in res if r[0] == name], key=lambda r: r[1])
    lin = np.array([r[2] for r in rows]); a = np.array([r[3] for r in rows])
    clipped = a.max(-1) >= 0.999
    k = int(np.argmax(clipped)) if clipped.any() else None
    stages = {"linear": lin, "pbr_oog": np.array([pbr_oog(x) for x in lin]),
              "clipgamut": np.array([through(std, r[5]) for r in rows])}
    YA = np.array([uv_hue_chroma(x)[2] for x in a])                  # pcond as shipped
    dYA = np.diff(np.log(np.maximum(YA, 1e-9)))
    for stage, arr in stages.items():
        h, ch, Y = np.array([uv_hue_chroma(x) for x in arr]).T
        u, v = ch * np.cos(np.radians(h)), ch * np.sin(np.radians(h))
        duv = np.hypot(np.diff(u), np.diff(v))
        nb = np.array([np.mean(np.r_[duv[i - 2:i], duv[i + 1:i + 3]]) if 2 <= i < len(duv) - 2 else np.inf
                       for i in range(len(duv))])
        seam = (duv > 3 * nb) & (duv > 0.002)
        arc = ch[1:] * np.radians(np.abs((np.diff(h) + 180) % 360 - 180))
        dY = np.diff(np.log(np.maximum(Y, 1e-9)))
        pop = np.abs(dY - dYA) > np.log(1.05)
        fall = (dY - dYA) < np.log(1 - 3 / 128)
        ok = not seam.any() and not pop.any() and not fall.any()
        where = lambda m: ",".join(str(i + 1) for i in np.flatnonzero(m)) or "-"
        print(f"  {name:9s} {stage:9s}: colour seams {where(seam):7s} (max du'v' step {duv.max():.4f}, "
              f"max hue arc {arc.max():.4f}); luminance pops vs pcond {where(pop):9s} added falls {where(fall)[:22]:22s}"
              f" [pcond clips from frame {k}]  {'ok' if ok else ('FAIL' if stage == 'linear' else 'defect (reported)')}")
        if not ok and stage == "linear":
            fails.append(f"{name}/{stage}")
        np.savetxt(f"{out}/{MODE}_{name.replace(' ', '_')}_{stage}.txt", np.c_[L, h, ch, Y, YA, clipped],
                   header="L_cdm2 hue_uv_deg chroma_uv Y_stage Y_pcond_as_shipped pcond_clipped", fmt="%.6g")
if fails:
    sys.exit(f"CONTINUITY SWEEP ({MODE}) FAILED: " + ", ".join(fails))
print("PASS")
