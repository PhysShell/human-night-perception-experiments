# D2-A1b pre-registration: one fixed global shoulder on the frozen axis-A luminance (probe, not a proposed D1)

Following `d2/TEMPLATE.md`. Committed **before** any A1b code or output. D1 is not changed. `d1/verify_manifest.sh`
runs before and after, and its output is recorded.

## Origin
- **`d2/a1/PREREG.md` §5 named A1b** as the next step if a global scale does not suffice. A1a2 then showed that the
  linear *shape* survives on one hold-out, so A1b was not run.
- **D2-A2b stage 2** (`d2/a2/PREREG_A2b_stage2.md`, `7a44961`/`a4f61f1`) found a real **global-scalar highlight/shadow
  trade-off.** The same content-appropriate Q99.9 scale selection fixes RoadLine (A2c) but visibly crushes S1/S2
  (−3.36 stops).
- Per its pre-registered reading 2, **A1b is earned.**
- D2-B3 (adaptation field / CIE 257) stays **LOCKED** until A1b's result.

## 1. Question
Can one standard, parameter-free global luminance shoulder resolve the trade-off? It must remove RoadLine's broad
roadway saturation while keeping S1's weak night structure.

## 2. The operator (frozen here; the only one; a probe)
**f(Y) = Y / (1 + Y)**, the simple global operator of Reinhard, Stark, Shirley & Ferwerda 2002 (Eq. 3).
- Its slope → 1 in the shadows; it compresses highlights smoothly and asymptotically into [0, 1).
- **Applied to:** the frozen axis-A luminance Y_A (`extract()` → `Ynew`, display-relative, 1 = the frozen display peak),
  as **f(max(Y_A, 0))**.
  - Y_A < 0 would give Yreq < 0.1 and be clipped to the floor either way. The count is reported.
- **The one change:** Yreq = 0.1 + 99.9 · f(max(Y_A, 0)). It is applied *only* when forming the requested display
  luminance.
- **Axis B is untouched:** the modified luminance is **not** fed back into B. B's input stays the physical scene, as
  frozen. This is an A-only experiment.
- **Unchanged:** the display path (Y-priority projection, encoder).
- **No scale factor:** the operator stands alone, with no pcond-scale change and no s.
- **No parameters:** there is no L_white, knee, key, exposure, "softer" variant or colour handling.
- **Status: a counterexample probe for the question in §1.** It is not a proposed final D1 curve. It may be too
  aggressive in the mid/high tones; that is part of what is tested.

## 3. Stage 1: RoadLine-A2 canonical + S1 only (0 renders)
**RoadLine** (frozen cache `RLA2_canonical`):

| id | criterion |
|---|---|
| R3 | extraction C0/C2/C3 (frozen); display G1–G3, S-1…S-3 (E1 class: FAIL stays FAIL, classified) |
| R4 / R5 | as A1a (addendum-6 estimator); the linear anchor is the frozen linear anchor (no shoulder, as in RoadLine-A2) |
| H3 | frame floor ≤ 0.62 % and field floor ≤ 0.62 % |
| H2v2 | **report only, not a KILL.** A2c showed 0.150 % can be visually fine |
| **V6** | external observer, sheet: frozen D1 vs shoulder, full frame plus the A2c road crop (rows 410–820, cols 560–1360, 1:1). Is broad roadway saturation gone? Is the road gradient preserved? Is there a new A-side defect? |

**S1** (frozen cache `S1`; the frozen `d1/final/run.py` text, still loop restricted to S1, F1/S2 not run):

| id | criterion |
|---|---|
| P | P-1, P-2a, P-2b, P-3, **P-4** (its Yexp uses the same f), **P-5** |
| **V** | external observer, band sheet as in A2b stage 2 (full frame plus the 1:1 sky/poplar/lamp band rows 100–420), frozen D1 vs shoulder. Are sky separation, the poplar silhouettes and the weak structure near the lamp line kept? Is there a darkness collapse or a new A-side defect? |

**Report** (both scenes; no gate, no new constant):
- Q50/Q90/Q99/Q99.9 of the frozen Y_A;
- luminance and any-channel ceiling, frozen → shoulder;
- floor, frozen → shoulder;
- median display luminance, frozen → shoulder;
- the count of Y_A < 0;
- for S1: the P-5 metrics (sky, lamp/sky, poplar Weber, reversals, halo), frozen → shoulder.

**My reading** is written, hashed from the command output and committed before the verdict. It does not count.

## 4. Stage-1 KILL
- RoadLine still has visible broad roadway saturation (V6);
- **or** S1 visibly loses structure or collapses into darkness;
- **or** a new A-side defect on either;
- **or** a new substantive automatic failure: R3 (other than E1), R4, R5, H3, or any S1 P-gate.

**No retry:** no coefficient on Reinhard, no white point, no knee, no 0.8/0.9, no "a bit softer". Dead is dead.

## 5. Stage 2 (only after stage-1 PASS; its own addendum with code committed before running)
No-regression on:
- the hero, Camera B and Camera C;
- S0, S3_bar, S3_nobar, S4, S5 and F1;
- **all 48 S2 frames with P-7, mandatory** (the nonlinearity can change temporal amplitudes);
- the full P-1…P-8;
- external frozen-vs-shoulder sheets for natural scenes where the difference is materially visible.

Report per scene, as in §3.

## 6. Reading (fixed now)
1. **RoadLine PASS, S1 PASS, then stage 2 PASS:** nonlinear highlight compression resolves the scalar trade-off, and
   the A1b hypothesis survives. Adoption, and choosing a production curve, are a separate task.
2. **RoadLine PASS and S1 FAIL (dark or structure):** even a shadow-preserving global shoulder does not resolve the
   conflict. Richer adaptation / local metering (D2-B3) gets grounds.
3. **RoadLine FAIL:** the simple global-shoulder direction is KILLed.

## 7. Budget
0 renders; minutes of CPU; two sheets.

## Prediction (recorded before running; only frozen, already-published numbers used)
- **S1 is nearly unchanged in the dark parts.**
  - The frozen displayed sky is 0.318 cd/m², so Y_A ≈ 0.0022, where f changes values by ≈ 0.2 %.
  - The poplar Weber stays ≈ 0.59, and P-5 passes.
  - The lamps are compressed from far above the peak to just below it; lamp/sky stays ≫ 10.
- **RoadLine:**
  - The lit road (Y_A ≈ 2–4 under the frozen scale) maps to about 0.67–0.8 of the peak. Broad saturation should be
    gone.
  - **The risk is a flat, greyish road:** the gradient is compressed about 3× in slope over that range. The V6
    gradient question may fail.
  - Lamp cores no longer reach the peak, so they may show B's chroma instead of white. A possible new-looking lamp
    appearance; I expect it to be judged within the declared B-tint class.
- **R4/R5 pass** (f is strictly monotonic), and **H3 passes.**
- **Overall: stage-1 PASS is more likely than not.** The main risk is the RoadLine gradient.
