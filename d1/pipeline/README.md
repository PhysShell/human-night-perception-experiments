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
