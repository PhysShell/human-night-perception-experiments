# N1.7 pre-registration: keyframe motion stress on frozen D1 (B → C with a turn)

Committed **before** any N1.7 render or code. **Frozen D1 only.** A1b is not used; it was rejected as a D1 replacement
(`d2/DECISION_D2.md`). `d1/verify_manifest.sh` runs before and after.

## Question (narrow)
**Frozen D1 must remain spatially and tonally stable as the lamp enters the frame along a fixed B → C path.**

This is an application stress test inside the accepted N1 scene. It is **not** evidence of perceptual superiority.

## The path (fixed now)
- **Endpoints:** the accepted views B and C (`n1/views.json`), whose accepted renders and D1 outputs are reused.
  - B = (3, 47, 1.7), yaw 180°, pitch −3°.
  - C = (0.5, 18, 1.7), yaw −8.4° ≡ 351.6°, pitch 0°.
- **Position:** linear in t.
- **Yaw:** the **shortest signed path**, yaw(t) = 180° + 171.6°·t (not −188.4°).
- **Pitch:** linear, pitch(t) = −3°·(1 − t).
- **Keyframes, chosen to sample the source entry** (user decision). With linear yaw, the lamp head enters the frame
  only at t ≈ 0.82.

  | key | t | loc (x, y, z) | yaw | pitch | lamp head (projected px) | content |
  |---|---|---|---|---|---|---|
  | B | 0 | (3, 47, 1.7) | 180° | −3° | behind | accepted |
  | K070 | 0.70 | (1.25, 26.7, 1.7) | 300.12° | −0.9° | (−1019, −204): out | pool edge in frame; lamp and pole out |
  | K080 | 0.80 | (1.0, 23.8, 1.7) | 317.28° | −0.6° | (−136, 0): just out | pole at the left edge; lamp head just outside |
  | K0875 | 0.875 | (0.8125, 21.625, 1.7) | 330.15° | −0.375° | (324, 81): in | lamp inside |
  | C | 1 | (0.5, 18, 1.7) | 351.6° | 0° | (961, 153): in | accepted |

- The unequal spacing between neighbours is accepted, and it is stated in the visual question.

## Rendering (3 new renders, K070, K080, K0875)
- **Settings:** exactly the accepted B/C path. The entries are added to `n1/views.json` (the B/C entries unchanged) and
  rendered by `n1/view_render.py`, unchanged:
  - frozen `scene.py`, hash-checked;
  - stage b, 4096 spp, the same seed;
  - OIDN with the addendum-5 settings.
- **Known limitation, kept for consistency:** the accepted views keep the default `clip_end` of 1000 m
  (erratum N1-E1). The keyframes use the same, so the sequence is internally consistent.
- **OIDN gate per keyframe (N1.5 rule):** |denoised/noisy − 1| ≤ 2 % on the keyframe's crops.
  - **Crop rule, fixed now:** the union of the B and C pre-registered crop points that project in front of the camera,
    at least 24 px inside the frame.
  - Fewer than 2 such crops: the keyframe's OIDN gate is **INVALID**, not PASS, and it is reported.
- **Then:** the frozen D1 via `n1/view_eval.py` (unchanged), as for B and C. The raw multilayer EXR is deleted after
  its gate, for disk.

## Gates
**Automatic, per keyframe:**

| id | criterion |
|---|---|
| OIDN | as above |
| R3 | extraction C0 bit-identical, C2/C3 ≥ 99.9 %; display G1–G3, S-1…S-3 (E1 class: literal FAIL, classified, not STOP) |
| CF | floor ≤ 0.6250 %; any-channel ceiling ≤ 4.3545 % (the exact accepted-scene anchors) |
| SRC | where the projected lamp head is ≥ 7 px inside the frame (K0875; C as accepted): the lamp-head max code in r ≤ 3 px minus the annulus 4.5–7 px median ≥ 1 code |
| report | pcond EXPOSURE and tone-map mode; median Y_disp; frame luminance ceiling; floor; for B → K070 → K080 → K0875 → C, the log2 EXPOSURE step between neighbours (no numeric gate) |

**Visual:**
- **Who:** the external observer.
- **Sheet:** B, K070, K080, K0875, C in path order (sheet format), with t shown.
- **Not blind:** it is a continuity check.
- **Questions:**
  1. **Any new artifact class?**
  2. **Any sudden exposure/tone jump between neighbours** beyond what the viewpoint change explains, given the
     unequal t spacing?
  3. **Does the source enter gradually** (pole at the edge, then the lamp), rather than "teleporting" through a
     pipeline effect?
  4. **Is dark structure kept** (barn mass, lane, field; no collapse)?
  5. **Do the known residuals stay known** (white lamp core, B rod-term tint, E1)?
- **My reading** is hashed from the command output and committed before the verdict. It does not count.

## STOP / continue
- **Any new substantive failure is a STOP:** an automatic gate other than E1, or a visual "yes" to 1, 2 or 3, or a
  "no" to 4 or 5. **No dense motion is rendered.**
- **All pass:** a short dense motion along the same path becomes justified, with its **own addendum** (frame count,
  budget, and P-7 temporal gates on the clip), committed before rendering.

## Budget
3 Blender renders at the accepted B/C settings; minutes of CPU for D1; one sheet. The disk is tight (≈ 180 MB free),
so the keyframes are rendered one at a time, with the raw EXR deleted after its gate.

## Prediction (recorded before rendering)
- **OIDN and R3 pass.** E1-class 1-px literal FAILs are possible, as on C.
- **pcond's linear scale** moves smoothly from B (EXPOSURE 453.5, inside the pool) through the turn. It rises as the
  bright pool leaves the dominant part of the frame (K070 ≈ C-like, ~900–1000), with no reversal larger than
  ≈ 0.5 stop between neighbours.
- **The source enters gradually:** at K080 the pole is at the edge and the lamp is outside; at K0875 the lamp head is
  present with ≥ 1 code.
- **Main risk:** K080, where the bright pool fills the lower left while the lamp is just outside. A visibly brighter or
  darker frame than its neighbours is possible, because pcond's log-average adaptation shifts with what enters.

## Amendment 1 (before any render; no data seen): OIDN windows in image space
The pre-registered world-point crop rule gives 0 crops (K070) and 1 crop (K080), because the B/C points are not
visible from the turned camera. That would make OIDN INVALID on 2 of 3 keyframes. It was my design error.

**Replacement.** The OIDN gate checks the denoiser bias on the rendered frame, so world points are not needed.
- **Windows:** for every N1.7 intermediate keyframe, five fixed **48×48 image-space windows**, computed once from the
  1920×820 frame size and **identical for K070/K080/K0875**. Centres:

  | window | centre (px) |
  |---|---|
  | frame centre | (960, 410) |
  | upper-left quadrant | (480, 205) |
  | upper-right quadrant | (1440, 205) |
  | lower-left quadrant | (480, 615) |
  | lower-right quadrant | (1440, 615) |

- **Gate:** |mean_denoised / mean_noisy − 1| ≤ 2 % in **every** window.
- **Report only:** the whole-frame mean bias.
- **Lamp head:** if it is inside the frame, one 48×48 lamp-head window is added, **report only**. It does not affect
  PASS/FAIL, so the gate does not tighten because of the event under study.
- **A window crossing the frame edge is a design error, not a runtime fallback.** None does with these centres.
- **Implementation:** the gate step is `n1/n17/gate.py`, which mirrors `n1/view_eval.py`'s gate step with these
  windows. The D1 step is `n1/view_eval.py VIEW d1`, unchanged. The `views.json` keyframe entries carry `crops: {}`
  (unused).

## Run incident (driver `0b0b8c4`)
- **The disk filled during the K0875 render.** Blender wrote a **corrupted** raw EXR: OIIO reported "some scanline
  chunks were missing or corrupted", and the noisy-pass means were 0 in several windows.
- My gate then deleted that raw file. The K0875 OIDN "FAIL" and D1 output came from corrupted data. **They are
  invalid, not results**, and they were deleted.
- **K0875 is re-rendered** with the same driver, after freeing package caches (pip/uv, not experiment data).
- **K070 and K080 were checked.** Their `view_cdm2.exr` and D1 PNGs read without error and contain no zero pixels.
  K080's `view_rgb.exr` (a Cycles-unit copy that D1 does not use) had failed to write and was deleted.

## Automatic results (`results_N17.json`, code `8d8f904`): **all PASS**; visual pending
`d1/verify_manifest.sh`: all OK (before and after the driver runs, and at evaluation).

| key | t | pcond EXPOSURE (linear) | median Y_disp | luminance ceiling | floor | OIDN (windows) | R3 | SRC |
|---|---|---|---|---|---|---|---|---|
| B | 0 | 453.5 | 1.738 | 0 % | 0 % | accepted | accepted | lamp behind |
| K070 | 0.70 | 869.5 | 0.596 | 0 % | 0 % | PASS (max 0.17 %) | PASS; **G3 literal FAIL, E1 class** | lamp out |
| K080 | 0.80 | 865.2 | 0.585 | 0.23 % | 0 % | PASS (max 0.15 %) | PASS | lamp out (x ≈ −136) |
| K0875 | 0.875 | 868.8 | 0.623 | 0.57 % | 0 % | PASS (max 0.11 %; lamp-head window, report only, 0.07 %) | PASS | **PASS** |
| C | 1 | 982.6 | 0.692 | 0.444 % | 0 % | accepted | accepted (E1, as recorded) | PASS |

**CF:** every keyframe passes. The any-channel ceiling is ≤ 4.3545 % and the floor is 0 %.

**log2 EXPOSURE steps** (report, not gated):

| step | log2 |
|---|---|
| B → K070 | +0.94 |
| K070 → K080 | −0.007 |
| K080 → K0875 | +0.006 |
| K0875 → C | +0.18 |

**K070's E1 classification:** one in-gamut pixel with a channel within 10⁻⁸ of the sRGB knee. It is classified by
`eval.py`'s diagnostic, as in `d1/ERRATA.md` E1.

**Against the prediction:**
- **Right:**
  - OIDN and R3 pass, with E1 1-px as expected;
  - the scale rises from B to about 870, C-like;
  - the source enters gradually, with SRC passing at K0875;
  - no reversal larger than 0.5 stop.
- **The K080 risk did not materialise in the numbers:** it is flat against its neighbours. The visual gate decides.

**Sequence sheet:** `N17_sequence_sheet.png` (B → K070 → K080 → K0875 → C, t and yaw shown).

**My reading** `N17_my_reading.txt`: sha256 `0ae89a8f412d879d4d7b72640b49e9143c3bed33ba589dfaed34135f5053c190`, taken from the command output.

## Visual verdict (external observer; `N17_sequence_sheet.png` from `f2a7309`, my reading not opened): **PASS**
| check | verdict | note |
|---|---|---|
| new artifact class | **PASS: none** | no halos, bands, colour breaks, geometric flashes or display-path artefacts |
| sudden exposure/tone jump | **PASS** | K070 → K080 → K0875 → C changes consistently with the turn and the entering lit area |
| gradual source entry | **PASS** | pool influence, then the pole at the left edge, then the lamp head, then C |
| dark structure | **PASS** | the barn stays a readable mass; the lane and pool edges are kept; no formless black floor |
| known residuals | **PASS / known** | white core where expected; warm/pink B flank; K070's E1 pixel not visible |

**The observer's notes:**
- K070 → K080 → K0875 is the key segment, and it is stable. The practical enters without the rest of the frame jumping.
  C reads as a natural continuation, not a different tone-mapper regime.
- **B → K070:** the visual and exposure difference is large (+0.94 stop), but it is **not classified as a
  discontinuity**. The interval spans Δt = 0.70 and a ≈ 120° turn, so it was not sampled. Keeping it report-only was
  right.

**My reading** (`N17_my_reading.txt`, sha256 `0ae89a8f…`, committed in `6adafdf` before the verdict): PASS on all five.
It agrees; it does not count.

**Outcome:** N1.7 sparse keyframe stress **PASS**, and a dense-motion addendum is justified.
- **Its main purpose is B → K070**, the 70 % of the path the sparse test left unobserved.
- **P-7** runs per frame over the whole path, with no exposure smoothing.
- **A temporal FAIL** would be a sharp pcond-scale transition within a narrow t range.
