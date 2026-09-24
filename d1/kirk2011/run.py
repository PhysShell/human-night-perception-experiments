#!/usr/bin/env python3
"""Run the Kirk & O'Brien 2011 GIMP plug-in core (Y. J. Lee 2012, built by setup.sh) on the frozen D0 inputs.

    d1/kirk2011/setup.sh
    tracks/temporal-glare-2009/py.sh d1/kirk2011/run.py

Configs (input-contract.md):
  NATIVE_DEFAULT            the plug-in as GIMP runs it: an 8-bit RGB image x exposure 64, all defaults, full
                            pipeline (core -> Durand/Paris bilateral 50.0 -> reduceRange + blend with the 8-bit
                            source). ADAPTED: the 8-bit image is made from the absolute EXR by the fixed
                            viewing aid (key 0.18 of the input, clip, sRGB OETF, 8 bit), because the plug-in only
                            accepts 8-bit display images.
  DOCUMENTED_TARGET_CONFIG  float absolute input, scale s so that the plug-in's L+M response of a D65 white of
                            Y cd/m^2 equals the photopic retinal illuminance in trolands through a fixed 7 mm pupil
                            (the unit of the 0.33 gain constant in Cao et al. 2008 / Miyahara et al. 1993). ADAPTED
                            (units + pupil are ours; the paper leaves exposure free). Core only (up to lms2display).
  SENSITIVITY_RUN           S1 at DOCUMENTED_TARGET_CONFIG x 10^k, k = 0, 2, 4, 6.
Outputs: .cache/out/<config>/<scene>.exr (linear float; the core's RGB is the plug-in's monitor RGB, written as
Rec.709 without conversion), <scene>_blend.exr, NATIVE also <scene>_final.png / <scene>_input8.png; runs.json.
"""
import json, os, subprocess, sys, hashlib
import numpy as np
import OpenImageIO as oiio

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
C = os.path.join(HERE, ".cache")
DRIVER = os.path.join(C, "build/kirk_driver")
FREDO = os.path.join(C, "src/LOWLIGHT_LINUX/FredoToneMap")
INP = os.path.join(REPO, "d0/work/inputs")
SCENES = ["S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"]
W709 = np.array([0.2126, 0.7152, 0.0722])

# plug-in HDRToLMSR matrix rows L and M (src/hdrToLMSR.cc): L+M response per unit of linear RGB white
H_L = np.array([0.000167179131, 0.021378405283, -0.000600300420])
H_M = np.array([0.000037285102, 0.017335413184, -0.000607142696])
LM_WHITE = float(H_L.sum() + H_M.sum())
PUPIL_MM = 7.0
TD_PER_CDM2 = np.pi * (PUPIL_MM / 2) ** 2           # trolands per cd/m^2 through a 7 mm pupil
S_TARGET = TD_PER_CDM2 / LM_WHITE                   # driver scale: q_L + q_M (white) = Td


def read_exr(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float32)


def write_exr(p, a):
    a = np.ascontiguousarray(a, dtype=np.float32)
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], a.shape[2] if a.ndim == 3 else 1, oiio.FLOAT)
    o = oiio.ImageOutput.create(p); o.open(p, spec); o.write_image(a); o.close()


def srgb_oetf(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def srgb_eotf(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def viewing_aid_scale(rgb):
    """fixed viewing aid: exposure k so that the log-average luminance of THIS input maps to 0.18"""
    Y = rgb @ W709
    return 0.18 / float(np.exp(np.mean(np.log(Y + 1e-9))))


def to_8bit(rgb, k):
    return np.round(srgb_oetf(rgb * k) * 255).astype(np.uint8)


def run_driver(mode, raw, w, h, scale, prefix):
    # the donor hard-codes /tmp paths; give it a private /tmp = .cache/tmp (mount namespace)
    tmp = os.path.join(C, "tmp"); os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, PATH=FREDO + ":" + os.environ.get("PATH", ""))
    cmd = f'mount --bind "{tmp}" /tmp && exec "{DRIVER}" {mode} "{raw}" {w} {h} {scale!r} "{prefix}"'
    r = subprocess.run(["unshare", "-m", "sh", "-c", cmd], env=env, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"driver failed: {r.stdout}\n{r.stderr}")
    return r.stdout


def main():
    runs = []
    work = os.path.join(C, "work"); os.makedirs(work, exist_ok=True)
    jobs = []
    for s in SCENES:
        jobs.append(("NATIVE_DEFAULT", s, s, 1.0))
        jobs.append(("DOCUMENTED_TARGET_CONFIG", s, s, 1.0))
    for k in (0, 2, 4, 6):
        jobs.append(("SENSITIVITY_RUN", "S1", f"S1_x1e{k}", 10.0 ** k))
    for cfg, scene, name, mult in jobs:
        out = os.path.join(C, "out", cfg); os.makedirs(out, exist_ok=True)
        rgb = read_exr(os.path.join(INP, scene + ".exr")) * np.float32(mult)
        h, w = rgb.shape[:2]
        pre = os.path.join(work, f"{cfg}_{name}")
        rec = dict(config=cfg, scene=scene, name=name, level_multiplier=mult, width=w, height=h)
        if cfg == "NATIVE_DEFAULT":
            k = viewing_aid_scale(rgb); img8 = to_8bit(rgb, k)
            raw = pre + "_in.u8"; img8.tofile(raw)
            log = run_driver("native8", raw, w, h, 64.0, pre)
            fin = oiio.ImageBuf(pre + "_final.png").get_pixels(oiio.UINT8)[..., :3]
            oiio.ImageBuf(img8).write(os.path.join(out, name + "_input8.png"))
            os.replace(pre + "_final.png", os.path.join(out, name + "_final.png"))
            write_exr(os.path.join(out, name + ".exr"), srgb_eotf(fin / 255.0))            # final, decoded sRGB
            write_exr(os.path.join(out, name + "_input8_linear.exr"), srgb_eotf(img8 / 255.0))
            rec.update(stage_exr="final (reduceRange output, 8-bit sRGB-encoded, decoded to linear)",
                       exposure=64.0, input8_viewing_aid_k=k,
                       input_meaning="8-bit sRGB codes of the viewing-aid encoding (key 0.18 of input); "
                                     "the plug-in multiplies raw codes by 64")
        else:
            raw = pre + "_in.f32"; rgb.astype(np.float32).tofile(raw)
            log = run_driver("float", raw, w, h, S_TARGET, pre)
            rec.update(stage_exr="core (lms2display output, linear, plug-in monitor RGB)", scale=S_TARGET,
                       scale_rule=f"q_L+q_M(D65 white, Y=1 cd/m^2) = {TD_PER_CDM2:.3f} Td (pupil {PUPIL_MM} mm)",
                       input_meaning="absolute linear Rec.709 cd/m^2 x scale -> plug-in HDR units")
        core = np.fromfile(pre + "_core.f32", np.float32).reshape(h, w, 3)
        blend = np.fromfile(pre + "_blend.f32", np.float32).reshape(h, w)
        write_exr(os.path.join(out, name + ("_core.exr" if cfg == "NATIVE_DEFAULT" else ".exr")), core)
        write_exr(os.path.join(out, name + "_blend.exr"), blend[..., None])
        for f in os.listdir(work):
            if f.startswith(f"{cfg}_{name}_"):
                os.remove(os.path.join(work, f))
        rec["blend_median"] = float(np.median(blend)); rec["blend_mean"] = float(blend.mean())
        rec["driver_log_tail"] = log.strip().splitlines()[-1]
        runs.append(rec); print(cfg, name, "blend mean %.3f" % rec["blend_mean"], flush=True)
    meta = dict(donor="Kirk & O'Brien 2011 via Y. J. Lee GIMP plug-in (LOWLIGHT_LINUX.zip)",
                zip_sha256=hashlib.sha256(open(os.path.join(C, "LOWLIGHT_LINUX.zip"), "rb").read()).hexdigest(),
                driver="d1/kirk2011/driver.cpp", plugin_defaults=dict(exposure=64.0, kappa1=.33, kappa2=.5,
                rho1=.8, rho2=.139, rho3=.4, rho4=.6, alpha=.6189, y=15.0, z=.24, redGreenVal=0, blueYellowVal=0,
                luminanceVal=0, durand_contrast=50.0), target_scale=S_TARGET, LM_white_per_unit_rgb=LM_WHITE,
                runs=runs)
    json.dump(meta, open(os.path.join(HERE, "runs.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
