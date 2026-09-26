# D1-A0 / D1-A1: axis separation and the Wanat 2014 global tone curve

**Pre-registered** in `PREREG.md` (commit `44210bb`, before any code).

    tracks/temporal-glare-2009/py.sh d1/axis_a/kill_tests.py   # A0 + K0-K3 -> kill_tests.json, kill_curves.png
    tracks/temporal-glare-2009/py.sh d1/axis_a/run_scene.py    # A1 scene gates on S1 -> scene.json
    (wanat_global.py: our implementation of §4.1.1, Eqs. 5-11; CSF = HDR-VDP-2.2.2 ncsf*MTF*sA, S = 8.6)

## D1-A0 axis separation: PASS
B output rescaled per pixel to the physical Y. The results were exactly 0 for Δchroma, Δhue and ΔY/Y, on every
patch and on S1.
- The kernel's luminance gain is separable from its colour mechanism, so the architecture "B = chromaticity,
  A = luminance" stands.
- The test was nearly tautological, as expected: a scalar does not change chromaticity.

## D1-A1 synthetic kill tests: all PASS (our implementation reproduces the paper's stated behaviour)

| test | result |
|---|---|
| K0a same luminance (10⁻³…10² → 10⁻³…10²) | exact identity (max \|T − l\| = 0) |
| K0b 100 → 1 | slope 0.63 in bright tones (< 1), 2.06 in dark tones: "less steep for bright, steeper for dark" ✓ |
| K0c 100 → 1000 | slope 0.92–1.00 ("little change in shape") ✓ |
| K1 night 10⁻⁴…10² → SDR100 | monotone, spans exactly [0.1, 100] ✓ |
| K2 no crushed decade in 10⁻³…10² | decade slopes 0.42–0.65 ✓ |
| K3 dark contrast reduced relative to bright | 0.42 (10⁻³–10⁻²) < 0.65 (1–100) ✓ |

## D1-A1 on S1: FAIL (A1-S3, silhouettes)

| gate | value | |
|---|---|---|
| A1-S1 sky ≤ 2 cd/m² | 0.10004 cd/m², the display black | ✓ |
| A1-S2 lamps / sky ≥ 10, monotone | 43 (lamps 4.3 cd/m² median) | ✓ |
| **A1-S3 silhouette Weber ≥ 0.1** | **0.0003** | **✗** |
| A1-S4 B chromaticity untouched | Δu′v′ ≤ 3·10⁻¹⁶ on unclipped pixels | ✓ |

- Channel below black: 97.8 % of pixels. Above peak: 10⁻⁵.
- Controls (no gate): pcond V0 gives sky 0.32 cd/m², silhouette 0.56; Mantiuk08 auto gives 12.5 and 0.79.
- `sheet_S1.png` shows the image, the curves and the diagnostic.

**What happens.**
- S1's curve (source 2.7·10⁻⁵…302 cd/m² → SDR100) is **flat from the scene minimum up to ~5·10⁻⁴ cd/m²**. Above
  that its slope rises to ≈ 0.59.
- The whole night (sky 2.9·10⁻⁴, poplars and ground below it) lands on display black. Only the lamp ribbon remains.
- That is the model's own prediction:
  - with ρ = 2 cpd and S = 8.6, the threshold at 3·10⁻⁴ cd/m² is Mt = 0.66 (Gt = 0.34);
  - the representative contrast G = 0.4 is therefore barely supra-threshold;
  - below ~1.5·10⁻⁴ it is invisible (Mt ≥ 1, capped);
  - so the optimiser spends no display range there.

**Why this is not a reason to tune (diagnostic only, not a gate).**
1. **Single representative frequency.** ρ = 2 cpd is near the *photopic* peak. At 3·10⁻⁴ cd/m² the same CSF
   gives Mt = 0.28 at 0.5 cpd against 0.66 at 2 cpd: the scotopic peak moves to low frequencies. The poplar
   silhouettes are large, low-frequency structures.
2. **Out of the validated range.**
   - Wanat & Mantiuk's matching experiments used 1D/2D neutral-density filters in front of a ~200 cd/m² display,
     i.e. retargeting down to a ~2 cd/m² peak.
   - S1's sky is several decades below that. ρ = 2 cpd, G = 0.4 and S = 8.6 were chosen there.
   - The HDR-VDP-2.2.2 CSF table itself ends at 0.002 cd/m²; its parameters are clamped below.
3. **Changing ρ (or G) until S1's silhouettes appear would be fitting the method to our scene.** It is not
   done.

**Status.**
- **A0 PASS.**
- **A1 implementation validated** (K0–K3).
- **A1 on the physical night: FAIL (pre-registered A1-S3).** The global-only Wanat curve, used with the paper's
  parameters, crushes scotopic scene levels to display black.
- The residual is specific: large, low-frequency structure (silhouettes) that the fixed-ρ global model treats as
  sub-threshold. This is exactly the kind of residual the pre-registration named as the only reason to open A2.
- Candidate next steps, each needing its own pre-registration (none started):
  - **A2:** Wanat's multi-band local contrast, which evaluates thresholds per frequency band and so uses the
    low-frequency scotopic sensitivity;
  - accept that the global model is not applicable below its validated range, and state an explicit lower bound.
