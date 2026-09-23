"""Report/plot script (no model): reads ADAPTED_e8_point_source_octave.mat written by
e8_point_source.m (ISETBio wvf-human optics under Octave) and summarises
 - E9: radial profiles of the model's own PSF per wavelength & pupil (plotting shipped model output)
 - E8: encircled-energy radii of the point image, photopic (ISET's own oiGet illuminance) and
       scotopic (retinal photons -> energy weighted by CIE 1951 V'(lambda) from colour-science),
       and the energy fraction inside one display pixel at 32 / 48.4 / 73 px/deg.
Usage: python e8_analyze.py <mat> <outdir>"""
import sys, os, json
import numpy as np, scipy.io as sio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import colour

m = sio.loadmat(sys.argv[1], squeeze_me=True)
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
wave = np.atleast_1d(m["wave"]).astype(float)
names = [str(n) for n in np.atleast_1d(m["names"])]
pupils = np.atleast_1d(m["pupils"]).astype(float)
umdeg = float(m["umPerDegree"])
Vs = colour.colorimetry.SDS_LEFS_SCOTOPIC["CIE 1951 Scotopic Standard Observer"].copy().align(
    colour.SpectralShape(wave[0], wave[-1], wave[1] - wave[0])).values
h, cc = 6.62607015e-34, 2.99792458e8

def radial_ee(img, arcmin_per_px):
    iy, ix = np.unravel_index(np.argmax(img), img.shape)
    # energy centroid near the peak (sub-pixel)
    y, x = np.indices(img.shape)
    tot = img.sum()
    cy, cx = (img * y).sum() / tot, (img * x).sum() / tot
    r = np.hypot(y - cy, x - cx) * arcmin_per_px
    o = np.argsort(r.ravel()); cum = np.cumsum(img.ravel()[o]) / tot
    rr = r.ravel()[o]
    ee = lambda f: float(np.interp(f, cum, rr))
    def box(pxdeg):
        half = 60.0 / pxdeg / 2
        msk = (np.abs((y - cy) * arcmin_per_px) <= half) & (np.abs((x - cx) * arcmin_per_px) <= half)
        return float(img[msk].sum() / tot)
    return dict(ee50_arcmin=ee(0.5), ee80_arcmin=ee(0.8), ee90_arcmin=ee(0.9), ee95_arcmin=ee(0.95),
                frac_in_px_32=box(32), frac_in_px_48p4=box(48.4), frac_in_px_73=box(73)), (rr, cum)

rows = []
fig, axs = plt.subplots(1, len(pupils), figsize=(4 * len(pupils), 3.6), sharey=True)
for ip, p in enumerate(pupils):
    ax = axs[ip]
    for sname in names:
        tag = f"{sname}_p{int(round(p*10)):02d}"
        ph = np.real(m["oiphotons_" + tag]).astype(float)  # Octave leaves ~1e-8 relative imaginary FFT residue
        um = np.atleast_1d(m["oiumperpix_" + tag]).astype(float)[0]
        apx = um / umdeg * 60.0
        illum = np.real(m["oiillum_" + tag]).astype(float)
        energy = ph * (h * cc / (wave * 1e-9))[None, None, :]
        scot = (energy * Vs[None, None, :]).sum(-1)
        rp, curve = radial_ee(illum, apx)
        rs, _ = radial_ee(scot, apx)
        rows.append(dict(spectrum=sname, pupil_mm=p, arcmin_per_px=apx,
                         **{"photopic_" + k: v for k, v in rp.items()},
                         **{"scotopic_" + k: v for k, v in rs.items()}))
        ax.plot(curve[0], curve[1], label=sname)
    ax.set_xscale("log"); ax.set_xlim(0.2, 30); ax.grid(alpha=.3)
    ax.set_title(f"pupil {p:g} mm"); ax.set_xlabel("radius (arcmin)")
    for pxdeg, ls in [(32, ":"), (73, "--")]:
        ax.axvline(60 / pxdeg / 2, color="k", ls=ls, lw=.8)
axs[0].set_ylabel("encircled photopic energy"); axs[-1].legend(fontsize=8)
fig.suptitle("ADAPTED: ISETBio wvf-human (Thibos 2009 mean eye + LCA + lens), point source, Octave\n"
             "dotted/dashed: half-width of one pixel at 32 / 73 px/deg", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(out, "ADAPTED_e8_encircled_energy.png"), dpi=110)

# E9: PSF radial profiles per wavelength
fig, axs = plt.subplots(1, len(pupils), figsize=(4 * len(pupils), 3.6), sharey=True)
for ip, p in enumerate(pupils):
    ax = axs[ip]
    for w in [450, 500, 550, 590, 650]:
        psf = m[f"psf_p{int(round(p*10)):02d}_w{w}"].astype(float)
        s = np.atleast_1d(m[f"psfsamp_p{int(round(p*10)):02d}_w{w}"]).astype(float)
        c = psf.shape[0] // 2
        prof = psf[c, c:] / psf.max(); r = s[c:] - s[c]
        ax.semilogy(r, np.maximum(prof, 1e-6), label=f"{w} nm")
    ax.set_xlim(0, 15); ax.set_ylim(1e-5, 1.2); ax.grid(alpha=.3)
    ax.set_title(f"pupil {p:g} mm"); ax.set_xlabel("arcmin from centre")
axs[0].set_ylabel("PSF / peak (horizontal cut)"); axs[-1].legend(fontsize=8)
fig.suptitle("ADAPTED (model output, not measured data): ISETBio wvf-human PSF per wavelength; focus at 550 nm", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(out, "ADAPTED_e9_psf_vs_wavelength_pupil.png"), dpi=110)

import csv
with open(os.path.join(out, "ADAPTED_e8_point_source_metrics.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
for r in rows:
    print(f"{r['spectrum']:9s} p={r['pupil_mm']:.1f} EE50 {r['photopic_ee50_arcmin']:.2f}' EE90 {r['photopic_ee90_arcmin']:.2f}' "
          f"in32px {r['photopic_frac_in_px_32']:.2f} in73px {r['photopic_frac_in_px_73']:.2f} | scot EE50 {r['scotopic_ee50_arcmin']:.2f}' EE90 {r['scotopic_ee90_arcmin']:.2f}'")
