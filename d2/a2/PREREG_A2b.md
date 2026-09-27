# D2-A2b pre-registration: global histogram highlight guard on the frozen axis-A exposure

Following `d2/TEMPLATE.md`. Committed **before** any A2b code or output. D1 is not changed. `d1/verify_manifest.sh`
runs before and after, and its output is recorded.

The user called this "D2-A2 stage 2". It is named **A2b** here so it is not confused with the stage 2 of `PREREG.md`
(the `-w` hold-out), which was never run.

## Origin
- **D2-A1 closed:** the linear shape is not falsified, and an oracle global scale survives a hold-out.
- **D2-A2 `-w`: KILL** (`ab1cea5`). Native centre weighting moves the scale −0.009 stop.
- **The remaining suspect:** pcond's global scale selection, whose adaptation level is the log-average.
- Adaptation / CIE 257 / D2-B3 and the A1b shoulder stay **LOCKED**.

## 1. Question
Can one simple global image statistic, a luminance-percentile highlight guard on top of the existing pcond exposure,
select the scale by itself? It must correct RoadLine and leave already-accepted scenes untouched or still accepted.

## 2. Policy (frozen here; one algorithm, no new constant)
- **Input:** the frozen axis-A luminance Y_A (`extract()` → `Ynew`: display-relative, 1 = display peak, pre-clipgamut,
  unclipped). It is scalar luminance **before B and before display RGB**. There are no RGB/channel quantities.
- **q = Q99.9(Y_A).**
  - It is taken over **all pixels of the frame**: no road mask, no centre weighting, no semantic region.
  - Computed with `numpy.percentile(Y_A, 99.9)` (linear interpolation).
- **s_hist = min(1, (99.9 − 0.1) / (99.9 · q))**.
  - This is the largest s ≤ 1 such that Q99.9 of the requested display luminance Yreq = 0.1 + 99.9·s·Y_A equals
    99.9 cd/m², the H2v2 threshold. If q ≤ 0, s_hist = 1.
  - **s_hist = 1 means the guard is inactive:** the output must be **bit-identical** to frozen D1 (checked).
- **The one change to D1:** Yreq = 0.1 + 99.9 · s_hist · Y_A. Where the frozen gate code recomputes Yexp from Y_A, the
  same s_hist is applied to that one image.
- **Origin of 99.9:** it is the 0.1 % luminance-ceiling budget already frozen in D2-A1a2 (H2v2), not a new knob, and
  it is not presented as an industry standard.
- **Per image:** the policy is evaluated per image, including each S2 video frame. There is no temporal smoothing.
- **Oracle:** s = 0.2641 is **not** given to the policy and is **not** a PASS criterion.

## 3. Stage 1: RoadLine-A2 canonical only (0 renders)
| id | criterion |
|---|---|
| **H2v2** | road luminance ceiling ≤ 0.1 % (geometric road mask, as A1a2) |
| **H3** | frame floor ≤ 0.62 % **and** field floor ≤ 0.62 % |
| **R3** | extraction C0/C2/C3 (frozen cache `RLA2_canonical`); display gates G1–G3, S-1…S-3 (E1 class: FAIL stays FAIL, classified) |
| **R4 / R5** | as A1a (addendum-6 estimator; linear anchor at the same s_hist) |
| **V6** | if the automatic gates pass: external observer, sheet format. Is there broad roadway saturation, or a new A-side defect? |
| report | s_hist, stops = log2 s_hist, log2(s_hist / 0.2641); Q50/Q90/Q99/Q99.9/Q99.99 of Y_A; H1 any-channel and C1 chromatic ceilings |

**Stage-1 KILL:** any gate above fails. The simple histogram-guard hypothesis is dead. **There is no 99.8, 99.5, 99 or
Low/High-percent retry.**

## 4. Stage 2: only after stage-1 PASS (V6 included)
The policy picks its own s_hist on every accepted input. **s = 0.2641 is not reused.**

**Inputs:**
- N1 Camera C (`n1/work/view_C/view_cdm2.exr`);
- N1 hero (`n1/work/hero_cdm2.exr`);
- N1 Camera B, if its input is present;
- the whole D1 corpus through the frozen `d1/final/run.py` logic (S0–S5, S3_bar/nobar, S2 frames, F1), with outputs in
  `d2/a2/work/`.

**Required table:** per scene: frozen EXPOSURE (pcond), q, s_hist, Δ stops, guard active (s_hist < 1). S1, S3 and S5
are reported separately in the text.

**Gates:**
- **Inactive scenes:** bit-identical to frozen D1 output.
- **Camera C:**
  - HO1 luminance ceiling ≤ 0.444 %;
  - HO2 floor ≤ 0.62 %;
  - HO3 lamp head ≥ 1 code;
  - R3.
- **Hero and B:**
  - frame luminance ceiling ≤ the frozen-D1 value of that view;
  - floor ≤ 0.62 %;
  - R3.
- **Corpus:**
  - D1 final P-1…P-8, except P-7 (not run, as in A1a: S2 frames are not written);
  - per natural still: ceiling ≤ 4.35 % and floor ≤ 0.62 %;
  - E1 knee-class literal FAILs stay FAIL and are classified; they are not a KILL.
- **Visual (external observer, sheet format):**
  - V6 on Camera C and on the hero, if the guard is active on them;
  - one comparison sheet, frozen vs guard, for every active natural corpus still.
  - The question: is there a new A-side defect, darkness collapse, or structure visibly degraded?

**Stage-2 KILL:**
- a new substantive corpus FAIL (other than E1);
- a new visual A-side defect on the hero or Camera C;
- R4/R5 loss where they apply;
- darkness collapse;
- visibly degraded structure on an accepted scene the guard darkens;
- **or the guard is active on every accepted natural scene**: that is a global ND filter, not exposure selection.

There is no policy fix after viewing. **The stage-2 code gets its own addendum, committed before it runs.**

## 5. Reading (fixed now)
- **Stages 1 and 2 PASS:** a simple global exposure selection suffices; adaptation physiology is not needed for this
  failure.
- **Stage 1 PASS, stage 2 FAIL because accepted scenes get too dark:** a global scalar has an intrinsic
  highlight/shadow trade-off, and **A1b (shoulder) earns its turn**.
- **Stage 1 FAIL** (a global histogram cannot infer the needed scale): more complex metering / an adaptation-field
  study (D2-B3) becomes justified.

## 6. Budget
0 Blender renders; minutes of CPU; no new caches for stage 1, since the frozen `RLA2_canonical` extraction is reused.

## 7. Baseline check
`d1/verify_manifest.sh` before and after, into `results_A2b.json`.

## Prediction (recorded before running; no A2b statistic has been computed)
- **Stage 1: uncertain, with the risk on H3/V6, not on H2v2.**
  - The frame's top 0.1 % (≈ 1 570 px) includes all lamp cores and their surroundings, which lie far above the road.
  - If lamp-area pixels alone exceed 0.1 % of the frame, q is set by lamps, and s_hist ≪ 0.2641: over-darkening, with
    the risk of a field floor (H3) or a "too dark" V6.
  - If not, q is set by the brightest road, and s_hist ≈ 0.2641 or lower.
  - H2v2 likely passes in both cases: it holds whenever at least 0.1 % of the frame is brighter than the road's own
    p99.9, which lamp areas plus the near road probably provide. This is not guaranteed.
- **Stage 2:** the guard is predicted **inactive on S0/S3/S4-type scenes with no bright practicals**, and **active on
  the hero, Camera C and S1**. Active on scenes with bright points, it will darken them. That is the main stage-2 risk.
