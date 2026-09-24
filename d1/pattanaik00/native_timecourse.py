#!/usr/bin/env python3
"""NATIVE EXAMPLE for pfstmo_pattanaik00 -t: the paper's adaptation experiments as stimulus sequences.

Pattanaik et al. 2000 describe (sec. 2, Fig. 2/3; sec. 5): dark adaptation is slow (pigment regeneration, tau_cone 110 s,
tau_rod 400 s, rods take tens of minutes), light adaptation is fast (neural t0_cone 80 ms, t0_rod 150 ms, bleaching by
the new light); title-page example: moonlight (A = 0.01 cd/m^2) -> sudden 1000 cd/m^2 at T = 30 ms: next frame almost
entirely white, colourful daylight restored over the following frames; tunnel: slower adjustment entering than leaving.

Stimulus: 64x16 uniform neutral (D65, R=G=B) field at the background level L(t) with four 4x4 test patches at
0.1, 0.3, 3, 10 x L (they carry < 7 % of the pixels, so the log-average goal is ~ L). Frames are generated as pfs
frames directly (pfs matrix) and streamed through ONE `pfstmo_pattanaik00 -t --fps F -v` process. Recorded per frame:
tool output luminance (relative display value, 1.0 = the tool's display white 125 cd/m^2) of background and patches,
and the tool's own adaptation state (A_cone, A_rod, B_cone, B_rod) from --verbose.
  nix develop -c python3 d1/pattanaik00/native_timecourse.py
-> d1/pattanaik00/native_timecourse.json ; plot: tracks/temporal-glare-2009/py.sh d1/pattanaik00/plot_timecourse.py
"""
import json, os, subprocess, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, TMP, pfs_bytes_rgb, run_stream, parse_state, read_pfs_frame, PFS_RGB2XYZ

H, W = 16, 64
PATCHES = {"x0.1": (slice(2, 6), slice(4, 8), 0.1), "x0.3": (slice(2, 6), slice(20, 24), 0.3),
           "x3": (slice(10, 14), slice(36, 40), 3.0), "x10": (slice(10, 14), slice(52, 56), 10.0)}
BG = np.ones((H, W), bool)
for r, c, _ in PATCHES.values():
    BG[r, c] = False


def field(L):
    a = np.full((H, W), L, np.float32)
    for r, c, k in PATCHES.values():
        a[r, c] = L * k
    return np.repeat(a[..., None], 3, -1)


def check_writer():
    """our pfs writer == pfsinpfm channel data (same matrix, same rows)"""
    import OpenImageIO as oiio
    a = field(3.7); a[0, :, 0] *= 2                      # asymmetric rows/channels
    pfm = f"{TMP}/chk.pfm"
    spec = oiio.ImageSpec(W, H, 3, oiio.FLOAT); b = oiio.ImageBuf(spec)
    b.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), a); b.write(pfm)
    import io
    ref = read_pfs_frame(io.BytesIO(subprocess.run(["pfsinpfm", pfm], stdout=subprocess.PIPE, check=True).stdout))[1]
    mine = read_pfs_frame(io.BytesIO(pfs_bytes_rgb(a)))[1]
    os.remove(pfm)
    return float(max(np.abs(ref[k] - mine[k]).max() for k in "XYZ"))


def schedule(segments, fps):
    """segments: [(level cd/m^2, seconds)] -> per-frame levels"""
    lv = []
    for L, s in segments:
        lv += [L] * int(round(s * fps))
    return lv


def keep_index(levels, fps):
    """frames stored in the json: every frame for 3 s after each level change, then 1 per second (+ last)"""
    keep, last_change = set(), 0
    for i, L in enumerate(levels):
        if i and L != levels[i - 1]:
            last_change = i
        if i - last_change < 3 * fps or (i - last_change) % int(round(fps)) == 0 or i == len(levels) - 1:
            keep.add(i)
    return keep


def run(name, segments, fps, extra=(), label="NATIVE_EXAMPLE"):
    levels = schedule(segments, fps)
    cache = {}

    def gen():
        for L in levels:
            if L not in cache:
                cache[L] = pfs_bytes_rgb(field(L))
            yield cache[L]
    keep = keep_index(levels, fps)
    rec = {k: [] for k in ["frame", "t_s", "L_bg", "out_bg"] + [f"out_{p}" for p in PATCHES]}
    nonfinite = [0]

    def on_frame(i, tags, ch):
        Y = ch["Y"]
        nonfinite[0] += int((~np.isfinite(Y)).sum())
        if i not in keep:
            return
        rec["frame"].append(i); rec["t_s"].append(i / fps); rec["L_bg"].append(levels[i])
        rec["out_bg"].append(float(Y[BG].mean()))
        for p, (r, c, _) in PATCHES.items():
            rec[f"out_{p}"].append(float(Y[r, c].mean()))
    cmd = ["pfstmo_pattanaik00", "-v", "-t", "--fps", f"{fps:g}"] + list(extra)
    t0 = time.time()
    log = run_stream(cmd, gen(), on_frame, f"{TMP}/tc_{name}.log")
    st = parse_state(log)
    assert len(st) == len(levels), (len(st), len(levels))
    for k in ["Acone", "Arod", "Bcone", "Brod"]:
        rec[k] = [st[i][k] for i in rec["frame"]]
    # static (no -t) reference: what the tool shows for each level held forever (its own steady state, 5 x logavg)
    static = {}
    for L in sorted(set(levels)):
        o = []
        run_stream(["pfstmo_pattanaik00"], iter([pfs_bytes_rgb(field(L))]), lambda i, t, ch: o.append(float(ch["Y"][BG].mean())),
                   f"{TMP}/tc_static.log")
        static[f"{L:g}"] = o[0]
    print(f"[timecourse] {name}: {len(levels)} frames {time.time() - t0:.1f}s nonfinite={nonfinite[0]}", flush=True)
    return {"name": name, "label": label, "fps": fps, "segments_cd_m2_s": segments, "command": " ".join(cmd) +
            "  (stdin: synthetic pfs frames 64x16; stdout parsed)", "frames": len(levels), "nonfinite_output_values": nonfinite[0],
            "static_no_t_output_bg": static, "series": rec}


def step_stats(r, t_step, direction):
    """time after a step until out_bg has covered 63 % / 95 % of its change in log10 (from the frame before the step
    to the value at the end of the segment)."""
    t = np.array(r["series"]["t_s"]); y = np.log10(np.maximum(r["series"]["out_bg"], 1e-7))
    i0 = int(np.searchsorted(t, t_step)) - 1
    seg_end = t_step + [s for _, s in r["segments_cd_m2_s"]][[round(sum(s for _, s in r["segments_cd_m2_s"][:k]), 6) for k in
                                                              range(len(r["segments_cd_m2_s"]))].index(round(t_step, 6))]
    i1 = int(np.searchsorted(t, seg_end)) - 1
    ya = y[i0 + 1:i1 + 1]; ta = t[i0 + 1:i1 + 1] - t_step
    res = {"out_before": float(10 ** y[i0]), "out_first_frame_after": float(10 ** ya[0]), "out_end_of_segment": float(10 ** ya[-1]),
           "out_extreme": float(10 ** (ya.min() if direction == "down" else ya.max()))}
    # timing of the recovery from the first-frame extreme to the end value
    ext = int(np.argmin(ya) if direction == "down" else np.argmax(ya))
    d = ya[-1] - ya[ext]
    for q in (0.63, 0.95):
        idx = np.where((ya[ext:] - ya[ext]) / d >= q)[0] if abs(d) > 1e-9 else []
        res[f"t_recover_{int(q * 100)}pct_s"] = float(ta[ext + idx[0]]) if len(idx) else None
    return res


if __name__ == "__main__":
    os.chdir(os.path.join(HERE, "..", ".."))
    out = {"what": __doc__, "writer_check_max_abs_diff_vs_pfsinpfm": check_writer(), "runs": []}
    DARK_S = 1800
    runs = [
        ("A_1000_to_0.01_fps24", [(1000, 30), (0.01, DARK_S), (1000, 30)], 24, ["-c", "1000"]),
        ("B_1000_to_0.01_fps60", [(1000, 30), (0.01, DARK_S), (1000, 30)], 60, ["-c", "1000"]),
        ("C_100_to_0.01_fps24", [(100, 30), (0.01, DARK_S), (100, 30)], 24, ["-c", "100"]),
        ("D_title_page_0.01_to_1000_T30ms", [(0.01, 1), (1000, 10)], 1 / 0.030, ["-c", "0.01"]),
        ("E_static_0.01_no_init_fps24", [(0.01, 10)], 24, []),
    ]
    for name, seg, fps, extra in runs:
        r = run(name, seg, fps, extra)
        if name[0] in "ABC":
            r["dark_step"] = step_stats(r, 30, "down"); r["light_step"] = step_stats(r, 30 + DARK_S, "up")
        if name[0] == "D":
            r["light_step"] = step_stats(r, 1, "up")
        out["runs"].append(r)
    json.dump(out, open(f"{HERE}/native_timecourse.json", "w"), indent=0)
    for r in out["runs"]:
        print(r["name"], {k: r[k] for k in ("dark_step", "light_step", "static_no_t_output_bg") if k in r})
