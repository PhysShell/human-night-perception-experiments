#!/usr/bin/env python3
"""M2 (NATIVE setup, separate outputs): from the official tutorial configuration
(doc/getting_started/3_atmosphere_adaptive_optics.ipynb, hcipy 0.7.1) measure separately
  (a) image motion   : PSF centroid (G-tilt) per frame, one-axis RMS
  (b) PSF / seeing   : short-exposure vs long-exposure PSF (FWHM, peak ratio)
  (c) scintillation  : pupil-plane normalised intensity variance sigma_I^2, point vs aperture-averaged
Tutorial parameters are used unchanged (8.2 m pupil, r0 0.2 m @500 nm, L0 20 m, v 10 m/s, lambda 1 um;
Mauna Kea 6-layer model, r0 0.1 m @550 nm, lambda 2 um, super-Gaussian pupil). NOT our scene.
Only hcipy does the optics; this script only measures its outputs and prints the textbook
reference numbers (formulas cited in tracks/hcipy/sources.md) for comparison.
  usage: m2_separate_effects.py OUTDIR
"""
import json, os, sys, time
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from hcipy import *

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng_seed = 1; np.random.seed(rng_seed)
res = {'hcipy_version': __import__('hcipy').__version__, 'seed': rng_seed}
RAD2AS = 180 / np.pi * 3600

# ---------------- (a)+(b): tutorial single InfiniteAtmosphericLayer ----------------
D_tel, wavelength = 8.2, 1e-6
pupil_grid = make_pupil_grid(512, D_tel)
# The tutorial's own focal grid (q=8, 16 lambda/D radius = 0.41 arcsec) is SMALLER than the seeing disc
# (0.98 lambda/r0 = 0.44 arcsec FWHM at 1 um), so centroid and FWHM measured on it are truncated.
# For measurement we widen the field to 80 lambda/D radius at q=2 (same pupil, same layer).
focal_grid = make_focal_grid(2, 80, spatial_resolution=wavelength / D_tel)
prop = FraunhoferPropagator(pupil_grid, focal_grid)
aperture = make_circular_aperture(D_tel)(pupil_grid)
r0_500, L0, v = 0.2, 20, 10
layer = InfiniteAtmosphericLayer(pupil_grid, Cn_squared_from_fried_parameter(r0_500, 500e-9), L0, v)
wf = Wavefront(aperture, wavelength)
diff = prop(wf).intensity
x, y = focal_grid.x, focal_grid.y

def centroid(I):
    return float((I * x).sum() / I.sum()), float((I * y).sum() / I.sum())

def fwhm_equiv(I):
    # diameter of the circle with the same area as the region above half maximum
    return float(2 * np.sqrt(np.sum(I > I.max() / 2) * focal_grid.delta[0] * focal_grid.delta[1] / np.pi))

# time series (frozen flow evolution, as the tutorial's layer.t) : 400 frames, 10 ms
dt, N = 0.01, 400
cx, cy, peaks, fw_short = [], [], [], []
long_exp = 0
t0 = time.time()
for i in range(N):
    layer.t = i * dt
    I = prop(layer(wf)).intensity
    c = centroid(I); cx.append(c[0]); cy.append(c[1])
    peaks.append(float(I.max() / diff.max())); fw_short.append(fwhm_equiv(I))
    long_exp = long_exp + I
    if i == 0: first = I.copy()
long_exp = long_exp / N
# tip-tilt-removed ("shift-and-add") long exposure: short-exposure PSF core without motion
res['a_image_motion_timeseries'] = {
    'frames': N, 'dt_s': dt, 'wind_m_s': v,
    'rms_one_axis_x_arcsec': float(np.std(cx) * RAD2AS), 'rms_one_axis_y_arcsec': float(np.std(cy) * RAD2AS),
    'note': 'frozen flow: 400 frames = 40 m of screen = ~5 pupil crossings; statistics correlated'}
# independent realisations for unbiased tilt statistics
cxi, cyi, ztilt = [], [], []
ens = 0
Zb = make_zernike_basis(3, D_tel, pupil_grid, starting_mode=2)
Zproj = np.linalg.pinv(np.array([z * aperture for z in Zb]).T)
for i in range(200):
    layer.reset(make_independent_realization=True)
    I = prop(layer(wf)).intensity
    c = centroid(I); cxi.append(c[0]); cyi.append(c[1])
    ztilt.append(Zproj.dot(layer.phase_for(wavelength) * aperture)[:2])
    ens = ens + I
ens = ens / 200

def radial_fwhm(I):
    r = np.hypot(x, y); rb = np.linspace(0, r.max(), 400)
    idx = np.digitize(r, rb); prof = np.array([I[idx == j].mean() if np.any(idx == j) else np.nan for j in range(1, len(rb))])
    rc = 0.5 * (rb[1:] + rb[:-1]); half = np.nanmax(prof[:3]) / 2
    j = np.argmax(prof < half)
    return float(2 * np.interp(half, [prof[j], prof[j - 1]], [rc[j], rc[j - 1]]))

# von Karman Zernike-tilt reference from HCIPy's OWN test-suite formula (tests/test_atmosphere.py,
# zernike_variance_von_karman, Noll-normalised Z2/Z3 in rad^2); angle = sqrt(var) * lambda / (pi R)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../research-cache/hcipy/src/tests'))
from test_atmosphere import zernike_variance_von_karman
vk = float(zernike_variance_von_karman(1, 1, D_tel / 2, 1 / L0, layer.Cn_squared, wavelength))
ztilt = np.array(ztilt)
r0_lam = r0_500 * (wavelength / 500e-9) ** 1.2
tilt_kolmo = np.sqrt(0.170 * (wavelength / D_tel) ** 2 * (D_tel / r0_lam) ** (5 / 3))
res['a_image_motion_independent'] = {
    'realisations': 200,
    'rms_one_axis_arcsec (PSF centroid = G-tilt)': float(np.sqrt(0.5 * (np.var(cxi) + np.var(cyi))) * RAD2AS),
    'rms_one_axis_arcsec (phase Zernike Z2/Z3 = Z-tilt)': float(np.sqrt(ztilt.var(0).mean()) * wavelength / (np.pi * D_tel / 2) * RAD2AS),
    'reference_vonKarman_Ztilt_one_axis_arcsec (hcipy test formula, L0=20 m)': float(np.sqrt(vk) * wavelength / (np.pi * D_tel / 2) * RAD2AS),
    'reference_Kolmogorov_Gtilt_one_axis_arcsec (0.170 (lambda/D)^2 (D/r0)^5/3, L0=inf)': float(tilt_kolmo * RAD2AS),
    'note': 'finite L0=20 m (D/L0=0.41) must reduce tilt below the L0=inf reference'}
fw_long = fwhm_equiv(long_exp)
res['b_psf'] = {
    'r0_at_lambda_m': r0_lam,
    'diffraction_FWHM_arcsec (1.03 lambda/D)': float(1.03 * wavelength / D_tel * RAD2AS),
    'short_exposure_equivFWHM_arcsec_mean': float(np.mean(fw_short) * RAD2AS),
    'long_exposure_equivFWHM_arcsec (400 correlated frames, still speckled)': float(fw_long * RAD2AS),
    'ensemble_long_exposure_radial_FWHM_arcsec (200 independent realisations)': float(radial_fwhm(ens) * RAD2AS),
    'reference_vonKarman_seeing_FWHM_arcsec (Tokovinin 2002: x sqrt(1-2.183 (r0/L0)^0.356))': float(0.98 * wavelength / r0_lam * np.sqrt(1 - 2.183 * (r0_lam / L0) ** 0.356) * RAD2AS),
    'reference_seeing_FWHM_0.98lambda_over_r0_arcsec (Kolmogorov)': float(0.98 * wavelength / r0_lam * RAD2AS),
    'short_exposure_peak_over_diffraction_mean': float(np.mean(peaks)),
    'long_exposure_peak_over_diffraction': float(long_exp.max() / diff.max()),
    'note': 'short-exposure "equivalent FWHM" of a speckled PSF is only the area above half of its brightest speckle'}
res['seconds_part_ab'] = round(time.time() - t0, 1)

fig, ax = plt.subplots(1, 4, figsize=(16, 4))
ext = np.array([x.min(), x.max(), y.min(), y.max()]) * RAD2AS
for a, im, tt in zip(ax[:3], [diff, first, ens], ['diffraction', 'short exposure (1 frame)', 'long exposure (200 independent realisations)']):
    a.imshow(np.log10(im.shaped / diff.max() + 1e-12), vmin=-3, vmax=0, extent=ext, origin='lower'); a.set_title(tt); a.set_xlabel('arcsec')
ax[3].plot(np.arange(N) * dt, np.array(cx) * RAD2AS, label='x'); ax[3].plot(np.arange(N) * dt, np.array(cy) * RAD2AS, label='y')
ax[3].set_xlabel('t [s]'); ax[3].set_ylabel('centroid [arcsec]'); ax[3].legend(); ax[3].set_title('image motion (tutorial layer)')
fig.suptitle('NATIVE hcipy tutorial setup (8.2 m, r0=0.2 m@500nm, L0=20 m, v=10 m/s, 1 um) - NOT our scene')
fig.tight_layout(); fig.savefig(os.path.join(out, 'NATIVE_m2_psf_and_image_motion.png'), dpi=70); plt.close(fig)

# ---------------- (c): tutorial Mauna Kea MultiLayerAtmosphere with scintillation ----------------
t0 = time.time()
pg = make_pupil_grid(256, 1.5)
layers = make_mauna_kea_atmospheric_layers(pg, outer_scale=L0)
atmos = MultiLayerAtmosphere(layers, scintillation=True)
atmos.Cn_squared = Cn_squared_from_fried_parameter(0.1, 550e-9)
lam_s = 2e-6
p = np.exp(-(pg.as_('polar').r / 0.68) ** 20)
pup = make_circular_aperture(1)(pg) > 0
r = pg.as_('polar').r
point_vals, avg = [], {d: [] for d in (0.05, 0.2, 1.0)}
for i in range(60):
    atmos.reset()
    for l in atmos.layers: l.reset(make_independent_realization=True)
    I = atmos(Wavefront(Field(p, pg), lam_s)).intensity
    point_vals.append(np.asarray(I[pup]))
    for d in avg:
        avg[d].append(float(I[r <= d / 2].mean()))
pv = np.concatenate(point_vals)
sI_point = float(pv.var() / pv.mean() ** 2)
k = 2 * np.pi / lam_s
heights = np.array([l.height for l in layers]); cn2 = np.array([l.Cn_squared for l in layers])
sR2_plane = float(2.25 * k ** (7 / 6) * np.sum(cn2 * heights ** (5 / 6)))   # plane-wave Rytov, discrete layers
res['c_scintillation'] = {
    'wavelength_m': lam_s, 'realisations': 60, 'layer_heights_m': heights.tolist(), 'layer_Cn2dh': cn2.tolist(),
    'sigma_I2_point (pupil pixels 5.9 mm)': sI_point,
    'reference_weak_plane_wave sigma_I2 = 2.25 k^7/6 sum Cn2_i h_i^5/6': sR2_plane,
    'sigma_I2_aperture_averaged': {f'{d} m': float(np.var(v_) / np.mean(v_) ** 2) for d, v_ in avg.items()},
    'note': 'periodic 1.5 m grid: Fresnel zones sqrt(lambda h) up to 0.18 m, wrap-around; indicative only'}
res['seconds_part_c'] = round(time.time() - t0, 1)
fig, ax = plt.subplots(1, 2, figsize=(9, 4))
imshow_field(I * pup, pg, ax=ax[0], cmap='gray'); ax[0].set_title('pupil intensity (last realisation)')
ax[1].hist(pv / pv.mean(), bins=100, density=True); ax[1].set_xlabel('I/<I> (pupil pixels)'); ax[1].set_title(f'sigma_I^2 = {sI_point:.3f}')
fig.suptitle('NATIVE hcipy tutorial Mauna Kea layers, lambda 2 um - NOT our scene'); fig.tight_layout()
fig.savefig(os.path.join(out, 'NATIVE_m2_scintillation.png'), dpi=70); plt.close(fig)
json.dump(res, open(os.path.join(out, 'NATIVE_m2_separate_effects.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
