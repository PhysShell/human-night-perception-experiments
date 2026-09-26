# D1-A2-K0 pre-registration: analytic feasibility gate for Wanat 2014 local contrast (A2) on S1

Committed **before** running. No pyramid reconstruction and no rendered image: only the CSF already implemented
(`d1/axis_a/wanat_global.py`), Eq. 15 and Eq. 17, and a band-energy census of S1's silhouette region.

## What the paper does (verified in the authors' preprint §4.1.2)
- Laplacian bands k = 1…N with peak frequency ρ_k = 2^−(k+1)·Rppd (Eq. 15).
- "We select N so that the coarsest band (except the base band) has the peak frequency less or equal to 2 cpd."
- The base band comes from the global step (A1).
- Eq. 17: m_k = (c_k − G(Mt) + G(M̃t)) / c_k. The thresholds use the band's peak frequency and the pixel luminance
  of the source (Y) and of the retargeted base band (Ỹ).
- At **Rppd = 73** (PHONE, primary): bands 18.25, 9.13, 4.56, 2.28 and **1.14** cpd, so N = 5.
  **Everything below ~1 cpd stays in the A1 base band.**
- Scene angles, Rppd = 32 (sensitivity only): bands 8, 4 and 2 cpd, so N = 3.

## Silhouette region (luminance-defined, declared now)
- Physical S0/S1 luminance, above the horizon (rows < first ground row − 12).
- Pixels darker than 0.5 × the sky median, as connected components ≥ 100 px. The two largest are the big poplars:
  57 × 221 and 53 × 162 px.
- **ROI** = those two components dilated by 60 px, restricted to rows above the horizon (poplar + surrounding sky).
- L_tree = the median over the two components; L_sky = the sky-mask median; G_src = ½·log10(L_sky / L_tree).

## K0-1: band-energy census
- Non-decimated pyramid on log10 L_physical: lowpass_0 = identity, lowpass_k = Gaussian with σ = 2^(k−1) px,
  band_k = lowpass_(k−1) − lowpass_k, base = lowpass_N.
- The measured peak frequency of each band is reported next to Eq. 15's ρ_k.
- Energy fraction in the ROI: Σ band_k² / Σ (log L − mean_ROI)², and likewise for the base (about its ROI mean).

## K0-2: ideal Eq. 17 prediction
- If the whole silhouette contrast G_src sat in a single band at frequency ρ:
  G̃(ρ) = G_src − Gt(L_src, ρ) + Gt(L_tgt, ρ), with Gt from the same capped CSF (Mt ≤ 0.999).
- L_src = √(L_sky · L_tree). Sky-only and tree-only values are reported as sensitivity.
- L_tgt = the A1 base-band display luminance at the silhouette (S1 A1 curve: 0.1 cd/m² for both sky and poplars;
  taken from `d1/axis_a/scene.json`).
- Displayed Weber = 1 − 10^(−2·max(G̃, 0)).
- ρ ∈ {0.25, 0.5, 1, 1.14 (= ρ_N at 73 ppd), 2, 2.28}.

## KILL rules (any one kills published A2 for S1)
1. **K0-1:** base-band energy fraction in the ROI ≥ 0.5 at Rppd = 73. The silhouette signal stays mainly in A1's
   crushed base band.
2. **K0-2:** even the ideal Eq. 17 at the lowest processed band, ρ_N = 1.14 cpd, predicts displayed Weber < 0.1.
3. **K0-3:** Weber ≥ 0.1 appears only at ρ < ρ_N. That would need a pyramid extended below the published range:
   a new A2′ (our modification of Wanat), to be pre-registered separately. It is **not** a PASS of A2.
- **PASS** (full A2 allowed) only if none of 1–3 holds.

## Predictions, recorded before running (project lead's)
- Published A2 will likely not restore the region-level silhouette gate, because the relevant ~0.5 cpd content
  stays mostly in the A1 base band.
- If A2 is killed: open A3 as a separate near-threshold branch: Kellnhofer et al. 2015 (absolute-threshold rod
  noise), with Ferwerda et al. 1996 as the first cheap audit. Not another generic tone mapper.
