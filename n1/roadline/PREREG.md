# N1.6 RoadLine pre-registration: a line of real road luminaires receding into a moonless night, through the frozen D1

Committed **before** any RoadLine scene code. D1 is unchanged (`d1-baseline`); `d1/verify_manifest.sh` runs before and
after every run. This is **not D2**: no model changes. The hypothesis of adapting per pixel vs over an adaptation field
(D2-B3) stays closed; CIE 257:2026 is noted as its future reference, not used here.

## Question
Does the frozen D1 render the project's original stimulus — a line of distant road lights at night — without
distorting what the luminaires physically send to the eye?

## Two stimuli, one frozen geometry (`B0_RESULTS.md`, `LUMINAIRE.md`)
| | A (mandatory, first) | B (B0 PASS; only after A's verdict) |
|---|---|---|
| luminaire | Cooper Streetworks **Archeon ARCH-AF16-50-D-U-T2R-7030**, LED Type II roadway optic | Cooper Streetworks **RMA15SXX22**, 150 W HPS, open-bottom Type II acrylic refractor |
| photometry | LM-63 absolute, 5813 lm; **measured intensity at V = 90° is 0 cd** | LM-63 relative, 12772 lm luminaire; 1372 cd at V = 90° along the road |
| file | sha256 `01f3de18…`, fetched by URL, not committed | sha256 `5041092f…`, fetched by URL, not committed |
| spectrum → colour | 3000 K Planckian (Kim et al. cubic, as N1) | HPS: CIE xy (0.52, 0.42), a typical high-pressure-sodium chromaticity (approximate; labelled so) |
| emitter size | luminous opening from the file: 0.5 × 0.75 ft → a 0.15 × 0.23 m rectangle | from the file's luminous dimensions |

The word "full-cutoff" is not used: its lamp-lumen-based definition is superseded (IES RP-8, LCS). The data are stated
literally.

**Frozen geometry (both):**
- flat ground: field (Lambertian 0.08, as N1) plus a 7 m road (asphalt 0.07, the N1 material);
- no buildings, trees, hills, fog, volumes, bloom, glare or fill;
- **sky**: uniform 4·10⁻⁴ cd/m² (the M1/S0/S1 value, M1 tint). This is the sky's absolute luminance, not a claim about
  the eye's adaptation luminance. **No moon.**
- **eye**: 1.7 m, on the near road edge at (0.5, 0); looking along the road (+y), pitch 0°, HFOV 60°, 1920 × 820
  (32 px/deg), as the D1 corpus.
- **luminaires**: poles on the far edge (x = 7.5); luminaire centre (5.5, d, 8.0) over the road; street side (H = 0°)
  facing −x. The LM-63 table is applied through the Cycles IES texture on a point light.
- **distance ladder**: d = 25, 50, 100, 200, 400, 800, 1600 m, seven identical luminaires.

**Predicted from the LM-63 tables** (`n1/roadline/lm63.py`) for the exact eye direction, including the 5 m lateral
offset (V from nadir; H from the street side):

| d (m) | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| V / H (°) | 76.1 / 78.7 | 82.9 / 84.3 | 86.4 / 87.1 | 88.2 / 88.6 | 89.1 / 89.3 | 89.55 / 89.6 | 89.77 / 89.8 |
| A: I towards the eye (cd) | 2372 | 252 | 57.8 | 19.9 | 9.6 | 4.7 | 2.3 |
| A: E at the eye (lx) | 3.4 | 9.8·10⁻² | 5.7·10⁻³ | 5.0·10⁻⁴ | 6.0·10⁻⁵ | 7.3·10⁻⁶ | 9.1·10⁻⁷ |
| B: I towards the eye (cd) | 6939 | 4009 | 2478 | 1882 | 1624 | 1497 | 1434 |
| B: E at the eye (lx) | 10.1 | 1.6 | 0.25 | 4.7·10⁻² | 1.0·10⁻² | 2.3·10⁻³ | 5.6·10⁻⁴ |
| emitter size at 32 px/deg | 22 px | 11 | 5.5 | 2.8 | 1.4 | 0.7 | 0.3 |

## Pipeline (all frozen, as in N1)
- Cycles CPU, 4096 spp, the same seed; OIDN with the addendum-5 settings; the noisy pass stored.
- The render is multiplied by 179 → cd/m², then D1 as on the N1 hero (extraction + C0 self-check, B, Y-priority
  display).
- The V0 pcond path.
- The plain-Blender comparator: factory AgX; exposure in whole stops **chosen from a ladder and committed before any D1
  output of that stimulus exists**.

## Gates, per stimulus
| id | criterion |
|---|---|
| **R1 photometry** | For every lamp, its rendered intensity towards the eye = LM-63 I(direction) within **10 %** (the N1 L4 tolerance). Measured from the raw scene-linear render: the lamp window's integrated luminance above the local background × pixel solid angle × distance². Also: the illuminance under the 25-m lamp = I(0°)/h² within 10 %, from an albedo-1 probe as in N1 |
| **R2 OIDN bias** | ≤ 2 % on crops fixed in the code before the render: near road, far road, field, sky. **Also on each lamp window's integrated signal**, since the denoiser must not erase or smear point sources |
| **R3 D1 self-check** | C0 bit-identical, C2/C3; display gates G1–G3, S-1…S-3. The sRGB knee artefact is a known class (`d1/ERRATA.md` E1): FAIL stays FAIL, classified if it is that class |
| **R4 ordering** | Where the scene-linear lamp signal decreases with d, the D1 output lamp signal (display luminance integrated over the lamp window above background) decreases too. Adjacent lamps both at the display floor are N/A, not an inversion |
| **R5 presence** | A lamp is *present* in an image if its window contains at least one pixel ≥ 1 16-bit code above the local-background median. **D1 must show present exactly the lamps that the raw linear anchor shows present** (the N1 "raw" variant: scene Y × k with the N1 anchor rule, scene colour, Y-priority). D1 making a lamp vanish earlier, or persist longer, than the linear anchor is a FAIL of R5 |
| **R6 colour by distance** | Reported: the u′v′ hue and chroma of each lamp core in D1 vs scene. Visual only, part of V6; the known rod-term residual (`d2/b2`) is declared |
| **V1–V6** | By the same external observer, on the D1 image alone, in the sheet format that opens. Declared residuals: white cores at the SDR peak; the rod-term pinkish tint on warm light |
| **V7 blind** | A blind sheet: D1 / V0 / plain Blender, seed-0 permutation, key hash committed before showing, judged by the external observer. The question: which renders a line of distant road lights most convincingly |

## KILL (stops N1 before motion)
- R4 or R5 fails: D1 reorders, erases or artificially keeps identical lamps.
- R1 or R2 fails and cannot be classified as a scene or measurement error: then the stimulus itself is not trusted.
- A new display pathology (clipping/gamut) not in the declared classes.
- On the blind sheets D1 is judged **worse than V0 on both A and B**, and no D1 advantage appears anywhere in this
  stimulus.

A physical disappearance is not a KILL. A's far lamps are expected to fall towards invisibility because the measured
intensity near the horizon is small. What is tested is whether D1 **follows** the physics (R4/R5 against the linear
anchor), not whether all seven lamps are visible.

## Budget and order
1. A: one static still (+ probes).
2. A verdict.
3. Then B: one static still.

There is no animation before both verdicts. The motion step (N1.7) needs its own addendum.

## Predictions (recorded before running)
- **R1 passes** for both, within 10 %, if Cycles' IES texture follows the table. That is the main technical risk: the
  Cycles IES normalisation and the camera visibility of an IES point light are untested here. If R1 fails, the failure
  is located in the renderer before anything else.
- **A:** the lamps at 25–200 m are clearly present; 400 m faintly; **800 and 1600 m absent or at the edge** of
  presence in the raw anchor and in D1 alike. The image reads as a few lamps plus their road pools, not a long string.
- **B:** all seven lamps present as a receding string: the M1-like stimulus, now from a measured luminaire.
- **R4 and R5 pass** for both (D1's A is a single global pcond scale, and B changes no luminance).
- The far HPS cores in B are small bright points, rendered close to photopic by B's per-pixel law; the rod-term tint
  is expected mainly on the dim road pools, not on the cores.

---

## Addendum 1 (committed before any scene code): N1.6A0, single-luminaire IES calibration and orientation check
A0 comes **first**, as its own kill-gate. N1.6A1 (the full RoadLine-A still) runs only if A0 passes.

**Mapping hypothesis, fixed before testing:**
- The Cycles IES texture outputs the table **normalised to its maximum** (factor f(dir) ∈ [0, 1]).
- A point light of power P then has I(dir) = K · P/(4π) · f(dir) (K = 179, the N1/M1 convention).
- So **P = 4π · I_max / K**, with I_max = 4844.7 cd for Archeon.
- The emission node strength is 1, the colour is 3000 K at unit luminance, and the radius is 0.105 m (a disc of the
  file's 0.15 × 0.23 m luminous area).
- **Orientation:** the light points down (V = 0° = −z). The table's H = 0° (street side) is placed along the light's
  local axis that faces −x (across the road) in the scene.
- The exact node vector/rotation used is recorded in code. A0 tests it and it is not tuned.

**A0 measurements** (the same frozen sky, ground, materials and camera as A; one luminaire):
1. **Intensity by direction.**
   - Albedo-1 Lambertian patches, 0.3 m, facing the light at 10 m in directions (V, H):
     (0, –), (45, 0), (60, 0), (60, 90), (60, 180), (75, 90), (82.5, 90), (87.5, 90), (90, 90).
   - Measured I = π·L·r² (small orthographic cameras, as in N1).
   - **PASS:** every direction within **10 %** of the LM-63 value where the table gives ≥ 10 cd. Where it gives
     < 10 cd (V = 90°: 0 cd), the measured value is < 10 cd.
2. **Camera-visible emitter.**
   - The luminaire at d = 25, 100, 400 m, one at a time, seen from the A eye.
   - Integrated lamp-window luminance above background × pixel solid angle × distance² = LM-63 I(eye direction)
     within **10 %** (R1's rule).
3. **Ground check.** Illuminance under the luminaire (albedo-1 probe at the road surface) = I(0°)/h² within 10 %.

**Outcome:**
- **All pass:** A1 is built with this exact mapping.
- **Any fail:** stop and diagnose (normalisation, orientation, camera visibility), and report. Any correction is
  derived from the Cycles/Blender behaviour it reveals and registered as a further addendum before A1. It is never
  fitted to make A1 look right.

---

## A0 run 1: **FAIL** (`a0_A_v1_FAIL.json`) and Addendum 2, three corrections derived from Cycles itself (committed before re-running)
Run 1 failed everywhere:
- probe intensities were 63–3210 × the table, with a direction-dependent ratio;
- the emitter was invisible to the camera.

Diagnosed from the Cycles source (`intern/cycles/util/ies.cpp`, `intern/cycles/kernel/svm/ies.h`, fetched from
projects.blender.org) and one Blender check. **Nothing below is fitted to the probes.**

1. **Normalisation.**
   - Cycles does not normalise to the maximum. The IES node outputs **candela × 4π/177.83** (`ies.cpp`: "4·π/177.83 as
     a Candela to Watt factor"; D65 efficacy 177.83 lm/W). The light's power multiplies that.
   - Hence I(dir) = candela(dir) · P · K/177.83 in our K = 179 convention, and **P = 177.83/179 W** gives I = the table
     exactly.
   - Run 1 used P = 4π·I_max/K = 340 W. The predicted nadir ratio is 340 × 179/177.83 = 342; measured 344.
2. **Orientation.**
   - `svm/ies.h`: V = acos(−z), **H = atan2(x, y) + π** in the light's local frame. So table H = 0 is local **−y**,
     H = 90° is local −x, and H = 180° is local +y.
   - To put H = 0 (street side) on world −x, the light is rotated **−90° about z** (run 1 used +180°).
   - Run 1 checked against that convention: my "V60/H0" probe was seen by Cycles as H = 270 (table 2248 → measured
     2235 after the scale); "V60/H180" as H = 90 (2248 → 2235); "V60/H90" as H = 0 (973 → 975). This explains why
     H0 and H180 were identical.
3. **Camera visibility.**
   - Blender light objects default to `visible_camera = False`, verified: a bare point light renders 0.
   - The light is set **`visible_camera = True`**, so the camera sees its 0.105 m sphere, shaded by the same IES
     emission.

The A0 gates are unchanged. A0 is re-run once.

---

## A0 run 2 (`a0_A_v2_FAIL.json`) and Addendum 3 (committed before run 3)
**Run 2.** All nine direction probes and the ground check **PASS**: ratio 0.991–1.021; V = 90° gives 1.7 cd against
the table's 0 (< 10). The addendum-2 normalisation and orientation are confirmed. The emitter check **FAILS**:
- **25 m: out of frame.** The luminaire at 8 m, 25 m away, is at 14.1° elevation; the frame top at pitch 0 is 13.85°.
  My PREREG prediction table did not check the frame. The 25 m lamp appears in A1 only through its road pool.
- **100 m: 0.82 × table; 400 m: 0.64 × table.**

**Diagnosis.** The same camera-visible point light **without IES** gives exactly P·K/4π at 100 and 400 m (14.2 vs
14.15 cd). So for camera rays Cycles does not evaluate the IES at the direction towards the eye. The deficit is in the
IES-shaded visible sphere, not in pixel integration or geometry.

**Addendum 3, derived from that behaviour** (the N1 construction):
- The IES point light is **hidden from the camera** and only illuminates; its illumination is verified by the probes.
- Each luminaire gets a **camera-only emitter**: a sphere of the same 0.105 m radius, uniform radiance
  **L = I_table(eye direction) / (π r²)** in the luminaire colour. It is invisible to diffuse, glossy, transmission,
  volume and shadow rays.
- I_table uses the exact eye direction from `lm63.py`.
- The emitter check therefore tests the construction plus pixel integration; the photometric truth comes from the
  table. This is stated as such.
- The **A0 emitter distances become 50, 100 and 400 m** (25 m is out of frame).
- The gates are unchanged; A0 is re-run once.

## A0 run 3: **PASS** (`a0_A.json`)
- **Direction probes and ground:** ratio 0.991–1.021 against the table; V = 90° gives 1.7 cd (< 10).
- **Camera-visible emitter:** 50 / 100 / 400 m give 247.9 / 57.1 / 9.4 cd against 251.5 / 57.8 / 9.6
  (ratio 0.986 / 0.987 / 0.979).
- **A1 is built with exactly this mapping:**
  - P = 177.83/K;
  - rotation −90° about z;
  - the IES light hidden from the camera;
  - a camera-only emitter with L = I_table(eye)/(π r²).
- **Correction to the prediction table:** the 25 m luminaire head is out of frame at pitch 0°. It appears only through
  its road pool.

---

## A1 run 1 invalid, and Addendum 4 (committed before re-rendering): the camera far clip
- A1 run 1 rendered the 1600 m luminaire as **nothing**: its window equals the sky, 4·10⁻⁴ cd/m².
- Cause: Blender's default camera `clip_end` is **1000 m** (verified). M1 used 60 km; `n1/roadline/scene.py` did not
  set it. So everything beyond 1 km was clipped: the 1600 m lamp and the far road and field.
- **Fix, implementing the PREREG geometry as written:** `clip_end = 60 000 m` (the M1 value) on the eye camera, and on
  the A0 emitter camera for consistency.
- Run 1 is discarded without evaluation. R1/R2 were aborted by a zero lamp signal at 1600 m, and no D1 output exists.
- The same default affected N1 (`n1/README.md`, erratum N1-E1).

## A1 run 2 (after addendum 4): **R1 FAIL (1600 m) and R2 FAIL (lamp windows at 400 and 800 m)**. Stopped per the KILL clause (`a1_A.json`)

**R1** (pre-registered window rule).

| d (m) | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|
| measured / table | 0.986 | 0.987 | 1.000 | 1.015 | 1.072 | **1.221** |

**R2 (OIDN):**
- the crops are within ±0.11 % and the whole frame +0.50 %;
- the lamp windows are within < 1 % except **400 m +4.16 %** and **800 m +5.79 %**.

**Diagnosis** (post-hoc diagnostic, not a change of the gates):
- **R1 at 1600 m is measurement contamination, not the render.**
  - With a circular aperture of the pixel filter's support (r = 2.5 px) and the sky as background, the 1600 m lamp
    gives **1.078**; with r = 4 px, 1.20. It grows with aperture.
  - The 9 × 9 window next to the horizon collects the far road pools (now rendered) and the 800 m lamp's filter tail
    8.4 px away.
  - At 100–800 m, every aperture gives 0.98–1.00.
  - **Classification:** measurement error of the pre-registered window rule near the horizon. It stays a literal
    FAIL.
- **R2 is a real denoiser bias on small point sources.**
  - The OIDN excess is independent of aperture: +4.3 % at 400 m, +6.2 % at 800 m (1–3 px emitters). It is < 1 % at
    50–200 m and −0.6 % at 1600 m.
  - The denoiser also does no visible work elsewhere: the pixel CoV of every crop is identical before and after
    (near road 0.026, far road 1.164, field 0.567, sky 0.000). This scene has no firefly regime: every surface is lit
    directly, with no occluders except the poles.
  - **Classification:** input preparation (denoiser) biasing the very quantity RoadLine tests. Under the KILL clause,
    **the denoised A1 image is not trusted.**

No D1, V0 or comparator output of A1 exists. The next step is a decision.

---

## Addendum 5 (committed before the 2048-spp render): no OIDN for RoadLine; a frozen point-source estimator; raw convergence
**The previous A1 run stays FAIL** under the original R1 and R2. Root causes:
- R1 at 1600 m: the 9 × 9 estimator is contaminated by the neighbouring lamp and the horizon;
- R2 at 400 and 800 m: OIDN introduces a real point-source bias above the frozen 2 % and gives no material variance
  reduction.

**RoadLine input preparation = raw Cycles (the Noisy Image pass), no OIDN**, only if the convergence test below
passes.
- The OIDN decision in N1 (hero, B, C: firefly regime) is untouched. The scenes are in different sampling regimes.
- **R2 becomes N/A (no denoiser used), not PASS.**
- The geometry is **not** changed (no lowering of the lamp row to help the metric).

**Frozen point-source estimator ("R1v2"), for R1, the convergence test, R4 and R5:**
- **centre:** the predicted emitter centre from `lamps.json` (continuous pixel coordinates; pixel centres at +0.5);
- **signal aperture:** all pixels whose centre lies within **r = 2.5 px** of it. 2.5 px is the support of Cycles'
  default Blackman-Harris 1.5 px filter;
- **background:** the median over the annulus **3.5 < r ≤ 6.0 px** around the same centre, excluding every pixel whose
  centre lies within 2.5 px of any other in-frame emitter centre;
- **signal:** Σ over the aperture (value − background) × pixel solid angle cos³θ/f². Intensity = signal × distance².

**Bounded convergence experiment:**
- **one** additional raw render at **2048 spp** (same scene, same seed; OIDN may run, but only its stored noisy pass is
  used), compared with the existing corrected 4096 raw;
- **pass:** every scene crop (near road, far road, field, sky; the N1 addendum-4 metric: median over 8 × 8 blocks of
  \|block median(4096)/block median(2048) − 1\|) **≤ 2 %**, **and** every in-frame emitter signal
  \|S4096/S2048 − 1\| ≤ 2 %;
- **PASS:** the existing raw 4096 is frozen as the RoadLine-A input. Then:
  1. R1v2;
  2. R2 = N/A;
  3. the comparator exposure before D1;
  4. D1 and the linear reference;
  5. R3–R5;
  6. V1–V6;
  7. the blind sheet.
- **FAIL:** stop. There is no 8192 spp and no third estimator.

## Addendum-5 result: **FAIL, stopped** (`a1_A.json`: `convergence`, `R1v2`)
**Convergence, raw 2048 vs raw 4096:**
- crops: near road 0.02 %, far road 0.13 %, field 0.11 %, sky 0.00 %, all PASS;
- emitters: 50 m +0.01 %, 100 m −0.07 %, 200 m +0.33 %, 400 m +0.79 %, **800 m +2.005 %**, **1600 m −2.385 %**
  (**FAIL**).

**R1v2 (4096 raw):**

| d (m) | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|
| measured / table | **0.541** | 0.982 | 0.983 | 0.987 | 0.995 | 1.078 |

**FAIL at 50 m.**

**Causes (diagnosis, no re-evaluation):**
- **Sub-pixel emitters are Monte-Carlo-limited.** The 0.105 m sphere is 0.44 px across at 800 m and 0.22 px at
  1600 m, so only a few per cent of camera samples hit it; the hit count fluctuates at ~2 % even at 2048/4096 spp.
  This is the unresolved-source sampling problem met in M2.5 (`m1/scene.py`, M25_LAMP_PX).
- **The addendum-5 estimator is wrong for resolved emitters. This is my design error.**
  - r = 2.5 px is the filter support for a *point*. The 50 m emitter is 6.9 px across, so the aperture truncates it
    (0.541). The 100 m emitter (3.5 px) is at the limit.
  - The run-2 diagnostic had already shown 0.541 at 50 m with r = 2.5, and I did not catch it when writing
    addendum 5.

Per addendum 5: stop. There is no 8192 spp and no third estimator without a decision.

---

## Addendum 6 (committed before any new render): the M2.5 split pass for the two unresolved far lamps only
The design is the user's review of my first draft. My draft **rejected**:
- enlarging sub-pixel emitters to 2 px inside the full render;
- a new ±2.5 px margin.

**Reason for the rejection.** Keeping I = L·πr² keeps the integrated intensity in linear optics, not the
**output-pixel stimulus**. D1 is nonlinear after rasterisation: B works per pixel, pcond depends on the luminance
distribution, and the display mapping is per pixel.
- For an unresolved source, the continuous linear image is defined by its intensity and the PSF.
- Artificial enlargement is allowed only if the supersampling/resampling provably reproduces the original
  output-pixel stimulus.

**What converged is not touched.**
- The scene crops (0.00–0.13 %) and the 50–400 m emitters (≤ 0.79 %) converged in addendum 5.
- The IES lighting of the road is unchanged.

**1. Base render.** RoadLine-A exactly as before (raw Cycles, 4096 spp, same seed, **no OIDN**). The only change: the
**camera-visible emitters of the 800 m and 1600 m luminaires are removed**; their IES lights stay.
- No new base ladder: the addendum-5 test showed that the non-emitter scene signal converges.

**2. Far-lamps pass (M2.5 method, `m25/render_clip.sh`, `m25/resample.py`).** It contains only the 800 m and 1600 m
camera-visible emitters: no sky, road, field, poles or lights. Nothing occludes them from the eye: the lines of sight
pass ≥ 6 m below the arms, and the poles stand beyond the lamps.
- **Enlargement.** The apparent diameter is raised to **0.7 px** (the M2.5 value), r′ = 0.35 · distance / f. The
  radiance is lowered by area so that I = L′·πr′² = I_table(eye).
- **Rendering.** 4× resolution, 1-px box filter, 256 spp (4096 per output pixel), fixed seed, no adaptive sampling.
- **Resampling** to the output with Cycles' Blackman-Harris over a 3-output-pixel window (`m25/resample.py`,
  unchanged).
- **Output.** The final scene-linear image = base + far pass.

**3. Estimator.**
- Aperture radius **r_ap = projected emitter radius (px) + 1.5 px**. 1.5 px is the half-width of Cycles'
  Blackman-Harris window (2 × filter_width 1.5 = 3 px; `film.cpp`, as in M2.5).
- **Base render, 50–400 m:** background = median of the annulus r_ap + 1 < r ≤ r_ap + 3.5 px, excluding pixels within
  r_ap of any other emitter centre.
- **Far pass:** the background is identically zero, so no background estimator is needed.
- The same estimator is used for R1, R4 and R5.

**Gates:**
1. **Far-pass convergence.** Two fixed seeds (0 and 1): for each far lamp, \|S_seed0/S_seed1 − 1\| ≤ 2 %.
2. **Far-pass equivalence (the M2.5 gate).**
   - Reference: the true-radius (0.105 m) emitters only, rendered directly at the output resolution with Cycles'
     own filter, 16 384 spp, seeds 0 and 1.
   - Per lamp: total energy far-pass/reference within max(2 %, 2 × the reference's seed spread).
   - **Output-pixel stimulus:** the 5 × 5 energy distributions, normalised to 1, satisfy Σ\|p_far − p_ref\| ≤ 0.10.
     The peak-pixel share is reported.
3. **R1** (±10 %, as pre-registered):
   - 800 and 1600 m from the far pass (I = S·d²);
   - 50–400 m from the base with the r_ap estimator.
   - The 25 m lamp is out of frame.
4. **R2:** N/A (no denoiser).

**KILL:** any far-pass gate fails, or R1 fails. RoadLine-A on the raster/Cycles method then stops for good; there is
no 8192 spp and no fourth estimator.

**If all pass:** the addendum-5 order applies:
1. the comparator exposure before D1;
2. D1 and the linear reference;
3. R3–R5;
4. V1–V6;
5. the blind sheet.
