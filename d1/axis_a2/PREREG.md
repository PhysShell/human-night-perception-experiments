# D1-A2 pre-registration: literal Wanat & Mantiuk 2014 local contrast retargeting (§4.1.2) on S1

Committed **before** any A2 code exists. One strict run "as Wanat 2014", with no improvements. It is allowed by
A2-K0 (`d1/axis_a2_k0/`), which did not find a cheap kill.

## Frozen inputs
- **A1:** the global tone curve T for S1 (`d1/axis_a/`, SDR100 DARK, dmin 0.1, dmax 100), unchanged.
- **B:** Cao/Kirk kernel κ = 3 plus the Wanat-derived local chroma collapse; chromaticity only (A0 architecture).
- **CSF:** HDR-VDP-2.2.2 full CSF, S = 8.6, Mt capped at 0.999 (as in A1).
- **Display geometry:** PHONE, Rppd = 73.

## Primary: literal Wanat14 (verified in the authors' preprint)
- l = log10 Y_source (physical cd/m²).
- Non-decimated Laplacian pyramid on l: k = 1…N, with **N = 5** (Eq. 15: ρ_k = 2^−(k+1)·73 = 18.25, 9.125,
  4.5625, 2.28125, 1.140625 cpd; the coarsest band has a peak ≤ 2 cpd).
- The pyramid filter is **not specified in the paper** ("non-decimated … all levels have the same resolution").
  Declared: lowpass_0 = l, lowpass_k = Gaussian(l, σ = 2^(k−1) px), P_k = lowpass_(k−1) − lowpass_k (as in K0).
- The pyramid's own base band (lowpass_N) is **discarded**. The base band is lowpass_N of the A1-retargeted log
  luminance, i.e. T applied at full resolution, then the same Gaussian (σ = 2^(N−1) px). This follows the paper's
  Fig. 2: tone curve on full resolution, then base-band extraction.
- **c_k** = Eq. 13 on the source l with σ_k = Eq. 14 = 0.5·Rppd/ρ_k = 2, 4, 8, 16, 32 px:
  c_k = √( g_σk ∗ [l − g_σk ∗ l]² ).
- **Eq. 17:** m_k = (c_k − G(Mt) + G(M̃t)) / c_k.
  - Mt = 1/(8.6·CSF(ρ_k, Y_source(x,y)));
  - M̃t = 1/(8.6·CSF(ρ_k, Ỹ_base(x,y))), with Ỹ_base = 10^(retargeted base band);
  - G(M) = ½ log10((1 + M)/(1 − M)).
- **m_k < 0 is kept as written.** The paper and the authors' patent give no clamp. A negative m flips the sign of
  that band.
- **Numerical convention (not a perceptual clamp):** where c_k < 10⁻⁹ (uniform region), P̃_k = 0.
- **Reconstruction:** l̃ = base + Σ_k P_k·m_k; Ỹ = 10^l̃, clipped to [0.1, 100] (display range; the clipped
  fraction is reported).
- **Colour:** B chromaticity at exactly Ỹ (A0). Encoding as in A1, SDR100 sRGB. Measured as emitted light via
  `d0/display_model.py`.

## Sensitivity only (not a candidate for a paper PASS)
- m_k = max(m_k, 0), everything else identical.
- If raw FAILs and the clamped version PASSes, the result is: **"Wanat14 A2 fails / is underspecified for S1; the
  clipped derivative merits a separate pre-registration."** It is not recoloured green.

## Reported diagnostics
- Per band: the fraction of pixels with m_k < 0, and the fraction of Σ|P_k| carried by pixels with m_k < 0.
- Clipped fraction at the display limits.

## Gates (on the displayed image; the same for raw and clamped)
The silhouette region is the one defined in A2-K0: the two luminance-defined large poplars; the sky is the sky-mask
median. This replaces the fragmentary D0 `tree` mask (see `d1/axis_a/README.md`). The D0-mask value is also
reported.

| id | criterion |
|---|---|
| A2-S1 night stays dark | sky median display luminance ≤ 2 cd/m² |
| A2-S2 lamps ordered and salient | median lamp / median sky ≥ 10 |
| **A2-S3 silhouettes** | Weber = 1 − median(poplar blobs) / median(sky) ≥ 0.1 |
| A2-S4 B untouched | \|Δu′v′\| ≤ 10⁻⁶ on pixels with no channel clipped |
| **A2-AR1 region polarity** | median poplar display luminance < median display luminance of the sky ring 5–20 px outside the poplars |
| **A2-AR2 edge polarity** | inner edge ring (poplar ∖ erode 2 px) paired to its nearest outer ring pixel (dilate 2 px ∖ poplar, above the horizon). Among pairs with source sky > tree, pairs whose display luminance reverses (outer ≤ inner): ≤ 5 % |
| **A2-AR3 halo** | median sky display luminance in the 5–20 px ring within a factor 1.5 of the median sky display luminance > 60 px from any poplar |

## Decision tree (agreed before running)
- **Raw PASS, no artefact failures:** keep Wanat local contrast. The near-threshold stochastic regime
  (Kellnhofer 2015) is handled separately afterwards.
- **Raw FAIL, clamp PASS:** Wanat14 does not pass. The clamp is not adopted unless separately pre-registered.
- **Raw and clamp FAIL:** KILL Wanat A2 for S1. Next is **A3a = Ashraf & Mantiuk 2024** (hybrid additive +
  multiplicative supra-threshold contrast matching, measured 0.02–2000 cd/m², 0.5/2/4 cpd), then
  Kellnhofer/Ferwerda for < 10⁻³ cd/m². No parameter tuning of Wanat.

## Predictions (recorded)
- None firm.
- K0's ideal upper bound was Weber 0.48 at 1.14 cpd, but only 6.6 % of the edge energy is in that band. In finer
  bands G̃ < 0, so m < 0 is expected on the poplar side of the edge. AR2 (reversals) is therefore the gate most
  likely to fail for raw.
