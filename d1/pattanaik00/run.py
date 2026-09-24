#!/usr/bin/env python3
"""D1-A donor pfstmo_pattanaik00 (pfstools 2.2.0), run NATIVELY on the frozen D0 inputs. Input contract:
d1/pattanaik00/input-contract.md. Nothing here tone-maps; the pfstools binary does. This file converts, streams,
parses and encodes (d0 output contract: 16-bit PNG code values).

configs (label):
  native_default      NATIVE_DEFAULT          `pfstmo_pattanaik00 | pfsgamma -g 2.2` (the man page pipeline), code values
                                              written as is and decoded as SDR100 (nearest scenario; sRGB vs 2.2)
  target              DOCUMENTED_TARGET_CONFIG  absolute cd/m^2 in (tool default -m 1), tool is display-unaware (display
                                              observer hard-coded: adaptation 25, white 125, black 3.9 cd/m^2): output
                                              is display-relative linear -> SDR100 sRGB OETF, BRIGHT500 ^(1/2.2)
  sens_abs125         SENSITIVITY_RUN         same tool output read as ABSOLUTE: 1.0 = the tool's internal display white
                                              125 cd/m^2 -> emitted on the scenario (clipped at its peak)
  sens_local          SENSITIVITY_RUN         --local (SCCG 2002 local adaptation), relative encoding as target
  target_floor        ADAPTED                 S3 only: pixels with RGB == 0 (the bar) set to 1e-6 cd/m^2 neutral, because
                                              Y = 0 gives 0/0 = NaN in the tool, which its clamp turns into white
  sens_ladder_x1eK    SENSITIVITY_RUN         S1 with the tool's own -m 10^K, K = 0,2,4,6, relative encoding
  clip_t24            DOCUMENTED_TARGET_CONFIG  S2, -t --fps 24 (the tool accepts any fps>0: 24 is exact), frames written SDR100
  clip_static         NATIVE_DEFAULT          S2 without -t (each frame independently adapted), stats only
  clip_hist100        SENSITIVITY_RUN         2 s (48 frames) uniform neutral 100 cd/m^2 then S2, -t --fps 24, stats only
  clip_hist100_long   SENSITIVITY_RUN, ADAPTED  2 s at 100 cd/m^2 then S1 held for 600 s, -t --fps 24, S1 4x4 box-
                                              downsampled (480x205) to keep runtime; stats only
  nix develop -c python3 d1/pattanaik00/run.py [stills|ladder|clips|long|all]
"""
import json, os, sys, time
import numpy as np
import OpenImageIO as oiio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HERE, OUT, INP, TMP, TOOL_DISPLAY_WHITE, srgb_oetf, g22, pfs_bytes_exr, pfs_bytes_rgb, run_stream,
                    parse_state, xyz_to_rgb, write_png16, tool_version)

SCEN = json.load(open(os.path.join(HERE, "..", "..", "d0", "display-scenarios.json")))
STILLS = ["S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"]
S2 = [f"{INP}/S2/frame_{i:04d}.exr" for i in range(1, 49)]
Yw = np.array([0.2126, 0.7152, 0.0722])
RUNS = []


def enc_rel(rgb, lum):
    return srgb_oetf(rgb) if SCEN["luminance"][lum]["transfer"] == "srgb" else g22(rgb)


def enc_abs(rgb, lum):
    s = SCEN["luminance"][lum]; pk, bk = s["peak_cd_m2"], s["black_cd_m2"]
    v = np.clip((TOOL_DISPLAY_WHITE * rgb - bk) / (pk - bk), 0, 1)
    return srgb_oetf(v) if s["transfer"] == "srgb" else g22(v)


def emitted_rel(Irel, lum):
    """analytic display model for per-frame stats: relative linear I (clipped) -> emitted cd/m^2 (same as d0 decode)"""
    s = SCEN["luminance"][lum]
    return s["black_cd_m2"] + (s["peak_cd_m2"] - s["black_cd_m2"]) * np.clip(Irel, 0, 1)


def diag(rgb, ref_Y):
    """failure diagnostics: non-finite values; 'white from NaN' = a channel at the clamp 1.0 where the input pixel is
    below the scene median (the tool's clamp maps NaN -> 1.0)"""
    white = (rgb >= 0.9999).any(-1)
    return {"nonfinite_values": int((~np.isfinite(rgb)).sum()), "channel_at_1_pct": float(100 * white.mean()),
            "channel_at_1_but_input_below_median_px": int((white & (ref_Y < np.median(ref_Y))).sum())}


def still(scene, config, label, extra=(), encs=(("SDR100", enc_rel), ("BRIGHT500", enc_rel)), floor=None, pipe=None, note=""):
    exr = f"{INP}/{scene}.exr"
    ref_Y = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[..., :3] @ Yw
    cmd = ["pfstmo_pattanaik00", "-v"] + list(extra)
    rec = {}

    def on_frame(i, tags, ch):
        rgb = xyz_to_rgb(ch).astype(np.float64)
        rec.update(diag(rgb, ref_Y)); rec["out_tags"] = tags
        rgb = np.nan_to_num(rgb, nan=0.0)
        rec["out_rel_Y_median"] = float(np.median(rgb @ Yw))
        for lum, f in encs:
            write_png16(f"{OUT}/{config}/{scene}__PHONE_{lum}_DARK.png", f(rgb, lum) if pipe is None else np.clip(rgb, 0, 1))
    t0 = time.time()
    log = run_stream(cmd, iter([pfs_bytes_exr(exr, floor)]), on_frame, f"{TMP}/log_{config}_{scene}.txt", pipe_after=pipe)
    st = parse_state(log)
    for lum, f in encs:
        RUNS.append({"config": config, "label": label, "scene": scene, "luminance": lum, "ambient": "DARK", "geometry": "PHONE",
                     "command": " ".join(cmd) + (" | " + " ".join(pipe) if pipe else "") +
                     "  (stdin: oiiotool EXR->PFM | pfsinpfm" + (f"; ADAPTED floor {floor:g} cd/m^2 on RGB==0 pixels, pfs written directly" if floor else "") + "; stdout parsed)",
                     "encoding": ("code = tool|pfsgamma -g 2.2 output as is" if pipe else f.__name__ + " " + SCEN["luminance"][lum]["transfer"]),
                     "note": note, "state": st[0] if st else "local: not printed (adaptation state unused, see audit)", **rec,
                     "output": f"{OUT}/{config}/{scene}__PHONE_{lum}_DARK.png", "seconds": round(time.time() - t0, 1)})
    print(f"[{config}] {scene} {time.time() - t0:.1f}s {rec.get('nonfinite_values')} white<med={rec.get('channel_at_1_but_input_below_median_px')}", flush=True)


def run_stills():
    for sc in STILLS:
        still(sc, "native_default", "NATIVE_DEFAULT", encs=(("SDR100", None),), pipe=["pfsgamma", "-g", "2.2"],
              note="man-page pipeline; gamma-2.2 code values decoded by d0 as SDR100 (sRGB): nearest scenario, not the tool's display")
        still(sc, "target", "DOCUMENTED_TARGET_CONFIG", note="display-unaware tool: relative output, scenario encoding only")
        still(sc, "sens_abs125", "SENSITIVITY_RUN", encs=(("SDR100", enc_abs), ("BRIGHT500", enc_abs)),
              note="tool output x 125 cd/m^2 (its hard-coded display white) emitted absolutely, clipped at the scenario peak")
        still(sc, "sens_local", "SENSITIVITY_RUN", extra=["--local"])
    for sc in ["S3_bar", "S3_nobar", "S5"]:
        still(sc, "target_floor", "DOCUMENTED_TARGET_CONFIG+ADAPTED", floor=1e-6,
              note="ADAPTED: RGB==0 pixels (S3_bar bar, 2398 px) set to 1e-6 cd/m^2 neutral; every channel floored at 1e-4 x Y "
                   "(S5: 80846 px with R = 0, 93 with B = 0); S3_nobar has no such pixels (input unchanged)")
        if sc != "S5":
            still(sc, "sens_local_floor", "SENSITIVITY_RUN+ADAPTED", extra=["--local"], floor=1e-6, note="--local on the floored input")


def run_ladder():
    for k in (0, 2, 4, 6):
        still("S1", f"sens_ladder_x1e{k}", "SENSITIVITY_RUN", extra=["-m", f"1e{k}"], encs=(("SDR100", enc_rel),),
              note=f"tool's own --mul 1e{k}: absolute level x 10^{k}")


def masks(name):
    m = dict(np.load(f"{INP}/masks/{name}.npz"))
    return m


def run_clip(config, label, extra, frames_iter_fn, n, write_lum=None, masks_fn=None, keep=lambda i: True, note=""):
    m = masks("S2"); sky = m["sky"]; lamp = m["lamp_any"]
    ser = {k: [] for k in ["frame", "t_s", "sky_median_SDR100", "sky_median_BRIGHT500", "mean_SDR100", "dark_median_SDR100",
                           "lamp_p99_SDR100", "out_rel_sky_median"]}
    nonfin = [0]; wr = [0]

    def on_frame(i, tags, ch):
        if not keep(i):
            return
        rgb = xyz_to_rgb(ch).astype(np.float64)
        nonfin[0] += int((~np.isfinite(rgb)).sum()); rgb = np.nan_to_num(rgb, nan=0.0)
        Irel = rgb @ Yw
        sk, lp = (sky, lamp) if masks_fn is None else masks_fn(i, Irel.shape)
        if sk is None:                                   # uniform history frame
            sk = np.ones(Irel.shape, bool); lp = np.zeros(Irel.shape, bool)
        ser["frame"].append(i); ser["t_s"].append(i / 24)
        ser["out_rel_sky_median"].append(float(np.median(Irel[sk])))
        for lum in ("SDR100", "BRIGHT500"):
            ser[f"sky_median_{lum}"].append(float(np.median(emitted_rel(Irel[sk], lum))))
        E = emitted_rel(Irel, "SDR100")
        ser["mean_SDR100"].append(float(E.mean())); ser["dark_median_SDR100"].append(float(np.median(E[~lp])))
        ser["lamp_p99_SDR100"].append(float(np.percentile(E[lp], 99)) if lp.any() else None)
        if write_lum:
            write_png16(f"{OUT}/{config}/S2__PHONE_{write_lum}_DARK/frame_{i + 1:04d}.png", enc_rel(rgb, write_lum)); wr[0] += 1
    cmd = ["pfstmo_pattanaik00", "-v"] + list(extra)
    t0 = time.time()
    log = run_stream(cmd, frames_iter_fn(), on_frame, f"{TMP}/log_{config}.txt")
    st = parse_state(log)
    for k in ("Acone", "Arod", "Bcone", "Brod"):
        ser[k] = [st[i][k] for i in ser["frame"]] if len(st) == n else None
    RUNS.append({"config": config, "label": label, "scene": "S2", "luminance": "SDR100,BRIGHT500 (stats)", "ambient": "DARK",
                 "geometry": "PHONE", "command": " ".join(cmd) + "  (stdin: one pfs stream; stdout parsed)", "frames": n,
                 "frames_written": wr[0], "nonfinite_values": nonfin[0], "note": note,
                 "output": f"{OUT}/{config}/S2__PHONE_{write_lum}_DARK/" if write_lum else None,
                 "per_frame": ser, "seconds": round(time.time() - t0, 1)})
    print(f"[{config}] {n} frames {time.time() - t0:.1f}s nonfinite={nonfin[0]}", flush=True)


def run_clips():
    gen = lambda: (pfs_bytes_exr(e) for e in S2)
    run_clip("clip_t24", "DOCUMENTED_TARGET_CONFIG", ["-t", "--fps", "24"], gen, 48, write_lum="SDR100",
             note="fps 24 exact (tool accepts any fps > 0); frame 0 initialised to the static state (A = 5 x logavg)")
    run_clip("clip_static", "NATIVE_DEFAULT", [], gen, 48, note="no -t: every frame independently at the static state")
    uni = pfs_bytes_rgb(np.full((820, 1920, 3), 100.0, np.float32))
    genh = lambda: (uni if i < 48 else pfs_bytes_exr(S2[i - 48]) for i in range(96))
    m = masks("S2")
    run_clip("clip_hist100", "SENSITIVITY_RUN", ["-t", "--fps", "24"], genh, 96,
             masks_fn=lambda i, shp: (None, None) if i < 48 else (m["sky"], m["lamp_any"]),
             note="frames 0-47: uniform neutral 100 cd/m^2 (a lit house); frames 48-95: S2 frames 1-48")


def run_long():
    a = oiio.ImageBuf(f"{INP}/S1.exr").get_pixels(oiio.FLOAT)[..., :3]
    h, w = a.shape[0] // 4 * 4, a.shape[1] // 4 * 4
    small = a[:h, :w].reshape(h // 4, 4, w // 4, 4, 3).mean((1, 3)).astype(np.float32)
    m = masks("S1") if os.path.exists(f"{INP}/masks/S1.npz") else masks("S2")
    ds = lambda k: m[k][:h, :w].reshape(h // 4, 4, w // 4, 4).mean((1, 3)) > 0.5
    lampk = "lamp_any" if "lamp_any" in m else "lamp"
    sky_s, lamp_s = ds("sky"), m[lampk][:h, :w].reshape(h // 4, 4, w // 4, 4).any((1, 3))
    uni = pfs_bytes_rgb(np.full(small.shape, 100.0, np.float32)); s1 = pfs_bytes_rgb(small)
    N = 48 + 600 * 24
    keep = lambda i: i < 48 + 24 * 5 or i % 12 == 0 or i == N - 1
    la = lambda A: float(np.exp(np.mean(np.log(A + 1e-4))) - 1e-4)
    run_clip("clip_hist100_long", "SENSITIVITY_RUN", ["-t", "--fps", "24"], lambda: (uni if i < 48 else s1 for i in range(N)), N,
             masks_fn=lambda i, shp: (None, None) if i < 48 else (sky_s, lamp_s), keep=keep,
             note=f"ADAPTED resolution: S1 4x4 box-downsampled to {w // 4}x{h // 4}; tool log-average of the full S1 "
                  f"{la(a @ Yw):.4g} vs downsampled {la(small @ Yw):.4g} cd/m^2; 2 s neutral 100 cd/m^2 then S1 held 600 s")


def save():
    p = f"{HERE}/runs.json"
    old = json.load(open(p))["runs"] if os.path.exists(p) else []
    keys = {(r["config"], r["scene"], r["luminance"]) for r in RUNS}
    runs = [r for r in old if (r["config"], r["scene"], r["luminance"]) not in keys] + RUNS
    json.dump({"tool": tool_version(), "input": "d0/work/inputs: linear Rec.709/D65 float EXR, Y absolute cd/m^2, passed UNSCALED "
               "(input-contract.md)", "input_path": "oiiotool <exr> --ch R,G,B -d float -o x.pfm; pfsinpfm x.pfm | pfstmo_pattanaik00",
               "output_contract": "16-bit PNG code values under d1/pattanaik00/.cache/out/<config>/<scene>__PHONE_<LUM>_DARK.png; "
               "SDR100 sRGB piecewise, BRIGHT500 display-relative ^(1/2.2)", "runs": runs}, open(p, "w"), indent=1)


if __name__ == "__main__":
    os.chdir(os.path.join(HERE, "..", ".."))
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "floor":
        RUNS.clear()
        for sc in ["S3_bar", "S3_nobar", "S5"]:
            still(sc, "target_floor", "DOCUMENTED_TARGET_CONFIG+ADAPTED", floor=1e-6, note="ADAPTED: RGB==0 pixels set to 1e-6 cd/m^2 neutral; every channel floored at 1e-4 x Y (S5: 80846 px R = 0, 93 B = 0); S3_nobar unchanged")
            if sc != "S5":
                still(sc, "sens_local_floor", "SENSITIVITY_RUN+ADAPTED", extra=["--local"], floor=1e-6, note="--local on the floored input")
        save()
    if what in ("stills", "all"):
        run_stills(); save(); RUNS.clear()
    if what in ("ladder", "all"):
        run_ladder(); save(); RUNS.clear()
    if what in ("clips", "all"):
        run_clips(); save(); RUNS.clear()
    if what in ("long", "all"):
        run_long(); save(); RUNS.clear()
