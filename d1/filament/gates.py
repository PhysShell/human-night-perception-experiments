#!/usr/bin/env python3
"""D1-B1 gates for Filament scotopicAdaptation() (verbatim, .cache/scotopic). No night scene involved.
INPUT SCALE: the function receives Filament's post-exposure scene-linear Rec.709 and internally multiplies by 380.
Filament defines no cd/m^2 anchor. Here v = linear Rec.709 in cd/m^2 x s, with s = 1 as the primary convention
(input read as cd/m^2), reported as an explicit axis (s = 0.01, 1, 100 in G4).
 G1 nightAdaptation = 0: identity (float32) on random colours, grey ramp, primaries
 G2 nightAdaptation 0..1 (101 steps): finite, smooth (max |2nd difference|), black -> black
 G3 patches at a = 1 across luminance 100 .. 1e-4 cd/m^2: out/in luminance, hue angle and chroma (u'v' about D65),
    negative RGB, NaN
 G4 level dependence of the effect: |delta u'v'| of a neutral grey vs luminance, for s in {0.01, 1, 100}
  tracks/temporal-glare-2009/py.sh d1/filament/gates.py  -> gates.json, gates.png
"""
import json, os, subprocess
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.dirname(os.path.abspath(__file__)); C = f"{D}/.cache"; BIN = f"{C}/scotopic"
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WU = np.array([0.1978, 0.4683])


def run(rgb, a):
    rgb = np.ascontiguousarray(rgb, np.float32).reshape(-1, 3)
    rgb.tofile(f"{C}/g_in.f32")
    subprocess.run([BIN, f"{C}/g_in.f32", f"{C}/g_out.f32", str(len(rgb)), repr(float(a))], check=True)
    return np.fromfile(f"{C}/g_out.f32", np.float32).reshape(-1, 3).astype(np.float64)


def uvY(rgb):
    X = rgb @ M709.T; s = X[:, 0] + 15 * X[:, 1] + 3 * X[:, 2] + 1e-30
    return np.stack([4 * X[:, 0] / s, 9 * X[:, 1] / s], -1), X[:, 1]


def hue_chroma(rgb):
    uv, Y = uvY(np.maximum(rgb, 0)); d = uv - WU
    return np.degrees(np.arctan2(d[:, 1], d[:, 0])), np.hypot(d[:, 0], d[:, 1]), Y


R = {}
rng = np.random.default_rng(0)
# G1
cols = np.concatenate([rng.uniform(0, 1, (10000, 3)) * 10 ** rng.uniform(-4, 2, (10000, 1)), np.eye(3), np.ones((1, 3)) * np.logspace(-4, 2, 13)[:, None]])
o = run(cols, 0.0); rel = np.abs(o - cols) / np.maximum(np.abs(cols), 1e-12)
errmax = float((np.abs(o - cols).max(1) / cols.max(1)).max())
R["G1_identity_a0"] = {"max_rel_err_per_channel": float(rel[cols > 1e-9].max()), "max_abs_err_rel_to_max_channel": errmax,
                       "white_1cd_out": run(np.ones((1, 3)), 0.0)[0].tolist(),
                       "criterion": "error relative to the colour's largest channel < 1e-5 (REVISED after the first run: the per-channel relative error "
                                    "was 3.6e-3, but only on channels ~1e-6 of the colour's max, i.e. float32 round-off through the 3x3 inverse)",
                       "pass": bool(errmax < 1e-5)}
# G2
aa = np.linspace(0, 1, 101); probe = np.array([[1, 1, 1], [1, 0.6, 0.25], [0.2, 0.2, 1.0], [1, 0, 0]]) * 0.01
outs = np.stack([run(probe, a) for a in aa])          # (101, 4, 3)
d2 = np.abs(np.diff(outs, 2, axis=0)).max() / np.abs(outs).max()
blk = run(np.zeros((1, 3)), 1.0)[0]
R["G2_sweep_a"] = {"finite": bool(np.isfinite(outs).all()), "max_second_difference_rel": float(d2), "black_at_a1": blk.tolist(),
                   "linear_in_a": bool(np.allclose(outs, outs[0] + np.outer(aa, np.ones(12)).reshape(101, 4, 3) * (outs[-1] - outs[0]), rtol=1e-4, atol=1e-9)),
                   "pass": bool(np.isfinite(outs).all() and np.all(blk == 0))}
# G3
patches = {"red": [1, 0, 0], "green": [0, 1, 0], "blue": [0, 0, 1], "cyan": [0, 1, 1], "warm_lamp": [1, 0.55, 0.2], "yellow": [1, 1, 0],
           "white": [1, 1, 1], "grey18": [0.18, 0.18, 0.18]}
levels = np.logspace(2, -4, 7)
g3 = {}
for name, c in patches.items():
    c = np.array(c, float); Yc = (M709 @ c)[1]
    ins = np.array([c / Yc * L for L in levels])     # patch at luminance L cd/m^2
    oi = run(ins, 1.0); h0, c0, Y0 = hue_chroma(ins); h1, c1, Y1 = hue_chroma(oi)
    g3[name] = [{"L_in": float(L), "Y_out_over_in": float(Y1[i] / Y0[i]), "hue_in": float(h0[i]), "hue_out": float(h1[i]), "chroma_in": float(c0[i]),
                 "chroma_out": float(c1[i]), "min_rgb_out_rel": float(oi[i].min() / max(np.abs(oi[i]).max(), 1e-30)), "finite": bool(np.isfinite(oi[i]).all())} for i, L in enumerate(levels)]
R["G3_patches_a1_s1"] = g3
# G4
Ls = np.logspace(3, -6, 91); g4 = {}
for s in (0.01, 1.0, 100.0):
    grey = np.ones((len(Ls), 3)) * Ls[:, None] * s
    o = run(grey, 1.0) / s; uv0, _ = uvY(np.ones((len(Ls), 3)) * Ls[:, None]); uv1, Y1 = uvY(np.maximum(o, 0))
    g4[str(s)] = {"L": Ls.tolist(), "duv": np.hypot(*(uv1 - uv0).T).tolist(), "Y_ratio": (Y1 / Ls).tolist()}
R["G4_neutral_vs_level"] = {k: {"duv_at_L": {f"{L:g}": float(v["duv"][i]) for i, L in enumerate(Ls) if i % 10 == 0}} for k, v in g4.items()}
json.dump(R, open(f"{D}/gates.json", "w"), indent=1)
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for s, v in g4.items():
    ax[0].semilogx(v["L"], v["duv"], label=f"s = {s}"); ax[1].semilogx(v["L"], v["Y_ratio"], label=f"s = {s}")
ax[0].set(xlabel="neutral input luminance [cd/m^2] (x s into the function)", ylabel="|delta u'v'| at a = 1", title="G4: Purkinje shift of a neutral vs level")
ax[1].set(xlabel="input luminance [cd/m^2]", ylabel="Y out / Y in", title="G4: luminance change of a neutral"); ax[0].legend(); ax[1].legend()
for name in ("red", "green", "blue", "warm_lamp", "white"):
    ax[2].semilogx(levels, [r["hue_out"] for r in g3[name]], "o-", label=name)
ax[2].set(xlabel="patch luminance [cd/m^2] (s = 1)", ylabel="hue angle about D65 [deg], out", title="G3: output hue at a = 1"); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{D}/gates.png", dpi=100)
for f in ("g_in.f32", "g_out.f32"):
    os.remove(f"{C}/{f}")
print(json.dumps({k: v for k, v in R.items() if k.startswith(("G1", "G2"))}, indent=1))
print(json.dumps(R["G4_neutral_vs_level"], indent=1)[:1500])
