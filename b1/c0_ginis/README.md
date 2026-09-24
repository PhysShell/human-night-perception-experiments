# C0: External check of B1.1 against Ginis et al. 2012

**Label: DIGITIZED_EXTERNAL_VALIDATION.** This compares B1.1 with a PSF measured in living eyes.
Nothing in B1.1 was refitted or changed. B, β and every other setting are as in `b1/README.md` §B1.1.
The model profiles are read straight from `b1/results/b1_1_profiles.csv`.

Source paper: Ginis H, Pérez GM, Bueno JM, Artal P. "The wide-angle point spread function of the human eye
reconstructed by a new optical method." *J Vis* 12(3):20 (2012), doi:10.1167/12.3.20.

    tracks/temporal-glare-2009/py.sh b1/c0_ginis/digitize.py   # -> ginis2012_fig7_digitized.csv, ginis2012_fig7_grid.csv
    tracks/temporal-glare-2009/py.sh b1/c0_ginis/compare.py    # -> result.json, compare.png

`digitize.py` needs the figure images in `.cache/`. That folder is git-ignored because the images are copyrighted.
To rebuild it, download the PDF below and run `pdfimages -j -f 7 -l 8 ginis2012.pdf .cache/fig`. The script checks the sha256 of each image.

## Sources and data availability

| what | URL | result |
|---|---|---|
| Journal page (ARVO) | https://jov.arvojournals.org/article.aspx?articleid=2121053 (also the `doi=` URL and the `/arvo/content_public/...pdf` URL) | 403, Cloudflare challenge |
| Wayback Machine snapshots | web.archive.org/... (found through the archive.org availability API) | blocked by the egress policy |
| Europe PMC, PubMed E-utilities | `europepmc/webservices/rest/search?query=DOI:10.1167/12.3.20`, `efetch db=pubmed id=22451158` | not in PMC, no supplementary files. The PubMed record lists "Erratum in J Vis 12(4), doi 10.1167/12.4.15" |
| Unpaywall, OpenAlex, CORE, Semantic Scholar | APIs | the only open-access location is the publisher. The Semantic Scholar PDF link redirects to a bot wall |
| **Artal lab (Univ. Murcia) PDF** | **https://lo.um.es/lo.um/wp-content/uploads/2012/05/2012_JOV_TheWide_Ginis.pdf** | **200, 3,684,790 B**; the sha256 is listed below. This is the publisher's typeset PDF (3B2), created 2012-04-04 |
| Erratum 10.1167/12.4.15 | ARVO (articleid=2121129), Crossref, OpenAlex, Semantic Scholar | **text not obtainable**: ARVO is behind Cloudflare, and no abstract or full text is indexed anywhere. **What the erratum changes is NOT VERIFIED.** |

- **Numerical data:** none public. There is no supplement, no Zenodo, figshare or OSF deposit, and no data on the lab page.
  The authors were not contacted, as instructed. So the only route was to digitize the figures.
- **Possible erratum issue:** the Fig. 7 caption and text say the figure shows "the two subjects in Figure 5".
  Fig. 5 shows only GP, but the Fig. 7 legend reads **GP and CS**. CS is otherwise mentioned only in the subject list (Fig. 5b shows GP and JB).
  This mismatch may be what the erratum corrects. It is unresolved here. The lab PDF was created on 2012-04-04, after the
  2012-03-26 online date, so it may already include the correction, but this cannot be confirmed.
- **Sha256 of the cached files** (in `.cache/`, not tracked):
  - PDF: `15623e535963a0657fb95112485dce9ae76c18a170a0ec4ae6cdd0f4e7a70f68`
  - Fig. 7 (`fig-002.jpg`, object 86, 2399×1915): `5ff92d615a133ffe6dbad111be77f7ae502ce4a8a1f5737c336ae1472beaaaa4`
  - Fig. 6 (`fig-001.jpg`, object 80, 2150×1856): `8b8a2efac06f0db0530a4b0311e127dd1aca644051a3dc7adc2dd37fd02ae0de`

## What was digitized

- **Fig. 7 (p. 8).** Caption: "Comparison between two reconstructed PSFs (red and blue lines) based on data here recorded and those
  corresponding to two existing models in the literature (solid and dashed black lines). (Equations from Vos & van den Berg, 1999.)"
  - Axes as printed: x "Angle [degrees]" (linear, 0–8); y "**Log(PSF)**" (linear, −2 to 7).
  - Curves digitized:
    - **Subject GP** (blue): its trace ends at 7.77°.
    - **Subject CS** (pink): its trace ends at 7.89°.
    - **Vos and van den Berg (1999)** (black solid): digitized only at ≥ 3°, as a check on units.
- **Fig. 6 (p. 7).** "Double- and single-pass PSFs for subject GP (raw data in Figure 5, no CL)".
  - The blue "Reconstructed PSF" curve was digitized as a second, independent trace of GP.
  - Fig. 6 has no overlapping curves, so this trace is the **primary GP profile**. Fig. 7 GP is used as a cross-check.
- **Units.** The y axis is log10 of PSF in sr⁻¹. Three independent checks support this:
  1. Fig. 5b of the same paper labels the PSF "PSF at 5.25 degrees [sr⁻¹]".
  2. The age-adapted Stiles–Holladay curve in Fig. 7 matches 10/θ² sr⁻¹. For example, log ≈ 1.0 at 1° and −0.4 at 5°.
  3. The digitized Vos–van den Berg curve lies 0.044–0.066 log **above** our CIE_RAW (age 24, p 0.5) over 3.25–7.75°.
     Ginis do not state which age or pigmentation they used for it.
  - **So absolute levels can be compared.** There is no separate normalisation step. Ginis normalise Ic to the largest disk (8.1°),
    which makes their PSF carry all of its energy inside 8.1°. That biases their level upward by −log10 EE(8.1°), which is ≲ 0.02 log.
- **Measurement conditions (from the paper).**

  | | Ginis et al. 2012 | B1.1 model |
  |---|---|---|
  | subjects | 3 normal young subjects (GP, JB, CS), **ages not given** | calibrated to CIE age 24, p 0.5 |
  | light | 530 ± 30 nm (FWHM) | 550 nm |
  | pupil | dilated (≥ 6 mm), but light passes through **two 2-mm sub-apertures** whose centres are 4 mm apart (entry and exit) | 6 mm |
  | angles | 50 disks, 0.18–8.1° | profile to 10° |

  - The reconstructed PSF is **not raw data**. It is built in three steps:
    1. The analytic function of Eq. 6 is fitted to the radial integral Ic(θ): (1−a)·Airy(2 mm) + a·b/(θ+θ0)ⁿ, with n ≈ 2 and θ0 small.
    2. Differentiating the fit gives the double-pass PSF (Eq. 3).
    3. The single-pass PSF is then taken as F⁻¹{√|F(PSF_dp)|} (Eq. 4). This assumes rotational symmetry and identical passes.
  - Below about 0.5–1° the curve is essentially the 2-mm Airy model, not the eye. The paper says the PSF beyond ~1° is
    "unlikely to be influenced by aberrations". The derivatives were fitted over 0.5–2° and 2.5–8°.
  - **Supported range used here:**
    - **Primary: 1.0–7.5°.**
    - Secondary: 0.5–7.5°.
    - The core is not compared.
- **Method (`digitize.py`, `calib.json`).**
  - **Calibration.** Tick centres were found by detecting tick marks and recorded by hand in `calib.json`.
    `digitize.py` fits a linear pixel-to-data map to them by least squares. Residuals of that fit: x 0.0005° and y 0.0009 log (Fig. 7).
  - **Curve extraction.** Each curve is selected by an RGB rule and the legend boxes are masked. In each pixel column, the curve
    value is the median row of the largest contiguous run of selected pixels. The results are resampled to a 0.25° grid
    (`ginis2012_fig7_grid.csv`); the full per-column trace is in `ginis2012_fig7_digitized.csv`.
  - **Uncertainty (1σ, log10).** Three sources are combined:
    - Tick calibration: 300 draws with every tick jittered by N(0, 2 px) give ≤ 0.012.
    - Line-centre estimator (median vs mean vs mid-range) gives ≤ 0.002.
    - The Fig. 7 GP trace minus the Fig. 6 GP trace is ≤ 0.004 at ≥ 1.25°, but **0.039 at 1.0°**, where GP, CS and the black
      curves cross in Fig. 7. The Fig. 7 − Fig. 6 difference at each angle is added in quadrature to GP's uncertainty. Its largest value in 0.75–1.25° (0.039) is added to CS's uncertainty over that range.
  - **Total: ≤ 0.04 log at the crossing (1°), ≤ 0.013 elsewhere.** This is far below the differences between model and data
    and between the two subjects.

## Results (log10 model / Ginis; positive means the model is above the measurement)

| vs | model | 0.5° | 1° | 2° | 3° | 5° | 7° | mean offset 1–7.5° | log RMS 1–7.5° | offset-free log RMS 1–7.5° | log-log slope 1–7.5° (model / Ginis) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GP | **THIBOS_PLUS_ARIAS** | +0.11 | −0.10 | −0.27 | −0.37 | −0.48 | −0.56 | −0.41 | 0.43 | 0.13 | −2.62 / −2.08 |
| GP | CIE_RAW | +0.17 | −0.11 | −0.31 | −0.40 | −0.47 | −0.51 | −0.41 | 0.43 | 0.11 | −2.52 / −2.08 |
| GP | THIBOS_ONLY | −1.31 | −1.63 | −1.92 | −2.09 | −2.25 | −2.34 | −2.14 | 2.15 | 0.20 | −2.91 / −2.08 |
| CS | **THIBOS_PLUS_ARIAS** | −0.16 | −0.08 | +0.06 | +0.11 | +0.20 | +0.25 | +0.15 | 0.18 | 0.10 | −2.62 / −3.00 |
| CS | CIE_RAW | −0.10 | −0.09 | +0.02 | +0.08 | +0.21 | +0.30 | +0.15 | 0.19 | 0.12 | −2.52 / −3.00 |
| CS | THIBOS_ONLY | −1.58 | −1.62 | −1.58 | −1.62 | −1.57 | −1.54 | −1.58 | 1.58 | 0.03 | −2.91 / −3.00 |
| mean(GP, CS) in log | **THIBOS_PLUS_ARIAS** | −0.03 | −0.09 | −0.11 | −0.13 | −0.14 | −0.16 | −0.13 | 0.13 | 0.020 | −2.62 / −2.54 |
| mean(GP, CS) in log | CIE_RAW | +0.04 | −0.10 | −0.15 | −0.16 | −0.13 | −0.11 | −0.13 | 0.14 | 0.017 | −2.52 / −2.54 |

Numbers for the secondary range (0.5–7.5°) are in `result.json`. For THIBOS_PLUS_ARIAS they are log RMS 0.42 (GP), 0.17 (CS)
and 0.13 (mean). The offset-free log RMS for the mean is 0.03.

**Reading the results.**
- **The two eyes differ more from each other than the model differs from either.**
  - GP − CS is 0.33 log at 2° and 0.81 log at 7°.
  - Their log-log slopes are −2.08 and −3.00.
  - B1.1 THIBOS_PLUS_ARIAS (slope −2.62) lies **between the two eyes at every angle ≥ 1.75°**:
    - 0.05–0.25 log above CS;
    - 0.24–0.60 log below GP.

    Over 1.0–1.5°, where the two eyes cross, it is 0.04–0.21 log below both.
  - Against the log mean of the two eyes it is:
    - 0.13 log low overall (a factor 0.74);
    - a close match in shape (offset-free log RMS 0.020; slope −2.62 vs −2.54).
- **B1.1 behaves like its calibration target.** Relative to either subject, THIBOS_PLUS_ARIAS and CIE_RAW give almost the same
  residuals, within 0.05 log. B1.1 was fitted to CIE over 0.5–8°, so this is expected. What this test really checks is:
  - CIE 135/1 (young eye) against optical in-vivo data;
  - B1.1's reproduction of CIE.

  It does not find anything the CIE calibration missed. It also does not contradict it.
- **Without the scatter screen, the aberration-only eye (THIBOS_ONLY) is 1.5–2.3 log too low.** This confirms that B1.1
  needs its wide-angle mechanism. CS's small offset-free RMS (0.03) against THIBOS_ONLY is a coincidence of slope:
  the offset is 1.6 log.
- **This is not a population test.** There are two eyes, one of them (GP) with more scatter than CIE's young eye.
  - Fig. 5b gives the double-pass PSF at 5.25° as roughly 2.4–3.1 sr⁻¹ (interquartile) for GP and 2.1–2.9 sr⁻¹ for JB, a third eye not shown in Fig. 7.
  - A deviation of ±0.5 log from a single eye is within the normal spread between young eyes: CIE's own p-factor
    and age terms span about ±0.3–0.5 log.

## Verdict

**This is a usable but weak external validation.**
- It **passes** in the following sense: across 1–7.5°, the unrefitted B1.1 wide-angle PSF lies inside the band spanned by the two
  optically measured normal eyes. Its offset from their log mean is −0.13 log on average (−0.09 to −0.18 over 1–7.5°), with essentially the same shape.
- It is **weak** for five reasons:
  1. There are only n = 2 eyes, and their ages are not reported.
  2. The data are a model-based reconstruction (Eq. 6 power-law fit, then a double-pass square-root deconvolution) through
     2-mm sub-apertures at 530 nm, compared with our 6-mm, 550-nm model.
  3. The curves are digitized.
  4. The erratum's content could not be checked.
  5. The subject labels are ambiguous (the caption says "Figure 5" subjects; the legend says GP/CS).
- It cannot tell B1.1 apart from CIE_RAW, because they differ by < 0.05 log here.
- It should not be used for fitting anything.

## Limitations (summary)

- **Wavelength:** 530 vs 550 nm. Scatter changes little with wavelength over this range, so this is a small effect.
- **Pupil:**
  - The paper argues that scatter does not depend on pupil size (Franssen 2007).
  - The shape of the core does depend on it, which is why the core is excluded.
- **Reconstruction:** Eq. 4 assumes the two passes are identical and the PSF is rotationally symmetric, but the passes go
  through different sub-apertures. Light diffusing in the choroid and retina may widen the measured PSF (the paper says so).
  The light used is transmitted through the ocular media only, with no iris or sclera transmission, whereas CIE's psychophysical
  functions include it.
- **Normalisation:** Ic is set to 1 at 8.1°, which biases the level by ≲ +0.02 log.
- **Digitization:** ≤ 0.013 log (1σ) except ≤ 0.04 near the 1° crossing.
- **Coverage:** JB's reconstructed PSF is not shown in any figure. The artificial-scatter (contact lens) conditions were not used, as instructed.
