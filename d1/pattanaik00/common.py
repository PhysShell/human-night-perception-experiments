"""Shared helpers for the D1 pattanaik00 donor runs (pfstools 2.2.0 `pfstmo_pattanaik00`).

Stream handling follows d0/donors/mantiuk08/run_pfstmo.py: EXR -> PFM (oiiotool, format only) -> pfsinpfm -> ONE
pfstmo process for all frames of a sequence; the pfs stream the tool writes is parsed frame by frame (X,Y,Z float
channels; pfs' own RGB<->XYZ matrix). Synthetic stimuli (uniform fields) are written as pfs frames directly with
the same matrix (checked equal to pfsinpfm's channel data, see native_timecourse.py).
Only frames in flight are held in RAM.
"""
import os, subprocess, threading
import numpy as np
import OpenImageIO as oiio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.join(ROOT, "d1", "pattanaik00")
CACHE = os.path.join(HERE, ".cache")
TMP = os.path.join(CACHE, "tmp")
OUT = os.path.join(CACHE, "out")
INP = os.path.join(ROOT, "d0", "work", "inputs")
os.makedirs(TMP, exist_ok=True)

# pfs' own colour matrices (src/pfs/colorspace.cpp, pfstools 2.2.0)
PFS_RGB2XYZ = np.array([[0.412424, 0.357579, 0.180464], [0.212656, 0.715158, 0.072186], [0.019332, 0.119193, 0.950444]], np.float32)
PFS_XYZ2RGB = np.array([[3.240708, -1.537259, -0.498570], [-0.969257, 1.875995, 0.041555], [0.055636, -0.203996, 1.057069]], np.float32)

# the tool's hard-coded display observer (tmo_pattanaik00.cpp l.73-90; paper sec. 4.3)
TOOL_DISPLAY_WHITE = 125.0     # cd/m^2 = 5 x G_display(25); tool output 1.0 == this luminance


def srgb_oetf(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(l, 1 / 2.4) - 0.055)


def g22(l):
    return np.power(np.clip(l, 0, 1), 1 / 2.2)


# ---------------------------------------------------------------- pfs stream I/O
def pfs_bytes_exr(exr, floor=None):
    """EXR -> PFM (oiiotool) -> pfsinpfm -> pfs bytes. floor: ADAPTED variant, pixels with all channels <= 0 are set to
    a neutral `floor` cd/m^2 (S3_bar's bar is exactly 0), and every channel is floored at 1e-4 x Y (S5 has R = 0 pixels, which
    the tool turns into R = 1.0 because pfs' XYZ->RGB round trip makes them slightly negative and pow(neg, s) = NaN)."""
    pfm = f"{TMP}/in_{os.getpid()}_{threading.get_ident()}.pfm"
    if floor is None:
        subprocess.run(["oiiotool", exr, "--ch", "R,G,B", "-d", "float", "-o", pfm], check=True)
        b = subprocess.run(["pfsinpfm", pfm], check=True, stdout=subprocess.PIPE).stdout
        os.remove(pfm)
        return b
    a = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[..., :3].copy()
    z = (a <= 0).all(-1); a[z] = floor
    Y = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    a = np.maximum(a, 1e-4 * Y[..., None])        # channels <= 0 (S5 red) -> 1e-4 x Y: survives the pfs matrix round trip
    return pfs_bytes_rgb(a)


def pfs_bytes_rgb(rgb, tags=(("LUMINANCE", "ABSOLUTE"),)):
    """numpy HxWx3 linear Rec.709 cd/m^2 -> one pfs frame (X,Y,Z), same matrix and row order as pfsinpfm."""
    h, w = rgb.shape[:2]
    XYZ = (rgb.astype(np.float32) @ PFS_RGB2XYZ.T).astype("<f4")
    hdr = f"PFS1\n{w} {h}\n3\n{len(tags)}\n" + "".join(f"{k}={v}\n" for k, v in tags) + "X\n0\nY\n0\nZ\n0\nENDH"
    return hdr.encode() + b"".join(np.ascontiguousarray(XYZ[..., i]).tobytes() for i in range(3))


def _readline(f):
    s = f.readline()
    if not s:
        raise EOFError
    return s.decode().rstrip("\n")


def read_pfs_frame(f):
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
        ch[n] = np.frombuffer(f.read(4 * w * h), np.float32).reshape(h, w)
    return tags, ch


def xyz_to_rgb(ch):
    return np.stack([ch["X"], ch["Y"], ch["Z"]], -1) @ PFS_XYZ2RGB.T


def run_stream(cmd, frame_bytes_iter, on_frame, log_path, pipe_after=None):
    """Feed an iterator of pfs frame bytes as ONE stream into cmd (optionally | pipe_after); on_frame(i, tags, ch)."""
    with open(log_path, "wb") as log:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, bufsize=1 << 20)
        q = None
        src = p.stdout
        if pipe_after:
            q = subprocess.Popen(pipe_after, stdin=p.stdout, stdout=subprocess.PIPE, stderr=log, bufsize=1 << 20)
            p.stdout.close(); src = q.stdout
        err, n_in = [], [0]

        def feed():
            try:
                for b in frame_bytes_iter:
                    p.stdin.write(b); n_in[0] += 1
                p.stdin.flush()
            except Exception as ex:                     # noqa: BLE001
                err.append(ex)
            finally:
                p.stdin.close()
        t = threading.Thread(target=feed); t.start()
        i = 0
        while True:
            fr = read_pfs_frame(src)
            if fr is None:
                break
            on_frame(i, *fr); i += 1
        t.join(); rc = p.wait(); rq = q.wait() if q else 0
    if rc != 0 or rq != 0 or err or i != n_in[0]:
        raise RuntimeError(f"{cmd} rc={rc}/{rq} err={err} frames={i}/{n_in[0]}; see {log_path}")
    return open(log_path, errors="replace").read()


def parse_state(log):
    """Per-frame adaptation state from the tool's --verbose stderr (printed only in the global model)."""
    st, cur = [], {}
    keys = {"adaptation cone": "Acone", "adaptation rod": "Arod", "bleaching cone": "Bcone", "bleaching rod": "Brod"}
    for l in log.splitlines():
        l = l.split(": ", 1)[1] if l.startswith("pfstmo_pattanaik00: ") else l
        for k, v in keys.items():
            if l.startswith(k):
                cur[v] = float(l.split(":")[1])
                if v == "Brod":
                    st.append(cur); cur = {}
    return st


def write_png16(path, code):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    q = np.round(np.clip(code, 0, 1) * 65535).astype(np.uint16)
    spec = oiio.ImageSpec(q.shape[1], q.shape[0], 3, oiio.UINT16)
    spec.attribute("png:compressionLevel", 9)
    b = oiio.ImageBuf(spec)
    b.set_pixels(oiio.ROI(0, q.shape[1], 0, q.shape[0], 0, 1, 0, 3), np.ascontiguousarray(q))
    assert b.write(path), b.geterror()


def tool_version():
    import shutil
    exe = shutil.which("pfstmo_pattanaik00")
    return {"pfstools": "2.2.0", "binary": os.path.realpath(exe) if exe else None, "operator": "pfstmo_pattanaik00",
            "source": "pfstools-2.2.0.tgz (sha256 9bf6844985663226c21998eeb43c261acb8e4b3891b9a91b729554406289d7ca), src/tmo/pattanaik00; "
                      "identical in master c860691 (diff -r empty)"}
