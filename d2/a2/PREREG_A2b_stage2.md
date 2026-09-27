# D2-A2b stage 2 pre-registration: the unchanged Q99.9 guard as a per-scene exposure selector

Committed **before** any stage-2 code or output. It follows `PREREG_A2b.md` §4 and `PREREG_A2c.md` §7 (A2c PASS,
`c3132ff`).

**Standing results:**
- **A2b stage 1 stays a literal KILL on H2v2.** A2c showed that H2v2 was over-strict against the visual defect.
- **The Q99.9 policy is not accepted.**
- D1 is not changed. `d1/verify_manifest.sh` runs before and after.

## 1. Question
Does the **same, unchanged** policy behave as an exposure selector on independent scenes? That means it corrects where
exposure is bad, and leaves already-accepted scenes untouched or still accepted, stably over time. The alternative is
a disguised ND filter.

## 2. The policy: identical code, not a copy
- **Where it comes from.** The function `s_hist` is loaded from the committed `d2/a2/run_A2b.py` (`bacfd86`, the code
  that produced A2b/X):
  - its source segment is extracted with `ast`;
  - its sha256 is **asserted** equal to the value recorded in the stage-2 code, computed from `bacfd86`;
  - it is exec'd, not retyped.
- **The scale-line substitution** in the frozen display code is the same string as in `run_A2b.py`, also asserted.
- **Per image.** Each S2 frame is its own image. **There is no temporal smoothing.**
- **s = 0.2641 is not used anywhere.**

## 3. Inputs (all existing; 0 renders)
| scene | input | frozen A cache | frozen D1 output (for bit-identity / comparison) |
|---|---|---|---|
| Hero | `n1/work/hero_cdm2.exr` | `N1_hero` | `n1/renders/final/hero.png` |
| Camera B | `n1/work/view_B/view_cdm2.exr` (**present**, so included) | `N1_B` | `n1/renders/final/cam_B.png` |
| Camera C | `n1/work/view_C/view_cdm2.exr` | `N1_C` | `n1/renders/final/cam_C.png` |
| S0, S1, S3_bar, S3_nobar, S4, S5, F1 | `d0/work/inputs/…`, `d1/pipeline/.cache/F1.exr` | frozen | `d0/work/out/d1_pipeline/final/*.png` |
| S2 frames 1–48 | `d0/work/inputs/S2/` | frozen | `d0/work/out/d1_pipeline/final/S2__PHONE_SDR100_DARK/` |

The corpus runs through the frozen `d1/final/run.py` text, exec'd with only these replacements:
- **the scale line**, as above;
- **`S_H` added** to `run_image`'s returned dict;
- **Yexp** in the P-4 logic uses that image's `S_H`;
- **the output folder** is `d2/a2/work/final`;
- **S2 frames** are written to a temporary file, read into memory and deleted;
- **the acceptance JSON path** is `d2/a2/work/acceptance_A2b2.json`.

**Scope.** The corpus is D1's own P-gates on the stills, F1 and the S2 frames. RoadLine is not re-run; its stage-1
numbers and the A2c verdict stand.

## 4. P-7 (S2 temporal): mandatory now
- **What runs.** The frozen D0 `clip_metrics` from `d0/metrics.py`, **unchanged**, on the 48 guarded S2 frames.
- **How the frames reach it.** `read_code` is pointed at the in-memory frame codes (streaming; disk is ~220 MB). The
  frames keep their `frame_NNNN.png` names, so the function's own frame-index parsing is unchanged.
- **Criterion (frozen `d1/final/PREREG.md` P-7):**
  - global-mean max step ≤ 2 %;
  - sky-median max step ≤ 2 %;
  - isolated flashes ≤ 1.
- **Reported per frame:** q, s_hist, Δ stops, active.
- **No separate threshold on Δs_hist** (that would be a new constant). The output gate decides.
- **Any P-7 failure is a stage-2 KILL.**

## 5. Gates
| id | scene(s) | criterion |
|---|---|---|
| **BI** | every image where s_hist = 1 | the output PNG is **bit-identical** to the frozen D1 output |
| **R3** | hero, B, C | extraction C0 bit-identical, AX-C2/C3 ≥ 99.9 %; display G1–G3, S-1…S-3 (E1 class classified, not KILL) |
| **HO** | C | HO1 luminance ceiling ≤ 0.444 %; HO2 floor ≤ 0.62 %; HO3 lamp head (961, 153) ≥ 1 code (as A1a2) |
| **CF** | hero, B | frame luminance ceiling (Y_disp ≥ 99.9) ≤ that view's frozen-D1 value; floor ≤ 0.62 % |
| **P** | corpus | D1 final P-1…P-6, P-8 (as `d1/final/run.py`), and P-7 per §4; per natural still: frame any-channel ceiling ≤ 4.35 % and floor ≤ 0.62 %; E1 knee-class literal FAILs stay FAIL, classified, not KILL |
| **ND** | natural accepted scenes: hero, B, C, S0, S1, S3_bar, S3_nobar, S4, S5, S2 (active if any frame is active) | the guard must be **inactive on at least one** |
| **V** | every **active** natural scene | external observer, sheet format, frozen D1 vs guard side by side: new A-side defect? darkness collapse? structure visibly degraded? |

**Not applicable:**
- R4/R5 are N/A here: they were defined only for the RoadLine lamp row, which is not re-run.
- F1 is synthetic and outside ND and V.

## 6. Required table (`results_A2b2.json` and the README)
Per scene: frozen EXPOSURE (pcond), q = Q99.9(Y_A), s_hist, Δ stops, active, frame luminance ceiling, floor,
automatic verdict, visual needed.
- **RoadLine:** its stage-1 numbers; "A2c: already established".
- **S2:** summarised as min/median/max, with the per-frame rows in the JSON.
- **S1, S3 and S5** are commented separately in the text.

## 7. KILL (unchanged from `PREREG_A2b.md` §4, plus P-7)
- a new substantive corpus FAIL (anything but the E1 class);
- **a P-7 failure**;
- a BI failure;
- a new visual A-side defect on the hero, B or C;
- darkness collapse;
- visibly degraded structure on an accepted scene the guard darkens;
- **ND:** the guard is active on every natural accepted scene.

There is no policy fix after viewing.

## 8. Reading (fixed now)
1. **Automatic and visual PASS:** RoadLine is corrected, most ordinary scenes are untouched, and S2 is stable. **Q99.9
   behaves as a real exposure selector.** D2-B3 is not needed for this failure. Adopting it into D1 is a separate
   decision with the full no-regression set.
2. **FAIL because active accepted scenes become too dark** (visual or floor): the global-scalar highlight/shadow
   trade-off is confirmed, so **A1b (shoulder) is earned**.
3. **FAIL by ND, by P-7 instability, or by content-inappropriate activation:** the **global-histogram branch is
   KILLed**, and only then does richer metering / adaptation-field research (D2-B3) get grounds.

## 9. Budget
0 renders. The corpus plus S2 take minutes of CPU. Outputs are only the stills/F1/view PNGs, ≈ 30 MB; the S2 frames
stay in memory.

## Prediction (recorded before running; no stage-2 statistic has been computed)
- **Inactive:** S0, S3_bar, S3_nobar and S4, which have no bright practicals: q ≤ 1, so bit-identical.
- **Active:**
  - S1 (lamps against the sky) and S5: small darkening, well under 1 stop;
  - the hero, B and C (a practical lamp in frame): the hero and C were accepted at a 0.44 % / ≲ 4 % ceiling, so q > 1,
    and I expect |Δ| ≈ 0.5–1.5 stops.
- **ND passes** (≥ 4 inactive).
- **P-7 is the real risk.** S2's lamps drive q frame by frame. I expect the mean step to stay under 2 %, with no
  flashes, but with low confidence.
- **The main stage-2 risk is visual:** darker hero/C.

## Automatic results (`results_A2b2.json`; code `13a6bb5`, report fix `34800ce`)
**Run history.** Run 1 crashed in *reporting*: pcond took the mapped branch on F1, so there is no EXPOSURE header. It
crashed after the corpus gates had printed and before any result file. The report fix changes no gate and no policy,
and the full re-run is the result. `d1/verify_manifest.sh` before and after: all OK. The policy code's sha256 is
asserted equal to `bacfd86`.

| scene | frozen EXPOSURE | q = Q99.9(Y_A) | s_hist | Δ stops | active | luminance ceiling (frozen) | floor | automatic |
|---|---|---|---|---|---|---|---|---|
| RoadLine (stage 1) | 444.8 | 3.711 | 0.2692 | −1.89 | yes | road 0.150 % | 0 % | literal KILL H2v2; A2c visual PASS |
| Hero | 1136.8 | 1.290 | 0.7741 | **−0.37** | yes | 0.100 % (0.192 %) | 0 % | CF PASS, R3 PASS |
| Camera B | 453.5 | 0.286 | 1 | 0 | no | 0 % (0 %) | 0 % | BI PASS, CF PASS, R3 PASS |
| Camera C | 982.6 | 1.591 | 0.6280 | **−0.67** | yes | 0.101 % (0.444 %) | 0 % | HO1–HO3 PASS (head 56 966 codes), R3 PASS |
| S0 | 1390.4 | 0.061 | 1 | 0 | no | — | 0 % | BI PASS, P PASS |
| **S1** | 1390.0 | **10.23** | **0.0977** | **−3.36** | yes | any-ch 0.17 % (0.32 %) | 0 % | P-1…P-5 PASS |
| S3_bar | 1260.8 | 0.003 | 1 | 0 | no | — | **0.6250 %** | BI PASS, P PASS; **CF literal FAIL** (see below) |
| S3_nobar | 1260.2 | 0.003 | 1 | 0 | no | — | 0 % | BI PASS, P PASS |
| S4 | 16.7 | 0.583 | 1 | 0 | no | — | 0 % | BI PASS, P PASS |
| S5 | 6.86 | 0.898 | 1 | 0 | no | any-ch **4.3545 %** | 0 % | BI PASS, P PASS; **CF literal FAIL** (see below) |
| F1 (synthetic) | — (mapped) | 0.925 | 1 | 0 | no | — | — | BI PASS, P-8 PASS |
| **S2** (48 frames) | 1390.0 | 10.01–10.26 | 0.0974–0.0998 (median 0.0982) | **≈ −3.35** | all 48 | ≤ 0.100 % | 0 % | P-1…P-4 PASS, BI n/a |

**Corpus P-gates:**
- P-1 … P-6 and P-8 all PASS.
- **P-2b PASS everywhere.** The E1 knee artefact did not occur on the guarded images.

**P-7 (S2 temporal): PASS.**
- mean max step 0.28 %;
- sky-median max step 0.19 %;
- isolated flashes 0;
- source-energy modulation 1.2 %.

**BI:** PASS on every inactive image.

**ND:** PASS. The guard is active on the hero, C, S1 and S2, and inactive on B, S0, S3_bar, S3_nobar, S4 and S5.

**CF literal FAILs on S3_bar and S5, stated and classified:**
- **The numbers.**
  - S3_bar floor 0.6250 % > 0.62 %;
  - S5 any-channel ceiling 4.3545 % > 4.35 %.
- **Both images are inactive and bit-identical to the accepted frozen D1 outputs.**
- **Cause.** The limits are those images' own frozen values, rounded *down* when written (D2-A1 PREREG: "S3_bar
  0.62 %", "S5 4.35 %").
- **Classification.** Anchor rounding in my threshold transcription, measurement design. **Not a guard effect.** The
  FAILs stay literal.

**S1 in plain terms, the main finding:**
- **The guard sees q = 10.2.** The street lamps cover more than 0.1 % of the frame at ten times the display peak. It
  therefore darkens the whole moonlit scene by **3.36 stops**.
- **P-5 passes, but with a large movement:**

  | S1 metric | frozen D1 | guard | P-5 limit |
  |---|---|---|---|
  | displayed sky | 0.318 cd/m² | 0.121 cd/m² | — |
  | poplar Weber | 0.593 | **0.152** | ≥ 0.1 |
  | lamp/sky | 315 | 598 | — |

- S2 (the same scene family) is darkened identically and stably.
- Whether this is "visibly degraded structure" or "darkness collapse" is the **visual** gate's call.

**S3 and S5 are untouched.**

**Against the prediction:**
- **Right:**
  - S0/S3/S4 inactive;
  - ND passes;
  - C at −0.67 stop.
- **Wrong:**
  - **S1 predicted as a small darkening under 1 stop; it is −3.36 stops;**
  - S5 predicted active; it is inactive;
  - hero predicted at 0.5–1.5 stops; it is −0.37 stop;
  - P-7 predicted as the real risk; it passes easily.

**Visual gate still to run** (external, frozen vs guard): hero, Camera C, S1, S2. The S2 frames were streamed, not
kept. For the sheet, frames 1 and 48 are recomputed through the identical code path, with s_hist asserted equal to the
recorded per-frame value.

**Visual sheets:**
- `renders/A2b2_sheet_{hero,C,S1,S2}.png`, made by `sheet_A2b2.py`;
- the S2 frames' s_hist matched the recorded values;
- S1/S2 are laid out as the full frame plus a 1:1 sky band (layout only).

**My reading** `A2b2_my_reading.txt`, sha256 `8dbca947ee144b6d879c09daa9eb0814334212c54e79313142fec76c89196e5e`, was committed before the verdict.

## Visual verdict (external observer, given without opening my reading): **stage 2 FAIL**
| scene | new A-side defect | darkness collapse | structure visibly degraded | verdict |
|---|---|---|---|---|
| Hero (−0.37 stop) | no | no | no | **PASS** |
| Camera C (−0.67 stop) | no | no | no | **PASS** |
| **S1 (−3.36 stops)** | **yes: excessive global darkening** | not a literal floor collapse, but substantial perceptual crushing | **yes** | **FAIL** |
| **S2 (≈ −3.35 stops)** | **yes: the same class** | not a literal collapse | **yes** | **FAIL** |

**Observer's notes:**
- **S1.** Frozen D1 separates sky, poplar silhouettes, the source line and the horizon. Under the guard, the sky/
  background separation shrinks, the silhouettes separate worse, and the low-contrast structure around the lamp row is
  pressed into darkness.
  - The automatic floor = 0 % is not wrong: it is not a literal black floor.
  - The P-5 pass (poplar Weber 0.152 ≥ 0.1) did not catch it.
- **S2.** P-7 PASS is confirmed visually: the guard is consistent from frame to frame. It proves the absence of
  flicker, not the absence of exposure damage ("very reliably spoiled exposure").
- **The cause is not content-inappropriate activation.** The lamps really do cover more than 0.1 % of the frame, and
  the global scalar protects the highlights, as designed. The problem is structural: **one global scale cannot keep
  both the bright practicals and the low-contrast night structure of S1/S2.** RoadLine needs strong darkening; the hero
  and C tolerate moderate darkening; S1/S2, under the same principle, are damaged.

**My reading** (`A2b2_my_reading.txt`, sha256 matches `3ab0cbac…`): hero PASS, C PASS, S1 FAIL, S2 FAIL. It agrees; it
does not count.

**Outcome (§8, reading 2, pre-registered):**
- **Stage 2 FAIL.** Cause: the global-scalar highlight/shadow trade-off.
- **The Q99.9 global selector is not acceptable as it is.**
- **The global-histogram branch is not disproven** as a selector: its activation was content-appropriate, and ND and
  P-7 passed.
- **D2-B3 is not earned by this result.**
- **A1b** (one pre-registered, luminance-only, monotonic shoulder after the frozen A, B frozen; `d2/a1/PREREG.md` §5)
  **is now earned.** The independent counterexample is RoadLine versus S1/S2 under one scalar.
- The CF literal FAILs on S3_bar and S5 stay recorded as classified (anchor rounding, bit-identical inactive outputs).
