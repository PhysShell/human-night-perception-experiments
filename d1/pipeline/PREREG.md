# D1 acceptance pre-registration: the frozen A+B pipeline on the whole corpus

Committed **before** the pipeline code runs. Nothing below may be tuned per scene.

## Frozen pipeline (D1 result, a composite model, not a single physiological model of vision)
- **Axis A:** the pcond-derived scotopic luminance mapping.
  - Radiance `pcond -s -c`, path A of `m1/pcond_colorimetric.sh` (`ra_xyze` → pcond on XYZE).
  - Defaults: Ldmax 100, 100:1. No `-a`, `-v` or `-h`.
  - HFOV = image width / scene px/deg (manifest), as in D0.
  - Luminance only: Y_display = 0.1 + 99.9·Y_rel (SDR100 DARK display model).
- **Axis B:** chromaticity only. The Filament-derived Cao/Kirk kernel (verbatim, a = 1, κ = 3) followed by the
  Wanat-derived local chroma collapse (t = L/(L + 0.108), per-pixel physical L, radial u′v′, Y- and hue-preserving).
- **Recombination (A0):** x = b · (Y_display / Y(b)).
- **Encoding:** SDR100 sRGB, 16-bit PNG, D0 output contract.
- **Out of scope:** axis C (near-threshold temporal rod noise, Kellnhofer 2015). Also local contrast (Wanat A2,
  killed), acuity and glare.

## Corpus
- S0, S1, the S2 clip (48 frames), S3_bar and S3_nobar, S4, S5.
- **F1:** a synthetic patch fixture.
  - An image of 7 patches (neutral, red, green, blue, cyan, warm lamp, yellow) × 13 luminance levels
    (10⁻⁴…10² cd/m², half-decade steps).
  - Each patch is 32 × 32 px on a 10⁻⁵ cd/m² background.
  - HFOV 30°.
- Outputs go to `d0/work/out/d1_pipeline/frozen/`, so `d0/metrics.py` can measure them exactly like the D0 donors.

## Acceptance gates (necessary conditions; applied to every still, the clip and F1)
| id | criterion |
|---|---|
| P-1 numerics | finite; no NaN or Inf |
| P-2 B preserved | \|Δu′v′\| (displayed vs B) ≤ 10⁻⁶ on pixels with no channel clipped |
| P-3 clipping | pixels with a channel above the display peak ≤ 1 % |
| P-4 luminance order | Spearman ρ(physical Y, displayed Y) ≥ 0.98 per still, on a 20 000-pixel random subsample (seed 0) |
| P-5 S1 | the A3-K0 gates reproduce: sky ≤ 2 cd/m², lamps/sky ≥ 10, poplar Weber ≥ 0.1, reversals ≤ 5 %, halo within 1.5× |
| P-6 S3 | the bar stays darker than the sky beside it on the display (displayed bar Weber > 0). The HDR-VDP P_det diagnostic is reported, not gated |
| P-7 S2 temporal | D0 clip metrics: global-mean max frame step ≤ 2 %, sky-median max step ≤ 2 %, isolated-flash frames ≤ 1 |
| P-8 F1 | for each colour, displayed Y non-decreasing with patch luminance; each patch's displayed u′v′ equals B's (P-2); no patch channel above the peak except for levels ≥ 10 cd/m² (reported) |
| P-9 new artefact classes | a contact sheet of all stills plus crops. Any artefact class not seen in A3-K0 (halo, banding, contrast reversal, colour fringing, blocking) is recorded as a FAIL with a description. This is a visual check, stated as such |

**Outcome.**
- All gates pass: **D1 accepted**, pipeline frozen.
- Any gate fails: D1 stays open for that failure only. No re-tuning of A or B inside this acceptance; a fix needs
  its own pre-registration.
