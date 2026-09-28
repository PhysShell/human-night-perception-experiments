# D2-G1 pre-registration: observer glare architecture. Gates G0.1–G0.3 (no renders, no glare implementation)

Following `d2/TEMPLATE.md`. Committed **before** any G1 code or output. D1 is not changed; A1b is closed and not
touched. `d1/verify_manifest.sh` runs before and after. **No Blender render and no new glare stage are built** until
G0.1–G0.3 have passed.

## Origin
- **T0b** (`d2/a1/PREREG_T0.md`) added a full CIE 146 veil to the RoadLine scene before pcond's adaptation. The frozen
  A-side saturation disappeared: the scale fell 3.7–4.4 stops.
- The **erratum** to T0b:
  - that result belongs to the *coupling* chosen;
  - pcond's own `-v` uses VADAPT = 0.08, an implementation heuristic, and sees only in-image sources;
  - the dominant source (the 25 m lamp) is outside the frame.

## Architecture constraint (fixed now)
**D2-G1 does not attempt one universal glare kernel.**

| angular domain | territory |
|---|---|
| **< 0.1°** | B1 / full ocular PSF (`b1/`). **Not** CIE 146, whose domain ends at 0.1°. |
| **0.1°–100°** | CIE 146:2002 general disability-glare equation, where applicable: point source, E_glare in the plane of the eye |
| **the display's own physical glare** | a separate "second eye" (the viewer in front of the screen), a bounded correction, never mixed into the simulated veil |

## Scope
- **Scene:** the RoadLine-A2 canonical input, with the lamp metadata in `n1/roadline/work/A/lamps.json` and the camera
  geometry (eye (0.5, 0, 1.7), HFOV 60°, 1920×820, pitch 0).
- **Display:** the PHONE geometry (73 px/deg: the 60° render shown on ≈ 26.3°), SDR100, DARK.
- **Display images:** the frozen D1 output (`n1/roadline/renders/A2_canonical_final.png`) and the A1b shoulder output
  (`d2/a1/renders/roadline_A1b.png`).
- **CIE 146 parameters:** p = 0.5; ages A = 25 and 70, the T0b bracket, unchanged.
- Other scenes are out of scope for G0.

## G0.1: observer-centric source inventory
**Necessary condition:** the target glare must be representable from a bounded, observer-centric source inventory.

**The inventory**, in eye coordinates, not frame coordinates. One row per source:
- `source_id`, `world/display`;
- `E_eye [lx]` in the plane of the eye;
- `theta_from_fixation [deg]` (per target);
- `angular_size [deg]`;
- `inside_camera_frame?`, `inside_display?`;
- `CIE146_valid?`: 0.1° ≤ θ ≤ 100° **and** a point source (angular size ≤ θ/10).

**WORLD inventory:** everything physically present around the observer.
- **Point luminaires:** all 7 from `lamps.json`, including the out-of-frame 25 m one. E = I_table/r² · cos θ.
- **Extended in-frame sources:** every non-lamp frame pixel, aggregated in 4×4 blocks, is a source with
  E = L·Ω·cos θ. This covers the lit road, which T0b did not include.
- **Extended off-frame sources**, as a bound: the ground below the bottom frame edge and beside the frame, within 100°
  of each target.
  - Its luminance is bounded by the maximum luminance in the bottom 10 frame rows.
  - Off-frame sky uses the sky median.

**DISPLAY inventory:** only what actually emits from the screen area. That is the display image pixels, at 73 px/deg,
using the decoded SDR100 luminance. Used in G0.3.

**Targets:** 500 random pixels per region (road, field, sky), seed 0. The target is fixated, the T0b convention.

**Result: the veil contribution by angular band, per region.** Shares of the total veil (median over targets):

| band | status |
|---|---|
| < 0.1° | **not CIE 146**, B1/core territory. Computed with θ clamped at 0.1°, **as an indicator only** |
| 0.1–1° | CIE 146 |
| 1–30° | CIE 146 |
| 30–100° | CIE 146 |
| of which **off-camera, inside 100°** | point (25 m lamp) and extended (bound) |
| of which **extended** (block sources) | in-frame and off-frame |
| > 100° | outside the domain; E reported, no veil |

**"Relevant":** a region is relevant if its median veil/scene ≥ 0.01.

**G0.1 KILL** of the architecture "CIE 146 over the pixels of the frame is sufficient". In any relevant region, the
share of the veil from (< 0.1°) + (off-frame sources) + (extended sources) exceeds **0.10**.
- **This kills that architecture, not the glare track.**
- **The necessary condition itself fails** only if the important off-frame contribution **cannot** be supplied from
  scene metadata. The RoadLine luminaires can; the off-frame ground is only bounded.
- Separately, if the < 0.1° share exceeds 0.10 in a relevant region, the B1 PSF, not CIE 146, must carry that part.

## G0.2: sensitivity to the veil → adaptation coupling
**Necessary condition:** the decision must not depend critically on an arbitrary veil → adaptation coupling.

**Definitions:**
- **Display content:** the retinal-image hypothesis, as in T0b: C = L_scene + V, where V is the T0b point-source veil
  for the given age.
- **Adaptation input:** L_adapt = L_scene + α·V, with **α ∈ {0, 0.08, 1}**.
  - α = 0: the veil does not adapt.
  - α = 0.08: Radiance's VADAPT *magnitude*, a heuristic. **Not** its exact form: pcond uses (1 − α)·L + α·V_pcond,
    where V_pcond is its own in-image veil.
  - α = 1: T0b.

**Mechanism:** pcond's own `-I` (DO_PREHIST).
- The adaptation histogram is computed from L_adapt by Radiance's `phisto`.
- It is fed to the frozen A command on the content image, through copies of `axis_a.sh`/`axis_a_x.sh`. Their diff
  against the frozen scripts is **exactly** the `-I` flag plus the histogram on stdin, asserted in code.
- The frozen D1 display and the A1b shoulder follow unchanged.

**Validity control:** α = 0 through `-I` on the unveiled scene (C = L) must reproduce the frozen RoadLine pcond
EXPOSURE (444.77) **within 5 %**. Otherwise the `-I` path is INVALID, and G0.2 is re-planned, not reinterpreted.

**Measured per (α, A):** pcond EXPOSURE; C1 (frozen road fraction at the peak ≥ 50 %); C2 (shoulder road fraction at
the peak ≤ 0.1 %); presence of all in-frame lamps under frozen and under the shoulder (addendum-6 estimator).

**G0.2 KILL** of "one α can be adopted by convention": for either age, C1, C2 or presence differs between α = 0.08 and
α = 1. Then no single number may be chosen "because Radiance". The coupling becomes an explicit open research
question.

## G0.3: bound on the display's own glare (double counting)
**Necessary condition:** the physical glare produced by viewing the display must be small enough not to invalidate the
simulated glare.

**Per in-frame luminaire i**, glare source against glare source:
- **E_real,i** = I_i/r_i² · cos θ_i, in vacuum, at the eye in the scene.
- **E_disp,i** = Σ (L_disp − L_bg)·Ω_px·cos θ over the source's display aperture, as an upper bound.
  - The aperture is the addendum-6 emitter radius + 1.5 px.
  - L_bg is the annulus median.
  - Ω_px = (π/180/73)² sr.
  - L_disp is the DARK-decoded display luminance of the frozen D1 and the shoulder images.
- **r_E,i = E_disp,i / E_real,i.**
- **The display is minified.** θ_disp ≈ 0.438·θ_scene, and the CIE veil grows at small angles. So also:
  r_V,i = CIE veil from the display source at its display angle ÷ CIE veil from the real source at its scene angle,
  at the same target set.

**Reported per source, as requested (not gated):** r_E,i and r_V,i.

**Gated quantity (changed from the request before any data; reason below):** the aggregate, unit-consistent ratio
r = max over relevant regions of median_targets [ V_disp(t) / (g · V_sim(t)) ].
- **V_disp(t):** the CIE 146 veil in the viewer's eye from **all** display pixels (the second eye), at display angles,
  when the displayed target t is fixated. The display luminance is decoded DARK SDR100, 73 px/deg.
- **V_sim(t):** the simulated WORLD veil at t (the G0.1 inventory, A = 25 and 70).
- **g:** the displayed luminance per unit scene luminance at the veil level. For the frozen pipeline this is the
  linear-branch slope 99.9·k (k from the frozen extraction, ≈ 2.55 per cd/m²). For the shoulder the slope in the
  shadows is the same.
- **Why not max_i r_i.**
  - A per-source ratio is ill-conditioned for sources whose real glare is negligible. The 1600 m lamp has
    E_real ≈ 7·10⁻⁷ lx, yet one displayed pixel at 100 cd/m² gives ≈ 6·10⁻⁶ lx, so r_i ≈ 8 while both are
    irrelevant.
  - r_E also compares display light with scene light without the tone-mapping scale.
  - The question "does the display's own glare invalidate the simulated glare" is answered in the same units at the
    same fixations.
- **Limits:**
  - **r < 0.01:** physical screen glare is negligible.
  - **0.01 ≤ r < 0.10:** it is a bounded correction; record it.
  - **r ≥ 0.10: KILL** the assumption "physical display glare can be ignored".
  - The 1 %/10 % limits are pre-chosen engineering tolerances, not physiology.

**Off-frame sources:** E_disp = 0 (r = 0). Their absence from the display is G0.1's concern, not G0.3's.

**Diagnostic only, not gated:** the whole-screen illuminance at the eye, as a surround/adaptation diagnostic. It is
never compared with source-specific glare.

## Outcomes (fixed now)
- **G0.1–G0.3 all PASS:** a frame-pixel CIE 146 veil with a fixed coupling, and no display-glare correction, is
  defensible for RoadLine. A G1 implementation PREREG may follow.
- **Any KILL:** the specific simplification is dead, as stated per gate. The next step is decided by the user.
  - Nothing is implemented until the architecture is settled.
  - D2-B3 stays LOCKED.

## Budget
0 renders; minutes of CPU; pcond runs through `-I` copies for G0.2. Disk ≈ 40 MB per (α, A) run, deleted between runs,
with only the JSON kept.

## Prediction (recorded before any computation)
- **G0.1: KILL** of the frame-pixel architecture.
  - The off-frame 25 m lamp alone gave ≈ 76 % of the centre veil in T0b.
  - The extended lit road adds E of order 0.1–0.3 lx, comparable to the 50 m lamp's 0.1 lx, which T0b ignored.
  - < 0.1° matters only within a few pixels of each lamp: its share is small outside the lamp apertures.
  - The necessary condition itself **holds**: the off-frame luminaires are known from the metadata.
- **G0.2: KILL** of the "one α" convention.
  - At α = 0.08 the sky's adaptation input rises only about 17× (not ≈ 200×), so the frame log-mean moves much less
    than at α = 1.
  - I expect C1 to hold at α = 0.08 and fail at α = 1. Low confidence.
  - C2 holds at every α.
- **G0.3:**
  - **Per source:** r_i ≪ 0.01 for the near lamps (50 m: E_real ≈ 0.1 lx vs E_disp ≈ 10⁻⁵ lx). r_i > 1 for the far
    lamps (1600 m, ≈ 8), which is why r_i is not gated.
  - **Aggregate:**
    - At targets far from the displayed lamps, V_sim·g, dominated by the off-frame 25 m lamp (≈ 0.08–0.19 cd/m² scene ×
      g ≈ 254), is ≈ 20–50 cd/m² of displayed veil.
    - The phone's own veil from a few bright pixels is ≪ 1 cd/m².
    - **Predicted PASS (r < 0.01)**, medium confidence. Near the displayed lamps the ratio rises, and the road region
      may land in the 0.01–0.10 band.

## Amendment 1 (user review, before any code; supersedes the conflicting text above)
**G0.1:**
- **No double counting.**
  - The gated quantity is **unsupported_share**: the veil contribution of the **union** of sources that are
    (θ < 0.1°) OR off-frame OR not point-source-valid, each source/block counted once.
  - The separate breakdowns (< 0.1°, off-frame, extended, angular bands) stay diagnostic.
  - **KILL** of the frame-pixel architecture if unsupported_share > 0.10 in any relevant region, for either age.
- **"angular size ≤ θ/10" is *our* operational point-source criterion.** It is not a property of CIE 146, which defines
  its point-source formulae and the 0.1°–100° General Equation but states no such size rule.
- **The off-frame ground is a conservative upper bound.** unsupported_share is also reported *without* the off-frame
  extended bound. If the KILL holds only with the bound, the recorded wording is:
  > frame-only sufficiency is not established under the conservative off-frame bound

  **not** "the actual off-frame ground contributes > 10 %".

**G0.2:** unchanged.
- **Implementation note:** the adaptation histogram comes from Radiance's `phisto`, applied to the adaptation image
  after the same cd/m² → Radiance conversion as the frozen A script. `pcond -I` reads that histogram on stdin.

**G0.3 (replaces the gated quantity above; the per-source r_E,i and r_V,i stay report-only):**
```
for A in {25, 70}, alpha in {0.08, 1}, pipeline in {frozen, shoulder}:
    M = the mapping chosen in G0.2 for (A, alpha)   # pcond -I with the histogram of L + alpha*V
    display_with    = output(content = L + V,  mapping M)
    display_without = output(content = L,      same mapping M)   # same -I histogram => same mapping
    dYsim(t)   = Y_disp(display_with, t) - Y_disp(display_without, t)            # cd/m^2 on the display
    Vscreen(t) = CIE 146 veil (age A, p = 0.5) in the viewer's eye from ALL pixels of display_with,
                 phone geometry 73 px/deg, target t fixated at its display position, sources 0.1-100 deg only
    r_region   = median over relevant targets [Vscreen / dYsim]
r = max over A x alpha x pipeline x relevant regions
```
- **"Relevant targets":** the targets of the G0.1 relevant regions for that age, with dYsim > 10⁻⁶ cd/m². Targets
  where the simulated veil adds nothing on the display (e.g. both states clipped at the peak) are excluded, and their
  count is reported.
- **Display angles** are the linear pixel offsets / 73 px/deg (small-angle phone geometry). The per-pixel solid angle
  is (π/180/73)². The < 0.1° screen contribution is reported separately, as an indicator.
- **The limits are unchanged:** r < 0.01 negligible; 0.01–0.10 bounded correction; **≥ 0.10 KILL**.
- **α = 0** stays the G0.2 validity/control probe. It is reported for G0.3 but excluded from the gate.

**Control for V:** V is recomputed with the T0b formula (point lamps, E attenuated by T(r), CIE 146, θ clamped at
0.1°). Its frame-centre value must equal T0b's `results_T0.json` value (glare25 0.0837876, glare70 0.190384) to
10⁻⁶ relative.
