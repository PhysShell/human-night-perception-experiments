# D1 acceptance: the frozen A+B pipeline on the whole corpus

**Pre-registered** in `PREREG.md` (commit `4214002`, before any pipeline code). Nothing was tuned after the run.

    tracks/temporal-glare-2009/py.sh d1/pipeline/make_f1.py          # F1 fixture -> .cache/F1.exr (+ layout)
    nix develop -c d1/pipeline/run_axis_a.sh                          # frozen axis A (axis_a.sh = pcond -s -c) -> .cache/A
    tracks/temporal-glare-2009/py.sh d1/pipeline/pipeline.py          # B + recombination + P-1..P-6, P-8 -> acceptance.json
    tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline        # P-7 (S2 clip) -> d0/results/tables/metrics.jsonl
    nix develop -c d1/pipeline/diag_p4.sh                             # DIAGNOSTIC only (P-4 cause), not a gate

Outputs go to `d0/work/out/d1_pipeline/frozen/` (not committed). `sheet_acceptance.png` shows S0 and S1 in full,
a poplar crop ×4, the lamp ribbon at 1:1, S3_bar ×4 and F1. The S4/S5 sheet uses Fairchild-derived inputs and is
not committed (`d0/work/sheets/`).

## Result: D1 NOT accepted. 3 of 9 gates fail; D1 stays open for exactly these failures

| gate | result | values |
|---|---|---|
| P-1 numerics | **PASS** | all stills, F1 and all 48 S2 frames finite |
| P-2 B preserved | **PASS** | max \|Δu′v′\| on unclipped pixels 3.4·10⁻¹⁶ (stills, F1); 3.6·10⁻⁸ (S2 frames) |
| P-3 clipping ≤ 1 % | **FAIL (S5)** | S5 **4.13 %**. Others: S1 0.32 %, S4 0.11 %, S0/S3 ≤ 0.003 %, S2 max 0.32 % |
| P-4 Spearman ≥ 0.98 | **FAIL (S4, S5, S3_nobar)** | S0 0.987, S1 0.987, S3_bar 1.000, **S4 0.937**, **S5 0.968**, **S3_nobar undefined (NaN)**; S2 min 0.987 |
| P-5 S1 A3-K0 gates | **PASS** | sky 0.316 cd/m², lamps/sky 262, poplar Weber 0.591, reversals 0 %, halo ratio 0.91 |
| P-6 S3 bar | **PASS** | displayed bar Weber 0.75 (bar darker than the sky beside it) |
| P-7 S2 temporal | **PASS** | mean max step 0.07 %, sky-median max step 0 %, isolated flashes 0 |
| P-8 F1 | **FAIL** | red and blue not monotone; blue above peak at 1 and 3.16 cd/m² (below the 10 cd/m² allowance) |
| P-9 new artefact classes | **FAIL (S5), visual** | S5 twilight sky: large saturated, clipped bright-blue area. No halo, banding, reversal, fringing or blocking on any still |

F1 displayed luminance (cd/m², median per patch; source 10⁻⁴ … 10² in half decades; `*` = channel above peak):

| colour | 10⁻⁴ | 10⁻³ | 10⁻² | 10⁻¹ | 1 | 3.16 | 10 | 31.6 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| neutral | 0.12 | 0.35 | 1.37 | 4.59 | 8.93 | 13.4 | 23.6 | 47.7 | 91.0 |
| red | 0.10 | 0.15 | 0.53 | 2.03 | 6.48 | 11.4 | 21.5* | 21.4* | 21.3* |
| blue | 0.18 | 0.72 | 2.58 | 6.33 | 11.0* | 9.75* | 8.03* | 7.66* | 7.44* |
| green | 0.12 | 0.36 | 1.42 | 4.71 | 9.08 | 13.6 | 23.7 | 47.8 | 71.7 |

Cyan, warm lamp and yellow are monotone and never above peak below 10 cd/m².

## Diagnosis (after the run; describes the failures, changes nothing)

**R1: P-3, P-8, P-9: no gamut handling in the A0 recombination.**
- Axis A assigns Y_display from luminance alone. It does not know the largest luminance the display can emit at
  B's chromaticity: ≈ 21.3 cd/m² for the Rec.709 red primary, ≈ 7.3 cd/m² for the blue primary, 100 for white.
- Recombination x = b·(Y_display/Y(b)) then asks for more than the display can produce. The channel clips, the
  emitted Y falls back to the ceiling and hue shifts towards the primary.
- On F1, the ceiling itself depends on the source level. At low L, B's chroma collapse pulls blue towards white,
  so the ceiling is high. As L rises, B restores saturation and the ceiling falls towards the pure primary
  (blue ≈ 7.3, red ≈ 21.3). Once a patch sits at the ceiling, its emitted Y therefore *decreases* with source
  luminance: blue 11.0 → 7.44, red 21.5 → 21.3.
- S5 is the scene-scale instance: the bright, still mesopic twilight sky keeps a saturated blue chromaticity from B
  and receives a Y_display that blue cannot carry.
- Not caught earlier because A3-K0 was gated on S1 only, where just 0.3 % of pixels clip. V0 (pcond as a whole
  renderer) had its own out-of-gamut handling; A0 dropped it together with pcond's chromaticity.

**R2: P-4 on S4/S5: `-c` versus a photopic-rank gate.**
- `diag_p4.sh` reran axis A with `-s` only. Spearman(physical Y, axis-A Y) = **1.000** on both S4 and S5, against
  0.937 / 0.968 with `-s -c`.
- The order change therefore comes entirely from `-c`, whose scotopic luminous response ranks blue above red at
  low levels. That is the intended Purkinje behaviour of the frozen axis A.
- P-4 was written against photopic Y, so the gate and the frozen model disagree on semantics. It is recorded as a
  FAIL as pre-registered; it is not reinterpreted after the fact.

**R3: P-4 on S3_nobar: a gate-definition defect.** S3_nobar is a near-uniform field. Spearman is undefined on
(near-)constant input and returns NaN; NaN ≥ 0.98 is false. The pipeline itself behaves correctly on S3_nobar:
P-1, P-2 and P-3 all pass.

## What passes
- On the reference scene (S1), the whole pipeline reproduces A3-K0:
  - the night stays dark (0.32 cd/m²);
  - poplars are separated from the sky (Weber 0.59) with no halo or reversal;
  - lamps are bright (lamps/sky 262), with saturation retention 0.52 (V0: 0.35);
  - B's chromaticity is exact.
- The pipeline adds no temporal artefact on S2 and keeps the S3 bar visible.
- S0 and S4 look plausible on the sheet.
- The failures are confined to a single mechanism class: bright saturated chromaticities, and `-c` against
  photopic order. No new spatial artefact class appeared.

## Outcome (per PREREG)
- D1 is **not accepted**. It stays open for exactly R1, R2 and R3.
- A and B are unchanged. Every fix needs its own pre-registration. Candidates, none started:
  - **R1 gamut-aware recombination.** Either cap Y_display at the luminance the display can emit at B's
    chromaticity (this keeps hue and B, but loses monotonicity at the cap), or compress chroma towards white
    until the colour fits (this keeps Y but deliberately breaks P-2 on those pixels). Gates: F1 monotone, P-3 on S5.
  - **R2.** Either redefine P-4 against the scotopic/mesopic-weighted luminance that `-c` actually targets, or
    accept `-s` and lose `-c`'s scotopic luminous response. The choice is about semantics and belongs to the lead.
  - **R3.** Define P-4 only where the physical-Y dynamic range of the subsample exceeds a threshold. Otherwise
    report it as N/A.

---

# D1-R1: display-aware minimum chroma projection (`PREREG_R1_gamut.md`, commit `42944c6`, before code)

    tracks/temporal-glare-2009/py.sh d1/pipeline/pipeline.py r1_gamut      # -> acceptance_r1.json, d0/work/out/d1_pipeline/r1_gamut/
    tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline             # P-7 and D0 metrics for r1_gamut

The `frozen` variant of `pipeline.py` is unchanged (same code path, the default). `sheet_r1_F1.png` shows F1 frozen
vs R1. The S5 comparison sheet is Fairchild-derived and not committed (`d0/work/sheets/sheet_d1_r1_S5.png`).

## Result: R1 KILLED by its pre-registered rule (G3 literal, G5)

| gate | result | values |
|---|---|---|
| R1-G1 in-gamut identity | **PASS** | max \|Δ\| = 0 on every image |
| R1-G2 P-2a | **PASS** | \|Δu′v′\| ≤ 3.4·10⁻¹⁶ (stills, F1), S2 all pass |
| R1-G3 P-2b | **FAIL (literal)** | ΔY/Y ≤ 1.0·10⁻⁷ ✓, chroma never increases ✓, tightness 0 ✓; **hue: max 3.14 rad** |
| R1-G4 gamut | **PASS** | every channel in [0.1, 100]; P-3 above-peak 0 on every image (S5: 4.13 % → 0) |
| R1-G5 F1 monotone | **FAIL** | blue: 12.7 → **17.7 → 12.2** → 13.8 → 13.9 cd/m² (source 1 → 3.16 → 10 → 31.6 → 100). No patch above peak; red now monotone |
| R1-G6 numerics | **PASS** | finite everywhere |
| R1-G7 S5 visual | clipping removed; **saturated blue sky essentially unchanged** | projected 4.1 % of S5, median t = 0.91 (p5 0.81) |

Reported: P-5 PASS (sky 0.316, lamps/sky 316, poplar Weber 0.591, reversals 0, halo 0.91). P-6 PASS (0.75).
P-7 PASS (mean step 0.07 %, sky step 0, flashes 0). **S1 lamp saturation retention 0.52 → 0.0007** (D0 metric).

## Diagnosis (after the run; nothing changed)

**G3 is a gate-definition defect.**
- Every hue-failing pixel (S0 9, S1 4716, S4 191, S5 326) has Y_A = 100 cd/m², the display peak: pcond gave
  Y_rel ≥ 1, clamped by ≤ 10⁻⁷.
- At peak luminance the only colour SDR100 can emit is white. So t = 0, the output chroma is exactly 0 (≤ 6·10⁻¹⁷),
  and hue is undefined.
- On every pixel with output chroma > 10⁻⁶, the hue error is ≤ 1.9·10⁻¹³ rad.
- The pre-registered mask used B's chroma instead of the output's. It is recorded as FAIL anyway.

**G5 is not caused by the projection; the non-monotonicity is inside the frozen axis A.**
- R1 keeps Y_A exactly (ΔY/Y ≤ 10⁻⁷), so the blue non-monotonicity is already present in Y_A.
- Cause, from the Radiance source: pcond converts to the output primaries in `matscan()` (`src/px/pcond2.c`), then
  calls `clipgamut()` (`src/common/spec_rgb.c:482`). That function pulls out-of-gamut colours towards a grey with
  the same **RGB channel mean**, not the same luminance.
- Measured on the axis-A output:
  - blue 10 cd/m² → RGB (0.047, 0.055, **1.0**), Y_rel 0.121;
  - blue 3.16 → (0.117, 0.125, 0.856), Y_rel 0.176;
  - red 100 → (**0.996**, 0.22, 0.22), Y_rel 0.387, against neutral 0.910.
- The frozen axis-A luminance ("Rec.709 luminance of pcond's display-relative output") therefore contains pcond's own
  non-luminance-preserving gamut clip.
- No downstream gamut mapper can repair this, because the Y it receives is already non-monotone.
- The earlier R1 diagnosis ("no gamut step at recombination") was right for P-3 and wrong as the complete
  explanation of P-8.

**G7 / the old P-9 observation.**
- The saturated S5 sky is mostly B's chromaticity at the sky's (mesopic–photopic) luminance, not clipping. Only 4 %
  of S5 needed projection, and only by ~10 % chroma.
- Whether a saturated twilight sky is an *artefact* or the correct appearance is a question about B; R1 cannot
  answer it.

**Lamp colour.**
- pcond maps the S1 lamp cores to Ldmax. At Y = 100 a Y-preserving projection must emit white, so the lamps lose
  all colour (retention 0.0007).
- The frozen pipeline kept lamp colour (0.52) only by violating Y through channel clipping.
- pcond's own output is white there too (`clipgamut` brt > brtmax → white).

## Outcome
- **R1 is KILLED as pre-registered.** The pipeline stays at the frozen version; `acceptance.json` is unchanged.
- The kill is informative:
  - the projection itself behaved exactly as specified (G1, G2, G4, G6; Y and hue preserved wherever hue exists);
  - the remaining F1 failure sits upstream, in how axis A's luminance is extracted from pcond.
- Candidate next step, needing a new pre-registration (not started):
  - **A-extraction fix.** Take Y_A = F(L_eff), where F is pcond's own tone-mapping function written by
    `pcond -x mapfile` (`putmapping()`), and L_eff is the post-`scotscan()` effective luminance recomputed exactly
    from the XYZE file pcond reads (`pcond3.c:474`, `cielum()`). This is pcond's luminance before `clipgamut()`.
  - The same L_eff is the natural reference for P-4 v2.
  - Lamp-core colour at peak luminance remains a separate, unavoidable SDR trade-off: Y or chroma.
