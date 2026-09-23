"""COMMON report (no model): compares the S0 source footprint in the stimulus (cd/m^2) with the
ISETBio retinal illuminance after wvf-human optics (3 / 7 mm). Background removed, each
normalised to unit sum; reports energy fractions in the centre pixel / 3x3 / 5x5 and plots.
Usage: python c3_report_S0.py <COMMON_S0_iset_wvfhuman.mat> <S0_crop64.mat> <outdir>"""
import sys, os, json
import numpy as np, scipy.io as sio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
r = sio.loadmat(sys.argv[1], squeeze_me=True); s = sio.loadmat(sys.argv[2], squeeze_me=True); out = sys.argv[3]
Y = s["Y"]; N = Y.shape[0]
def norm(a):
    b = a - np.median(a); b[b < 0] = 0; return b / b.sum()
def fr(a):
    iy, ix = np.unravel_index(np.argmax(a), a.shape)
    return {k: float(a[iy - h: iy + h + 1, ix - h: ix + h + 1].sum()) for k, h in [("1x1", 0), ("3x3", 1), ("5x5", 2), ("9x9", 4)]}
res = {"stimulus": fr(norm(Y))}
fig, axs = plt.subplots(1, 3, figsize=(11, 3.6))
ims = [("stimulus S0 (cd/m^2)", Y)]
for p in (3, 7):
    I = np.real(r[f"illum_p{p}"]); pad = (I.shape[0] - N) // 2
    Ic = I[pad: pad + N, pad: pad + N]
    res[f"retina_{p}mm"] = fr(norm(Ic))
    res[f"retina_{p}mm"]["peak_over_background"] = float(Ic.max() / np.median(Ic))
    ims.append((f"ISETBio retinal illuminance, {p} mm", Ic))
res["stimulus"]["peak_over_background"] = float(Y.max() / np.median(Y))
for ax, (t, a) in zip(axs, ims):
    im = ax.imshow(np.log10(a), cmap="magma"); ax.set_title(t, fontsize=9); plt.colorbar(im, ax=ax, fraction=.046, label="log10")
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("COMMON S0: 2x2 deg crop at 32 px/deg; ISETBio wvf-human (Thibos 2009 mean eye, no intraocular scatter) under Octave", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(out, "COMMON_S0_iset_wvfhuman.png"), dpi=110)
json.dump(res, open(os.path.join(out, "COMMON_S0_iset_wvfhuman_fractions.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
