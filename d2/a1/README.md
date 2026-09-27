# D2-A1 / A1a result: **literal KILL (H2)**. Per the PREREG, A1b is next. The diagnosis is recorded below.

Pre-registered in `PREREG.md` (`d6c1aa5`); code `run.py` (`efce658`); results in `results.json`. `d1/verify_manifest.sh`
was OK before and after. No frozen file was touched.

## RoadLine-A2 canonical, frozen D1 with Y_A × 0.2641
| gate | frozen D1 | A1a | verdict |
|---|---|---|---|
| **H1** frame fraction at a channel ceiling (≤ 4.35 %) | 17.92 % | **0.29 %** | PASS |
| **H2** road pixels at a channel ceiling (≤ 0.1 %) | 82 % above the peak | **1.15 %** | **FAIL** |
| H3 floor (frame / field) (≤ 0.62 %) | 0 / 0 | 0 / 0 | PASS |
| R3 extraction C0; display gates | | C0 ✓; G1–G3, S-1…S-3 ✓ | PASS |
| R4 ordering | | no inversion | PASS |
| R5 presence vs the linear anchor (same s) | | all six present in both | PASS |

**Diagnosis of the H2 failure** (after the run; the verdict is not changed):
- **Where:** all 3410 road pixels at the ceiling (29–38 m from the eye, the brightest pool) have the **blue** channel at
  65535. R and G reach the ceiling in only 208 of them.
- **Why:** axis B's rod-term tint (the known residual, `d2/b2`) turns the lit road bluish, so the blue channel reaches
  100 cd/m² while the display luminance is 87–100 cd/m².
- **Luminance itself:** road pixels at the luminance peak (≥ 99.9 cd/m²) are **208 = 0.07 %**, within 0.1 %.
- **Cause:** H2 counted "any channel" and so conflated B's colour with A's luminance saturation. That is my gate-design
  error, since s was derived from luminance (road p99.9 at the peak).
- **Classification:** measurement design, with a known B residual involved. **It stays a literal FAIL.**

**What A1a showed nonetheless (for the record, not a PASS):**
- One global scale removes the broad luminance saturation: 17.9 % → 0.29 % of the frame clipped; the road luminance at
  the peak falls to 0.07 %.
- It does so without darkness collapse (floor 0 %) or lamp-order/presence loss.
- The V6 visual gate was not reached; the image is in `renders/a1a_sheet.png` (frozen D1 vs A1a).

## Corpus under the same fixed s (secondary, reported)
- **P-1, P-2a, P-3, P-4, P-5, P-6, P-8 all PASS.**
  - S1: sky 0.158 cd/m², lamps/sky 635, poplar Weber 0.316, reversals 0, halo 0.95.
  - S3 Weber 0.446.
  - Ceiling fractions ≤ 2.0 % (F1). S3_bar floor 0.62 %, equal to the anchor.
- **P-2b FAIL on S5 and on some S2 frames.** On S5, S-2 shows a chroma increase of 1.0·10⁻⁸ (tolerance 10⁻¹²); G3 has
  no bad pixel; S2 frame 1 passes.
- Classification: the sRGB knee round-trip class (`d1/ERRATA.md` E1), made more likely by the darker encoding. It
  stays a literal FAIL.
- P-7 was not run.

## Consequence (per the PREREG)
- **A1a is KILLed.** The next step per section 5 is **A1b**: one pre-registered luminance-only monotonic shoulder after
  the frozen A, B frozen.
- If A1b fails too, the direction is KILLed.

## Superseded next step: A1a2, then D2-A1 closed
- At the user's direction, A1b was **not** run. The corrected falsifier A1a2 (`PREREG_A1a2.md`, `9852123`; code
  `c1b76d9`; `results_a1a2.json`) ran instead. It has a luminance-based H2v2 and an independent hold-out (N1 Camera C,
  the same s).
- **Automatic results:** H2v2 0.070 %; HO1 0.046 %; HO2 0 %; HO3 readable; R3 PASS; manifest OK before and after.
- **V6 (external): PASS.**
- **Conclusion:** the linear shape of axis A is not falsified, and pcond's exposure selection is the remaining suspect.
  **D2-A1 is closed**; A1a stays a literal KILL. See the verdict section in `PREREG_A1a2.md`.
