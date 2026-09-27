# D2-A1 pre-registration: is a single global linear exposure sufficient for bright-practical night scenes?

Following `d2/TEMPLATE.md`. Committed **before** any D2-A1 code. D1 is not changed. `d1/verify_manifest.sh` runs
before and after, and its output is recorded.

**Origin.** N1.6 RoadLine-A2 (`n1/roadline/PREREG_A2.md`, `a60ac6d`), blind order Blender AgX > V0 > D1. D1 got
**V6 FAIL** for broad roadway saturation, classified as a **new D1 failure on axis A**:
- the frozen A (`d1/pipeline/axis_a.sh`: `pcond -s -c -p …`, no `-l`/`-e`) took its linear fall-back on this scene;
- the display peak lands at 0.3928 cd/m² of scene;
- **82.0 % of the road surface** and all lamps clip (17.9 % of the frame);
- V0 (the same A) clips 16.2 %; plain AgX clips 0 %.

## 1. Question
Is the defect the **scale** that pcond's exposure selection chose, or the **linear shape** itself?

## 2. Necessary condition (what must be true for the cheapest fix)
A single global linear scale on the frozen A output, all else frozen, removes the broad roadway saturation without
collapsing the dark part, the far lamps, or D1's corpus behaviour.

## 3. Cheapest falsifier: A1a (no new render; minutes of CPU)
- **Probe:** Y_A → **s·Y_A with s = 0.2641 (1.92 stops down)**. Everything else frozen: B, the Y-priority display, the
  RoadLine-A2 canonical input, the extraction.
- **Choice of s, fixed now from measured data, not by eye:**
  - s puts the **99.9th percentile of the road surface's scene luminance** (1.488 cd/m²; geometric road mask x 0–7 m,
    3–1700 m from the eye) exactly at the display peak.
  - It is the most favourable single global scale for the road. If even this fails, "a different global scale"
    is falsified.
  - The request's 1.62 stops came from the median of an ad-hoc near-road crop (1.2 cd/m²). It would leave every road
    pixel above 1.2 cd/m² at the ceiling, which does not test the question.
- **Implementation:** `d2/a1/run.py` calls the frozen D1 code with the one change Yreq = 0.1 + 99.9 · s · Y_A. No
  frozen file is edited.

## 4. Gates for A1a on RoadLine-A2 (canonical input)
**New automatic gate family, closing the RoadLine hole** where R4/R5 passed over a white field.
- **H1 saturated area.** Frame fraction with any channel at the display ceiling ≤ **4.35 %**. That is the maximum over
  the visually accepted natural-scene D1 outputs (S5 4.35 %; the F1 fixture, 7.41 %, is excluded as synthetic patches
  driven to the peak by design). RoadLine under frozen D1: 17.92 %.
- **H2 road gradient.** Fraction of road-surface pixels at the ceiling ≤ **0.1 %** (≈ 0 by the choice of s; a check of
  the implementation).
- **H3 darkness not collapsed.** Frame fraction with all channels at the display floor ≤ **0.62 %** (the maximum over
  accepted outputs, S3_bar), **and** the same over the field (off-road ground) pixels.
- **R4 and R5.** As in RoadLine-A2, the addendum-6 estimator. The linear anchor gets the same s.
- **R3.** The display gates G1–G3, S-1…S-3 (the known knee artefact, `d1/ERRATA.md` E1: FAIL stays FAIL, classified).
- **V6.** The external observer on the A1a RoadLine D1 image (not blind): is the broad roadway saturation gone, and is
  there a new defect class? Declared residuals: white lamp cores; the B rod-term tint.

## 5. KILL of A1a (a global scale does *not* suffice)
H1, H2, H3, R4 or R5 fails, or V6 finds broad saturation or a new class. Then open **A1b**: one pre-registered,
luminance-only, monotonic shoulder after the frozen A, B frozen; its own PREREG. If A1b fails too, the whole direction
is KILLed. There is no operator tournament.

## 6. Corpus check under the same fixed s (secondary, reported; decides the *next* question)
D1 final gates P-1…P-8 on the D1 corpus with Yreq = 0.1 + 99.9·s·Y_A, using the frozen `d1/final/run.py` logic.
- Outputs go to `d2/a1/work/`; the frozen `d1/final/acceptance.json` and outputs are not touched.
- **Deviation from the request, stated:** a fixed s derived from RoadLine is not an exposure policy. Applying it to
  every corpus scene tests "is a uniformly 1.92-stop-darker D1 still acceptable", not "is a global scale sufficient".
- **Reading rule:**
  - **RoadLine passes and the corpus passes:** a fixed darker exposure is viable; report it.
  - **RoadLine passes and the corpus fails:** a *per-scene* global scale suffices, but not a fixed one. The defect is
    **exposure selection**, so the next research question is about selection/adaptation (the only place where CIE
    257 / D2-B3 may enter), **not a shoulder**.
  - **RoadLine fails:** A1b.

## 7. Budget
Minutes of CPU, **0 new renders**.

## 8. Baseline check
`d1/verify_manifest.sh` before and after; the output goes into `results.json`.

## 9. No regression
Applies to any adopted change, which is not this probe. A1a is a counterexample probe, not a candidate.

## Prediction (recorded before running)
- **H1, H2, R4 and R3 pass.**
- **H3 is the risk:** the field (median 0.080 cd/m²) and the sky (4·10⁻⁴) drop 1.92 stops towards the display floor.
- **R5 likely passes**, with less saturation on the far lamps: the 1600 m core (≈ 1.7 cd/m² peak pixel) may now fall
  below the peak.
- The corpus automatic gates pass: P-4 by construction, P-5…P-8 are ratios. What changes there is absolute darkness,
  which only a visual gate can judge.
