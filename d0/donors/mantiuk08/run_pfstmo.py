#!/usr/bin/env python3
"""D0 donors B (pfstmo_mantiuk08, Mantiuk/Daly/Kerofsky 2008) and D2 control (pfstmo_reinhard02), run NATIVELY.

Nothing here tone-maps: the pfstools binaries do. This file only
  (1) converts our frozen inputs (linear Rec.709/D65 float EXR, absolute cd/m^2) to PFM with oiiotool and hands them to
      pfstools' own reader pfsinpfm (no scaling, no WHITE_Y tag; pfsinpfm tags LUMINANCE=RELATIVE, which
      pfstmo_mantiuk08 ignores - see d0/input-contracts/mantiuk08.md),
  (2) streams all frames of a clip through ONE pfstmo process (so the tool's temporal tone-curve filter sees them),
  (3) parses the pfs stream the tool writes (X,Y,Z float channels, pfs' own RGB<->XYZ matrix), and
  (4) writes 16-bit PNG code values in the scenario encoding (d0/display-scenarios.json):
        mantiuk08 SDR*: the tool's output IS the pixel value of the display function we gave it -> written as is.
        mantiuk08 HDR1000: the LUT display function is indexed by p = V_PQ / V_PQ(1000); we convert p back to the PQ
                           signal of the Rec.709 channel, re-express it in Rec.2020 primaries, PQ-encode (ENCODING only).
        reinhard02: display-relative linear -> clamp [0,1] -> sRGB OETF (SDR100) or ^(1/2.2) (SDR200, BRIGHT500).
Frames are processed one at a time (peak RAM ~ a few frames of 1920x820 float).
  nix develop -c python3 d0/donors/mantiuk08/run_pfstmo.py [native|mantiuk08|reinhard02|all] [--only CONFIG]
"""
import json, os, shutil, subprocess, sys, threading, time
import numpy as np
import OpenImageIO as oiio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.chdir(ROOT)
TMP = "d0/work/mantiuk08_tmp"
INP = "d0/work/inputs"
OUT = "d0/work/out"
CURVES = "d0/results/curves/mantiuk08"
LUTDIR = "d0/donors/mantiuk08/luts"
SCEN = json.load(open("d0/display-scenarios.json"))
MAN = json.load(open(f"{INP}/manifest.json"))
os.makedirs(TMP, exist_ok=True)

# pfs' own colour matrices (src/pfs/colorspace.cpp, pfstools 2.2.0), used by pfsinpfm/pfsoutpfm
PFS_RGB2XYZ = np.array([[0.412424, 0.357579, 0.180464], [0.212656, 0.715158, 0.072186], [0.019332, 0.119193, 0.950444]], np.float32)
PFS_XYZ2RGB = np.array([[3.240708, -1.537259, -0.498570], [-0.969257, 1.875995, 0.041555], [0.055636, -0.203996, 1.057069]], np.float32)
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M2020 = np.array([[0.6369580, 0.1446169, 0.1688810], [0.2627002, 0.6779981, 0.0593017], [0.0000000, 0.0280727, 1.0609851]])
M709_TO_2020 = np.linalg.inv(M2020) @ M709
GEOM = {"PHONE": "ppd=73:d=0.3", "DESKTOP": "ppd=48.4:d=0.6"}      # -s spec; see contract: ignored by 2.2.0 (finding)
STILLS = ["S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"]
S2_FRAMES = [f"{INP}/S2/frame_{i:04d}.exr" for i in range(1, 49)]
# Which S2 clips get their 48 PNG frames WRITTEN (the tool always runs on all frames and tone curves are always
# saved). A full-resolution 16-bit frame is ~7 MB, so one clip is ~350 MB: D0_WRITE_S2="all" (default, full
# reproduction), "none", or a comma list of donor:config:LUM, e.g. "mantiuk08:video_whiteauto:SDR100".
WRITE_S2 = os.environ.get("D0_WRITE_S2", "all")


def write_s2(donor, config, lum):
    return WRITE_S2 == "all" or f"{donor}:{config}:{lum}" in WRITE_S2.split(",")


BUILD = os.environ.get("D0_PFSTOOLS_BUILD", "2.2.0")     # "master": d0/donors/mantiuk08/pfstools-master.nix first on PATH


def tool_version():
    exe = shutil.which("pfstmo_mantiuk08")
    if BUILD == "master":
        return {"pfstools": "master c8606912656a3adebaeaddce66cf559bec643e11 (2025-09-20, unreleased 2.2.1)", "binary": os.path.realpath(exe),
                "source": "https://git.code.sf.net/p/pfstools/git", "build": "d0/donors/mantiuk08/pfstools-master.nix"}
    return {"pfstools": "2.2.0", "binary": os.path.realpath(exe),
            "source": "https://downloads.sourceforge.net/project/pfstools/pfstools/2.2.0/pfstools-2.2.0.tgz",
            "source_sha256": "9bf6844985663226c21998eeb43c261acb8e4b3891b9a91b729554406289d7ca",
            "build": "nix/pfstools.nix (repo flake; OpenEXR/ImageMagick/Qt/GL/Matlab/Octave off)"}


# ---------------------------------------------------------------- transfer functions
def srgb_eotf(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def srgb_oetf(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(l, 1 / 2.4) - 0.055)


PQ = dict(m1=0.1593017578125, m2=78.84375, c1=0.8359375, c2=18.8515625, c3=18.6875)


def pq_eotf(v):                                             # code -> cd/m^2
    p = np.power(np.clip(v, 0, 1), 1 / PQ["m2"])
    return 10000 * np.power(np.maximum(p - PQ["c1"], 0) / (PQ["c2"] - PQ["c3"] * p), 1 / PQ["m1"])


def pq_oetf(L):                                             # cd/m^2 -> code
    y = np.power(np.clip(L, 0, 10000) / 10000, PQ["m1"])
    return np.power((PQ["c1"] + PQ["c2"] * y) / (1 + PQ["c3"] * y), PQ["m2"])


V_PQ_1000 = float(pq_oetf(1000.0))


# ---------------------------------------------------------------- display functions (-d) per scenario
def display_function(lum, amb):
    """Return (df_spec for -d, description). SDR100/HDR1000 via LUT file (pixel value -> cd/m^2, incl. reflected
    ambient as the man page asks); SDR200/BRIGHT500 via the tool's own gamma-gain-black-ambient model."""
    s, a = SCEN["luminance"][lum], SCEN["ambient"][amb]
    pk, bk, E, k = s["peak_cd_m2"], s["black_cd_m2"], a["E_ambient_lux"], a["reflectivity"]
    refl = E * k / np.pi
    if s["transfer"] == "gamma2.2":
        return f"g=2.2:l={pk:g}:b={bk:g}:k={k:g}:a={E:g}", f"GGBA L=(l-b)V^2.2+b+k/pi*a, l={pk}, b={bk}, k={k}, a={E} lx"
    os.makedirs(LUTDIR, exist_ok=True)
    p = np.linspace(0, 1, 4001)                            # tool limit: < 4096 rows
    if s["transfer"] == "srgb":
        L = bk + (pk - bk) * srgb_eotf(p) + refl
        what = f"LUT sRGB piecewise: L = {bk} + {pk - bk}*EOTF_sRGB(V) + {refl:.4g}"
    elif s["transfer"] == "pq":
        L = bk + pq_eotf(p * V_PQ_1000) * (pk - bk) / pk + refl
        what = (f"LUT PQ: tool pixel p = V_PQ/{V_PQ_1000:.6f} (V_PQ(1000 cd/m^2)); L = {bk} + PQ(p*{V_PQ_1000:.6f})*"
                f"{(pk - bk) / pk:g} + {refl:.4g}")
    path = f"{LUTDIR}/{lum}_{amb}.csv"
    with open(path, "w") as f:
        for pi_, Li in zip(p, L):
            f.write(f"{pi_:.6f},{Li:.8g}\n")
    return f"lut={path}", what


# ---------------------------------------------------------------- pfs stream I/O
def pfs_bytes(exr):
    """EXR -> PFM (oiiotool, format conversion only) -> pfsinpfm (pfstools' reader) -> pfs stream bytes."""
    pfm = f"{TMP}/in_{os.getpid()}.pfm"
    subprocess.run(["oiiotool", exr, "--ch", "R,G,B", "-d", "float", "-o", pfm], check=True)
    b = subprocess.run(["pfsinpfm", pfm], check=True, stdout=subprocess.PIPE).stdout
    os.remove(pfm)
    return b


def _readline(f):
    s = f.readline()
    if not s:
        raise EOFError
    return s.decode().rstrip("\n")


def read_pfs_frame(f):
    """Parse one frame of a pfs stream (src/pfs/pfs.cpp writeFrame). Returns (tags, {name: HxW float32}) or None."""
    magic = f.read(5)
    if not magic:
        return None
    assert magic == b"PFS1\n", magic
    w, h = map(int, _readline(f).split())
    nch = int(_readline(f))
    tags = dict(_readline(f).split("=", 1) for _ in range(int(_readline(f))))
    names = []
    for _ in range(nch):
        names.append(_readline(f))
        for _ in range(int(_readline(f))):
            _readline(f)
    assert f.read(4) == b"ENDH"
    ch = {}
    for n in names:
        buf = f.read(4 * w * h)
        ch[n] = np.frombuffer(buf, np.float32).reshape(h, w)
    return tags, ch


def xyz_to_pfs_rgb(ch):
    XYZ = np.stack([ch["X"], ch["Y"], ch["Z"]], -1)
    return XYZ @ PFS_XYZ2RGB.T


def write_png16(path, rgb):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    q = np.round(np.clip(rgb, 0, 1) * 65535).astype(np.uint16)
    spec = oiio.ImageSpec(q.shape[1], q.shape[0], 3, oiio.UINT16)
    spec.attribute("png:compressionLevel", 9)
    b = oiio.ImageBuf(spec)
    b.set_pixels(oiio.ROI(0, q.shape[1], 0, q.shape[0], 0, 1, 0, 3), np.ascontiguousarray(q))
    assert b.write(path), b.geterror()


def run_stream(cmd, exrs, on_frame, log_path):
    """Feed all exrs as ONE pfs stream into cmd; call on_frame(i, tags, channels) for each output frame."""
    with open(log_path, "wb") as log:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, bufsize=1 << 20)
        err = []

        def feed():
            try:
                for e in exrs:
                    p.stdin.write(pfs_bytes(e))
                    p.stdin.flush()
            except Exception as ex:                     # noqa: BLE001
                err.append(ex)
            finally:
                p.stdin.close()
        t = threading.Thread(target=feed); t.start()
        i = 0
        while True:
            fr = read_pfs_frame(p.stdout)
            if fr is None:
                break
            on_frame(i, *fr); i += 1
        t.join(); rc = p.wait()
    if rc != 0 or err or i != len(exrs):
        raise RuntimeError(f"{cmd} rc={rc} err={err} frames={i}/{len(exrs)}; see {log_path}")
    return open(log_path, errors="replace").read()


# ---------------------------------------------------------------- mantiuk08
RUNS = {"mantiuk08": [], "reinhard02": []}


def m08(config, label, scene, geom, lum, amb, white_y=None, fps=None, extra=(), default_all=False):
    exrs = S2_FRAMES if scene == "S2" else [f"{INP}/{scene}.exr"]
    tag = f"{scene}__{geom}_{lum}_{amb}"
    if default_all:                                          # NATIVE_DEFAULT: no display, size, white or fps option
        cmd = ["pfstmo_mantiuk08", "-v", "-q"]
        df_what, dfspec, ppd = "tool default -d pd=lcd (g=2.2, l=200, b=0.8, k=0.01, a=60 lx)", "(default pd=lcd)", "(default ppd=30)"
    else:
        dfspec, df_what = display_function(lum, amb)
        ppd = GEOM[geom]
        cmd = ["pfstmo_mantiuk08", "-v", "-q", "-d", dfspec, "-s", ppd]
        if white_y is not None:
            cmd += ["--white-y", f"{white_y:g}"]
        if fps is not None:
            cmd += ["--fps", f"{fps:g}"]
    cmd += list(extra)
    curve = f"{CURVES}/{config}/{tag}.csv"
    os.makedirs(os.path.dirname(curve), exist_ok=True)
    cmd += ["--output-tone-curve", curve]
    outdir = f"{OUT}/mantiuk08/{config}"
    transfer = SCEN["luminance"][lum]["transfer"] if not default_all else "gamma2.2(pd=lcd)"
    written = scene != "S2" or write_s2("mantiuk08", config, lum)

    def on_frame(i, tags, ch):
        if not written:
            return
        p = xyz_to_pfs_rgb(ch)                               # tool's per-channel pixel values for its display function
        if transfer == "pq":
            q709 = pq_eotf(np.clip(p, 0, 1) * V_PQ_1000)     # PQ-domain linear, Rec.709 channels
            code = pq_oetf(np.maximum(q709 @ M709_TO_2020.T, 0))
        else:
            code = p
        path = f"{outdir}/{tag}/frame_{i + 1:04d}.png" if scene == "S2" else f"{outdir}/{tag}.png"
        write_png16(path, code)
    t0 = time.time()
    log = run_stream(cmd, exrs, on_frame, f"{TMP}/log_{config}_{tag}.txt")
    info = [l for l in log.splitlines() if l.strip() and "took" not in l and "completed" not in l]
    note = ("tool defaults: pd=lcd (g=2.2, l=200, b=0.8, k=0.01, a=60 lx), ppd=30; the code values are gamma-2.2 pixel "
            "values of THAT display; decoding them as SDR200_DARK is the nearest scenario, not the tool's own display") if default_all else ""
    RUNS["mantiuk08"].append({"config": config, "label": label, "note": note, "scene": scene, "geometry": geom, "luminance": lum,
                              "ambient": amb, "command": " ".join(cmd) + "  (stdin: pfsinpfm <oiiotool EXR->PFM>; stdout parsed)",
                              "display_function": dfspec, "display_function_what": df_what, "display_size": ppd,
                              "white_y": "auto (none: no option, no WHITE_Y tag)" if white_y is None else white_y,
                              "fps": fps if fps is not None else ("tool default 25 (single frame: filter inactive)" if scene != "S2" else "25 default"),
                              "fps_note": "ADAPTED: S2 is 24 fps; pfstools 2.2.0 accepts only 25/30/60, nearest (25) used" if scene == "S2" else "",
                              "white_y_rule": {None: "", "anchor": "absolute intent: WHITE_Y = scenario display peak (cd/m^2)"}.get(
                                  "anchor" if config.endswith("whiteanchor") else None, "sensitivity value" if white_y is not None else ""),
                              "frames": len(exrs), "frames_written": written, "encoding": transfer, "tone_curve_csv": curve,
                              "output": f"{outdir}/{tag}" + ("/" if scene == "S2" else ".png"),
                              "tool_build": BUILD, "tool_stderr": info[:12], "seconds": round(time.time() - t0, 1)})
    print(f"[mantiuk08] {config} {tag} {time.time() - t0:.1f}s", flush=True)


def anchor_white(lum):
    """ANCHOR (see contract): absolute intent - the scene luminance equal to the display peak is mapped to the peak."""
    return float(SCEN["luminance"][lum]["peak_cd_m2"])


WHITE_SWEEP = [4e-4, 4e-3, 4e-2, 4e-1, 4.0]


def run_mantiuk08(only=None):
    def want(c):
        return only is None or c == only or (only.endswith("*") and c.startswith(only[:-1]))
    if want("native_default"):
        m08("native_default", "NATIVE_DEFAULT", "S1", "PHONE", "SDR200", "DARK", default_all=True)
    lums = ["SDR100", "SDR200", "BRIGHT500", "HDR1000"]
    for sc in STILLS:
        for lum in lums:
            if want("target_whiteauto"):
                m08("target_whiteauto", "DOCUMENTED_TARGET_CONFIG", sc, "PHONE", lum, "DARK")
            if want("target_whiteanchor"):
                m08("target_whiteanchor", "DOCUMENTED_TARGET_CONFIG", sc, "PHONE", lum, "DARK", white_y=anchor_white(lum))
    for wy in WHITE_SWEEP:
        c = f"sens_whitey_{wy:g}"
        if want(c):
            m08(c, "SENSITIVITY_RUN", "S1", "PHONE", "SDR100", "DARK", white_y=wy)
    if want("sens_desktop"):
        m08("sens_desktop", "SENSITIVITY_RUN", "S1", "DESKTOP", "SDR100", "DARK")
    if want("sens_dim"):
        m08("sens_dim", "SENSITIVITY_RUN", "S1", "PHONE", "SDR100", "DIM")
    if want("sens_sceneadapt_auto"):                        # undocumented native option --scene-y-adapt (-a) auto
        m08("sens_sceneadapt_auto", "SENSITIVITY_RUN", "S1", "PHONE", "SDR100", "DARK", extra=["--scene-y-adapt", "auto"])
    for lum in ["SDR100", "BRIGHT500"]:
        if want("video_whiteauto"):
            m08("video_whiteauto", "DOCUMENTED_TARGET_CONFIG", "S2", "PHONE", lum, "DARK", fps=25)
        if want("video_whiteanchor"):
            m08("video_whiteanchor", "DOCUMENTED_TARGET_CONFIG", "S2", "PHONE", lum, "DARK", fps=25, white_y=anchor_white(lum))


def run_unfiltered_curves():
    """Per-frame tone curves WITHOUT the temporal filter: each S2 frame in its own process (a 1-frame stream; the
    IIR filter's output equals its input for the first frame). Images discarded, curves kept for the smoothness check."""
    for lum, wy in [("SDR100", None), ("BRIGHT500", None), ("SDR100", 100.0), ("BRIGHT500", 500.0)]:
        cfg = "video_unfiltered_whiteauto" if wy is None else "video_unfiltered_whiteanchor"
        dfspec, _ = display_function(lum, "DARK")
        out = f"{CURVES}/{cfg}/S2__PHONE_{lum}_DARK.csv"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as fo:
            for i, e in enumerate(S2_FRAMES):
                tc = f"{TMP}/tc.csv"
                cmd = ["pfstmo_mantiuk08", "-q", "-d", dfspec, "-s", GEOM["PHONE"], "-o", tc]
                if wy is not None:
                    cmd += ["--white-y", f"{wy:g}"]
                run_stream(cmd, [e], lambda *a: None, f"{TMP}/log_unf.txt")
                for line in open(tc):
                    fo.write(f"{i}," + line.split(",", 1)[1])
        print(f"[mantiuk08] unfiltered curves {cfg} {lum}", flush=True)


# ---------------------------------------------------------------- reinhard02 control (defaults)
def run_reinhard02():
    encs = {"SDR100": srgb_oetf, "SDR200": lambda l: np.power(np.clip(l, 0, 1), 1 / 2.2),
            "BRIGHT500": lambda l: np.power(np.clip(l, 0, 1), 1 / 2.2)}
    for sc in STILLS + ["S2"]:
        exrs = S2_FRAMES if sc == "S2" else [f"{INP}/{sc}.exr"]
        cmd = ["pfstmo_reinhard02", "-v"]
        nan = [0]

        def on_frame(i, tags, ch):
            rgb = xyz_to_pfs_rgb(ch).astype(np.float64)
            bad = ~np.isfinite(rgb); nan[0] += int(bad.any(-1).sum()); rgb[bad] = 0
            for lum, f in encs.items():
                if sc == "S2" and not write_s2("reinhard02", "defaults", lum):
                    continue
                tag = f"{sc}__PHONE_{lum}_DARK"
                path = f"{OUT}/reinhard02/defaults/{tag}/frame_{i + 1:04d}.png" if sc == "S2" else f"{OUT}/reinhard02/defaults/{tag}.png"
                write_png16(path, f(rgb))
        t0 = time.time()
        log = run_stream(cmd, exrs, on_frame, f"{TMP}/log_r02_{sc}.txt")
        info = [l for l in log.splitlines() if l.strip() and "Computing" not in l]
        for lum in encs:
            RUNS["reinhard02"].append({"config": "defaults", "label": "CONTROL_DEFAULTS", "scene": sc, "geometry": "PHONE",
                                       "luminance": lum, "ambient": "DARK",
                                       "command": " ".join(cmd) + "  (stdin: pfsinpfm <oiiotool EXR->PFM>; stdout parsed; each frame independent, no -t)",
                                       "parameters": {"key": 0.18, "phi": 1.0, "scales": False, "white": "Lmax of the frame (tool default)", "temporal_coherent": False},
                                       "encoding": {"SDR100": "clamp[0,1] -> sRGB OETF", "SDR200": "clamp[0,1] -> ^(1/2.2)", "BRIGHT500": "clamp[0,1] -> ^(1/2.2)"}[lum],
                                       "display_unaware": "tool output is display-relative; only the encoding differs between luminance scenarios",
                                       "frames": len(exrs), "frames_written": sc != "S2" or write_s2("reinhard02", "defaults", lum), "nonfinite_pixels_set_to_0": nan[0],
                                       "output": f"{OUT}/reinhard02/defaults/{sc}__PHONE_{lum}_DARK" + ("/" if sc == "S2" else ".png"),
                                       "tool_stderr": info[:8], "seconds": round(time.time() - t0, 1)})
        print(f"[reinhard02] {sc} {time.time() - t0:.1f}s nonfinite={nan[0]}", flush=True)


def run_master():
    """D0.1: the same pipeline on pfstools master (c860691). Checks what changed since 2.2.0 (--tone-value, the geometry
    no-op) on the scenes where it matters; config names carry the build."""
    assert BUILD == "master"
    for sc in ["S0", "S1", "S3_bar", "S3_nobar"]:
        for lum in ["SDR100", "BRIGHT500"]:
            m08("master_whiteauto", "DOCUMENTED_TARGET_CONFIG", sc, "PHONE", lum, "DARK")
            m08("master_whiteanchor", "DOCUMENTED_TARGET_CONFIG", sc, "PHONE", lum, "DARK", white_y=anchor_white(lum))
            m08("master_tonemax_whiteauto", "SENSITIVITY_RUN", sc, "PHONE", lum, "DARK", extra=["--tone-value", "max"])
    m08("master_desktop", "SENSITIVITY_RUN", "S1", "DESKTOP", "SDR100", "DARK")


def save_runs(donor):
    p = f"{OUT}/{donor}/runs.json"
    old = json.load(open(p))["runs"] if os.path.exists(p) else []
    keys = {(r["config"], r["scene"], r["geometry"], r["luminance"], r["ambient"]) for r in RUNS[donor]}
    runs = [r for r in old if (r["config"], r["scene"], r["geometry"], r["luminance"], r["ambient"]) not in keys] + RUNS[donor]
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({"tool": tool_version() | {"operator": f"pfstmo_{donor}"},
               "input": "d0/work/inputs (manifest.json): linear Rec.709/D65 float EXR, absolute cd/m^2, passed UNSCALED",
               "input_path": "oiiotool <exr> --ch R,G,B -d float -o x.pfm; pfsinpfm x.pfm | <tool>",
               "output_contract": "16-bit PNG code values; SDR100 sRGB, SDR200/BRIGHT500 gamma 2.2 display-relative, HDR1000 PQ Rec.2020 absolute",
               "runs": runs}, open(p, "w"), indent=1)


def native_example():
    """NATIVE REPRO: Debevec memorial.hdr (the man page's own example image), tool defaults and the man page's pd=crt."""
    src = f"{TMP}/memorial.hdr"
    if not os.path.exists(src):
        subprocess.run(["curl", "-sL", "--max-time", "120", "-o", src, "https://www.pauldebevec.com/Research/HDR/memorial.hdr"], check=True)
    rec = []
    for name, args in [("native_memorial_default", []), ("native_memorial_pd_crt", ["-d", "pd=crt"])]:
        pfs = subprocess.run(["pfsinrgbe", src], check=True, stdout=subprocess.PIPE).stdout
        r = subprocess.run(["pfstmo_mantiuk08", "-v", "-q"] + args, input=pfs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        import io
        tags, ch = read_pfs_frame(io.BytesIO(r.stdout))
        code = np.clip(xyz_to_pfs_rgb(ch), 0, 1)
        h, w = code.shape[:2]
        small = code[: h // 2 * 2, : w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean((1, 3))  # 2x2 box, for size only
        q = np.round(small * 255).astype(np.uint8)
        spec = oiio.ImageSpec(q.shape[1], q.shape[0], 3, oiio.UINT8)
        b = oiio.ImageBuf(spec); b.set_pixels(oiio.ROI(0, q.shape[1], 0, q.shape[0], 0, 1, 0, 3), np.ascontiguousarray(q))
        os.makedirs("d0/results/stills/mantiuk08", exist_ok=True)
        b.write(f"d0/results/stills/mantiuk08/{name}.png")
        rec.append({"name": name, "command": "pfsinrgbe memorial.hdr | pfstmo_mantiuk08 " + " ".join(args) + " | (pfs stream -> RGB pixel values -> 2x2 box downsample -> 8-bit PNG)",
                    "stderr": [l for l in r.stderr.decode().splitlines() if "took" not in l][:10]})
    json.dump({"image": "memorial.hdr (Paul Debevec, Fiat Lux / HDR research page; https://www.pauldebevec.com/Research/HDR/memorial.hdr, "
                        "1343485 bytes, sha256 18376b9219927b363127817900b1c170a0f752f52a63f5949655b4150e35061d); not stored in the repo",
               "why": "the example image used throughout the pfstmo_mantiuk08 man page", "runs": rec},
              open("d0/results/stills/mantiuk08/native_memorial.json", "w"), indent=1)
    print("[native] done", flush=True)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if what in ("native", "all"):
        native_example()
    if what in ("mantiuk08", "all"):
        run_mantiuk08(only); save_runs("mantiuk08")
    if what in ("unfiltered", "all"):
        run_unfiltered_curves()
    if what == "master":
        run_master(); save_runs("mantiuk08")
    if what in ("reinhard02", "all"):
        run_reinhard02(); save_runs("reinhard02")
