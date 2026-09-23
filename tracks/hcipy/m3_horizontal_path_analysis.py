#!/usr/bin/env python3
"""M3 ANALYSIS (closed-form textbook quantities, NOT a simulator, NOT hcipy output).
Expected turbulence magnitudes for the baseline scene geometry (lamps 2.2-14 km, eye 1.7 m, lamps 9 m)
and a human pupil. Every formula is cited in tracks/hcipy/sources.md (ids in brackets):
  spherical-wave Fried parameter, constant Cn2      r0 = [0.423 k^2 Cn2 (3/8) L]^(-3/5)          [LC06 eq.1]
  plane-wave Rytov variance                          sR2 = 1.23 Cn2 k^(7/6) L^(11/6)             [KK15 eq.8]
  spherical-wave Rytov variance (weak sigma_I^2)     b02 = 0.5  Cn2 k^(7/6) L^(11/6)             [KK15 eq.9]
  spherical all-regime point-receiver sigma_I^2      exp[0.49b02/(1+0.56 b0^(12/5))^(7/6)
                                                        +0.51b02/(1+0.69 b0^(12/5))^(5/6)] - 1     [AP05 ch.9, not verified]
  spherical strong-regime asymptote                  1 + 2.73 / b02^(2/5)                         [KK15 eq.11]
  aperture averaging, spherical, weak                A = [1 + 0.214 (k D^2/4L)^(7/6)]^(-1)        [KK15 eq.21]
  angle-of-arrival variance (plane, one axis)        2.91 Cn2 L D^(-1/3)  (D >> l0)
                                                     1.64 Cn2 L l0^(-1/3) (D << l0)               [KK15 eq.18]
  spherical-wave AoA = 3/8 x plane (path weight (z/L)^(5/3), integral 3/8)                        [AP05, LC06 weight]
  isoplanatic angle (Fried, plane-wave weighting)    theta0 = [2.905 k^2 Cn2 (3/8) L^(8/3)]^(-3/5) [LC06 eq.8]
  seeing FWHM (only meaningful when D >> r0)         0.98 lambda / r0                             [hcipy seeing_to_fried_parameter]
  frozen-flow time scales                            f ~ v_perp / scale                           (order of magnitude, ASSUMPTION)
Cn2 is taken constant along the path (horizontal path assumption [FG04 p.12]; the 1.7 m -> 9 m slant
is ignored: under stable night conditions Cn2 ~ h^0 [KK15 table, Gurvich model]).
  usage: m3_horizontal_path_analysis.py OUTDIR
"""
import csv, json, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ARCMIN = 180 / np.pi * 60
lam = 550e-9; k = 2 * np.pi / lam
Ls = [2200, 3000, 5000, 10000, 14000]                      # m, baseline scene lamp distances
Cn2s = {'1e-16 very weak': 1e-16, '1e-15 stable night': 1e-15, '8.4e-15 SLC night <18.5 m': 8.4e-15,
        '1e-14 moderate': 1e-14, '1e-13 strong (upper bound)': 1e-13}
pupils = [0.005, 0.006, 0.007]                               # m
l0s = [0.001, 0.01]                                         # inner scale range near ground [FG04 p.8/p.11]
v_perp = [0.5, 3.0]                                         # m/s crosswind ASSUMPTION (calm-to-light night wind)
PX_ARCMIN = {'PHONE_TARGET': 60 / 73.0, 'DESKTOP_TARGET': 60 / 48.4}   # stimuli/display_targets.json

def sI2_all(b02):
    b0 = np.sqrt(b02)
    return np.exp(0.49 * b02 / (1 + 0.56 * b0 ** (12 / 5)) ** (7 / 6) + 0.51 * b02 / (1 + 0.69 * b0 ** (12 / 5)) ** (5 / 6)) - 1

rows = []
for cname, Cn2 in Cn2s.items():
    for L in Ls:
        r0 = (0.423 * k ** 2 * Cn2 * 3 / 8 * L) ** (-3 / 5)
        rho0 = r0 / 2.1
        sR2 = 1.23 * Cn2 * k ** (7 / 6) * L ** (11 / 6)
        b02 = 0.5 * Cn2 * k ** (7 / 6) * L ** (11 / 6)
        fres = np.sqrt(L / k)
        theta0 = (2.905 * k ** 2 * Cn2 * 3 / 8 * L ** (8 / 3)) ** (-3 / 5)
        for D in pupils:
            A = 1 / (1 + 0.214 * (k * D ** 2 / (4 * L)) ** (7 / 6))
            aoa_D = np.sqrt(3 / 8 * 2.91 * Cn2 * L * D ** (-1 / 3))
            aoa_l0 = [np.sqrt(3 / 8 * 1.64 * Cn2 * L * l0 ** (-1 / 3)) for l0 in l0s]
            aoa_lo, aoa_hi = min([aoa_D] + aoa_l0), max([aoa_D] + aoa_l0)
            rows.append({
                'Cn2_case': cname, 'Cn2_m-2/3': Cn2, 'L_m': L, 'pupil_mm': D * 1e3,
                'r0_spherical_mm': r0 * 1e3, 'D_over_r0': D / r0, 'rho0_mm': rho0 * 1e3,
                'fresnel_sqrt(L/k)_mm': fres * 1e3,
                'rytov_plane_sR2': sR2, 'rytov_spherical_b02': b02,
                'sigmaI2_point_allregime': sI2_all(b02),
                'sigmaI2_strong_asymptote': (1 + 2.73 / b02 ** 0.4) if b02 > 1 else np.nan,
                'aperture_avg_A_weak': A,
                'sigmaI2_pupil_weak_only': b02 * A if b02 < 0.3 else np.nan,
                'aoa_rms_one_axis_arcmin_min': aoa_lo * ARCMIN, 'aoa_rms_one_axis_arcmin_max': aoa_hi * ARCMIN,
                'aoa_rms_in_PHONE_px_max': aoa_hi * ARCMIN / PX_ARCMIN['PHONE_TARGET'],
                'aoa_rms_in_DESKTOP_px_max': aoa_hi * ARCMIN / PX_ARCMIN['DESKTOP_TARGET'],
                'seeing_lambda_over_r0_arcmin': lam / r0 * ARCMIN,
                'diffraction_lambda_over_D_arcmin': lam / D * ARCMIN,
                'isoplanatic_theta0_arcmin': theta0 * ARCMIN,
                'f_scint_weak_Hz_(v/sqrt(lambda L))': f'{v_perp[0] / np.sqrt(lam * L):.1f}-{v_perp[1] / np.sqrt(lam * L):.1f}',
                'f_scint_strong_Hz_(v/rho0)': f'{v_perp[0] / rho0:.1f}-{v_perp[1] / rho0:.1f}',
            })
keys = list(rows[0].keys())
with open(os.path.join(out, 'ANALYSIS_m3_horizontal_path_eye.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
    for r in rows:
        w.writerow({k_: (f'{v:.4g}' if isinstance(v, float) else v) for k_, v in r.items()})

# compact summary at D = 6 mm
summ = [r for r in rows if r['pupil_mm'] == 6.0]
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for cname in Cn2s:
    rr = [r for r in summ if r['Cn2_case'] == cname]
    Lk = [r['L_m'] / 1e3 for r in rr]
    ax[0].plot(Lk, [r['aoa_rms_one_axis_arcmin_max'] for r in rr], 'o-', label=cname)
    ax[1].plot(Lk, [r['sigmaI2_point_allregime'] for r in rr], 'o-', label=cname)
    ax[2].plot(Lk, [r['r0_spherical_mm'] for r in rr], 'o-', label=cname)
for name, px in PX_ARCMIN.items():
    ax[0].axhline(px, ls='--', c='k' if name == 'PHONE_TARGET' else 'gray', lw=1); ax[0].text(2.2, px * 1.08, f'1 px {name}', fontsize=8)
ax[0].set_yscale('log'); ax[0].set_ylabel('image motion RMS, one axis [arcmin] (upper of D/l0 forms)'); ax[0].set_xlabel('L [km]')
ax[1].set_yscale('log'); ax[1].set_ylabel('scintillation index sigma_I^2 (point receiver; A~1 for 6 mm)'); ax[1].set_xlabel('L [km]')
ax[2].axhline(6, ls='--', c='k', lw=1); ax[2].text(2.2, 6.6, 'pupil 6 mm', fontsize=8)
ax[2].set_yscale('log'); ax[2].set_ylabel('spherical-wave r0 [mm] @550 nm'); ax[2].set_xlabel('L [km]'); ax[2].legend(fontsize=7)
fig.suptitle('ANALYSIS (closed-form, cited formulas) - horizontal night path, human pupil 6 mm, lambda 550 nm')
fig.tight_layout(); fig.savefig(os.path.join(out, 'ANALYSIS_m3_horizontal_path_eye.png'), dpi=80)
print(f"{'Cn2':>28} {'L':>6} {'r0mm':>7} {'b02':>8} {'sI2':>6} {'A':>6} {'aoa_arcmin':>14} {'seeing':>7} {'theta0':>7} {'f_scint':>10}")
for r in summ:
    print(f"{r['Cn2_case']:>28} {r['L_m']:6d} {r['r0_spherical_mm']:7.1f} {r['rytov_spherical_b02']:8.3g} {r['sigmaI2_point_allregime']:6.3f} {r['aperture_avg_A_weak']:6.3f} "
          f"{r['aoa_rms_one_axis_arcmin_min']:6.3f}-{r['aoa_rms_one_axis_arcmin_max']:6.3f} {r['seeing_lambda_over_r0_arcmin']:7.3f} {r['isoplanatic_theta0_arcmin']:7.3f} {r['f_scint_weak_Hz_(v/sqrt(lambda L))']:>10}")
