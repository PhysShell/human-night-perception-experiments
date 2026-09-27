#!/usr/bin/env python3
"""D2-B2 cheap falsifier, exactly as d2/b2/PREREG.md (committed before this code). Frozen B code only (called, not
edited); the kernel binary is also run with nightAdaptation = 0 (its rod term off) as the decisive control.
  tracks/temporal-glare-2009/py.sh d2/b2/run.py -> d2/b2/results.json, d2/b2/paths.png"""
import json, os, subprocess, sys
import numpy as np, OpenImageIO as oiio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])          # frozen B: filament(), stage(), uv(), chroma(), hue(), M709, WU
t = lambda L: L / (L + 0.108)
OUT = "d2/b2"; TMP = f"{OUT}/.cache"; os.makedirs(TMP, exist_ok=True)
VIS, ROT = 0.002, -15.5                                           # B4-G4 visibility floor; half the hero's -31 deg


def kernel(rgb, na):
    """The frozen Filament kernel binary, f = scotopic(kappa*rgb, na)/kappa; na = 1 is exactly filament()."""
    a = np.ascontiguousarray(rgb * KAPPA, np.float32).reshape(-1, 3); a.tofile(f"{TMP}/i.f32")
    subprocess.run([BIN, f"{TMP}/i.f32", f"{TMP}/o.f32", str(len(a)), str(na)], check=True)
    return np.fromfile(f"{TMP}/o.f32", np.float32).reshape(-1, 3).astype(np.float64) / KAPPA


def planck(T):
    x = -0.2661239e9 / T ** 3 - 0.2343589e6 / T ** 2 + 0.8776956e3 / T + 0.179910
    y = (-1.1063814 * x ** 3 - 1.34811020 * x ** 2 + 2.18555832 * x - 0.20219683) if T < 2222 else \
        (-0.9549476 * x ** 3 - 1.37418593 * x ** 2 + 2.09137015 * x - 0.16748867)
    X, Z = x / y, (1 - x - y) / y
    rgb = np.linalg.solve(M709, [X, 1.0, Z]); return rgb / (M709[1] @ rgb)


def dh(a, b): return (a - b + 180) % 360 - 180


def B(rgb, L, na):
    f = kernel(rgb, na); return f, stage(f, L, t(L), "uv")


ver = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True)
res = {"prereg": "d2/b2/PREREG.md", "verify_manifest": {"rc": ver.returncode, "out": ver.stdout}, "warm": {}}
WARM = {f"planck_{T}K": planck(T) for T in (2200, 2700, 3000, 3500)}
WARM.update({"F1_warm_lamp": np.array([1, 0.55, 0.2]), "orange": np.array([1, 0.5, 0.0]), "yellow": np.array([1, 1, 0.0])})
LS = np.append(np.logspace(-4, 2, 61), 200.0)
f_, ax = plt.subplots(1, 2, figsize=(15, 7))
for name, c in WARM.items():
    c = c / (M709[1] @ c); rgb = LS[:, None] * c[None, :]
    h_in = hue(rgb)[0]; row = {"input_hue_deg": float(h_in), "input_chroma": float(chroma(rgb)[0]), "L": LS.tolist()}
    for na in (1, 0):
        f, b = B(rgb, LS, na); cb, hb, hf = chroma(b), hue(b), hue(f); d = dh(hb, h_in)
        vis = cb >= VIS
        row[f"na{na}"] = {"chroma_B": cb.tolist(), "hue_B": hb.tolist(), "hue_f": hf.tolist(),
                          "min_dhue_visible_deg": float(d[vis].min()) if vis.any() else None,
                          "L_at_min": float(LS[vis][np.argmin(d[vis])]) if vis.any() else None,
                          "through_neutral": bool(any((cb[i] < VIS) and (abs(dh(hb[i + 1], hb[i - 1])) > 90) for i in range(1, len(LS) - 1)))}
        uvb = uv(b)
        ax[1 - na].plot(uvb[:, 0], uvb[:, 1], "-", lw=1.2, label=name)
    res["warm"][name] = row
for a_, ttl in zip(ax, ("full B (rod term ON, nightAdaptation = 1)", "same stage, rod term OFF (nightAdaptation = 0)")):
    a_.plot(*WU, "k+", ms=14); a_.set_title(ttl, fontsize=10); a_.set_xlabel("u'"); a_.set_ylabel("v'"); a_.set_aspect("equal")
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(f"{OUT}/paths.png", dpi=80)
# hero pool flank (same region and mask as the N1 diagnosis) and F1 warm_lamp patches
sys.path.insert(0, "n1"); from cam import project as cam_project
phys = oiio.ImageBuf("n1/work/hero_cdm2.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)
disp = oiio.ImageBuf("n1/renders/final/hero.png").get_pixels(oiio.FLOAT)[..., :3]
cx, cy = cam_project((4.5, 43, 0)); sl = (slice(int(cy) - 60, int(cy) + 60), slice(int(cx) - 330, int(cx) + 150))
lin = np.where(disp <= 0.04045, disp / 12.92, ((disp + 0.055) / 1.055) ** 2.4)
m = ((lin @ M709[1]) * 100)[sl]; m = (m > 5) & (m < 60)
px = phys[sl][m]; L = px @ M709[1]; h_in = hue(px)
hero = {"n_px": int(m.sum()), "L_cdm2_p5_p50_p95": np.percentile(L, [5, 50, 95]).tolist(), "input_hue_median": float(np.median(h_in)),
        "input_chroma_median": float(np.median(chroma(px)))}
for na in (1, 0):
    f, b = B(px, L, na)
    hero[f"na{na}"] = {"chroma_B_median": float(np.median(chroma(b))), "hue_B_median": float(np.median(hue(b))),
                       "dhue_median_deg": float(np.median(dh(hue(b), h_in)))}
res["hero_pool_flank"] = hero
f1 = oiio.ImageBuf("d1/pipeline/.cache/F1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)
lay = [p for p in json.load(open("d1/pipeline/.cache/F1_layout.json")) if p["colour"] == "warm_lamp"]; f1r = []
for p in lay:
    q = f1[p["y0"] + 4:p["y0"] + p["size"] - 4, p["x0"] + 4:p["x0"] + p["size"] - 4].reshape(-1, 3).mean(0)[None, :]; Lq = q @ M709[1]
    r_ = {"L": float(Lq[0])}
    for na in (1, 0):
        f, b = B(q, Lq, na); r_[f"na{na}"] = {"chroma_B": float(chroma(b)[0]), "dhue_deg": float(dh(hue(b), hue(q))[0])}
    f1r.append(r_)
res["F1_warm_lamp"] = f1r
# necessary conditions
w = res["warm"]
N1 = all((v["na1"]["min_dhue_visible_deg"] is not None) and v["na1"]["min_dhue_visible_deg"] <= ROT for v in w.values())
N2 = hero["na1"]["dhue_median_deg"] <= ROT
rot_off = {k: v["na0"]["min_dhue_visible_deg"] for k, v in w.items()}
N3 = any((x is not None) and x <= ROT for x in rot_off.values()) or hero["na0"]["dhue_median_deg"] <= ROT
res["necessary"] = {"N1_systematic": N1, "N2_inside_B": N2, "N3_not_rod_term": N3,
                    "min_dhue_rod_on": {k: v["na1"]["min_dhue_visible_deg"] for k, v in w.items()}, "min_dhue_rod_off": rot_off}
res["verdict"] = "N1-N3 PASS: a non-model rotation exists (one correction may be pre-registered)" if (N1 and N2 and N3) else \
    "KILL: " + ", ".join(n for n, ok in (("N1", N1), ("N2", N2), ("N3", N3)) if not ok) + " failed"
json.dump(res, open(f"{OUT}/results.json", "w"), indent=1, default=float)
print(json.dumps({k: res[k] for k in ("necessary", "hero_pool_flank", "verdict")}, indent=1, default=float))
print("F1", [(round(r_["L"], 4), round(r_["na1"]["dhue_deg"], 1), round(r_["na0"]["dhue_deg"], 1)) for r_ in f1r])
print("through_neutral rod ON:", {k: v["na1"]["through_neutral"] for k, v in w.items()})
