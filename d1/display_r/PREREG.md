# D1-DR pre-registration: display realisation of (Y_A, u′v′_B) on SDR100, with two symmetric candidates

Committed **before** any DR code exists.

**Inputs (frozen).**
- Y_A = the axis-A luminance extracted before pcond's gamut clip (`d1/a_extract/`, v2 PASS). Requested display
  luminance Y_req = 0.1 + 99.9·Y_A cd/m²; it can exceed 100.
- b = the frozen B output (Filament-derived Cao/Kirk κ = 3 plus the Wanat-derived local chroma collapse).
- Requested emitted colour: x₀ = b·(Y_req/Y(b)).
- Display gamut: every emitted Rec.709 channel in [0.1, 100] cd/m² (SDR100 DARK, `d0/display_model.py`).

The conflict between Y_A and u′v′_B is now genuine: no pcond `clipgamut` hides it any more. Neither coordinate is
assumed to win. Gamut-mapping practice treats luminance, chroma and hue as a trade-off (e.g. ITU-R BT.2407 on
luminance-preserving conversion and the effective gamut at a given luminance).

## Candidates (registered as equals; no fitted constants)
- **C-priority (keep u′v′_B).** Y_out = min(Y_req, Y_max(u′v′_B)): x = s·x₀, s = min(1, 100/max(x₀)). Scaling keeps
  u′v′ exactly.
- **Y-priority (keep Y).** x = w + t·(x₀ − w), w = clamp(Y_req, 0.1, 100)·(1, 1, 1), t = the largest value in [0, 1]
  inside the gamut, in closed form. This is the R1 projection, unchanged. It keeps Y and the u′v′ hue angle; chroma
  only falls.

**Below-black class (both candidates, same rule).**
- A chromaticity needing a channel < 0.1 cd/m² at its Y cannot be reached by lowering Y. It can be reached by raising
  Y, but that breaks Y_out ≤ Y_A.
- For pixels where, *after* the candidate's own step, a channel is < 0.1, both candidates apply the Y-priority
  projection at their current Y. For C-priority this replaces the requested chromaticity only where it is
  unreachable at any Y ≤ Y_A.
- The fraction of this class is reported per image and candidate.

Input-class labels, per pixel, from x₀: **in-gamut**; **above-peak** (max x₀ > 100); **below-black** (min x₀ < 0.1).
A pixel can be both.

## Corpus
- F1; S1; S5.
- S0, S3_bar and S3_nobar for the common gates.
- The S2 clip (48 frames) for P-7. Its Y_A comes from the same frozen extraction (`axis_a_x.sh` + `extract()`); C0
  and C3 are reported for the S2 frames too.
- Outputs go to `d0/work/out/d1_pipeline/dr_cprio/` and `dr_yprio/`, so `d0/metrics.py` measures them.

## Common gates (both candidates must be judged on all of these)
| id | criterion |
|---|---|
| DR-G1 physical | every emitted channel in [0.1, 100] (tolerance 10⁻⁹ relative), every image and every frame; finite |
| DR-G2 in-gamut identity | pixels with x₀ in gamut: output = x₀ exactly |
| DR-G3 no hue reversal | \|Δhue(u′v′) output vs B\| ≤ 10⁻⁶ rad where the output chroma and B's chroma are both > 10⁻⁶. Hue is N/A where the output chroma is 0 (e.g. t = 0 at peak white) |
| DR-G4 F1 monotone | emitted Y_out non-decreasing with source L for every colour (relative tolerance 10⁻⁶) |
| DR-G5 S1 (= P-5) | sky ≤ 2 cd/m², lamps/sky ≥ 10, poplar Weber ≥ 0.1, reversals ≤ 5 %, halo within 1.5× |
| DR-G6 S3 (= P-6) | displayed bar Weber > 0 |
| DR-G7 S2 (= P-7) | global-mean max step ≤ 2 %, sky-median max step ≤ 2 %, isolated-flash frames ≤ 1 |

## Candidate-specific gates
| id | C-priority | Y-priority |
|---|---|---|
| **S-1 its kept coordinate** | \|Δu′v′\| (emitted vs B) ≤ 10⁻⁶ on every pixel outside the below-black class | \|ΔY\|/Y ≤ 10⁻⁶ against clamp(Y_req, 0.1, 100) on every pixel |
| **S-2 direction** | Y_out ≤ Y_req·(1 + 10⁻⁹) everywhere; = Y_req outside the above-peak class | output chroma ≤ B chroma (+10⁻¹²) everywhere |
| **S-3 minimality** | pixels with Y_out < Y_req·(1 − 10⁻⁹) ⊆ the above-peak class, and each has max channel = 100 within 10⁻⁹ | projected pixels have a channel on a bound within 10⁻⁹ (t is the maximum) |

## Excluded from DR's KILL (stated before running)
- **Old P-9 / the S5 blue sky.** Only ~4.35 % of S5's requested pairs lie outside SDR100 (`d1/a_extract/`); the
  saturated sky is mostly in-gamut B chromaticity. A display mapper is not required to change in-gamut colour.
  Whatever remains is recorded as a **B residual**, not a DR failure.
- **Old P-4** (photopic-rank Spearman): replaced later by P-4 v2 (reference L_eff) plus R3. It is reported, not gated.
- **Whole-lamp saturation retention** (the D0 metric): misleading here. As Y → 100 cd/m² the SDR gamut collapses to
  the white point. It is replaced by core/shoulder reporting below.

## Reported (no gate)
**S1 lamps, split by requested luminance.** Within the D0 lamp mask dilated by 3 px:
- **core** = Y_req ≥ 90 cd/m²;
- **shoulder** = 50 ≤ Y_req < 90.

For each part, per candidate: pixel count, median Y_out/Y_req, and the median output u′v′ chroma / B chroma (chroma
retention). Also the mean u′v′ hue of the output against B.

Also reported:
- **S5:** fraction per input class; median sky u′v′ chroma for B and for each candidate. The prediction below is
  checked explicitly.
- **Per image:** fraction per input class and the below-black fallback fraction.
- **F1:** Y_out(L) and chroma retention per colour and level.
- **Old P-4 Spearman** (information only).

## Decision
- A candidate that fails any common gate or any of its own S-1…S-3 is **KILLED** as a display mapper.
- **Exactly one survives:** it is frozen.
- **Both survive:** there is no technical decision. The choice is a **product decision**, named as such, and made on
  the reported lamp core/shoulder, F1 and S5 numbers. It is not made on "which looks nicer".
- **Neither survives:** both are KILLED. Next is a hybrid registered separately; no tuning inside this run.

## Predictions (recorded before running)
- **C-priority** keeps warm lamps (shoulder and core retention ≈ 1, lower Y in the core), but probably **fails
  DR-G4 on F1**. As L rises, B restores saturation, so Y_max(u′v′_B) falls towards the primary ceilings (blue
  ≈ 7.3, red ≈ 21.3 cd/m²) while Y_A rises; Y_out = min(·) then decreases.
- **Y-priority** keeps every A gate and F1 monotonicity, and whitens saturated cores. In S1 the lamp core goes to
  white; the shoulder keeps part of its chroma.
- **S5 blue sky** will not disappear in either candidate, because most of it is in-gamut. That is a B residual, not a
  DR failure.
