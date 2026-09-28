# D2-A3a pre-registration: exposure-sufficiency oracle before the A1b shoulder

Following `d2/TEMPLATE.md`. Committed **before** any A3a code or output. D1 is not changed. A1b is not changed; it
stays "V6 fixed, V7 not restored" (`d2/a1/PREREG_A1b_V7.md`, `391e916`). D2-B3 stays LOCKED.

## Origin
- **A1b V7 FAIL:** in a blind comparison, Blender AgX +7 (hand-graded) was preferred to A1b (Z > X). The observer's
  reason: A1b's road is too light, and the darker road keeps the night and the locality of the lighting.
- **Descriptive (post-hoc) numbers:**

  | quantity | A1b | Blender |
  |---|---|---|
  | road median (cd/m²) | 63 | 39 |
  | field median (cd/m²) | 16.9 | 5.1 |
  | road p90/p10 | 1.65 | 2.21 |

- **Why the hypothesis is not trivially false.** A post-output ×0.62 would not change the contrast ratio. But a lower
  exposure *before* f(Y) = Y/(1+Y) compresses the highlights less, so the level drops and local contrast rises
  together.
- This is the structure of Reinhard et al. 2002: a luminance scaling (the key/exposure), then L/(1+L).

## 1. Question (one)
If A1b is given the ideal global exposure for RoadLine, does one scalar before the shoulder close the gap to Blender?

**This is an oracle, not an algorithm.** A semantic road mask is allowed *because* nothing here is proposed as a
selector.

## 2. The single change
**Yreq = 0.1 + 99.9 · f(max(s·Y_A, 0))**, with f(Y) = Y/(1+Y).

**Unchanged:** the RoadLine-A2 canonical input, the frozen extraction, B, the Y-priority display, the encoder, and
f itself.

**s is computed once, analytically, in code, before any A3a output exists:**
- **Target:** Y* = the road median of the Blender AgX +7 image, `n1/roadline/renders/A2_comparator.png`.
  - The road mask is the geometric one used throughout D2-A1/A2.
  - The decode is the SDR100 formula.
  - The value is already published (39.2 cd/m²) and is recomputed in code.
- **The formula:**
  - q = median over road pixels of the frozen Y_A (`extract("RLA2_canonical")`).
  - f(s·q) = (Y* − 0.1)/99.9, so **s = u/(1 − u)/q with u = (Y* − 0.1)/99.9**.
  - Because f is monotonic, this puts the requested road median exactly at Y*.
- **Expected value** from the published numbers: s ≈ 0.377 (−1.41 stops).
- **Exactly one s.** No second value and no "−1.2 stop might be better".

## 3. Gates
**Automatic** (RoadLine; as in A1b stage 1):
- **R3:** extraction C0/C2/C3; display G1–G3, S-1…S-3. E1 class: literal FAIL, classified, not KILL.
- **R4 / R5:** addendum-6 estimator; R5 against the frozen linear anchor (`n1/roadline/renders/A2_canonical_raw.png`).
- **H3:** frame floor ≤ 0.62 % and field floor ≤ 0.62 %.
- **Report only:**
  - s and its stops;
  - road median (check: ≈ Y*);
  - road p10/p90 and p90/p10;
  - field median;
  - H2v2;
  - the same statistics for A1b and Blender.

**Blind visual** (after the automatic gates pass):
- **Stimuli:** oracle-A1b, Blender AgX +7 and plain A1b.
- **Labels:** X/Y/Z from a numpy permutation with **seed 2**.
- **Layout:** the same as the A2 and V7 blind sheets: full frame plus the far-lamp crop (rows 330–440, cols 900–1180).
- **Key:** salted, git-ignored until the reveal, its sha256 committed before showing.
- **My reading:** hashed from the command output, committed before the verdict; it does not count.
- **Questions:** V1–V6 per label (V5 N/A), the most convincing night road, the worst, the full order.

## 4. KILL (the exposure-level hypothesis)
- oracle-A1b is ranked **below** Blender; **or**
- oracle-A1b gets V6 FAIL or a new A-side defect; **or**
- an automatic gate (R3 other than E1, R4, R5, H3) fails.

**Then:** the exposure branch stops. The remaining difference lies in the curve shape, local contrast, colour
rendering or another part of the pipeline, and no exposure selector is worth building.

## 5. PASS
oracle-A1b ≥ Blender (ranked above or tied), with V6 PASS and the automatic gates passing. Then:
- the current A1b shape is sufficient;
- the missing degree of freedom is the global exposure before the shoulder;
- **only then** may D2-A3b be opened: one published automatic key policy, with no sweep. The first candidate is
  Reinhard's parameter-free key estimation (log-average, robust min/max). It gets its own PREREG, with a full
  hold-out/corpus/temporal no-regression.

## 6. Budget
0 renders; minutes of CPU; one blind sheet.

## Prediction (recorded before running; only published numbers used)
- **s ≈ 0.377 (−1.41 stops).**
- Field median ≈ 7 cd/m²: less than proportional, because of the shoulder.
- Road p90/p10 rises from 1.65 towards ≈ 2.
- **Automatic gates pass.** R5 margins shrink but stay far above 1 code.
- **Visual: uncertain, a slight lean to PASS (tie or better).** The level and the contrast approach Blender's. The
  remaining risk is the cold/lavender B cast, which the observer noticed but did not name as the main reason, and
  which a darker road may make more or less visible.

## Automatic results (`results_A3a.json`, code `7c91d44`): **all PASS**; blind visual pending
`d1/verify_manifest.sh` before and after: all OK.

**The one s:**
- Y* = 39.218 cd/m², the Blender road median.
- q = 1.7054, the road median of the frozen Y_A.
- **s = 0.37737, i.e. −1.406 stops.**

**Gates:**
- **R3:** C0 bit-identical; C2/C3; display G1–G3, S-1…S-3 all PASS.
- **R4:** no inversion.
- **R5:** presence identical to the frozen linear anchor. All six lamps stay at 61 380–65 183 codes above the
  background.
- **H3:** floor 0 %.

| (report, display cd/m²) | road median | road p10 / p90 | road p90/p10 | field median | H2v2 |
|---|---|---|---|---|---|
| **oracle-A1b** | 39.22 | 22.5 / 49.0 | **2.18** | **7.16** | 0 % |
| A1b | 63.08 | 43.4 / 71.7 | 1.65 | 16.86 | 0 % |
| Blender AgX +7 | 39.22 | 21.7 / 48.0 | 2.21 | 5.07 | 0 % |
| frozen D1 | 100 | 76.4 / 100 | 1.31 | 20.23 | 82.0 % |

**Against the prediction:** s, the field ≈ 7 and the contrast approaching ≈ 2 were all right. The contrast is 2.18,
against Blender's 2.21.

**Blind sheet:**
- `renders/A3a_blind_sheet.png`, made by `sheet_A3a.py` (seed 2).
- **Key** `work/A3a_blind_key.json` (git-ignored until the reveal): sha256 `3399efc0a2310a7ecb2dcb1518400f4594fffc2f11d9adf081cdba493453e4ca`.
- **My reading** `A3a_my_reading.txt`: sha256 `262566e1ffe817b110d9bcaf7d100ea5841b361c9f3f9eee71221502889715d8`.

## Verdict and reveal: **KILL. Oracle-A1b ranked below Blender** (Z > Y > X)
The external blind verdict was given from the sheet only, without the key and without my reading.

| label | V1 | V2 | V3 | V4 | V5 | V6 |
|---|---|---|---|---|---|---|
| X | PASS | PASS | PASS | PASS | N/A | PASS |
| Y | PASS | PASS | PASS | PASS | N/A | PASS |
| Z | PASS | PASS | PASS | PASS | N/A | PASS |

**Ranking: Z > Y > X.** The strength of the differences:
- **Z > Y: "small but visible".**
- **Y > X: "clear".**

**Observer's notes:**
- **X:** no saturation defect, but the least convincing night: the road and field are too light, and the lighting is
  less local.
- **Y:** clearly better than X. The locality of the pools is restored, and the far lamps read. There is no new A-side
  defect, and a slight cold/lavender cast does not break structure.
- **Z:** very close to Y in road level and contrast, but "a little more natural in overall tonality and in the
  separation of the light road from the dark surround".

**Key** (`A3a_blind_key.json`, sha256 matches `3399efc0…`):
- **X = A1b**;
- **Y = oracle-A1b**;
- **Z = Blender AgX +7**.

**My reading** (`A3a_my_reading.txt`, sha256 matches `262566e1…`): X = A1b, Y = oracle, Z = Blender, Z ≥ Y > X,
"slight risk of Z > Y on the cast". It agrees; it does not count.

**Outcome (pre-registered, literal):**
- **KILL. Oracle-A1b is ranked below Blender; the exposure-level hypothesis does not close the gap.**
- Per §4, the exposure branch stops, and **no automatic exposure selector (D2-A3b) is opened.**

**Recorded plainly, not as a PASS:**
- One pre-shoulder scalar (−1.41 stops) moved A1b from a "clear" loss to a "small but visible" loss.
- The residual difference is described by the observer as **tonality/colour and a slightly different distribution of
  local contrast**, not a level error and not saturation. That matches the report numbers:
  - road level is equal (39.2 vs 39.2), and road p90/p10 is almost equal (2.18 vs 2.21);
  - the field stays brighter (7.2 vs 5.1);
  - the B cast is present in Y and absent in Z.
- Per §4, the remaining difference lies in the curve shape, the local-contrast distribution (the surround level) or
  the colour rendering, not in exposure selection.
- **A1b stays "V6 fixed, V7 not restored".** No candidate freeze.
