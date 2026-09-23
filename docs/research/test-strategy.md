# Test strategy (T2 freeze)

One command, `nix flake check` (~4 min on 4 CPU cores), must say that:
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
| `t2-golden` | baseline | 320×137, 128 spp, fixed seed. Scene in cd/m²: a pixel fails if \|d\| > 10⁻⁴ **and** > 5 %, ≤ 1 % may fail. Display PNG: Blender's render-test defaults (`--fail 0.016 --failpercent 1`) | pass (bit-identical rerun) |

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
reference / current / |diff| / FLIP. It uses NVlabs **FLIP** 1.2 (nixpkgs `flip`):
- **LDR-FLIP on the displayed image**, i.e. what the viewer sees after the frozen stack;
- **HDR-FLIP on the scene radiance.**

Two "for scale" rows show deliberate changes. A copy is in [`../t2-report/`](../t2-report/).

**Why the two FLIPs disagree, and which one matters.**
- vacuum → clear: LDR-FLIP (display) 0.038 vs HDR-FLIP (scene) 0.383.
- HDR-FLIP tone-maps the scene itself (ACES) over a bracket of exposures. It sees the scene the
  way a bracketing camera does, so it flags the whole hazy sky.
- LDR-FLIP on pcond's output flags only the lamp ribbon, which is what an observer of our
  display would notice.
- **For "would a viewer notice?", use LDR-FLIP on the pipeline output.** HDR-FLIP diagnoses the
  render itself.
- FLIP has a built-in gate mode (`--exit-on-test`, mean/median/max threshold). Kept off until
  the baseline has been compared across machines.

## Deferred, with the tool already identified

| when | test | tool (existing) | notes |
|---|---|---|---|
| M2.5 video | temporal visibility of changes, e.g. does shimmer read as blinking? | **ColorVideoVDP** (`cvvdp`, MIT, PyTorch, CPU works) | compare *display-referred* clips with a custom display model (peak 100 cd/m², black level, `E_ambient` 0); its 0.005 cd/m² luminance floor does not matter for display output |
| M2.5 video | the same with gaze on the ribbon | **FovVideoVDP** (`pyfvvdp`, CC BY-NC) | fixation point + ppd from the viewing geometry; achromatic |
| M2.5 video | a temporal golden clip | idiff per frame + cvvdp summary | like `t2-golden`, ~2 s clip |
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
A different CPU or Blender build may differ slightly in floating point, and the thresholds follow
Blender's own render-test practice. If a legitimate platform difference ever trips them, widen
them with evidence (a report showing FLIP ≈ 0), not by guesswork.
