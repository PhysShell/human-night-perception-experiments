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

## Addendum 2: dense motion, stage 1 = full-resolution pcond scale trace (before any trace render)
**Purpose.** Measure EXPOSURE(t) along the whole B → C path, above all B → K070 (70 % of the path, unobserved), before
any accepted-quality dense clip.

**Frames:**
- **t = 0, 0.025, …, 1.0: 41 frames.** The step is chosen so that the grid contains the accepted t = 0, 0.70, 0.80,
  0.875 and 1 as controls. The user suggested "e.g. 48".
- The path is exactly as above: position linear in t, yaw 180° + 171.6°·t, pitch −3°·(1 − t).

**Rendering:**
- **Full 1920×820, 128 spp, raw (no OIDN).** The frozen `scene.py` already sets `use_denoising = False`. The trace
  renderer `n1/n17/trace_render.py` applies `n1/view_render.py`'s camera replacements **without** its OIDN insertion,
  with 128 samples and the same seed.
- **Resolution is not reduced**, so small sources and pool edges stay the same raster stimulus for pcond.

**Per frame, numbers only:**
- the frozen A (`axis_a.sh` + `axis_a_x.sh`) on the ×179 Combined pass;
- **pcond EXPOSURE**, the tone-map branch (linear/mapped), frozen **Y_A median** and **median predicted Y_disp**
  (0.1 + 99.9·clip(Y_A, 0, 1));
- **scene statistics:** frame log-mean luminance, median luminance, Q99.9;
- lamp head in or out of frame (projected).

No D1 PNG and no OIDN. All render intermediates are deleted frame by frame.

**Validity control:** at t = 0, 0.70, 0.80, 0.875 and 1, the trace EXPOSURE must lie within **5 %** of the accepted
4096-spp value (453.5, 869.5, 865.2, 868.8, 982.6). Otherwise the 128-spp trace is **INVALID** as a proxy, and it is
reported, not interpreted.

**Stage-1 KILL (operational; no new numeric derivative threshold):**
- **automatic:** the mapping branch changes (linear ↔ mapped) anywhere on the path;
- **judged on the trace plot** (EXPOSURE(t), the scene log-mean(t) and lamp in/out, with each step's log2 change),
  by the external observer, **before** any stage-2 render:
  - a **localised sharp discontinuity** in EXPOSURE, clearly larger than the neighbouring steps and not explained by an
    equally sharp change of the scene statistic; **or**
  - the source enters the frame and EXPOSURE answers with a jump rather than a smooth transition.
- **KILL:** no dense 4096 clip. Only the bounded transition interval is studied, under its own addendum.

**Stage 1 smooth:** a prospective stage 2 (its own addendum, written after the trace and before any stage-2 render).
- **Frames:** 12–16 frames at the accepted settings (4096 spp, OIDN windows gate), at t positions fixed from the
  trace *before* rendering:
  - covering the B → K070 segment of largest EXPOSURE change;
  - several frames around the source entry t ≈ 0.82;
  - overlap with the accepted B, K070, K080, K0875 and C.
- **Checks:** OIDN, frozen D1, P-7-like temporal metrics, and a visual clip/contact sheet.
- If 12–16 frames prove too sparse for P-7, that is a separate fact and a separate budget decision.

**Budget:** 41 × (≈ 1.5 min render + ≈ 1 min A/extraction), about 2 hours. Disk is one frame at a time.

**Prediction:**
- The controls pass (the log-average is robust to 128-spp noise). Low confidence at t = 0: B stands inside the pool,
  and fireflies are possible.
- **EXPOSURE rises smoothly** from 453 to ≈ 870 over t ≈ 0.25–0.6, as the pool and wall leave the frame during the
  turn. It stays flat through the entry (0.7–0.875), then rises to 983.
- The branch stays linear. No KILL.

## Stage-1 trace results (`trace.jsonl`, `trace_results.json`, plot `N17_trace.png`; driver `235c53e`)
`d1/verify_manifest.sh` before and after: all OK. 41 frames completed. C0 is bit-identical on every frame.

**Validity controls: PASS.** trace/accepted EXPOSURE:

| t | trace/accepted |
|---|---|
| 0 | +0.29 % |
| 0.70 | +1.59 % |
| 0.80 | +1.57 % |
| 0.875 | +1.60 % |
| 1 | +1.29 % |

All are within 5 %. The 128-spp trace sits ≈ 1.5 % high: a small, uniform noise bias of the log-average.

**Automatic KILL (branch change): none.** The branch is linear on all 41 frames.

**Trace:**
- **Rise B → t 0.525:** EXPOSURE rises 455 → 854 in two smooth humps (t 0.125–0.25 and t 0.35–0.525).
- **Plateau t 0.525–0.8:** ≈ 850–893.
- **Dip at the source entry (t 0.80–0.825):** −0.023/−0.010 stop.
- **Rise t 0.9–1:** to 995.

**Steps:**
- The largest step is **+0.086 stop per Δt = 0.025** (t 0.45 → 0.475), flanked by +0.078 and +0.084. It is not
  localised.
- Per-step log2 EXPOSURE against per-step log2 scene log-mean: **correlation −0.96**. Every exposure change is matched
  by the scene statistic.

**Against the prediction:**
- **Right:** the controls pass; the branch stays linear; the rise is smooth; the entry is flat or dipping.
- **Mistimed:** I predicted the rise over t ≈ 0.25–0.6; it runs over 0.1–0.525, in two humps.

**My reading** `N17_trace_my_reading.txt`: sha256 `e833ac9981449f91ba06eb7eea7529e1ba8758922eefd55f686d406ff8442860`, taken from the command
output. **The judged KILL questions go to the external observer.**

## Stage-1 verdict (external observer): **PASS**
- **Localised exposure discontinuity:** no.
- **Source-entry exposure jump:** no.
- **Branch change:** no.
- **Validity controls:** PASS.

**Observer's notes:**
- **Largest step.** The largest step (+0.0863 stop, t 0.45 → 0.475) is part of a broader smooth transition, with a
  matching change in the scene statistic.
- **Lamp entry.** At t 0.80 → 0.825 there is no abrupt response.
- **Why it convinces.** EXPOSURE's derivative mirrors the scene log-mean (r = −0.962): pcond responds to content and
  makes no manoeuvres of its own.

**My reading** (`N17_trace_my_reading.txt`, sha256 `e833ac99…`): smooth, no KILL. It agrees; it does not count.

## Addendum 3: stage 2 (before any stage-2 render)
**Frames (user decision), 12 new frames at the accepted settings** (4096 spp, OIDN, the same seed, `view_render.py`
unchanged):

| t | covers |
|---|---|
| 0.125, 0.175, 0.225 | the first rise |
| 0.350, 0.400, 0.450, 0.475, 0.525 | the main change, including the largest step |
| 0.825, 0.850 | just after the lamp entry |
| 0.925, 0.975 | the final rise to C |

**The accepted anchors are reused, not re-rendered:** B = 0, K070, K080, K0875, C = 1. That makes **17 states** along
the path. The keyframe names are K0125 … K0975 (t × 1000), added to `views.json` by `make_keys2.py` (existing entries
unchanged, asserted).

**Per new frame** (driver `run_stage2.sh`, one frame at a time):
- render;
- OIDN windows gate (`gate.py`, amendment 1);
- `view_rgb.exr` deleted (D1 does not use it);
- the frozen A;
- the frozen D1 (`view_eval.py d1`);
- the per-frame evaluation (`frame_eval.py`);
- then the caches and `view_cdm2.exr` are deleted (disk). The D1 PNG and the JSON are kept.

**Gates:**

| id | criterion |
|---|---|
| OIDN | 5 windows, ≤ 2 % each |
| R3 | C0 bit-identical, AX-C2/C3 ≥ 99.9 %; display gates; a literal G3/S-2 FAIL is allowed only if the per-frame diagnostic classifies it as E1 (≤ 3 in-gamut px within 10⁻⁸ of the knee) |
| CF | floor ≤ 0.6250 %; any-channel ceiling ≤ 4.3545 % |
| SRC | lamp head ≥ 7 px inside the frame: ≥ 1 code above the annulus |
| TRACE | \|EXPOSURE_4096 / EXPOSURE_trace(t) − 1\| ≤ 5 % (the trace has every stage-2 t) |
| FLASH | over the 17 states in t order, isolated flashes ≤ 1. A flash is a state whose frame-mean Y_disp deviates by more than 20 % from **both** neighbours **in the same direction**: P-7's isolated-flash definition, applied to the frame mean. |

**P-7's step limits (2 % mean and sky steps) are not applicable:** they are defined for a static-camera clip, and here
the camera moves and turns by design.

**Visual:**
- **Who:** the external observer.
- **Contact sheet:** the 17 states in path order, t shown.
- **Not blind.**
- **Questions:**
  - any flicker or discontinuity not explained by the viewpoint change?
  - any new artifact class?
  - is dark structure kept?
  - do the known residuals stay known?
- **My reading** is hashed from the command output before the verdict.

**STOP / PASS:**
- **Any new substantive failure is a STOP:** a gate failure other than E1, or a visual yes to flicker, discontinuity
  or a new artifact.
- **All pass:** N1.7 motion stress **PASS** on the B → C path.

**Budget:** 12 × ≈ 47 min, about 9–10 hours. The disk peak is ≈ 110 MB per frame.

**Prediction:**
- All gates pass.
- TRACE deviations are about −1.5 % (the trace's noise bias).
- FLASH = 0.
- E1 1-px literal FAILs on some frames.
