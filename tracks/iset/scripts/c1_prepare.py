"""COMMON prep (format conversion only): read stimuli/pack/<S>/<S>_Y.pfm (cd/m^2, 32 px/deg),
crop a square window centred on meta.json source_px, write a MATLAB v5 .mat for Octave.
Usage: python c1_prepare.py <stimulus id> <half-size px> <out.mat>"""
import sys, json, os
import numpy as np, scipy.io as sio
sid, half, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "stimuli", "pack", sid)
meta = json.load(open(os.path.join(root, "meta.json")))
with open(os.path.join(root, f"{sid}_Y.pfm"), "rb") as f:
    kind = f.readline().strip(); w, h = map(int, f.readline().split()); scale = float(f.readline())
    Y = np.fromfile(f, dtype="<f4" if scale < 0 else ">f4").reshape(h, w)
Y = np.flipud(Y)  # PFM rows are stored bottom-to-top
sx, sy = [int(round(v)) for v in meta["source_px"]]
crop = Y[sy - half: sy + half, sx - half: sx + half].astype(np.float64)
E_px = crop.sum() * (np.deg2rad(1 / meta["px_per_deg"]) ** 2) - crop.min() * crop.size * (np.deg2rad(1 / meta["px_per_deg"]) ** 2)
print(sid, "crop", crop.shape, "max", crop.max(), "min", crop.min(), "source illuminance from crop (lx, bg removed)", E_px,
      "meta E_eye_lx", meta["E_eye_lx"])
sio.savemat(out, {"Y": crop, "px_per_deg": float(meta["px_per_deg"]), "E_eye_lx": float(meta["E_eye_lx"]), "id": sid})
