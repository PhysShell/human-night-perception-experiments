#!/usr/bin/env python3
"""B1.0 oracle validation: three independent reference PSFs, each reduced to ONE canonical package
(radial PSF [sr^-1], s = theta^2 PSF [deg^2 sr^-1], encircled energy, band energy, captured energy,
normalisation, support, sampling, age, pupil, pigmentation, wavelength). No fitting, no combination.

  O1  ISETCam wavefront toolbox, Thibos mean virtual eye, 6 mm, 550 nm, on its own PSF grid
      (b1/o1_iset_wvf.m): THIBOS_NATIVE, ZERO_DEFOCUS_550, BEST_FOCUS_550. ISET normalises the PSF to unit
      sum over its own square support.
  O2  CIE 135/1 Standard Glare Observer, spatial GSF, standard + age factor, evaluated analytically.
      CIE_FORMULA_RAW (as published, not renormalised) and CIE_KERNEL_FINITE_NORMALIZED (renormalised to
      unit energy on a declared disc). Never hdrvdp_otf_cie99 (b0 erratum).
  O3  IJspeert, van den Berg & Spekreijse 1993 via ISETCam human/ijspeert.m (b1/o3_ijspeert.m), analytic.

Angles: the analytic oracles are integrated on the sphere (dOmega = 2 pi sin(theta) dtheta); the gridded O1
uses the small-angle plane (sample solid angle = (arcmin/sample)^2), used well inside its +-15 deg support.
  tracks/temporal-glare-2009/py.sh b1/oracles.py -> b1/results/oracles.json, b1/results/*.csv, oracles.png
"""
import json, math, os
import numpy as np
from scipy.ndimage import map_coordinates

os.makedirs("b1/results", exist_ok=True)
ARC = math.pi / 180 / 60                          # rad per arcmin
TH = np.geomspace(0.1, 600, 400)                  # arcmin, 0.1' .. 10 deg
ZONES = [("CORE", 0, 1), ("NEAR_WINGS", 1, 10), ("MID", 10, 30), ("STRAYLIGHT", 30, 180), ("FAR", 180, 600)]
AGE, P_CIE, M_IJ = 24.0, 0.5, 0.106


# ---------------------------------------------------------------- O1: gridded ISET PSFs
def load_o1(eye, n, plane):
    tag = f"b1/out/o1_{eye}_N{n}_P{plane}"
    with open(tag + ".raw", "rb") as f:
        h, w, c, _ = np.fromfile(f, "<i4", 4); psf = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(float)
    return psf, json.load(open(tag + ".json"))


def o1_package(eye, n, plane):
    psf, meta = load_o1(eye, n, plane)
    d = meta["arcmin_per_sample"]; om = (d * ARC) ** 2
    cy, cx = np.unravel_index(psf.argmax(), psf.shape)
    # the wvf PSF is centred on its grid centre; use the grid centre, not the (aberrated) peak
    cy = cx = (psf.shape[0] - 1) / 2 if psf.shape[0] % 2 else psf.shape[0] / 2
    sup = meta["support_half_arcmin"]
    th = TH[TH <= sup * 0.98]
    ang = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    prof = np.array([map_coordinates(psf, [cy + t / d * np.sin(ang), cx + t / d * np.cos(ang)], order=1).mean() for t in th]) / om
    yy, xx = np.indices(psf.shape); r = np.hypot(yy - cy, xx - cx) * d
    o = np.argsort(r.ravel()); rs, cs = r.ravel()[o], np.cumsum(psf.ravel()[o])
    ee = np.interp(th, rs, cs)
    return th, prof, ee, {"captured_energy_on_support": float(psf.sum()), "support_half_arcmin": sup,
                          "arcmin_per_sample": d, "grid": f"{n} x {n}, pupil plane {plane} mm", "c4_um": meta["c4_um"],
                          "normalisation": "ISET: unit sum over its own square support (energy beyond the support is not represented)",
                          "wavelength_nm": 550, "pupil_mm": 6, "age": "not modelled (Thibos virtual eyes)",
                          "pigmentation": "not modelled"}


# ---------------------------------------------------------------- O2: CIE 135/1
def cie_raw(t_deg, age=AGE, p=P_CIE):
    t, a4 = np.asarray(t_deg, float), (age / 70.0) ** 4
    return ((1 - 0.08 * a4) * (9.2e6 / (1 + (t / 0.0046) ** 2) ** 1.5 + 1.5e5 / (1 + (t / 0.045) ** 2) ** 1.5)
            + (1 + 1.6 * a4) * ((400 / (1 + (t / 0.1) ** 2) + 3e-8 * t ** 2)
                                + p * (1300 / (1 + (t / 0.1) ** 2) ** 1.5 + 0.8 / (1 + (t / 0.1) ** 2) ** 0.5))
            + 2.5e-3 * p)


def sphere_ee(f_sr, t_max_deg, n):
    """cumulative integral of f over the sphere cap, on a grid dense near 0 (n points)"""
    t = np.concatenate([[0.0], np.geomspace(1e-7, t_max_deg, n)])
    tr = np.radians(t); g = f_sr(t) * 2 * np.pi * np.sin(tr)
    c = np.concatenate([[0], np.cumsum(0.5 * (g[1:] + g[:-1]) * np.diff(tr))])
    return t, c


# ---------------------------------------------------------------- O3: IJspeert
ij = np.loadtxt("b1/out/o3_ijspeert.csv", delimiter=",", skiprows=1)
def ij_psf(t_deg, col=1):
    return np.interp(np.radians(np.asarray(t_deg, float)), ij[:, 0], ij[:, col])


def analytic_package(f, label, meta, t_max=90.0):
    t, c = sphere_ee(f, t_max, 400001)
    t2, c2 = sphere_ee(f, t_max, 100001)                # quadrature convergence
    th_deg = TH / 60
    return (TH, f(th_deg), np.interp(th_deg, t, c),
            {**meta, "integral_to_90deg": float(c[-1]), "integral_to_10deg": float(np.interp(10, t, c)),
             "quadrature_check_rel_diff_EE(1')_(1e5_vs_4e5_pts)": float(abs(np.interp(1 / 60, t2, c2) / np.interp(1 / 60, t, c) - 1)),
             "support": "analytic, 0 .. 90 deg (sphere)"})


pk = {}
for eye, lab in (("native", "O1 ISET THIBOS_NATIVE"), ("zero", "O1 ISET ZERO_DEFOCUS_550"), ("best", "O1 ISET BEST_FOCUS_550")):
    # fine grid (+-117') for theta <= 30', the +-15 deg grid beyond. The FFT PSF is periodic: near the edge of a
    # grid, the wings of the neighbouring periods fold in (the +-117' grids are 44 % high at 100'), so each grid
    # is used only well inside its support. Overlap 10-30' is the convergence check.
    XO = 30.0
    tf, pf, ef, mf = o1_package(eye, 4001 if eye == "zero" else 2001, 32.424 if eye == "zero" else 16.212)
    tc, pc, ec, mc = o1_package(eye, 7801, 8.106)
    use_f = tf <= XO
    th = np.concatenate([tf[use_f], tc[tc > XO]]); ps = np.concatenate([pf[use_f], pc[tc > XO]])
    ee = np.concatenate([ef[use_f], np.interp(tc[tc > XO], tc, ec) - np.interp(XO, tc, ec) + np.interp(XO, tf, ef)])
    ov = (tf >= 10) & (tf <= XO)
    pk[lab] = (th, ps, ee, {**mc, "grids": {"fine": mf["grid"] + f", {mf['arcmin_per_sample']:.4f}'/sample, +-{mf['support_half_arcmin']:.0f}'",
                                            "coarse": mc["grid"] + f", {mc['arcmin_per_sample']:.4f}'/sample, +-{mc['support_half_arcmin']:.0f}'"},
                                 "profile_assembly": "same model on two sampling grids: fine for theta <= 30', +-15 deg grid beyond",
                                 "overlap_10_30arcmin_max_rel_diff_fine_vs_coarse": float(np.max(np.abs(np.interp(tf[ov], tc, pc) / pf[ov] - 1)))})
pk["O2 CIE_FORMULA_RAW"] = analytic_package(lambda t: cie_raw(t), "raw", {
    "age": AGE, "pigmentation_p": P_CIE, "pupil_mm": "none in the model", "wavelength_nm": "none (broadband)",
    "normalisation": "none: the published formula as is (sr^-1)", "age_factor_sign": "+ (standard observer)"})
t10, c10 = sphere_ee(lambda t: cie_raw(t), 10.0, 400001)
k10 = 1 / c10[-1]
pk["O2 CIE_KERNEL_FINITE_NORMALIZED (10 deg disc)"] = analytic_package(lambda t: cie_raw(t) * k10 * (np.asarray(t) <= 10), "fin", {
    "age": AGE, "pigmentation_p": P_CIE, "normalisation": f"renormalised to unit energy on the 10 deg disc (factor {k10:.5f}); zero beyond",
    "support": "disc, radius 10 deg"}, t_max=10.0)
pk["O3 IJSPEERT (m 0.106, 6 mm)"] = analytic_package(lambda t: ij_psf(t, 1), "ij", {
    "age": AGE, "pupil_mm": 6, "pigmentation_m": 0.106, "wavelength_nm": "none (not wavelength-dependent)",
    "normalisation": "as returned by ijspeert.m (the model's own)", "implementation": "ISETCam human/ijspeert.m (MIT), NATIVE"})
pk["O3 IJSPEERT (m 0.142, 6 mm) [sensitivity]"] = analytic_package(lambda t: ij_psf(t, 2), "ij2", {
    "age": AGE, "pupil_mm": 6, "pigmentation_m": 0.142, "normalisation": "as returned"})
pk["O3 IJSPEERT (m 0.106, 3 mm) [sensitivity]"] = analytic_package(lambda t: ij_psf(t, 3), "ij3", {
    "age": AGE, "pupil_mm": 3, "pigmentation_m": 0.106, "normalisation": "as returned"})

# ---------------------------------------------------------------- canonical packages, zones, crossover
out = {"conventions": {"theta": "arcmin unless stated", "PSF": "sr^-1", "s": "theta^2 * PSF with theta in deg: deg^2 sr^-1",
                       "EE": "fraction of the oracle's own total (its normalisation, see each package)",
                       "zones_arcmin": {z: [a, b] for z, a, b in ZONES}},
       "packages": {}, "zones": {}, "crossover": {}}
for lab, (th, ps, ee, meta) in pk.items():
    s = (th / 60) ** 2 * ps
    np.savetxt(f"b1/results/{lab.split(' (')[0].replace(' ', '_')}{'_' + lab.split('(')[1].split(')')[0].replace(' ', '').replace(',', '_') if '(' in lab else ''}.csv",
               np.c_[th, ps, s, ee], delimiter=",", header="theta_arcmin,psf_sr-1,s_deg2_sr-1,encircled_energy", comments="")
    out["packages"][lab] = meta
    zt = {}
    for z, a, b in ZONES:
        if th.max() < b * 0.98:
            zt[z] = "beyond support"; continue
        mid = 0.5 if a == 0 else math.sqrt(a * b)
        e_hi = float(np.interp(b, th, ee)); e_lo = float(np.interp(a, th, ee)) if a > 0 else 0.0
        zt[z] = {"band_energy": e_hi - e_lo, "cumulative_to_outer": e_hi,
                 "psf_at_mid_sr-1": float(np.interp(mid, th, ps)), "s_at_mid": float((mid / 60) ** 2 * np.interp(mid, th, ps)), "mid_arcmin": mid}
    out["zones"][lab] = zt

cie = lambda t: cie_raw(np.asarray(t) / 60)
ijf = lambda t: ij_psf(np.asarray(t) / 60, 1)
for lab in ("O1 ISET THIBOS_NATIVE", "O1 ISET ZERO_DEFOCUS_550", "O1 ISET BEST_FOCUS_550"):
    th, ps = pk[lab][0], pk[lab][1]
    for nm, ref in (("CIE_RAW", cie), ("IJSPEERT", ijf)):
        rt = ps / ref(th)
        cross = [float(th[i]) for i in range(1, len(th)) if (rt[i - 1] - 1) * (rt[i] - 1) < 0]
        out["crossover"][f"{lab} / {nm}"] = {
            "ratio_at_arcmin": {a: float(np.interp(a, th, rt)) for a in (0.3, 1, 3, 10, 30, 100, 300)},
            "ratio_equals_1_at_arcmin": cross,
            "ratio_below_0.1_from_arcmin": float(th[np.argmax(rt < 0.1)]) if (rt < 0.1).any() else None}
rt = ijf(TH) / cie(TH)
out["crossover"]["O3 IJSPEERT / CIE_RAW"] = {"ratio_at_arcmin": {a: float(np.interp(a, TH, rt)) for a in (0.3, 1, 3, 10, 30, 100, 300, 600)}}

# ISET numerical convergence across grids (zero-defocus eye)
conv = {}
ref = o1_package("zero", 4001, 32.424)
for n, pl in ((201, 16.212), (2001, 16.212), (4001, 16.212), (5201, 8.106), (7801, 8.106)):
    t, p, e, m = o1_package("zero", n, pl)
    conv[f"N{n}_P{pl} ({m['arcmin_per_sample']:.4f}'/sample, +-{m['support_half_arcmin']:.0f}')"] = {
        a: float(np.interp(a, t, p) / np.interp(a, ref[0], ref[1]) - 1) for a in (0.3, 1, 3, 10, 30) if a <= t.max()}
conv["reference_core"] = "N4001_P32.424 (0.0583'/sample, +-117'); relative PSF differences at radius (arcmin), core <= 30'"
t5, p5, _, _ = o1_package("zero", 5201, 8.106); t7, p7, _, _ = o1_package("zero", 7801, 8.106)
conv["wings_+-10deg_vs_+-15deg_grid (same sampling)"] = {a: float(np.interp(a, t5, p5) / np.interp(a, t7, p7) - 1) for a in (30, 100, 200, 300, 450, 590)}
conv["wings_note"] = ("periodic FFT PSF: wings of neighbouring periods fold in near the edge of each grid; "
                      "the +-15 deg grid is used for 30'..600' and its own fold-in at 600' is bounded by the +-10 vs +-15 comparison")
t201, p201, _, _ = o1_package("native", 201, 16.212)
conv["B0_default_grid_note"] = ("ISET oiCreate('wvf human') default: 201 samples on a 16.212 mm pupil plane -> PSF support +-11.7'. "
                                "B0's ISET kernels (via oiCompute) therefore had no wavefront PSF beyond ~12'.")
out["iset_grid_convergence"] = conv
# B0's ISET kernel (oiCompute path, ISET default wvf grid: 201 samples -> +-11.7' PSF support) vs O1 on its own grid
with open("b0/out/kernels/iset_kernel_550z.raw", "rb") as f:
    h, w, c, _ = np.fromfile(f, "<i4", 4); K = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(float)
K = np.maximum(K - np.median(K[:5, :5]), 0); K /= K.sum(); dk = 60 / 292.0
ky, kx = np.unravel_index(K.argmax(), K.shape); ang = np.linspace(0, 2 * np.pi, 720, endpoint=False)
th_z, ps_z = pk["O1 ISET ZERO_DEFOCUS_550"][0], pk["O1 ISET ZERO_DEFOCUS_550"][1]
out["b0_kernel_vs_O1"] = {a: {"b0_oiCompute_sr-1": float(map_coordinates(K, [ky + a / dk * np.sin(ang), kx + a / dk * np.cos(ang)], order=1).mean() / (dk * ARC) ** 2),
                              "O1_wvf_sr-1": float(np.interp(a, th_z, ps_z))} for a in (1, 3, 10, 18, 30, 60)}
json.dump(out, open("b1/results/oracles.json", "w"), indent=1)

# ---------------------------------------------------------------- plot
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(18, 5.2))
sty = {"O1 ISET THIBOS_NATIVE": "b-", "O1 ISET ZERO_DEFOCUS_550": "c-", "O1 ISET BEST_FOCUS_550": "c:",
       "O2 CIE_FORMULA_RAW": "k-", "O3 IJSPEERT (m 0.106, 6 mm)": "r-", "O3 IJSPEERT (m 0.106, 3 mm) [sensitivity]": "r:"}
for lab, st in sty.items():
    th, ps = pk[lab][0], pk[lab][1]
    ax[0].loglog(th, ps, st, label=lab); ax[1].loglog(th, (th / 60) ** 2 * ps, st, label=lab)
for a in (1, 10, 30, 180): [x.axvline(a, color="grey", lw=0.5, ls="--") for x in ax]
for x in ax: x.axvspan(300, 600, color="c", alpha=0.08)   # O1 not converged (FFT fold-in >= 10 %)
for lab, st in (("O1 ISET THIBOS_NATIVE", "b-"), ("O1 ISET ZERO_DEFOCUS_550", "c-")):
    th, ps = pk[lab][0], pk[lab][1]
    ax[2].loglog(th, ps / cie(th), st, label=f"{lab} / CIE"); ax[2].loglog(th, ps / ijf(th), st.replace("-", "--"), label=f"{lab} / IJspeert")
ax[2].loglog(TH, ijf(TH) / cie(TH), "r-", label="IJspeert / CIE")
ax[2].axhline(1, color="k", lw=0.8)
ax[0].set(ylabel="PSF [sr$^{-1}$]", title="radial PSF (zones: CORE | NEAR | MID | STRAYLIGHT | FAR)\nshaded: O1 ISET wing not converged (>= 10 % fold-in)")
ax[1].set(ylabel=r"s = $\theta^2$ PSF [deg$^2$ sr$^{-1}$]", title="straylight parameter", ylim=(1e-2, 1e3))
ax[2].set(ylabel="ratio", title="wavefront core / straylight oracles: crossover", ylim=(1e-4, 1e2))
for x in ax:
    x.set_xlabel("angle [arcmin]  (0.1' .. 10 deg)"); x.set_xlim(0.1, 600); x.grid(True, which="both", lw=0.3); x.legend(fontsize=7)
plt.tight_layout(); plt.savefig("b1/results/oracles.png", dpi=95)
print(json.dumps({k: out[k] for k in ("zones", "crossover", "iset_grid_convergence")}, indent=1, default=float)[:9000])
