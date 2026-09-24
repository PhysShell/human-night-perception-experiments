# B1 closeout: the eye-model research is frozen

B1 asked what light an eye puts on its retina from a distant bright point, from the aberration core out to
several degrees. It is closed here with its limitations stated. **No further eye-model work in this project**
unless a later round needs a specific, bounded reference.

Details: `b1/README.md` (B1.0 oracles and erratum, B1.1 unified pupil), `b1/c0_ginis/README.md` (external
validation), `b0/README.md` (erratum on `hdrvdp_otf_cie99`).

## What B1 demonstrated

- **Three reference PSFs, each in one canonical package** (sr⁻¹, s = θ²·PSF, encircled energy, band energy,
  normalisation, support):
  - the ISET/Thibos wavefront core;
  - CIE 135/1, the complete visual spread function;
  - IJspeert 1993.
- **CIE 135/1's small-angle part *is* IJspeert's visual PSF** (CIE text §3, ~4 mm pupil). CIE and IJspeert
  therefore agree partly by construction.
- **Where the models disagree.**
  - From ~2′ outwards the wavefront-only PSF falls far below the empirical complete models.
  - Beyond ~10′ it is 25–60× below them.
  - Read as a divergence map, not a physical aberration→scatter boundary.
- **A single energy-conserving pupil works as a mechanism** (Thibos Zernike + an Arias-style random phase screen,
  B1.1):
  - With the screen off it equals ISET's own PSF (1.6·10⁻⁷ of peak).
  - With the screen on it reproduces CIE's wings over 0.5–8° within 0.03 log.
  - It takes 0.205 of the energy out of the central 1′ while keeping the core's width (Strehl 0.68).
- **The naive composition `ISET ⊛ CIE` double-counts CIE's small-angle visual PSF.** The core FWHM doubles
  (1.7′) and Strehl drops to 0.13. In the wings the two are the same.
- **Two donor defects found and documented:**
  - HDR-VDP 3.0.7 `hdrvdp_otf_cie99` applies 1-D Fourier transforms as a 2-D OTF. That gives negative lobes and
    a veil 14× too low at 18′ (minimal repro and draft issue in `docs/upstream/hdrvdp-otf-cie99/`, not sent).
  - ISET's default `wvf` grid supports the PSF only to ±11.7′.

## External validation (C0.1): Ginis et al. 2012, J Vis 12(3):20

Label: **DIGITIZED_EXTERNAL_VALIDATION**. Weak but usable. B and β were not refitted.

- **Data.** No numerical data are public. The figure curves come from the Artal lab's copy of the typeset PDF:
  - Fig. 6: GP;
  - Fig. 7: GP and CS;
  - axes log₁₀ PSF in sr⁻¹, verified three ways;
  - digitization uncertainty ≤ 0.04 log.
- **Conditions.** 530 nm, two 2 mm sub-apertures, young eyes with unstated ages. The curves are **model-based
  double-pass reconstructions**, not raw data. The core (< ~1°) is essentially their 2 mm Airy model.
- **Result over 1–7.5°**, log₁₀(B1.1 / Ginis):

| | mean offset | log RMS | offset-free log RMS | log–log slope, model vs eye |
|---|---|---|---|---|
| subject GP | −0.41 | 0.43 | 0.13 | −2.62 vs −2.08 |
| subject CS | +0.15 | 0.18 | 0.10 | −2.62 vs −3.00 |
| log mean of GP, CS | −0.13 | 0.13 | 0.020 | −2.62 vs −2.54 |

- **The two measured eyes differ from each other by up to 0.81 log (at 7°), more than the model differs from
  either.** From 1.75° outwards the model lies between them.
- CIE 135/1 itself gives residuals within 0.05 log of B1.1's. The check therefore **cannot separate B1.1 from its
  own calibration target**. It only shows that the target sits inside the in-vivo spread of two young eyes.
- Wavefront-only (THIBOS_ONLY) is 1.5–2.3 log too low, so a scatter mechanism is required.
- **The erratum (J Vis 12(4), doi 10.1167/12.4.15) could not be read.** What it changes is not verified. The
  Fig. 7 caption/legend mismatch (GP+CS vs "subjects in Figure 5") may be what it corrects.

## What B1 did not demonstrate

- **That B1.1 is "the" human eye.** It is one mechanism, calibrated to one empirical target (CIE, age 24, p 0.5).
  The in-vivo check has two subjects who span more than the model's residual.
- **Near-core behaviour (C0.2, model uncertainty, kept as is).** The scatter-wing calibration does not determine
  the near-core/Strehl effect. With identical wings, the screen's high-frequency cutoff gives:

| screen high-pass | EE(1′) | Strehl | wing log RMS vs CIE |
|---|---|---|---|
| 1.5′ | 0.37 | 0.57 | 0.034 |
| 3′ (declared) | 0.45 | 0.68 | 0.032 |
| 6′ | 0.51 | 0.79 | 0.034 |

  No further search for the "correct" cutoff: it needs core data the project does not have.
- **Wavelength and fundus.**
  - A pupil phase screen gives the same wavelength law at every angle (−0.14 / −0.16 log, 650 vs 500 nm, at 0.5°
    and 6°).
  - Ginis et al. 2013 find a haemoglobin (fundus) signature at 0.5°. **FAIL at 0.5°**, for a known missing
    mechanism.
  - Fundus reflectance and light through the ocular wall (CIE's second part) are not in the model.
- Age, pigmentation, eccentricity, polychromatic focus, and angles beyond ~10° are not modelled or not validated.
- Nothing about **perception**: P_det numbers anywhere in B0/B1 are HDR-VDP-3 diagnostics, not human data.

## Why B1 is frozen

The remaining uncertainties are not ones a better model can close from here:
- the near-core cutoff;
- the fundus spectral term;
- the 0.8-log spread between individual eyes.

Each would need new measurements. B1 has already delivered what the project needs from it: which physical
features a bright point has, and where the models stop being determined.

## How B1 may be used later

- **Physical reference.** `b1/results/*.csv` (the three oracles) and `b1/results/b1_1_profiles.csv`, with their
  stated conventions, as a *target-side* description of a point source's retinal spread. Quote the model
  uncertainty (cutoff) and the inter-subject spread with any use.
- **Regression stimulus.** The canonical packages and the scatter_off identity (ISET = unified pupil with the
  screen off) are fixed numbers future code can be checked against.
- **Diagnostic observer.** As an optional stage in a diagnostic evaluation, always labelled as one model.
- **NOT the production renderer.** No display image is to be made by convolving with B1 PSFs; that would count the
  viewer's own optics twice (PSF × PSF). Display rendering is the D0 track (`d0/README.md`).
