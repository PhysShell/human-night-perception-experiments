#!/usr/bin/env python3
"""D1-B3 kappa sweep, exactly as d1/filament_b3/PREREG.md (committed before this ran).
Kernel: Filament scotopicAdaptation() verbatim (d1/filament/.cache/scotopic, d1/filament/setup.sh), a = 1,
input v = kappa * L_rgb (linear Rec.709, cd/m^2).
  tracks/temporal-glare-2009/py.sh d1/filament_b3/sweep.py -> results.json, gates.json, curves.png
"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
D = "d1/filament_b3"; C = f"{D}/.cache"; os.makedirs(C, exist_ok=True); BIN = "d1/filament/.cache/scotopic"
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WU = np.array([0.1978, 0.4683])
KAPPAS = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100]
LS = np.logspace(-4, 2, 61)
PATCH = {"neutral": [1, 1, 1], "red": [1, 0, 0], "green": [0, 1, 0], "blue": [0, 0, 1], "cyan": [0, 1, 1], "warm_lamp": [1, 0.55, 0.2], "yellow": [1, 1, 0]}


def kern(rgb, a=1.0):
    rgb = np.ascontiguousarray(rgb, np.float32).reshape(-1, 3); rgb.tofile(f"{C}/i.f32")
    subprocess.run([BIN, f"{C}/i.f32", f"{C}/o.f32", str(len(rgb)), repr(a)], check=True)
    return np.fromfile(f"{C}/o.f32", np.float32).reshape(-1, 3).astype(np.float64)


def uvY(rgb):
    X = np.maximum(rgb, 0) @ M709.T; s = X[..., 0] + 15 * X[..., 1] + 3 * X[..., 2] + 1e-30
    return np.stack([4 * X[..., 0] / s, 9 * X[..., 1] / s], -1), X[..., 1]


def luv(uv, Y, Yn):
    t = Y / Yn; Ls = np.where(t > (6 / 29) ** 3, 116 * np.cbrt(t) - 16, (29 / 3) ** 3 * t)
    return np.stack([Ls, 13 * Ls * (uv[..., 0] - WU[0]), 13 * Ls * (uv[..., 1] - WU[1])], -1)


def at(L, x, Lq):
    return float(np.interp(np.log10(Lq), np.log10(L), x))


def crossing(L, E, frac, Eplat):
    """lowest-to-highest L where E first falls below frac*Eplat (log interpolation); None if never"""
    t = frac * Eplat
    for i in range(1, len(L)):
        if E[i - 1] >= t > E[i]:
            f = (E[i - 1] - t) / (E[i - 1] - E[i]); return float(10 ** (np.log10(L[i - 1]) + f * (np.log10(L[i]) - np.log10(L[i - 1]))))
    return None


res = {"kernel": "Filament-derived Cao/Kirk kernel (scotopicAdaptation, filament ef1a133d, verbatim), a = 1, v = kappa * L",
       "prereg": "d1/filament_b3/PREREG.md", "kappas": KAPPAS, "L": LS.tolist(), "curves": {}}
for k in KAPPAS:
    res["curves"][str(k)] = {}
    for name, c in PATCH.items():
        c = np.array(c, float); ins = np.array([c / (M709 @ c)[1] * L for L in LS])
        out = kern(ins * k) / k
        uv0, Y0 = uvY(ins); uv1, Y1 = uvY(out); E = np.hypot(*(uv1 - uv0).T)
        d0, d1 = uv0 - WU, uv1 - WU
        dh = (np.degrees(np.arctan2(d1[:, 1], d1[:, 0]) - np.arctan2(d0[:, 1], d0[:, 0])) + 180) % 360 - 180
        dE = np.linalg.norm(luv(uv1, Y1, Y0) - luv(uv0, Y0, Y0), axis=-1)
        res["curves"][str(k)][name] = {"E": E.tolist(), "Y_ratio": (Y1 / Y0).tolist(), "dhue": dh.tolist(), "chroma_out": np.hypot(*d1.T).tolist(),
                                       "dE_uv": dE.tolist(), "rod_increment": (np.linalg.norm(out - ins, axis=1) / np.linalg.norm(ins, axis=1)).tolist(),
                                       "finite": bool(np.isfinite(out).all())}
# S1 for G5
img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)
m = dict(np.load("d0/work/inputs/masks/S1.npz")); H, W = img.shape[:2]
uv0, _ = uvY(img.reshape(-1, 3)); s1 = {}
for k in KAPPAS:
    out = kern(img.reshape(-1, 3) * k) / k; uv1, _ = uvY(out); E = np.hypot(*(uv1 - uv0).T).reshape(H, W)
    s1[str(k)] = {"E_sky_median": float(np.median(E[m["sky"]])), "E_lamp_median": float(np.median(E[m["lamp"]])),
                  "E_ground_median": float(np.median(E[m["ground"]]))}
res["S1"] = s1
# gates
G = {}
for k in KAPPAS:
    cv = res["curves"][str(k)]; g = {}
    g["G1"] = {n: {"E5": at(LS, v["E"], 5), "E0.005": at(LS, v["E"], 0.005), "ratio": at(LS, v["E"], 5) / max(at(LS, v["E"], 0.005), 1e-30)} for n, v in cv.items()}
    g["G1_pass"] = all(x["ratio"] <= 0.10 for x in g["G1"].values())
    En = np.array(cv["neutral"]["E"]); Ep = En[0]
    L50, L10, L90 = crossing(LS, En, .5, Ep), crossing(LS, En, .1, Ep), crossing(LS, En, .9, Ep)
    width = np.log10(L10 / L90) if (L10 and L90) else None
    g["G2"] = {"L50": L50, "L10": L10, "L90": L90, "width_decades": width}
    g["G2_pass"] = bool(L50 is not None and 0.005 <= L50 <= 5 and width is not None and width >= 1)
    g["G3"] = {n: [at(LS, v["E"], q) for q in (0.005, 0.05, 0.5, 5)] for n, v in cv.items()}
    g["G3_pass"] = all(a > b > c > d for a, b, c, d in g["G3"].values())
    g["G4"] = {"lamp_E200": at(LS, cv["warm_lamp"]["E"], 200) if False else float(np.interp(np.log10(200), np.log10(LS), cv["warm_lamp"]["E"], right=np.nan)),
               "neutral_E0.01": at(LS, cv["neutral"]["E"], 0.01)}
    # 200 cd/m^2 lies outside the 1e-4..1e2 grid: evaluate the lamp patch there directly
    c = np.array(PATCH["warm_lamp"], float); lin = c / (M709 @ c)[1] * 200
    o = kern(lin[None] * k) / k; e200 = float(np.hypot(*(uvY(o)[0][0] - uvY(lin[None])[0][0])))
    g["G4"]["lamp_E200"] = e200; g["G4"]["ratio"] = e200 / max(g["G4"]["neutral_E0.01"], 1e-30)
    g["G4_pass"] = g["G4"]["ratio"] <= 0.10
    g["G5"] = s1[str(k)] | {"ratio": s1[str(k)]["E_lamp_median"] / max(s1[str(k)]["E_sky_median"], 1e-30)}
    g["G5_pass"] = g["G5"]["ratio"] <= 0.25
    g["finite"] = all(v["finite"] for v in cv.values())
    g["admissible"] = all(g[f"G{i}_pass"] for i in range(1, 6)) and g["finite"]
    G[str(k)] = g
for f in ("i.f32", "o.f32"):
    os.remove(f"{C}/{f}")
json.dump(res, open(f"{D}/results.json", "w")); json.dump(G, open(f"{D}/gates.json", "w"), indent=1)
print("kappa | G1 worst E(5)/E(.005) | G2 L50 width | G3 | G4 ratio | G5 ratio | admissible")
for k in KAPPAS:
    g = G[str(k)]; w = max(x["ratio"] for x in g["G1"].values())
    print(f"{k:6g} | {w:.3f} {'P' if g['G1_pass'] else 'F'} | {g['G2']['L50'] and round(g['G2']['L50'],4)} {g['G2']['width_decades'] and round(g['G2']['width_decades'],2)} {'P' if g['G2_pass'] else 'F'} | "
          f"{'P' if g['G3_pass'] else 'F'} | {g['G4']['ratio']:.3f} {'P' if g['G4_pass'] else 'F'} | {g['G5']['ratio']:.3f} {'P' if g['G5_pass'] else 'F'} | {g['admissible']}")
# figure
fig, ax = plt.subplots(1, 3, figsize=(17, 4.5))
for k in KAPPAS:
    ax[0].semilogx(LS, res["curves"][str(k)]["neutral"]["E"], label=f"kappa {k:g}")
for n in PATCH:
    ax[1].semilogx(LS, res["curves"]["1"][n]["E"], label=n)
    ax[2].semilogx(LS, res["curves"]["1"][n]["Y_ratio"], label=n)
for a in ax:
    for x in (0.005, 5): a.axvline(x, color="k", ls=":", lw=0.8)
ax[0].set(title="neutral |delta u'v'| vs L, per kappa (a = 1)\ndotted: CIE mesopic range 0.005-5 cd/m^2 (envelope only)", xlabel="patch luminance [cd/m^2]", ylabel="E = |delta u'v'|")
ax[1].set(title="kappa = 1: E per patch", xlabel="patch luminance [cd/m^2]"); ax[2].set(title="kappa = 1: Y out / Y in per patch", xlabel="patch luminance [cd/m^2]")
ax[0].legend(fontsize=6); ax[1].legend(fontsize=6); ax[2].legend(fontsize=6)
plt.tight_layout(); plt.savefig(f"{D}/curves.png", dpi=100)
