# Test strategy (T2 freeze)

One command, `nix flake check` (~8 min on 4 CPU cores), must say that:
- the physical properties still hold;
- the frozen visual baseline is unchanged.

Everything else is a diagnostic or a later milestone. The rule behind this: M2 showed several
times that "the image looks odd" was really one of our own errors:
- a peak-pixel metric instead of lamp energy;
- a median over columns without lamps;
- a reference that still carried baked extinction;
- a test geometry whose own light polluted the measurement.

Tests caught these before eyes did.

## Three kinds of reference, three kinds of question

| reference | question it answers | examples here |
|---|---|---|
| **physical oracle** (closed form) | is it *right*? | radiometry (ρE/π, P/4π), Beer–Lambert, Spencer PSF |
| **implementation reference** (existing tool as shipped) | did *our glue* change the tool's result? | pcond mapping, LC luminance = pcond, Fog Glow adapter |
| **frozen baseline** (golden) | did *anything* change by accident? | golden vacuum/clear/mild |

None of these answers "is it more realistic?". That needs a ground truth or human judgement (see
Deferred).

## Implemented gates (`nix flake check`)

| check | kind | what must hold | result |
|---|---|---|---|
| `pcond-mapping` | implementation | pcond `-x` semantics (histogram 1.00; linear-mode bug 179/Ldmax guarded); LC luminance = pcond; clipped chroma kept within 2–3 RGBE steps | pass |
| `pcond-continuity` | property | colour ramp 0.03 → 30 cd/m² through the clip point: no colour seams (> 3× neighbours and > 0.002 u′v′), no luminance pops (> 5 % vs pcond), **intensity ↑ ⇒ pcond-stage luminance never falls**, no NaN/Inf | pass |
| `fog-glow-psf` | physical | Blender 5.2.2 Fog Glow at Size = ((180 − FOV)/170)³ follows Spencer Eq. 5 (±2 % at 0.09–3°, ±5 % at 10°), energy ≥ 0.97; has a negative control | pass |
| `t2-extinction` | physical + metamorphic | a small lamp at 1–15 km through the scene's own clear/mild layer: **T/T_Beer–Lambert ∈ [0.99, 1.02] per channel** where T ≥ 0.02 (measured within 0.4 %); T(vacuum) ≥ T(clear) ≥ T(mild) at every distance | pass |
| `t2-haze` | metamorphic | real scene, 8° window on the ribbon, vacuum → clear → mild through the frozen stack: direct lamp energy decreases; lamp contrast does not increase (scene and display); ribbon RMS width does not decrease; finite everywhere | pass |
| `t2-golden` | baseline | 320×137, 128 spp, fixed seed. Scene in cd/m²: a pixel fails if \|d\| > 10⁻⁴ **and** > 5 %, ≤ 1 % may fail. Display PNG: `--fail 0.016 --failpercent 1`, our starting threshold, taken from the base default of Blender 5.2.2's `render_report.py` (Cycles' own suites raise it per directory, e.g. volume 0.048 / 3 %) | pass (bit-identical rerun) |
| `m25-decomposition` | physical + implementation | the M2.5 clip render = haze pass + lamps pass equals the one-pass M2 render: background within 2 %; lamp energy (enlarged 0.7 px, supersampled, Blackman–Harris resample) vs true-radius lamps: total within 2 %, every bin within max(10 %, 2 × reference seed spread); spot shape (peak-row share) within 0.08 of Cycles' own filter | pass (1.001; 0.756 vs 0.798) |
| `m25-golden-clip` | baseline + invariants | 4-frame walking clip at the golden view: the clip invariants below, then per-frame scene and display compare as `t2-golden` | pass; negative controls: ×1.10 fails, sub-pixel camera shifts only warn (documented) |

**Clip invariants** (`m25/check_clip.py`, run on every clip):
- finite;
- pcond stays in linear mode with the same exposure on every frame (< 1 %): a global flicker
  no eye makes;
- lamp energy away from the frame edges: no single-frame blink > 0.5 % (steps from lamps leaving the frame or passing behind poplars are reported, not failed);
- no single-frame **blink** (a frame away from both neighbours in the same direction) > 20 %
  in luminance or > 0.004 u′v′ in 5×5 windows around lamps, on the pcond stage and the
  display, except at poplar edges (a lamp seen through a moving gap between trees really does
  blink; counted and reported);
- displayed ribbon band ≤ 2 % change per frame.

A step (occlusion, a lamp entering a pixel) is not a blink. The first version compared
frame t with its neighbours' mean and counted every step as a 50–100 % "spike".

Tests also run outside Nix: `t2/run_extinction.sh`, `t2/run_haze_metamorphic.sh`,
`t2/golden.sh check`, `python3 m1/test_*.py`, `m1/test_fog_glow.sh`.

**Deliberate baseline changes:**
1. `t2/golden.sh update`;
2. look at `t2/report.sh`;
3. commit the new `t2/golden/` with the reason.

### Test-design lessons (recorded because they were real mistakes)

- **Extinction test.** The first version kept the lamp's *angular* size constant. At 15 km that
  is a 26 m emitter whose own lit neighbourhood scatters ~σ_s·r·e^τ extra light onto its disc,
  so the test failed for a reason unrelated to extinction. A physically small lamp resolved by a
  narrow view fixed it.
- **Scene photometry.** Measure lamp **energy** (window sum minus background), not peak pixels.
  A sub-pixel lamp is spread differently by the pixel filter in different renders.
- **Far lamps.** Behind a few optical depths only a handful of camera samples reach a sub-pixel
  lamp. Per-bin values are then unbiased but skewed, so compare **sums**, not medians.
- **Near-grey mesopic colours.** Judge colour steps in u′v′ against a JND, not in hue degrees.

### Negative controls (`t2/golden_negative_control.txt`)

- mild vs the clear reference: **fails** on scene (38 % of pixels) and display (1.1 %).
- clear with scene ×1.10: **fails**.
- clear with scene ×1.03 (below tolerance): passes.
- **The display gate is coarse.** After pcond, even a different atmosphere changes only ~1 % of
  displayed pixels (the lamps). The scene gate is the sensitive one.

## Diagnostics (not gates): `t2/report.sh`

The HTML report follows the model of Blender's own render tests (`render_report.py`):
reference / current / |diff| / FLIP. A copy is in [`../t2-report/`](../t2-report/). It uses
NVlabs **FLIP**:
- **LDR-FLIP on the displayed PNG** (display-referred sRGB in [0, 1], what FLIP's LDR mode
  expects): what changed in the image the viewer actually sees after the frozen stack.
- **HDR-FLIP on the scene EXR**: FLIP runs its own bracket of exposures through its own tone
  mapper (ACES by default) and pools the differences. It answers what changed anywhere in the
  space of exposures of the HDR render, not through our pipeline.

Two "for scale" rows show deliberate changes.

**Reading the two numbers.**
- vacuum → clear: LDR-FLIP 0.037, HDR-FLIP 0.390; clear → mild: 0.025 and 0.336.
- HDR-FLIP is high because the haze changes the sky and the ground. Those changes show up at
  some exposures of the HDR bracket. After pcond, the sky sits below the display's black level
  (Ldmax / 100 = 1 cd/m²), and LDR-FLIP flags only the lamp ribbon.
- So: HDR-FLIP = "what changed substantially in the HDR render"; LDR-FLIP after pcond = "what
  changed in the viewer's final image". Both are useful; neither says which is more realistic.

**Pinned conditions.**
- **Version: FLIP 1.2** (nixpkgs; upstream is newer). This is the diagnostic baseline. After a
  FLIP upgrade, regenerate the reference report before comparing numbers. Upstream notes that
  error-map pixels can differ slightly between implementations and platforms; pooled values
  are more stable.
- **Viewing condition**, declared rather than FLIP's default (0.7 m from a 0.7 m-wide 4K
  display, ~67 ppd). **The image fills the camera's own 60° horizontal field of view.**
  - This is the only viewing in which angular sizes on screen equal those in the scene. Our
    ribbon widths are quoted in arcmin, and pcond's view header assumes the same.
  - ppd = image width / 60: 5.33 for the 320 px golden, 16 for the 960 px M2.5 clips.
  - `t2/report.sh` passes `-ppd` explicitly and prints it; `PPD=… t2/report.sh` overrides it
    for a real target display.
  - At 5.33 instead of 67 ppd, the numbers above moved by < 3 %.
- FLIP's gate mode (`--exit-on-test`) stays off until the baseline has been compared across
  machines.

## Deferred, with the tool already identified

| when | test | tool (existing) | notes |
|---|---|---|---|
| **done (M2.5)** | temporal visibility of render noise | **ColorVideoVDP** 0.5.7 (`nix develop .#video`, `m25/cvvdp.sh`), display model `m25/display_models_m25.json`: pcond's 100 cd/m², 100:1, dark room, 16 ppd | a diagnostic, not a gate; seed 0 vs 1: 9.72 JOD moving = 9.72 static → spatial noise, not temporal |
| **done (M2.5)** | a temporal golden clip | `m25-golden-clip` | 4 frames |
| M3 decision | does scintillation add a *visible* temporal difference over clip B? | ColorVideoVDP B vs B + scintillation, same seed | the JOD a change must exceed is the seed-noise level above (≈ 0.28) |
| M3 | the same with gaze on the ribbon | **FovVideoVDP** (`pyfvvdp`, CC BY-NC) | fixation point + ppd from the viewing geometry; achromatic |
| M3 decision | 2AFC "which is closer to the reference / to night perception?" | pairwise comparison with **pwcmp** (Mantiuk group, JOD scaling) or **ASAP** active sampling (gfxdisp) | needs reference photographs; split criteria (lights / darkness / colour); blind order |
| anytime | stills visibility at scene luminance, rods included | **HDR-VDP-3** (MATLAB/Octave, rod pathway) | stills only; not an appearance model |
| G3′ | glare veil magnitude | CIE 146:2002 equations vs Spencer PSF, same geometry and observer | a veil reference, not a model of the dark-adapted eye |
| G7 | scotopic weighting of real lamps | measured SPDs (LuxPy TM-30 sets, IES/PNNL calculator) | replaces the RGB→spectrum plausibility bracket |
| later | perceptual reference | real night photographs / HDR captures of a rural road with a lamp chain | the only way to test "more realistic" |

**Not used as gates:**
- LPIPS / SSIM: trained or designed for ordinary distortions of normalised RGB, not calibrated
  HDR night appearance.
- `idiff -p` (Yee perceptual): superseded here by FLIP.

**Cross-machine note.** The golden rerun is bit-identical on this machine and in the Nix sandbox.
A different CPU or Blender build may differ slightly in floating point. Blender's own practice is
per-suite thresholds, raised where platforms or devices differ (its Cycles volume tests use
0.048 / 3 %). If a legitimate platform difference ever trips them, widen
them with evidence (a report showing FLIP ≈ 0), not by guesswork.
