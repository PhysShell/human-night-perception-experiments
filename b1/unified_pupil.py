#!/usr/bin/env python3
"""B1.1: one energy-conserving pupil-plane model (mechanism experiment, not an oracle).

    P(x, y) = A(x, y) * exp{ i 2 pi / lambda * [ W_Thibos(x, y) + W_s(x, y) ] }      PSF = |F{P}|^2, unit sum

  * A, W_Thibos: NATIVE ISETCam wavefront toolbox (b1/o1_export_pupil.m), Thibos mean virtual eye, 6 mm,
    550 nm, exported on a 9216^2 grid with 1.3303 um pupil sampling (= Arias 2018's sampling; scatter
    Nyquist 11.8 deg at 550 nm, PSF sample 0.154').
  * W_s: ARIAS_REIMPLEMENTATION of Arias, Ginis & Artal 2018 (Biomed. Opt. Express, PMC6154192), eq. 2-3, from
    the paper (no author code):  W_s(i', j') = sum_ij U_ij R_ij cos(pi (i+1/2) i'/n) cos(pi (j+1/2) j'/n)
    over the pupil's bounding square (n = 4515 samples, side phi = 6.006 mm), R ~ N(0,1),
    U_ij = B f^beta, f = sqrt(f_i^2 + f_j^2), f_i = (i+1/2)/phi [the paper's label, cycles/mm];
    implemented as scipy dctn(U R, type 2) / 4, i.e. the paper's sum literally. B in um of optical path.
    The cosine's true spatial frequency is nu = f/2, scattering to theta = lambda nu.
  * High-pass (declared before fitting): U = 0 for theta(nu) < THETA_HP = 3' so the screen does not add
    low-order aberration on top of the Thibos Zernike terms (sensitivity 1.5' and 6').
Calibration target: CIE 135/1 complete visual spread (O2, + age factor, age 24, p 0.5) over 0.5-8 deg ONLY.
Staged: (1) beta from the shape of the wing (offset-free log residual), (2) B from its level,
(3) energy / EE only as checks. Tolerance declared: log10 RMS <= 0.10 and max |log10| <= 0.20 over 0.5-8 deg.
  tracks/temporal-glare-2009/py.sh b1/unified_pupil.py -> b1/results/b1_1.json, b1_1_*.csv, b1_1.png
"""
import json, math, os, sys, time
import numpy as np
import scipy.fft as sfft

WORK = 4
LAM0 = 550e-6                                     # mm
THETA_HP = float(os.environ.get("B1_THETA_HP", 3.0))   # arcmin
FIT = (30.0, 480.0)                               # arcmin: 0.5 .. 8 deg
TOL_RMS, TOL_MAX = 0.10, 0.20
ARC = math.pi / 180 / 60
sys.path.insert(0, "b1")


def read_raw(p):
    with open(p, "rb") as f:
        h, w, c, _ = np.fromfile(f, "<i4", 4)
        return np.fromfile(f, "<f4").reshape(h, w, c)[..., 0]


class Eye:
    def __init__(self, eye):
        t = f"b1/out/pupil_{eye}_N9216"
        self.meta = json.load(open(t + ".json")); self.N = self.meta["N"]; self.dx = self.meta["dx_mm"]
        self.W = read_raw(t + "_W.raw").astype(np.float64); self.A = read_raw(t + "_A.raw").astype(np.float64)
        self.r0, self.c0 = self.meta["crop_rows"][0] - 1, self.meta["crop_cols"][0] - 1
        self.n = self.W.shape[0]
        self.psfcrop = read_raw(t + "_psfcrop.raw").astype(np.float64)


def screen(n, dx, B, beta, seed, theta_hp=THETA_HP, lam=LAM0):
    phi = n * dx
    fi = (np.arange(n) + 0.5) / phi
    f = np.hypot(fi[:, None], fi[None, :])
    U = B * f ** beta
    U[(f / 2) * lam < theta_hp * ARC] = 0.0                      # high-pass: nu = f/2, theta = lambda nu
    R = np.random.default_rng(seed).standard_normal((n, n))
    return sfft.dctn(U * R, type=2, workers=WORK) / 4.0


def psf_of(eye, Ws=None, lam=LAM0, aperture_mm=None):
    """unit-sum PSF on the full grid; angular sample = lam / (N dx) rad"""
    N = eye.N; P = np.zeros((N, N), np.complex64)
    W = eye.W if Ws is None else eye.W + Ws
    A = eye.A
    if aperture_mm is not None:                                   # smaller pupil: same eye, central part
        yy, xx = np.indices(A.shape); cy = (A.shape[0] - 1) / 2
        A = A * (np.hypot(yy - cy, xx - cy) * eye.dx <= aperture_mm / 2)
    P[eye.r0:eye.r0 + eye.n, eye.c0:eye.c0 + eye.n] = (A * np.exp(-2j * np.pi * W / (lam * 1e3))).astype(np.complex64)   # W in um, lam in mm; ISET sign convention
    F = sfft.fft2(sfft.ifftshift(P), workers=WORK)
    I = sfft.fftshift((F.real ** 2 + F.imag ** 2).astype(np.float64))
    return I / I.sum()


_RIDX = {}
def radial(I, lam=LAM0, dx=None, N=9216):
    """azimuthal mean (sr^-1) and encircled energy at integer-sample radii; angle in arcmin"""
    if N not in _RIDX:
        c = N // 2; y = np.arange(N) - c
        _RIDX[N] = np.rint(np.hypot(y[:, None], y[None, :])).astype(np.int32).ravel()
    idx = _RIDX[N]
    s = np.bincount(idx, I.ravel()); n = np.bincount(idx)
    dth = lam / (N * dx)                                          # rad per sample
    r = np.arange(len(s)) * dth / ARC
    return r, s / np.maximum(n, 1) / dth ** 2, np.cumsum(s), dth / ARC


from oracles_cie import cie_raw  # noqa: E402  (b1/oracles_cie.py: the O2 formula, shared with b1/oracles.py)
TH_FIT = np.geomspace(*FIT, 60)


def fit_err(r, p):
    lr = np.log10(np.interp(TH_FIT, r, p) / cie_raw(TH_FIT / 60))
    return lr


def metrics(r, p, ee, peak, off=None):
    m = {"EE_1arcmin": float(np.interp(1, r, ee)), "EE_10arcmin": float(np.interp(10, r, ee)),
         "EE_30arcmin": float(np.interp(30, r, ee)), "energy_beyond_0.5deg": float(1 - np.interp(30, r, ee)),
         "energy_beyond_8deg_on_support": float(1 - np.interp(480, r, ee)), "peak_fraction_per_sample": float(peak)}
    if off is not None:
        m["Strehl_ratio_on_over_off"] = float(peak / off)
    return m


def ensemble(eye, B, beta, seeds, **kw):
    acc = None; accs = []; peak = 0
    for sd in seeds:
        I = psf_of(eye, screen(eye.n, eye.dx, B, beta, sd, **{k: v for k, v in kw.items() if k == "theta_hp"}),
                   **{k: v for k, v in kw.items() if k in ("lam", "aperture_mm")})
        r, p, ee, _ = radial(I, kw.get("lam", LAM0), eye.dx, eye.N)
        accs.append(p); peak += I.max() / len(seeds)
        acc = I if acc is None else acc + I
        del I
    I = acc / len(seeds)
    r, p, ee, dth = radial(I, kw.get("lam", LAM0), eye.dx, eye.N)
    fwhm = 2 * math.sqrt((I >= 0.5 * I.max()).sum() / math.pi) * dth
    return r, p, ee, peak, np.array(accs), fwhm, I


if __name__ == "__main__":
    t0 = time.time(); out = {"declared": {"fit_range_arcmin": FIT, "theta_hp_arcmin": THETA_HP, "tol_log10_rms": TOL_RMS,
                                          "tol_log10_max": TOL_MAX, "target": "O2 CIE_COMPLETE_VISUAL_SPREAD (CIE 135/1 eq. 8, + age factor), age 24, p 0.5"}}
    Z = Eye("zero")
    # ---- scatter_off: our FFT of ISET's pupil must equal ISET's own PSF
    I0 = psf_of(Z); c = Z.N // 2
    crop = I0[c - 512:c + 513, c - 512:c + 513]
    out["scatter_off_vs_ISET"] = {"max_abs_diff_over_peak": float(np.abs(crop - Z.psfcrop).max() / Z.psfcrop.max()),
                                  "peak_ours": float(I0.max()), "peak_iset": float(Z.meta["psf_peak"])}
    r0_, p0, ee0, dth0 = radial(I0, LAM0, Z.dx, Z.N); peak0 = I0.max()
    fw0 = 2 * math.sqrt((I0 >= 0.5 * peak0).sum() / math.pi) * dth0
    out["THIBOS_ONLY"] = {**metrics(r0_, p0, ee0, peak0), "FWHM_equiv_arcmin": fw0}
    print("scatter_off", out["scatter_off_vs_ISET"], f"{time.time() - t0:.0f}s", flush=True)
    del I0

    # ---- stage 1: beta from the wing SHAPE (offset-free), B only roughly levelled
    def level_B(beta, B, seeds=(1, 2), n_it=5):
        for _ in range(n_it):   # wing ~ B^2 in the weak regime; iterate (the level regime is not weak)
            r, p, *_ = ensemble(Z, B, beta, seeds)
            off = fit_err(r, p).mean(); B *= 10 ** (-off / 2)
        return B, r, p
    shape = {}
    # start in the weak-scatter regime (phase rms ~0.15 rad at beta -1.214, B 0.003 um) and keep U the same at
    # f_ref = 127 /mm (theta ~ 2 deg) when beta changes: B = B0 f_ref^(beta0 - beta). A start at B = 1 um
    # (tens of radians of phase) is outside the B^2 regime and did not converge in the first attempt.
    for beta in (-0.9, -1.0, -1.1, -1.214, -1.3, -1.4, -1.5):
        B, r, p = level_B(beta, 0.003 * 127.0 ** (-1.214 - beta))
        lr = fit_err(r, p); shape[beta] = {"shape_rms_offset_free": float(np.std(lr)), "B_um": B}
        print("beta", beta, shape[beta], f"{time.time() - t0:.0f}s", flush=True)
    out["stage1_beta_shape"] = {str(k): v for k, v in shape.items()}
    bs = sorted(shape); ib = int(np.argmin([shape[b]["shape_rms_offset_free"] for b in bs]))
    if 0 < ib < len(bs) - 1:                                      # parabolic refinement
        x = np.array(bs[ib - 1:ib + 2]); y = np.array([shape[b]["shape_rms_offset_free"] for b in x])
        a = np.polyfit(x, y, 2); beta_star = float(-a[1] / (2 * a[0]))
    else:
        beta_star = float(bs[ib])
    out["beta_star"] = beta_star
    # ---- stage 2: B from the LEVEL (mean log10 ratio over the fit range = 0), 4 seeds
    Bs = shape[bs[ib]]["B_um"]
    for _ in range(5):
        r, p, *_ = ensemble(Z, Bs, beta_star, (1, 2, 3, 4))
        off = fit_err(r, p).mean(); Bs *= 10 ** (-off / 2)
    out["B_star_um"] = Bs
    print("B*", Bs, "beta*", beta_star, f"{time.time() - t0:.0f}s", flush=True)
    # ---- stage 3: final ensemble 16 seeds; convergence 4/8/16
    r, p, ee, peak, accs, fwhm, Iu = ensemble(Z, Bs, beta_star, range(1, 17))
    lr = fit_err(r, p)
    conv = {}
    for k in (4, 8, 16):
        conv[k] = float(np.sqrt(np.mean(np.log10(np.interp(TH_FIT, r, accs[:k].mean(0)) / np.interp(TH_FIT, r, p)) ** 2)))
    spread = np.std(np.log10(np.maximum(accs, 1e-30)), axis=0)
    out["THIBOS_PLUS_ARIAS"] = {**metrics(r, p, ee, peak, peak0), "FWHM_equiv_arcmin": fwhm,
                                "fit_log10_rms": float(np.sqrt(np.mean(lr ** 2))), "fit_log10_max": float(np.abs(lr).max()),
                                "PASS_calibration": bool(np.sqrt(np.mean(lr ** 2)) <= TOL_RMS and np.abs(lr).max() <= TOL_MAX),
                                "seed_convergence_log10_rms_vs_16": conv,
                                "single_seed_log10_sd_at_arcmin": {a: float(np.interp(a, r, spread)) for a in (1, 10, 30, 120, 480)}}
    out["energy_moved"] = {k: out["THIBOS_PLUS_ARIAS"][k] - out["THIBOS_ONLY"][k] for k in ("EE_1arcmin", "EE_10arcmin", "EE_30arcmin", "energy_beyond_0.5deg")}
    TH = np.geomspace(0.1, 600, 300)
    prof = {"THIBOS_ONLY": np.interp(TH, r0_, p0), "THIBOS_PLUS_ARIAS": np.interp(TH, r, p)}
    np.savetxt("b1/results/b1_1_profiles_zero.csv", np.c_[TH, prof["THIBOS_ONLY"], prof["THIBOS_PLUS_ARIAS"], cie_raw(TH / 60)],
               delimiter=",", header="theta_arcmin,THIBOS_ONLY,THIBOS_PLUS_ARIAS,CIE_RAW", comments="")

    # ---- NAIVE_CONVOLUTION_CONTROL: THIBOS_ONLY (x) CIE kernel (finite-normalised on the grid); NOT physically unified
    N = Z.N; y = (np.arange(N) - N // 2) * dth0 / 60          # deg
    K = cie_raw(np.hypot(y[:, None], y[None, :]))
    sub = (np.arange(16) + 0.5) / 16 - 0.5
    for dy in range(-3, 4):
        for dx_ in range(-3, 4):
            yy, xx = np.meshgrid((dy + sub) * dth0 / 60, (dx_ + sub) * dth0 / 60)
            K[N // 2 + dy, N // 2 + dx_] = cie_raw(np.hypot(yy, xx)).mean()
    K /= K.sum()
    I0 = psf_of(Z)
    Ic = sfft.fftshift(sfft.irfft2(sfft.rfft2(sfft.ifftshift(I0), workers=WORK) * sfft.rfft2(sfft.ifftshift(K), workers=WORK), s=I0.shape, workers=WORK))
    Ic = np.maximum(Ic, 0); Ic /= Ic.sum(); del K
    rc, pc, eec, _ = radial(Ic, LAM0, Z.dx, Z.N)
    fwc = 2 * math.sqrt((Ic >= 0.5 * Ic.max()).sum() / math.pi) * dth0
    lrc = fit_err(rc, pc)
    out["NAIVE_CONVOLUTION_CONTROL"] = {**metrics(rc, pc, eec, Ic.max(), peak0), "FWHM_equiv_arcmin": fwc,
                                        "fit_log10_rms_(not_fitted)": float(np.sqrt(np.mean(lrc ** 2))),
                                        "label": "NOT PHYSICALLY UNIFIED: counts CIE's small-angle visual PSF on top of the Thibos core"}
    prof["NAIVE_CONVOLUTION_CONTROL"] = np.interp(TH, rc, pc)
    del Ic, I0
    # divergences between unified and naive, by zone
    Z_ = [("CORE", 0, 1), ("NEAR_WINGS", 1, 10), ("MID", 10, 30), ("STRAYLIGHT", 30, 180), ("FAR", 180, 480)]
    out["unified_vs_naive_band_energy"] = {z: {"unified": float(np.interp(b, r, ee) - (np.interp(a, r, ee) if a else 0)),
                                               "naive": float(np.interp(b, rc, eec) - (np.interp(a, rc, eec) if a else 0)),
                                               "thibos_only": float(np.interp(b, r0_, ee0) - (np.interp(a, r0_, ee0) if a else 0))} for z, a, b in Z_}

    # ---- checks NOT used in the fit
    ext = {}
    # (a) same screen, native Thibos focus: the wings should not care about defocus
    Nn = Eye("native")
    rn, pn, een, pkn, _, fwn, _ = ensemble(Nn, Bs, beta_star, range(1, 9))
    In = psf_of(Nn); pk_off_n = In.max(); rno, pno, eeno, _ = radial(In, LAM0, Nn.dx, Nn.N); del In
    ext["native_eye_same_screen"] = {"wing_log10_diff_vs_zero_at_arcmin": {a: float(np.log10(np.interp(a, rn, pn) / np.interp(a, r, p))) for a in (30, 120, 480)},
                                     **{f"native_{k}": v for k, v in metrics(rn, pn, een, pkn, pk_off_n).items()}}
    prof["NATIVE_PLUS_ARIAS"] = np.interp(TH, rn, pn); del Nn
    # (b) pupil 3 mm with the same screen (Franssen 2007: straylight roughly independent of pupil size)
    r3, p3, *_ = ensemble(Z, Bs, beta_star, range(1, 9), aperture_mm=3.0)
    ext["pupil_3mm_vs_6mm_wing_log10_at_arcmin"] = {a: float(np.log10(np.interp(a, r3, p3) / np.interp(a, r, p))) for a in (30, 60, 120, 240, 480)}
    # (c) wavelength: same OPD screen at 500 and 650 nm (LCA of the core ignored; wings only)
    wl = {}
    for lam_nm in (500, 650):
        rl, pl, *_ = ensemble(Z, Bs, beta_star, range(1, 9), lam=lam_nm * 1e-6)
        wl[lam_nm] = {a: float(np.interp(a, rl, pl)) for a in (30, 360)}
    sl = {a: float(np.interp(a, r, p)) for a in (30, 360)}
    ext["wavelength_log10_s_650_minus_500_at_0.5deg_and_6deg"] = {str(a): float(np.log10(wl[650][a] / wl[500][a])) for a in (30, 360)}
    ext["wavelength_note"] = ("pure OPD screen, first order: PSF ~ lambda^(-4-2 beta) theta^(2 beta), the same at every angle. "
                              "Ginis et al. 2013 (IOVS 54:3702, abstract): at 0.5 deg straylight follows the haemoglobin transmittance "
                              "(fundus, rising beyond 600 nm), at 6 deg it depends less on wavelength. A pupil phase screen cannot "
                              "produce the fundus term.")
    out["checks_not_used_in_fit"] = ext
    # ---- high-pass sensitivity (same B*, beta*)
    hp = {}
    for th in (1.5, 6.0):
        rh, ph, eeh, pkh, *_ = ensemble(Z, Bs, beta_star, range(1, 5), theta_hp=th)
        hp[th] = {**metrics(rh, ph, eeh, pkh, peak0), "wing_log10_rms_vs_CIE": float(np.sqrt(np.mean(fit_err(rh, ph) ** 2)))}
    out["theta_hp_sensitivity"] = {str(k): v for k, v in hp.items()}
    np.savetxt("b1/results/b1_1_profiles.csv", np.c_[TH, *prof.values(), cie_raw(TH / 60)], delimiter=",",
               header="theta_arcmin," + ",".join(prof) + ",CIE_RAW", comments="")
    out["runtime_s"] = time.time() - t0
    json.dump(out, open("b1/results/b1_1.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))
