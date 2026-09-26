#!/usr/bin/env python3
"""D1-B4, exactly as d1/chroma_b4/PREREG.md (committed before this ran).
Upstream frozen: Filament-derived Cao/Kirk kernel, a = 1, kappa = 3 (d1/filament/.cache/scotopic).
Chroma stage: out = Y_f*(1,1,1) + w*(f - Y_f*(1,1,1)); w per pixel by bisection so that u'v' chroma out/f = t(L),
L = the pixel's physical input luminance (cd/m^2). Sensitivity variant: w = t(L).
  d1/filament/setup.sh; tracks/temporal-glare-2009/py.sh d1/chroma_b4/run.py -> results.json, gates.json, curves.png, sheet_S1.png
"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
D = "d1/chroma_b4"; C = f"{D}/.cache"; os.makedirs(C, exist_ok=True); BIN = "d1/filament/.cache/scotopic"; KAPPA = 3.0
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_Xw = M709 @ np.ones(3)
WU = np.array([4 * _Xw[0], 9 * _Xw[1]]) / (_Xw[0] + 15 * _Xw[1] + 3 * _Xw[2])   # exact u'v' of the Rec.709 white (1,1,1)
# CORRECTION after the first run: WU was the rounded (0.1978, 0.4683); 4e-5 off the white the stage mixes towards,
# which alone produced ~1 deg hue "errors" at chroma ~0.002 (B4-G4). Measurement fix only; no gate or law changed.
CAND = {"none": lambda L: np.ones_like(L),
        "pcond_c": lambda L: np.clip((L - 5.62e-3) / (5.62 - 5.62e-3), 0, 1),
        "wanat14": lambda L: L / (L + 0.108)}
PATCH = {"neutral": [1, 1, 1], "red": [1, 0, 0], "green": [0, 1, 0], "blue": [0, 0, 1], "cyan": [0, 1, 1], "warm_lamp": [1, 0.55, 0.2], "yellow": [1, 1, 0]}
LS = np.append(np.logspace(-4, 2, 61), 200.0)


def filament(rgb):
    rgb = np.ascontiguousarray(rgb * KAPPA, np.float32).reshape(-1, 3); rgb.tofile(f"{C}/i.f32")
    subprocess.run([BIN, f"{C}/i.f32", f"{C}/o.f32", str(len(rgb)), "1.0"], check=True)
    return np.fromfile(f"{C}/o.f32", np.float32).reshape(-1, 3).astype(np.float64) / KAPPA


def uv(rgb):
    X = rgb @ M709.T; s = X[:, 0] + 15 * X[:, 1] + 3 * X[:, 2] + 1e-300
    return np.stack([4 * X[:, 0] / s, 9 * X[:, 1] / s], -1)


def chroma(rgb): return np.hypot(*(uv(np.maximum(rgb, 0)) - WU).T)
def hue(rgb): d = uv(np.maximum(rgb, 0)) - WU; return np.degrees(np.arctan2(d[:, 1], d[:, 0]))


def stage(f, L, t, mode="uv"):
    Yf = f @ M709[1]; grey = Yf[:, None] * np.ones(3)
    if mode == "weight":
        w = t
    else:
        cf = chroma(f); target = t * cf; lo = np.zeros_like(t); hi = np.ones_like(t)
        for _ in range(50):
            mid = 0.5 * (lo + hi); cm = chroma(grey + mid[:, None] * (f - grey))
            up = cm < target; lo = np.where(up, mid, lo); hi = np.where(up, hi, mid)
        w = np.where(cf > 0, 0.5 * (lo + hi), 1.0)
    return grey + w[:, None] * (f - grey)


res = {"upstream": "Filament-derived Cao/Kirk kernel, a = 1, kappa = 3", "prereg": "d1/chroma_b4/PREREG.md", "L": LS.tolist(), "patches": {}}
G = {}
for cand, tl in CAND.items():
    for mode in ("uv", "weight"):
        key = f"{cand}/{mode}"; res["patches"][key] = {}
        for n, c in PATCH.items():
            c = np.array(c, float); ins = np.array([c / (M709 @ c)[1] * L for L in LS])
            f = filament(ins); o = stage(f, LS, tl(LS), mode)
            res["patches"][key][n] = {"chroma_in": chroma(ins).tolist(), "chroma_f": chroma(f).tolist(), "chroma_out": chroma(o).tolist(),
                                      "hue_f": hue(f).tolist(), "hue_out": hue(o).tolist(), "Y_out_over_Yf": ((o @ M709[1]) / (f @ M709[1])).tolist(),
                                      "E_f": np.hypot(*(uv(f) - uv(ins)).T).tolist(), "E_out": np.hypot(*(uv(np.maximum(o, 0)) - uv(ins)).T).tolist(),
                                      "finite": bool(np.isfinite(o).all()), "min_rgb": float(o.min())}
# S1
img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); H, W = img.shape[:2]
m = dict(np.load("d0/work/inputs/masks/S1.npz")); flat = img.reshape(-1, 3); Lpix = flat @ M709[1]
fS1 = filament(flat); s1 = {}; keep = {"input": img, "filament": fS1.reshape(H, W, 3)}
for cand, tl in CAND.items():
    o = stage(fS1, Lpix, tl(Lpix), "uv"); keep[cand] = o.reshape(H, W, 3)
    cf, co = chroma(fS1).reshape(H, W), chroma(o).reshape(H, W)
    s1[cand] = {"lamp_chroma_ratio_median": float(np.median((co / np.maximum(cf, 1e-12))[m["lamp"]])), "sky_chroma_median": float(np.median(co[m["sky"]])),
                "ground_chroma_median": float(np.median(co[m["ground"]])), "lamp_chroma_median": float(np.median(co[m["lamp"]])),
                "lamp_hue_median": float(np.median(hue(o).reshape(H, W)[m["lamp"]])), "finite": bool(np.isfinite(o).all()), "min_rgb": float(o.min())}
res["S1"] = s1
# gates (primary mode "uv")
for cand in CAND:
    P = res["patches"][f"{cand}/uv"]; g = {}
    i100 = LS >= 100
    g["G1"] = min(float(np.min(np.array(v["chroma_out"])[i100] / np.maximum(np.array(v["chroma_f"])[i100], 1e-12))) for n, v in P.items() if n != "neutral")
    g["G1_pass"] = g["G1"] >= 0.99
    low = LS <= 5; mono = {}
    for n, v in P.items():
        if n == "neutral": continue
        co = np.array(v["chroma_out"])[low]          # ascending L; "does not increase as L decreases" = non-decreasing in L
        mono[n] = float(np.max(-np.diff(co)))       # largest increase when stepping down in L
    g["G2_worst_increase"] = mono; g["G2_pass"] = all(x <= 1e-4 for x in mono.values())
    g["G3"] = max(float(np.max(np.array(v["chroma_out"])[LS <= 1e-3])) for v in P.values()); g["G3_pass"] = g["G3"] <= 0.01
    dh = []
    for v in P.values():
        co, hf, ho = map(np.array, (v["chroma_out"], v["hue_f"], v["hue_out"])); k = co >= 0.002
        dh.append(float(np.max(np.abs((ho - hf + 180) % 360 - 180)[k])) if k.any() else 0.0)
    g["G4"] = max(dh); g["G4_pass"] = g["G4"] <= 0.5
    g["G5"] = max(float(np.max(np.abs(np.array(v["Y_out_over_Yf"]) - 1))) for v in P.values()); g["G5_pass"] = g["G5"] <= 1e-4
    g["G6_pass"] = all(v["finite"] and v["min_rgb"] >= 0 for v in P.values()) and s1[cand]["finite"] and s1[cand]["min_rgb"] >= 0
    i01 = int(np.argmin(np.abs(np.log10(LS) + 1))); nv = P["neutral"]
    g["G7"] = {"E_out": nv["E_out"][i01], "E_f": nv["E_f"][i01], "ratio": nv["E_out"][i01] / nv["E_f"][i01]}; g["G7_pass"] = g["G7"]["ratio"] >= 0.3
    g["G8"] = s1[cand]; g["G8_pass"] = s1[cand]["lamp_chroma_ratio_median"] >= 0.9 and s1[cand]["sky_chroma_median"] <= 0.01
    g["supported"] = all(g[f"G{i}_pass"] for i in range(1, 9))
    G[cand] = g
for f in ("i.f32", "o.f32"):
    os.remove(f"{C}/{f}")
json.dump(res, open(f"{D}/results.json", "w")); json.dump(G, open(f"{D}/gates.json", "w"), indent=1)
print("cand     | G1 min ratio | G2 worst | G3 max chroma | G4 dhue | G5 dY | G6 | G7 ratio | G8 lamp ratio, sky chroma | supported")
for c, g in G.items():
    print(f"{c:8s} | {g['G1']:.4f} {'P' if g['G1_pass'] else 'F'} | {max(g['G2_worst_increase'].values()):.2e} {'P' if g['G2_pass'] else 'F'} | {g['G3']:.4f} {'P' if g['G3_pass'] else 'F'} | "
          f"{g['G4']:.3f} {'P' if g['G4_pass'] else 'F'} | {g['G5']:.1e} {'P' if g['G5_pass'] else 'F'} | {'P' if g['G6_pass'] else 'F'} | {g['G7']['ratio']:.3f} {'P' if g['G7_pass'] else 'F'} | "
          f"{g['G8']['lamp_chroma_ratio_median']:.3f}, {g['G8']['sky_chroma_median']:.4f} {'P' if g['G8_pass'] else 'F'} | {g['supported']}")
# figures
fig, ax = plt.subplots(1, 3, figsize=(17, 4.5))
for c, st in zip(CAND, ("-", "--", "-.")):
    for n, col in (("neutral", "k"), ("red", "r"), ("warm_lamp", "orange"), ("blue", "b")):
        ax[0 if n != "neutral" else 1].semilogx(LS, res["patches"][f"{c}/uv"][n]["chroma_out"], st, color=col, label=f"{c} {n}")
Lc = np.logspace(-4, 2.3, 200)
for c in CAND: ax[2].semilogx(Lc, CAND[c](Lc), label=f"t(L) {c}")
for a in ax:
    for x in (0.005, 5): a.axvline(x, color="k", ls=":", lw=0.8)
ax[0].set(title="chromatic patches: chroma out (u'v') vs L", xlabel="L [cd/m^2]"); ax[1].set(title="neutral: chroma out = Purkinje tint", xlabel="L [cd/m^2]")
ax[2].set(title="target saturation t(L)", xlabel="L [cd/m^2]"); [a.legend(fontsize=6) for a in ax]
plt.tight_layout(); plt.savefig(f"{D}/curves.png", dpi=100)
k = 0.18 / np.exp(np.mean(np.log(Lpix + 1e-9)))
def aid(x):
    v = np.clip(x * k, 0, 1); v = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055); h, w = v.shape[:2]
    return v[: h // 2 * 2, : w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean((1, 3))
names = ["input", "filament", "pcond_c", "wanat14"]
fig, axs = plt.subplots(len(names), 1, figsize=(10, 2.4 * len(names)))
for a, n in zip(axs, names):
    a.imshow(aid(keep[n])); a.axis("off")
    extra = "" if n in ("input", "filament") else f": sky chroma {s1[n]['sky_chroma_median']:.4f}, lamp chroma kept {s1[n]['lamp_chroma_ratio_median']:.3f}"
    a.set_title({"input": "S1 input [aid]", "filament": "Filament-derived Cao/Kirk kernel, a = 1, kappa = 3 [aid]"}.get(n, f"kernel + chroma stage {n} [aid]{extra}"), fontsize=8, loc="left")
fig.suptitle("[aid] = VIEWING AID (not part of any stage): the INPUT's log-average key 0.18 applied to every panel, clip, sRGB", fontsize=9)
plt.tight_layout(rect=[0, 0, 1, 0.98]); plt.savefig(f"{D}/sheet_S1.png", dpi=100)
