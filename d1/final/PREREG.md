# D1 final acceptance pre-registration: the frozen A + B + display pipeline on the whole corpus

Committed **before** the run. **No new investigation and nothing tunable.** It re-runs the D1 acceptance
(`d1/pipeline/PREREG.md`, `4214002`) with the components and gate corrections already decided and documented.

## Frozen pipeline (a composite model, not a single physiological model of vision)
- **A:** Radiance `pcond -s -c` (defaults, path A, HFOV from the manifest). Luminance = the Rec.709 luminance of pcond's
  **pre-gamut** output, reproduced exactly (`d1/a_extract/`, v2).
  - On our real scenes pcond runs its DO_LINEAR fall-back (the Ward 1994 contrast-based scale factor) plus the `-c`
    scotopic step.
- **B:** chromaticity only.
  - The Filament-derived Cao/Kirk kernel (verbatim, a = 1, κ = 3).
  - Then the Wanat-derived local chroma collapse (t = L/(L + 0.108)).
- **Display:** Y-priority minimum-chroma projection towards white at fixed Y into [0.1, 100]³ cd/m² (`d1/display_r/`,
  v2).
  - SDR100 DARK sRGB with the encoder knee at 0.04045/12.92; 16-bit PNG output.
- **Out of scope:** axis C (Kellnhofer 2015 temporal rod noise); local contrast (Wanat A2, killed); acuity; glare.

## Corpus
- S0, S1, the S2 clip (48 frames), S3_bar, S3_nobar, S4, S5 and F1. Nothing is added.
- Output: `d0/work/out/d1_pipeline/final/` → `d1/final/acceptance.json`, `d1/final/sheet_final.png` (commit-safe
  scenes). The S4/S5 sheet is not committed.

## Gates (unchanged wording from `4214002` except where noted; each change has its own committed rationale)
| id | criterion | change vs 4214002 |
|---|---|---|
| P-1 numerics | finite | – |
| P-2a | in-gamut pixels: output = recombination exactly, and \|Δu′v′\| (emitted vs B) ≤ 10⁻⁶ | P-2 split (`d1/pipeline/PREREG_R1_gamut.md`); B's chromaticity cannot be required where SDR100 cannot emit it |
| P-2b | projected pixels: \|ΔY\|/Y ≤ 10⁻⁶ vs clamp(Y_req); hue within 10⁻⁶ rad where output and B chroma > 10⁻⁶ (N/A at zero output chroma); chroma never increases; t maximal (a channel on a bound within 10⁻⁹) | the Y-priority S-1…S-3 gates plus DR-G3 (`d1/display_r/PREREG.md`) |
| P-3 clipping | every emitted channel in [0.1, 100] (10⁻⁹ relative): above-peak fraction **0** (was ≤ 1 %) | stricter; the display stage guarantees it |
| P-4 order | P4-G1 + P4-G2 against pcond's L_eff; R3 (N/A plus the flat guard) on a degenerate reference | `d1/p4v2/PREREG.md` |
| P-5 S1 | sky ≤ 2 cd/m², lamps/sky ≥ 10, poplar Weber ≥ 0.1, reversals ≤ 5 %, halo within 1.5× | – |
| P-6 S3 | displayed bar Weber > 0 | – |
| P-7 S2 | global-mean max step ≤ 2 %, sky-median max step ≤ 2 %, isolated flashes ≤ 1 | – |
| P-8 F1 | emitted Y non-decreasing per colour (relative tolerance 10⁻⁶); **no** patch channel above peak at any level; P-2a/P-2b hold | stricter (was: above peak allowed ≥ 10 cd/m²) |
| P-9 new artefact classes | contact sheet of all stills plus crops. Any **new** class (halo, banding, contrast reversal, colour fringing, blocking, posterisation at the projection boundary) is a FAIL with a description. Visual, stated as such | two known, documented outcomes are **not** new classes: S1 lamp cores whiten at the 100 cd/m² peak (the accepted Y-priority price, `d1/display_r/`); the S5 saturated blue sky (a B residual: in-gamut chromaticity of the frozen B) |

## Outcome
- **All gates pass:** **D1 accepted.** Pipeline frozen; D1 closed.
- **Any gate fails:** D1 stays open for that failure only, as a **new counterexample** with a diagnosis. The fix gets
  its own PREREG. No re-tuning inside this run.

## Prediction
All of P-1…P-9 pass. The gate values reproduce those already measured on the same frozen components (DR v2, P4v2):
- S1: sky 0.318, lamps/sky 315, Weber 0.593, reversals 0, halo 0.91;
- S3 Weber 0.753;
- S2 step 0.071 %, flashes 0;
- F1 monotone;
- P-4: 0 inversions, S3_nobar N/A.
