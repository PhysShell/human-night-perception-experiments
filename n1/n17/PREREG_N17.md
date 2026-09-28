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
