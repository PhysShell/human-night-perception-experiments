# D2-A2 pre-registration: exposure selection under bright practicals. First gate: native `pcond -w`

Following `d2/TEMPLATE.md`. Committed **before** any D2-A2 code or output. D1 is not changed. `d1/verify_manifest.sh`
runs before and after, and its output is recorded.

## Origin
D2-A1 is closed (`d2/a1/PREREG_A1a2.md`, `af8a50a`):
- the linear shape of axis A is not falsified;
- the oracle global scale s = 0.2641 survives an independent hold-out (N1 Camera C, external V6 PASS);
- **the remaining suspect is how pcond selects the global scale.**

Adaptation / CIE 257 / D2-B3 stay **LOCKED**.

## How the frozen A selects the scale (source, pinned Radiance `bcffc2b`, `src/px/pcond.c`, `pcond3.c`)
**Linear branch.** `check2do()` sets DO_LINEAR when the scene's log range fits the display range; otherwise the linear
branch is also taken when `mkbrmap()` fails. In the linear branch, with `-s`:
scalef = htcontrs(Lb(½(Bldmax + Bldmin))) / htcontrs(Lb(bwavg)).

**The world adaptation level is the log-average.** bwavg is the weighted mean of log luminance over the foveal image
plus `fvxr·fvyr·16` random point samples.
- On RoadLine it is dominated by the dark field and sky.
- So the display peak lands at 0.39 cd/m² of scene.

**`-w` (DO_CWEIGHT)** multiplies each **foveal-image** sample by centprob = max(0, 1 − xr² − yr²), where
xr = (x − ½(fvxr − 1))/90.
- **Paraboloid:** 0 at 90° from the centre.
- **The point samples are not centre-weighted.**
- **Foveal grid:** for the RoadLine/N1 views (-vtv -vh 60 -vv 27.7), fvxr = 66 and fvyr = 28, so the weights span
  only **0.85…1.00** across the frame.
- **Documented intent:** `-w` stops a bright *periphery* from pulling the exposure down.

## 1. Question
Does pcond's own native exposure-selection option `-w` select, for RoadLine, a scale whose effect is close to the
oracle (road not broadly saturated), without breaking Camera C and the corpus?

## 2. Necessary condition
A built-in or simple global policy selects for RoadLine a scale whose effect matches the oracle s = 0.2641
(H2v2 below) without darkness collapse or lamp order/presence loss.

## 3. Cheapest falsifier: `-w` alone
**The one change:** `pcond -s -c` → `pcond -s -w -c` in both of the following. Nothing else changes: B, the Y-priority
display, the extraction logic, the input.
- **The A output.** A copy of `d1/pipeline/axis_a.sh`.
- **The extraction.** A copy of `d1/a_extract/axis_a_x.sh`; its colour-control run `pcond -s` becomes `pcond -s -w`.

**Implementation:**
- `d2/a2/` holds the copies. Each copy's diff against its frozen source is checked to be exactly that flag.
- Caches go under new names (`A2w_*`) in the existing git-ignored cache directories.
- **No frozen file is edited or overwritten.**
- `pcond -x` mapfiles are kept for frozen and `-w` and committed (small text): the world → display luminance mapping.
  The frozen mapfile already exists from the D1 extraction.

**No parameter search.** There is no `-i` ladder, no `-I` histogram and no `-e`.

## 4. Stage 1 gates: RoadLine-A2 canonical input (the kill gate)
| id | criterion |
|---|---|
| **H2v2** | road-surface (geometric mask, as in D2-A1) fraction with display luminance ≥ 99.9 cd/m² ≤ **0.1 %** (the A1a2 metric) |
| **H3** | frame floor fraction ≤ 0.62 % **and** field floor fraction ≤ 0.62 % |
| **R3** | extraction C0 (vs the `-w` A output), C2/C3; display gates G1–G3, S-1…S-3 (E1 knee class: FAIL stays FAIL, classified) |
| **R4 / R5** | as in D2-A1 A1a (addendum-6 estimator; linear anchor at the same scale as the `-w` output) |
| **V6** | only if all the above pass: external observer, sheet format, RoadLine `-w` D1 image |
| report | H1 any-channel frame ceiling; C1 chromatic road ceiling; pcond mode (linear/mapped) and EXPOSURE for frozen and `-w`; the effective scale as log2 ratio vs frozen and vs the oracle (frozen × 0.2641) |

If `-w` flips pcond from the linear branch to histogram mapping, the gates apply unchanged. The flip is reported and is
not itself a KILL.

## 5. Stage 2 (runs only if stage 1 passes everything, V6 included)
- **Hold-out Camera C:**
  - HO1: luminance ceiling ≤ 0.444 %;
  - HO2: floor ≤ 0.62 %;
  - HO3: lamp head ≥ 1 code (as A1a2);
  - R3;
  - V6 by the external observer.
- **Corpus:** D1 final P-1…P-8 under `-w` (E1 class classified).
  - Per natural still: ceiling ≤ 4.35 % and floor ≤ 0.62 %.
  - An external visual comparison sheet, frozen vs `-w`: "no noticeable degradation".
- **The stage-2 code gets its own addendum,** committed before it runs.

## 6. KILL of the `-w` branch
- Any stage-1 gate fails (H2v2, H3, R3, R4, R5, V6), or any stage-2 gate fails.
- **Then:** the `-w` branch is closed. The next level is a generic **histogram-based global selection**, a new PREREG
  opened only by the user.
- **Only if** simple global image-statistic policies also die does D2-B3 (adaptation field, CIE 257) become justified.

## 7. Budget
**0 Blender renders:** only existing HDR/EXR, minutes of CPU. Disk ≈ 40 MB of cache for stage 1.

## 8. Baseline check
`d1/verify_manifest.sh` before and after; the output goes into `results.json`.

## 9. No regression
If `-w` survives both stages, it is a *candidate*. Adopting it is a separate decision, with the full D1 no-regression
set.

## Prediction (recorded before running, from the source above)
**Stage-1 KILL on H2v2.** `-w` cannot move the scale by −1.92 stops:
- **The weights are flat.** They span 0.85–1.00, and only the foveal half of the histogram is weighted.
- **The sign is wrong.** The bright lit road is in the lower *periphery*, and the dark horizon/sky is central.
  Down-weighting the periphery lowers bwavg, so it **raises** the exposure.

Expected: |Δ| < 0.3 stop, towards brighter; road luminance ceiling ≥ the frozen value's order (≫ 0.1 %). pcond stays in
the linear branch.

This outcome is still informative. It confirms that the frozen selection mechanism is the log-average adaptation
level, and that pcond's native centre weighting addresses the opposite failure (bright periphery).

## Stage 1 results (`results.json`, code `938c757`): **KILL on H2v2. The `-w` branch is closed**
`d1/verify_manifest.sh` before and after: all OK. The copies' diff against the frozen scripts is exactly the flag
(asserted in code).

**Scale** (mapfiles `map_RLA2_canonical_{frozen,w}.txt`):

| | frozen `-s -c` | `-s -w -c` |
|---|---|---|
| pcond branch | linear | linear |
| EXPOSURE (slope, cd/m² per cd/m²) | 444.77 | 442.12 |
| Δ vs frozen | — | **−0.009 stop** |
| needed (oracle s = 0.2641) | — | −1.92 stops |

**Gates:**

| gate | value | result |
|---|---|---|
| **H2v2** road luminance ceiling | **81.8 %** (limit 0.1 %) | **FAIL** |
| H3 floor, frame / field | 0 % / 0 % | PASS |
| R3: C0 bit-identical, C2/C3 100 %, display gates | all hold | PASS |
| R4 ordering | no inversion | PASS |
| R5 presence | identical to the anchor | PASS (trivially: all six lamps at the peak, 64 618 codes) |
| V6 | not reached (gated on automatic PASS) | — |

Reports: H1 any-channel frame ceiling 17.9 %; frame luminance ceiling 16.1 %; C1 chromatic road ceiling 6.4 %.

**Against the prediction:**
- **KILL on H2v2 and "stays linear" were predicted correctly.**
- **The magnitude was predicted correctly** (|Δ| < 0.3 stop).
- **The sign was predicted wrong.** The exposure moved 0.009 stop *darker*, not brighter. The shift is 0.5 % of the
  needed one, so the sign carries no practical weight, but the prediction is recorded as wrong on that point.

**Reading:**
- pcond's native centre weighting leaves the frozen selection essentially unchanged on a 60° view. The weights are
  0.85–1.00, and only the foveal half of the histogram is weighted.
- The saturating scale comes from the log-average adaptation level, which `-w` does not materially alter here.
- **The `-w` branch is KILLed.** Stage 2 is not run.
- Per section 6, the next level is a generic histogram-based global selection. It gets its own PREREG, opened only by
  the user.
- Adaptation / CIE 257 stay LOCKED.
