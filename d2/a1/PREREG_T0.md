# T0 pre-registration: distance-transport audit of the RoadLine-A2 stimulus (before D2-A1b stage 2)

Committed **before** any T0 code or output. It is not a renderer experiment: no Blender run, and no image is shown or
judged. The pipeline runs only to measure. A1b, D1 and the RoadLine stimulus are **not** changed.

## Why
The RoadLine scene (`n1/roadline/scene.py`) already has these right, and **no extra 1/r² is added**:
- the geometric distance dependence: Cycles' inverse-square falloff on surfaces;
- the LM-63 intensity towards the eye;
- the shrinking projected emitter, with camera-visible L = I/(πr²);
- R1 checked against LM-63 at 0.983–0.998.

What it does **not** have:
- **(a) atmosphere.** The old M1 baked Koschmieder extinction at V = 25 km (`m1/scene.py:236`,
  `exp(−3.912·d/V)`); RoadLine has vacuum.
- **(b) eye optics / disability glare** (the CIE veiling luminance).

**Question:** is either large enough to change the RoadLine stimulus or the visual conclusions that A1b stage 1
rests on?
- **C1:** frozen D1 shows *broad* roadway saturation.
- **C2:** the A1b shoulder removes it.

## Data (existing; 0 renders)
- `n1/roadline/work/A6/canonical_cdm2.exr` (scene cd/m²).
- `n1/roadline/work/A/lamps.json`: all 7 luminaires, including the **out-of-frame 25 m lamp**. It sits just above the
  top edge, with I_table = 2372 cd towards the eye. The table also gives distance r_m and the pixel position.
- The camera: eye (0.5, 0, 1.7), HFOV 60°, 1920×820, pitch 0, horizon row 410.

## Per-pixel distance (from the known geometry, no render)
- **Ground (rows below the horizon):** the ray length to the ground plane z = 0, d = t·√(F² + dx² + dy²)/F.
- **Above the horizon:**
  - a pixel brighter than 2 × the sky median is a pole, arm or luminaire. It gets the distance of the lamp whose
    projected pole column is nearest.
  - All other pixels are **sky**: at infinity and not attenuated, since the sky radiance is already the at-eye value.
- The fraction assigned to each class is reported.

## T0a: atmosphere (a transport effect; can fix the scene)
Koschmieder, V = 25 km (M1's value): T(d) = exp(−3.912·d/V), with airlight L_h·(1 − T). L_h is the median sky luminance
in the 20 rows above the horizon.
- **V_atm (conservative bound):** pixel = L·T(d)² + L_h(1 − T(d)).
  - T² bounds the extra lamp → surface path, since that path is ≤ the eye path for the lit near road.
  - Lamp and pole pixels use T(d).
- **Reported:**
  - T(d) for 50…1600 m;
  - the change in the scene-luminance histogram (road Q50/Q90/Q99/Q99.9, frame log-mean).
- **Measured through the frozen pipeline:**
  - the frozen A: `axis_a.sh` + `axis_a_x.sh` on the modified EXR, new cache names `T0_*`;
  - frozen D1 display → **C1** and the pcond EXPOSURE shift;
  - the A1b shoulder, via the `run_A1b.py` substitution → **C2**;
  - lamp presence (max code above the background, addendum-6 estimator) for all in-frame lamps, frozen and shoulder.

## T0b: disability glare (an observer effect; diagnostic only)
**Model.** The CIE 146:2002 general disability-glare equation:
L_veil / E_gl = 10/θ³ + (5/θ² + 0.1·p/θ)·(1 + (A/62.5)⁴) + 0.0025·p
- θ in degrees, clamped to ≥ 0.1°;
- p = 0.5;
- **ages A = 25 and 70**, a pre-registered bracket, not a search.

**Inputs.**
- E_gl,i = T(r_i)·I_i/r_i² · cos θ_i, for every lamp including the 25 m one.
- The veil map sums over all lamps and is added as neutral (D65) luminance.

**Variants.**
- **V_glare25** = V_atm, with eye-path T only (not T²), plus the veil for A = 25.
- **V_glare70** = the same plus the veil for A = 70.

**Measured:** the same pipeline and C1/C2 as T0a. Reported: veil/scene ratio medians over road, field and sky; the
frame fraction where veil > scene luminance.

**Stated deviation from the request.** Glare is not scene transport:
- The veil is formed in the observer's eye.
- Baking it into the scene input and then showing that on a display, which the viewer's own eye glares again, would
  count it twice.
- So **T0b cannot "fix the RoadLine transport"**. It measures how much the A-side conclusions depend on D1 having no
  glare stage.

## Criteria (fixed now)
**C1 (frozen D1 broad saturation holds):** road fraction with Y_disp ≥ 99.9 **≥ 50 %**. "Broad" means the majority of
the road; the vacuum value is 81.8 %.

**C2 (the shoulder removes it):** road fraction with Y_disp ≥ 99.9 **≤ 0.1 %**. The vacuum value is 0 %.

**Presence:** no in-frame lamp that is present under frozen D1 or under the shoulder in vacuum becomes absent.

**T0a result:**
- **PASS:** C1, C2 and presence all hold under V_atm, so the RoadLine conclusion is robust to the missing
  atmosphere: **GO A1b stage 2.**
- **KILL:** any of them fails, so the RoadLine transport is fixed (an atmosphere added) **before** A1b stage 2 or any
  adoption. That is its own PREREG.

**T0b reading:**
- **C1 and C2 hold under both glare variants:** the conclusions do not depend on the missing glare stage.
- **C1 fails** (frozen D1 no longer broadly saturates once the veil is in the input):
  - it is recorded that the A-side failure, as observed, is conditional on scene radiance **without** glare;
  - whether D1 should model disability glare is a separate D2 question, for the user to open;
  - it does **not** by itself block A1b stage 2, since stage 2 tests the shoulder on the stimuli D1 actually receives.
- **C2 fails:** it is recorded as a condition on any adoption.

## Budget
0 renders; minutes of CPU. Disk ≈ 40 MB per variant, with caches deleted between variants and only the JSON kept.
`d1/verify_manifest.sh` runs before and after.

## Prediction (recorded before computing anything)
- **T0a PASS:**
  - T(200 m) = 0.969 and T(1600 m) = 0.778;
  - the saturated near road is within ≈ 150 m, so T² ≥ 0.95 there;
  - C1 ≈ 80 %, C2 = 0 %;
  - the far lamps lose ≈ 22 % at 1600 m but stay present (a saturated core, far above one code).
- **T0b is large:**
  - The out-of-frame 25 m lamp alone gives E_gl ≈ 3 lx at the eye, about 14° above the line of sight. That is a veil
    of order 0.1–0.2 cd/m² at the frame centre (A = 25), and more at A = 70.
  - That exceeds the dark field (≈ 0.08) and the sky (4·10⁻⁴) over most of the frame.
  - The frame log-mean rises strongly, so pcond's linear scale drops. **C1 may fail under glare** (low confidence), and
    C2 should still hold.

## Results (`results_T0.json`, code `af92d4a`)
`d1/verify_manifest.sh` after every step: all OK.

**Pixel classes:** ground 49.9 %; above-horizon objects (poles, lamps) 0.64 %; sky 49.5 %. L_h = sky median = 4·10⁻⁴.

### T0a: atmosphere, V_atm (conservative T²). **PASS: the RoadLine conclusion is robust**
| quantity | vacuum | V_atm |
|---|---|---|
| frame log-mean | 0.006463 | 0.006485 (+0.3 %) |
| road Q99.9 (cd/m²) | 1.488 | 1.472 |
| pcond EXPOSURE | 444.77 | 444.71 (linear) |
| **C1** frozen road at peak | 81.8 % | **81.8 %** |
| **C2** shoulder road at peak | 0 % | **0 %** |
| presence | all six | all six, under both |

T(d): 50 m 0.992; 200 m 0.969; 400 m 0.939; 800 m 0.882; 1600 m 0.779.

**Per the pre-registered rule: GO A1b stage 2.** The missing atmosphere does not change the A1b stage-1 basis.

### T0b: disability glare (CIE 146, p = 0.5), diagnostic. **C1 FAILS under glare; C2 holds**
**The veil is dominated by the out-of-frame 25 m lamp:** E_gl = 3.43 lx at the eye.

| quantity | vacuum | glare A = 25 | glare A = 70 |
|---|---|---|---|
| veil at the frame centre (cd/m²) | — | 0.084 (0.064 from the 25 m lamp) | 0.190 (0.165) |
| median veil/scene: road | — | 0.06 | 0.14 |
| median veil/scene: field | — | 0.22 | 0.49 |
| median veil/scene: sky | — | 195 | 450 |
| frame fraction with veil > scene | — | 59.7 % | 62.7 % |
| frame log-mean | 0.0065 | 0.137 (21×) | 0.232 (36×) |
| **pcond EXPOSURE** (linear) | 444.8 | **34.5 (−3.7 stops)** | **20.4 (−4.4 stops)** |
| **C1** frozen road at peak | 81.8 % | **0 % → FAIL** | **0 % → FAIL** |
| **C2** shoulder road at peak | 0 % | **0 % → holds** | **0 % → holds** |
| road median Y_disp, frozen / shoulder | — | 14.1 / 12.4 | 8.9 / 8.2 |

**Presence under glare:**
- Frozen D1 **loses the 50 m and 100 m lamps**: 0 codes above the annulus, because the lamp sits inside its own saturated
  veil blob.
- The shoulder keeps all six (50 m: 1 305 codes, 100 m: 10 572 codes).
- It is reported here; the T0b presence reading was not a pre-registered gate.

**Reading (pre-registered):**
- **The A-side failure as observed is conditional on scene radiance *without* glare.** With a CIE veil in the input,
  pcond's log-average adaptation rises about 20–36×, and its linear scale falls by 3.7–4.4 stops. The broad road
  saturation disappears.
- Frozen D1 is pcond `-s -c`, deliberately **without** pcond's own veiling option `-a`.
- **Whether D1 should model disability glare is a separate D2 question for the user.** It does not by itself block A1b
  stage 2.
- **C2 holds under glare:** the shoulder's behaviour does not depend on it.

**Against the prediction:**
- **Right:**
  - T0a PASS, with the numbers as predicted;
  - T0b large, dominated by the 25 m lamp, with a centre veil of order 0.1–0.2 cd/m²;
  - "C1 may fail" — it did fail, on both ages;
  - C2 holds.
- **Not predicted:** frozen D1 losing the 50/100 m lamps into their veil blobs under glare.

## Errata (after the user's review; the results above are unchanged)
**E1: wrong pcond flag.**
- **The error:** "pcond's own veiling option `-a`" is wrong. In pcond, `-a` is the loss of visual **acuity**
  (DO_ACUITY), `-v` is **veiling glare** (DO_VEIL), and `-h` = `-a -v -s -c`.
- **Correction:** frozen D1 is pcond `-s -c`, without `-v`.
- **pcond's own glare coupling differs from T0b's.**
  - In `pcond4.c`: VADAPT = 0.08, the "fraction of adaptation from veil". `compveil()` mixes the veil into the foveal
    image at that fraction before the histogram is recomputed.
  - Radiance therefore does **not** feed the full veil 1:1 into exposure selection.
  - pcond's `-v` computes glare only from bright regions **inside** the image. It would not see the dominant
    out-of-frame 25 m lamp, which CIE 146 counts as a legitimate source (0.1°–100°).

**E2: the reading is too strong. It is replaced by:**
> Under the T0b coupling, where the full CIE 146 veil is added to the scene before adaptation, the observed A-side
> saturation disappears. Whether this coupling is an appropriate observer model is unresolved.

- The −3.7/−4.4-stop scale change and C1's failure belong to that specific coupling, not to human disability glare in
  general.
- **The "double counting" argument is also weakened.** pcond is designed to put simulated veiling glare into the
  display image, so an effect in the final picture is not double counting as such. The real question is how much
  optical glare the display itself adds for the viewer, compared with the real lamps (E_eye ≈ 3.4 lx from the 25 m
  lamp). That can be measured.

**Order (user decision):**
1. A1b stage 2 now.
2. A1b closed PASS/FAIL, with the operator unchanged.
3. Then a separate **D2-G1, observer glare architecture**, with three cheap kill-gates and no renders:
   - **G0.1:** CIE 146 source inventory, including out-of-frame sources;
   - **G0.2:** the adaptation coupling, full veil vs Radiance's VADAPT = 0.08;
   - **G0.3:** a display double-count bound, E_eye from the final SDR display vs the 3.4 lx of the real lamp.
