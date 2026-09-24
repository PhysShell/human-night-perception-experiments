#!/usr/bin/env python3
"""D0 donor: ACES 2.0 Output Transforms, run natively through OpenColorIO's built-in ACES 2.0 studio config.

No tone mapper is written here. The only operations outside OCIO are
  (1) the documented SCENE NORMALIZATION  ACES_scale = 2^EV / 100 cd/m^2  (see d0/input-contracts/aces2.md), a scalar
      multiply on linear Rec.709 (commutes with OCIO's 3x3 Linear Rec.709 -> ACES2065-1 matrix);
  (2) clipping OCIO's display code values to [0, 1] and quantising to 16-bit PNG.
Colour conversion (Linear Rec.709 (sRGB) -> ACES2065-1), the ACES 2.0 Output Transform (JMh rendering, peak, limiting
gamut) and the display encoding (sRGB piecewise / Rec.2100-PQ) are all OCIO built-ins of
  ocio://studio-config-v4.0.0_aces-v2.0_ocio-v2.5

Usage (from the repo root):
  python3 d0/donors/aces2/run.py setup        # creates d0/work/aces2_tmp/venv with opencolorio==2.5.2, OpenEXR, numpy
  <venv>/bin/python d0/donors/aces2/run.py native   # native repro vs official CTL (needs ctlrender, see build_ctl)
  <venv>/bin/python d0/donors/aces2/run.py render   # DOCUMENTED_TARGET_CONFIG + SENSITIVITY_RUN -> d0/work/out/aces2
  <venv>/bin/python d0/donors/aces2/run.py curve    # neutral absolute-luminance -> display-luminance table
Frames are processed one at a time (peak RAM well under 1 GB).
"""
import glob, hashlib, json, os, struct, subprocess, sys, time, zlib

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
D0 = os.path.join(REPO, "d0")
TMP = os.path.join(D0, "work", "aces2_tmp")
VENV = os.path.join(TMP, "venv")
INP = os.path.join(D0, "work", "inputs")
OUT = os.path.join(D0, "work", "out", "aces2")
RES = os.path.join(D0, "results")

CONFIG_URI = "ocio://studio-config-v4.0.0_aces-v2.0_ocio-v2.5"
SRC_CS = "Linear Rec.709 (sRGB)"            # OCIO's own colourspace for our linear Rec.709/D65 input
# scenario label -> (OCIO display, OCIO view, ACES CTL reference transform, metadata)
TARGETS = {
    "SDR100": ("sRGB - Display", "ACES 2.0 - SDR 100 nits (Rec.709)",
               "d65/srgb/Output.Academy.Rec709-D65_100nit_in_Rec709-D65_sRGB-Piecewise.ctl",
               dict(peak_cd_m2=100, limiting_gamut="Rec.709 / D65", encoding_primaries="Rec.709 / D65",
                    eotf="sRGB piecewise (IEC 61966-2-1)", transfer="srgb")),
    "HDR1000": ("Rec.2100-PQ - Display", "ACES 2.0 - HDR 1000 nits (P3 D65)",
                "d65/rec2100/Output.Academy.P3-D65_1000nit_in_Rec2100-D65_ST2084.ctl",
                dict(peak_cd_m2=1000, limiting_gamut="P3 / D65", encoding_primaries="Rec.2020 / D65",
                     eotf="SMPTE ST 2084 (PQ), absolute (code 1.0 = 10000 cd/m^2)", transfer="pq")),
    # our BRIGHT500 scenario is SDR gamma 2.2; ACES has no SDR-500 output, so this is the ACES 500-nit HDR (PQ) output
    "BRIGHT500_PQ": ("Rec.2100-PQ - Display", "ACES 2.0 - HDR 500 nits (P3 D65)",
                     "d65/rec2100/Output.Academy.P3-D65_500nit_in_Rec2100-D65_ST2084.ctl",
                     dict(peak_cd_m2=500, limiting_gamut="P3 / D65", encoding_primaries="Rec.2020 / D65",
                          eotf="SMPTE ST 2084 (PQ), absolute (code 1.0 = 10000 cd/m^2)", transfer="pq")),
}
REF_CD_M2 = 100.0          # documented normalization: ACES2065-1 value 1.0 <-> 100 cd/m^2 (ACES 2 CAM reference white)
SWEEP_EV = list(range(-4, 21, 2))
STILLS = ["S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"]


# ----------------------------------------------------------------------------------------------------------- setup
def setup():
    if not os.path.exists(os.path.join(VENV, "bin", "python")):
        os.makedirs(TMP, exist_ok=True)
        env = dict(os.environ, TMPDIR=TMP)
        subprocess.check_call([sys.executable, "-m", "venv", VENV], env=env)
        subprocess.check_call([os.path.join(VENV, "bin", "pip"), "install", "-q", "--no-cache-dir",
                               "opencolorio==2.5.2", "OpenEXR", "numpy"], env=env)
    print("venv:", VENV)


def build_ctl():
    """Official CTL reference (ctlrender) from github.com/ampas/CTL, built against nix-store OpenEXR/Imath/libtiff with
    the nix gcc wrapper (system gcc links the host glibc and fails at runtime). Transient: d0/work/aces2_tmp/ctl_*."""
    def one(pat):
        m = sorted(glob.glob(pat))
        if not m:
            raise SystemExit("missing " + pat)
        return m[0]
    s = "/nix/store/"
    pfx = ";".join([one(s + "*-imath-3.*[0-9]"), one(s + "*-openexr-3.*-dev"), one(s + "*-openexr-3.*[0-9]"),
                    one(s + "*-libdeflate-1.*[0-9]"), one(s + "*-libtiff-4.*-dev"), one(s + "*-libtiff-4.*[0-9]"),
                    one(s + "*-zlib-1.*-dev"), [d for d in glob.glob(s + "*-zlib-1.*[0-9]") if os.path.exists(d + "/lib/libz.so")][0]])
    gcc = one(s + "*-gcc-wrapper-*[0-9]") + "/bin"
    cmake = one(s + "*-cmake-[0-9]*[0-9]") + "/bin/cmake"
    for name, url in [("ctl_src", "https://github.com/ampas/CTL"), ("src_aces-core", "https://github.com/aces-aswf/aces-core"),
                      ("src_aces-output", "https://github.com/aces-aswf/aces-output")]:
        if not os.path.exists(os.path.join(TMP, name)):
            subprocess.check_call(["git", "clone", "-q", "--depth", "1", "--filter=blob:limit=5m", url, os.path.join(TMP, name)])
    b = os.path.join(TMP, "ctl_build")
    os.makedirs(b, exist_ok=True)
    subprocess.check_call([cmake, "../ctl_src", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_C_COMPILER={gcc}/gcc",
                           f"-DCMAKE_CXX_COMPILER={gcc}/g++", f"-DCMAKE_PREFIX_PATH={pfx}"], cwd=b)
    subprocess.check_call(["make", "-j3", "ctlrender"], cwd=b)


# ------------------------------------------------------------------------------------------------------------- I/O
def read_exr(path):
    import numpy as np, OpenEXR
    ch = OpenEXR.File(path).channels()
    if "RGB" in ch:
        a = ch["RGB"].pixels
    elif "RGBA" in ch:
        a = ch["RGBA"].pixels[..., :3]
    else:
        a = np.stack([ch[c].pixels for c in "RGB"], -1)
    return np.ascontiguousarray(a[..., :3], dtype=np.float32)


def write_exr(path, a):
    import numpy as np, OpenEXR
    OpenEXR.File({"compression": OpenEXR.ZIP_COMPRESSION}, {"RGB": np.ascontiguousarray(a, dtype=np.float32)}).write(path)


def write_png16(path, code01, transfer):
    """16-bit RGB PNG, code = round(clip(v,0,1)*65535). Sub filter, zlib 9. sRGB chunk (SDR) or cICP 9/16/0/1 (PQ)."""
    import numpy as np
    q = np.round(np.clip(code01, 0.0, 1.0) * 65535.0).astype(">u2")
    h, w, _ = q.shape
    raw = q.view(np.uint8).reshape(h, w * 6)
    f = raw.copy()
    f[:, 6:] = raw[:, 6:] - raw[:, :-6]                 # PNG filter 1 (Sub), bpp = 6, mod 256
    data = np.concatenate([np.ones((h, 1), np.uint8), f], 1).tobytes()

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    extra = chunk(b"sRGB", b"\x00") if transfer == "srgb" else chunk(b"cICP", bytes([9, 16, 0, 1]))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 2, 0, 0, 0)) + extra
                 + chunk(b"IDAT", zlib.compress(data, 9)) + chunk(b"IEND", b""))
    os.replace(path + ".part", path)
    return q


def decode_Y(q16, transfer):
    """Display luminance (cd/m^2, no black level / ambient) of 16-bit codes: for the per-run stats only.
    The metrics use d0/display_model.py."""
    import numpy as np
    v = q16.astype(np.float64) / 65535.0
    if transfer == "srgb":
        lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4) * 100.0
        return lin @ np.array([0.2126729, 0.7151522, 0.0721750])
    m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
    p = v ** (1 / m2)
    lin = 10000 * (np.maximum(p - c1, 0) / (c2 - c3 * p)) ** (1 / m1)
    return lin @ np.array([0.2627002, 0.6779981, 0.0593017])


def sha(path, n=16):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


# ------------------------------------------------------------------------------------------------------------ OCIO
def ocio_config():
    import PyOpenColorIO as ocio
    return ocio, ocio.Config.CreateFromFile(CONFIG_URI)


def processor(cfg, ocio, src, display, view):
    p = cfg.getProcessor(src, display, view, ocio.TRANSFORM_DIR_FORWARD)
    return p.getDefaultCPUProcessor()


def apply(cpu, a):
    a = np.ascontiguousarray(a, dtype=np.float32).copy()
    cpu.applyRGB(a)
    return a


def target_info(cfg, ocio, lum):
    display, view, ctl, meta = TARGETS[lum]
    vt = cfg.getDisplayViewTransformName(display, view)
    return dict(display=display, view=view, view_transform=vt,
                view_transform_builtin=str(cfg.getViewTransform(vt).getTransform(ocio.VIEWTRANSFORM_DIR_FROM_REFERENCE)),
                display_colorspace_builtin=str(cfg.getColorSpace(display).getTransform(ocio.COLORSPACE_DIR_FROM_REFERENCE)),
                ctl_reference=ctl, **meta)


# ---------------------------------------------------------------------------------------------------- native repro
SMPTE_CC24_AP0 = [  # ColorChecker24 in ACES2065-1, SMPTE ST 2065-1:2021 (as used in OCIO's own ACES2 unit test)
    (0.11877, 0.08709, 0.05895), (0.40002, 0.31916, 0.23736), (0.18476, 0.20398, 0.31311), (0.10901, 0.13511, 0.06493),
    (0.26684, 0.24604, 0.40932), (0.32283, 0.46208, 0.40606), (0.38605, 0.22743, 0.05777), (0.13822, 0.13037, 0.33703),
    (0.30202, 0.13752, 0.12758), (0.09310, 0.06347, 0.13525), (0.34876, 0.43654, 0.10613), (0.48655, 0.36685, 0.08061),
    (0.08732, 0.07443, 0.27274), (0.15366, 0.25692, 0.09071), (0.21742, 0.07070, 0.05130), (0.58919, 0.53943, 0.09157),
    (0.30904, 0.14818, 0.27426), (0.14901, 0.23378, 0.35939), (0.86653, 0.86792, 0.85818), (0.57356, 0.57256, 0.57169),
    (0.35346, 0.35337, 0.35391), (0.20253, 0.20243, 0.20287), (0.09467, 0.09520, 0.09637), (0.03745, 0.03766, 0.03895)]
# OCIO v2.5.2 tests/cpu/ops/fixedfunction/FixedFunctionOpCPU_tests.cpp, test aces_output_transform_20 (1000 nit, P3-D65):
# first 6 = ACEScg primaries/secondaries x4 (as AP0), 3 OCIO values, CC24, 18 % grey, perfect reflecting diffuser.
OCIO_UT_IN = [(2.781808965, 0.179178253, -0.022103530), (3.344523751, 3.617862727, -0.006002689),
              (0.562714786, 3.438684474, 0.016100841), (1.218191035, 3.820821747, 4.022103530),
              (0.655476249, 0.382137273, 4.006002689), (3.437285214, 0.561315526, 3.983899159),
              (0.11, 0.02, 0.04), (0.71, 0.51, 0.81), (0.43, 0.82, 0.71)] + SMPTE_CC24_AP0 + [(0.18,) * 3, (0.97784,) * 3]
OCIO_UT_OUT = [(4.966013432, -0.033002287, 0.041583523), (3.969460726, 3.825797558, -0.056160748),
               (-0.075460039, 3.689072609, 0.270235062), (-0.095436633, 3.650521517, 3.459975719),
               (-0.028881177, 0.196473420, 2.796123743), (4.900828362, -0.064385533, 3.838270903),
               (0.096890487, -0.001135427, 0.018971475), (0.809613585, 0.479857147, 0.814239979),
               (0.107417941, 0.920530438, 0.726379037), (0.115475342, 0.050812997, 0.030212998),
               (0.484880149, 0.301042914, 0.226769030), (0.098463453, 0.160814837, 0.277010798),
               (0.071130276, 0.107334509, 0.035097614), (0.207111374, 0.198474824, 0.375326097),
               (0.195447117, 0.481112540, 0.393299103), (0.571913302, 0.196873263, 0.041634843),
               (0.045791976, 0.069875412, 0.291233569), (0.424848884, 0.083199054, 0.102153927),
               (0.059589352, 0.022219239, 0.091246955), (0.360364884, 0.478741497, 0.086726815),
               (0.695661962, 0.371994466, 0.068298057), (0.011806240, 0.021665439, 0.199594870),
               (0.076526135, 0.256237596, 0.060564563), (0.300064713, 0.023416281, 0.030360531),
               (0.805483222, 0.596904039, 0.082996234), (0.388385385, 0.079899333, 0.245818958),
               (0.010951802, 0.196106046, 0.307181537), (0.921020269, 0.921707630, 0.912857533),
               (0.590191603, 0.588424563, 0.587825298), (0.337743223, 0.337686002, 0.338155240),
               (0.169266403, 0.169178575, 0.169557154), (0.058346011, 0.059387885, 0.060296256),
               (0.012581199, 0.012947144, 0.013654212), (0.145115077, 0.145115703, 0.145115480),
               (1.041565537, 1.041566610, 1.041566253)]


def make_chart():
    """ACES2065-1 test chart, 256 x 64: rows 0-15 neutral ramp 2^-26..2^+10 (log2-uniform over 256 columns), rows
    16-31 the 35 OCIO unit-test inputs (7 px wide patches), rows 32-63 1024*8 pseudo-random AP0 values (seed 20260924):
    AP1-bounded chroma, luminance log-uniform 1e-7..1e3."""
    import numpy as np
    W, H = 256, 64
    a = np.zeros((H, W, 3), np.float32)
    a[0:16] = (2.0 ** np.linspace(-26, 10, W))[None, :, None]
    for i, v in enumerate(OCIO_UT_IN):
        a[16:32, i * 7:(i + 1) * 7] = v
    rng = np.random.default_rng(20260924)
    ap1 = rng.random((32 * W, 3)) ** 2
    ap1 /= (ap1 @ np.array([0.2722287168, 0.6740817658, 0.0536895174]))[:, None] + 1e-12
    ap1 *= 10 ** rng.uniform(-7, 3, (32 * W, 1))
    AP1_TO_AP0 = np.array([[0.6954522414, 0.1406786965, 0.1638690622], [0.0447945634, 0.8596711185, 0.0955343182],
                           [-0.0055258826, 0.0040252103, 1.0015006723]])
    a[32:] = (ap1 @ AP1_TO_AP0.T).reshape(32, W, 3)
    return a


def native():
    import numpy as np
    ocio, cfg = ocio_config()
    os.makedirs(os.path.join(RES, "stills", "aces2"), exist_ok=True)
    os.makedirs(os.path.join(RES, "tables"), exist_ok=True)
    rep = dict(ocio_version=ocio.__version__, config=cfg.getName(), config_uri=CONFIG_URI, date=time.strftime("%Y-%m-%d"))
    # (a) OCIO's fixed-function ACES 2.0 op vs the upstream OCIO unit-test vectors (1000 nit, P3-D65 limiting)
    ff = ocio.FixedFunctionTransform(ocio.FIXED_FUNCTION_ACES_OUTPUT_TRANSFORM_20,
                                     [1000.0, 0.680, 0.320, 0.265, 0.690, 0.150, 0.060, 0.3127, 0.3290])
    got = apply(cfg.getProcessor(ff).getDefaultCPUProcessor(), np.array(OCIO_UT_IN, np.float32)[None])[0]
    d = np.abs(got - np.array(OCIO_UT_OUT))
    rep["ocio_fixed_function_vs_ocio_unit_test_vectors"] = dict(
        source="OpenColorIO v2.5.2 tests/cpu/ops/fixedfunction/FixedFunctionOpCPU_tests.cpp::aces_output_transform_20",
        n=len(OCIO_UT_IN), units="linear P3-D65, 1.0 = 100 cd/m^2", max_abs=float(d.max()), mean_abs=float(d.mean()),
        test_tolerance=1e-5)
    # (b) OCIO display/view vs the official ACES 2.0 CTL (ctlrender) on the same ACES2065-1 chart
    chart = make_chart()
    cpath = os.path.join(TMP, "native_chart_ap0.exr")
    write_exr(cpath, chart)
    ctlr = os.path.join(TMP, "ctl_build", "ctlrender", "ctlrender")
    env = dict(os.environ, CTL_MODULE_PATH=os.path.join(TMP, "src_aces-core", "lib"))
    rep["ctl"] = dict(ctlrender=subprocess.run([ctlr, "-help"], capture_output=True, text=True).stdout.splitlines()[:1],
                      ctl_repo_commit=git_head(os.path.join(TMP, "ctl_src")),
                      aces_core_commit=git_head(os.path.join(TMP, "src_aces-core")),
                      aces_output_commit=git_head(os.path.join(TMP, "src_aces-output")))
    rep["chart"] = make_chart.__doc__.strip()
    rep["targets"] = {}
    for lum, (display, view, ctl, meta) in TARGETS.items():
        o = apply(processor(cfg, ocio, "ACES2065-1", display, view), chart)
        opath = os.path.join(TMP, f"native_ctl_{lum}.exr")
        subprocess.check_call([ctlr, "-force", "-ctl", os.path.join(TMP, "src_aces-output", ctl), cpath, opath,
                               "-format", "exr32"], env=env, stdout=subprocess.DEVNULL)
        c = read_exr(opath)
        diff = np.abs(np.clip(o, 0, 1) - np.clip(c, 0, 1))
        rows = dict(ramp=slice(0, 16), ocio_unit_test_patches=slice(16, 32), random_ap0=slice(32, 64), all=slice(0, 64))
        r = dict(target=target_info(cfg, ocio, lum))
        for k, s in rows.items():
            dd = diff[s]
            r[k] = dict(max_abs_code=float(dd.max()), p99_abs_code=float(np.percentile(dd, 99)),
                        mean_abs_code=float(dd.mean()), max_abs_16bit=float(dd.max() * 65535),
                        frac_16bit_codes_equal=float(np.mean(np.round(np.clip(o[s], 0, 1) * 65535)
                                                             == np.round(np.clip(c[s], 0, 1) * 65535))),
                        frac_within_1_10bit_code=float(np.mean(dd * 1023 <= 1.0)))
        # a few named neutral pixels of the ramp
        xs = [int(round((np.log2(v) + 26) / 36 * 255)) for v in (2 ** -20, 2 ** -12, 2 ** -6, 0.18, 1.0, 2 ** 4, 2 ** 8)]
        r["ramp_probes"] = [dict(aces=float(chart[0, x, 0]), ocio=[float(t) for t in o[0, x]], ctl=[float(t) for t in c[0, x]])
                            for x in xs]
        rep["targets"][lum] = r
        big = lambda im: np.repeat(np.repeat(im, 2, 0), 2, 1)
        write_png16(os.path.join(RES, "stills", "aces2", f"native_chart_ocio_{lum}.png"), big(o), meta["transfer"])
        write_png16(os.path.join(RES, "stills", "aces2", f"native_chart_ctl_{lum}.png"), big(c), meta["transfer"])
        # difference image: |OCIO - CTL| in code values x 1000 (grey), for inspection only
        write_png16(os.path.join(RES, "stills", "aces2", f"native_chart_absdiff_x1000_{lum}.png"),
                    big(np.clip(diff * 1000, 0, 1)), "srgb")
    json.dump(rep, open(os.path.join(RES, "tables", "aces2_native_repro.json"), "w"), indent=1)
    print(json.dumps({k: {kk: vv["all"] for kk, vv in v.items()} if k == "targets" else v for k, v in rep.items()
                      if k in ("targets", "ocio_fixed_function_vs_ocio_unit_test_vectors")}, indent=1))


def git_head(d):
    try:
        return subprocess.check_output(["git", "-C", d, "log", "-1", "--format=%H %ci"], text=True).strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------- render
def scene_files():
    m = json.load(open(os.path.join(INP, "manifest.json")))
    out = [(s, os.path.join(INP, s + ".exr")) for s in STILLS]
    frames = sorted(glob.glob(os.path.join(INP, m["scenes"]["S2"]["dir"], "frame_*.exr")))
    assert len(frames) == 48, len(frames)
    return out, frames


def render_one(cpu, src, scale, dst, transfer):
    import numpy as np
    a = read_exr(src)
    stats = dict(input_min=float(a.min()), input_max=float(a.max()))
    a *= np.float32(scale)
    o = apply(cpu, a)
    del a
    q = write_png16(dst, o, transfer)
    Y = decode_Y(q, transfer)
    stats.update(frac_code0_all_channels=float(np.mean(np.all(q == 0, -1))),
                 max_code16=int(q.max()),
                 out_Y_cd_m2_percentiles={p: float(np.percentile(Y, p)) for p in (1, 50, 99, 99.9, 100)},
                 png_bytes=os.path.getsize(dst))
    return stats


def render(only=None):
    ocio, cfg = ocio_config()
    stills, frames = scene_files()
    me = sha(os.path.abspath(__file__))
    runs = []
    rpath = os.path.join(OUT, "runs.json")
    common = dict(code="d0/donors/aces2/run.py", code_sha256_16=me, ocio_version=ocio.__version__, config=cfg.getName(),
                  config_uri=CONFIG_URI, input_colorspace=SRC_CS, reference_colorspace="ACES2065-1",
                  geometry="PHONE", ambient="DARK",
                  geometry_ambient_note="ACES Output Transforms are per-pixel and geometry/ambient-unaware; PHONE and "
                                        "DARK are labels only (the same codes serve every geometry/ambient)")
    jobs = []
    for lum in TARGETS:
        for s, f in stills:
            jobs.append(("DOCUMENTED_TARGET_CONFIG", lum, 0, s, f, os.path.join(OUT, "DOCUMENTED_TARGET_CONFIG", f"{s}__PHONE_{lum}_DARK.png")))
        for f in frames:
            n = os.path.basename(f).replace(".exr", ".png")
            jobs.append(("DOCUMENTED_TARGET_CONFIG", lum, 0, "S2", f, os.path.join(OUT, "DOCUMENTED_TARGET_CONFIG", f"S2__PHONE_{lum}_DARK", n)))
    for ev in SWEEP_EV:
        cfgname = "SENSITIVITY_RUN_EV%s%02d" % ("p" if ev >= 0 else "m", abs(ev))
        jobs.append((cfgname, "SDR100", ev, "S1", os.path.join(INP, "S1.exr"), os.path.join(OUT, cfgname, "S1__PHONE_SDR100_DARK.png")))
    if only:
        jobs = [j for j in jobs if only in j[0] or only == j[1]]
    cpus = {}
    t0 = time.time()
    for i, (label, lum, ev, scene, src, dst) in enumerate(jobs):
        if lum not in cpus:
            cpus[lum] = processor(cfg, ocio, SRC_CS, TARGETS[lum][0], TARGETS[lum][1])
        scale = 2.0 ** ev / REF_CD_M2
        st = render_one(cpus[lum], src, scale, dst, TARGETS[lum][3]["transfer"])
        runs.append(dict(common, label="SENSITIVITY_RUN" if label.startswith("SENSITIVITY") else label, config_dir=label,
                         scene=scene, input=os.path.relpath(src, REPO), luminance=lum, target=target_info(cfg, ocio, lum),
                         exposure=dict(ev_stops=ev, aces_per_cd_m2=scale,
                                       rule="ACES2065-1 = M_709->AP0 . (Y_abs-scaled linear Rec.709) * 2^EV / 100 cd/m^2"),
                         output=os.path.relpath(dst, REPO), stats=st))
        if i % 20 == 0:
            print(f"[{i + 1}/{len(jobs)}] {time.time() - t0:.0f}s {os.path.relpath(dst, OUT)}", flush=True)
    doc = dict(donor="ACES 2.0 Output Transforms via OpenColorIO built-in config", n_runs=len(runs),
               output_contract="16-bit PNG RGB code values; SDR100: sRGB piecewise, Rec.709 primaries; "
                               "HDR1000/BRIGHT500_PQ: SMPTE ST 2084 PQ, Rec.2020 primaries; code 0 = display black",
               not_available=dict(SDR200="ACES 2.0 has no 200-nit SDR output transform",
                                  BRIGHT500="ACES 2.0 has no 500-nit SDR (gamma 2.2) output; BRIGHT500_PQ is the ACES "
                                            "HDR 500-nit P3-D65 limited Rec.2100-PQ output, NOT the SDR BRIGHT500 scenario"),
               runs=runs)
    json.dump(doc, open(rpath, "w"), indent=1)
    print("wrote", rpath, len(runs), "runs", f"{time.time() - t0:.0f}s")


def curve():
    """Neutral (D65 grey) absolute scene luminance -> display luminance, documented normalization, every target."""
    import numpy as np
    ocio, cfg = ocio_config()
    Ys = np.array([1e-6, 1e-5, 2.87e-5, 7.05e-5, 1e-4, 4e-4, 1e-3, 1.15e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3, 1, 1.92, 3, 10,
                   18, 30, 100, 300, 1000, 3000, 1e4], np.float32)
    rows = []
    for lum in TARGETS:
        cpu = processor(cfg, ocio, SRC_CS, TARGETS[lum][0], TARGETS[lum][1])
        o = apply(cpu, np.repeat((Ys / REF_CD_M2)[None, :, None], 3, 2))
        q = np.round(np.clip(o, 0, 1) * 65535).astype(np.uint16)
        Yd = decode_Y(q, TARGETS[lum][3]["transfer"])[0]
        Yf = decode_Y(np.clip(o, 0, 1) * 65535.0, TARGETS[lum][3]["transfer"])[0]      # before 16-bit quantisation
        rows.append(dict(target=lum, display_Y_cd_m2=[float(v) for v in Yd], display_Y_cd_m2_unquantised=[float(v) for v in Yf],
                         code_G_float=[float(v) for v in o[0, :, 1]], code16_G=[int(v) for v in q[0, :, 1]]))
    doc = dict(note="neutral input, documented normalization ACES = Y/100 cd/m^2 (EV 0); display luminance decoded from "
                    "the 16-bit code without black level/ambient", scene_Y_cd_m2=[float(v) for v in Ys], targets=rows)
    json.dump(doc, open(os.path.join(RES, "tables", "aces2_neutral_curve.json"), "w"), indent=1)
    for r in rows:
        print(r["target"], [f"{a:.3g}->{b:.3g}" for a, b in zip(Ys, r["display_Y_cd_m2_unquantised"])])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    if cmd == "setup":
        setup()
    elif cmd == "build_ctl":
        build_ctl()
    else:
        import numpy as np  # noqa: F401  (module-level use in helpers)
        globals()["np"] = np
        {"native": native, "render": lambda: render(sys.argv[2] if len(sys.argv) > 2 else None), "curve": curve}[cmd]()
