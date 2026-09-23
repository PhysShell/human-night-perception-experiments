# M1 / M1.1: a Blender-rendered, calibrated night scene through existing tools only

    nix develop
    nix flake check                                              # regression tests (pcond mapping + continuity, Fog Glow PSF)
    blender -b --factory-startup --python m1/calibrate.py -- m1/out/calib && python3 m1/check_calibration.py
    blender -b --factory-startup --python m1/scene.py -- m1/out/scene.exr 512    # ~7 min on 4 CPU cores
    m1/run_m1.sh m1/out/scene.exr 60 m1/out/results              # all display variants + contact sheets
    m1/run_colorimetry.sh                                        # M1.1 colorimetry gate (needs m0 data)
    uv venv --system-site-packages .venv && . .venv/bin/activate \
      && uv pip install --no-deps colour-science==0.4.7 luxpy==1.12.5 && python m1/scotopic_oracle.py

No vision algorithm, tone mapper, glare kernel or addon was written. Everything below is
configuration of existing tools, tests, or glue:

| file | what | kind |
|---|---|---|
| `calibrate.py`, `check_calibration.py` | closed-form radiometry checks of Cycles | test |
| `scene.py` | minimal scene (ground, poplars, lamps) with photometric light authoring | scene data |
| `pcond_colorimetric.sh` | Rec.709 → Radiance via `ra_xyze`, `pcond -s -c`, LC composition of two pcond outputs | glue |
| `fog_glow.py` | drives Blender's stock Glare node headless (version-pinned adapter) | configuration |
| `test_pcond_mapping.py`, `test_continuity_sweep.py`, `test_fog_glow.sh` (+ `check_fog_glow.py`) | regression tests, run by `nix flake check` | test |
| `check_colorimetry.py`, `run_colorimetry.sh`, `scotopic_oracle.py`, `gamut_compare.py` | M1.1 comparisons | test |
| `run_m1.sh` | conversions, OCIO display views, contact sheets | glue |
| `pcond_keep_hue.sh` | **deprecated** M1 route (Rec.709 data relabelled as Radiance RGB), kept as the "old" baseline | — |

Result files committed next to the scripts: `calibration_result.txt`, `fog_glow_check.txt`,
`pcond_mapping_test.txt`, `colorimetry_result.txt`, `scotopic_oracle_result.txt`,
`gamut_result.txt`, `continuity_sweep_result.txt`. The pcond `-x` bug report and its minimal
repro are in [`../docs/upstream/`](../docs/upstream/).

## 1. Calibration: Blender linear → cd/m²

Cycles 5.2.2 CPU is radiometrically exact in its own units (`calibration_result.txt`). Every case
matches the closed-form value to within 0.2 %:

- **Sun.** Strength E on a Lambertian surface gives radiance ρE/π.
- **Point light.** Power P gives intensity **P/(4π) W/sr**.
- **World background.** Strength B (with Color = 1) gives radiance B. The node's default
  colour is 0.05 grey, which silently divides the sky by 20.
- **Emission shader.** Strength S gives radiance S.
- **Sub-pixel emissive sphere.** Σ L·Ω over the pixels = I/d², so energy is conserved through
  sub-pixel sampling.
- ⚠ **Point lights are not camera-visible.** Visible lamps must be emissive meshes.

**Convention.**

> We adopt Radiance's 179 lm/W equal-energy-white convention as the RGB radiometric →
> photometric calibration.

- Lights are authored photometrically (cd, cd/m²) and divided by 179.
- Luminance = 179 · Y, where Y = 0.2126 R + 0.7152 G + 0.0722 B of Blender's scene-linear
  Rec.709.
- 179 lm/W is **not** the luminous efficacy of any real source. Real sodium, LED or moonlight
  have different spectral efficacies, and Cycles has no spectra.
- The RGB **values** match Radiance's radiometric scale. The RGB **space** does not: Radiance's
  standard primaries and equal-energy white are not Rec.709/D65. An M1 claim that "the Cycles
  EXR is directly a Radiance picture" was wrong for colour; see section 3.

## 2. Fog Glow: what Blender 5.2.2 does, and a pinned adapter

These findings come from reading `node_composite_glare.cc` and `fog_glow_kernel.cc` in the
Blender 5.2.2 source.

- **Kernel.** Spencer et al. 1995, Eq. 5 photopic: `0.384·f0 + 0.478·f1 + 0.138·f2`, θ in
  degrees. It is normalised to sum 1 and applied as an FFT convolution with zero padding.
- **FOV.** `FOV_k = lerp(180°, 10°, Size^(1/3))`, which does **not** depend on the camera. The
  kernel uses deg/px = FOV_k / max(w, h). So Size = ((180 − FOV)/170)³ matches the camera FOV
  along the larger image dimension (60° → 0.3517; FOV must be ≥ 10°).
- **This is a version-specific adapter, not a public Blender contract.**
  - `fog_glow.py` refuses to run on anything other than Blender 5.2.2 unless
    `FOG_GLOW_ALLOW_UNTESTED=1` is set.
  - `test_fog_glow.sh` is the gate for any upgrade: a single-pixel source, and the profile must
    match Spencer Eq. 5 within ±2 % from 0.09° to 3° and ±5 % at 10°, with energy ≥ 0.97. It is
    part of `nix flake check`.
  - Negative control: rendering with FOV 90° and checking at 60° fails at 0.3°, 3° and 10°
    (exit 1).
- **Node settings.**
  - Threshold 0 makes the adaptive smooth clamp exactly max(0, x).
  - Quality High avoids downsampling.
  - Use the **Glare** socket. The Image socket is input + glare, which double-counts the core.
- **Result:** within ±1 % over 0.09°–3°, −3 % at 10°, energy 0.984 (`fog_glow_check.txt`).
- **Limits.** Photopic PSF only; no age or pupil parameters.
- **Status.** Fog Glow stays **off** in the artistic pipeline (see section 5).

## 3. Colorimetry gate (M1.1)

**The M1 bug.** M1 gave pcond Rec.709 data *without* a PRIMARIES header, so pcond treated it as
Radiance-standard RGB. This avoided pcond's white clipping, but it lied about the colour space.
Consequences:
- luminance was computed with the wrong weights;
- `-c` applied its scotopic RGB weights to the wrong primaries (the red probe came out 14 %
  brighter than on the honest path);
- a separate bug: with no primaries conversion, pcond's grey output overshot display max by
  1.48×.

**Now: all colour conversion is done by Radiance's own `ra_xyze`**, starting from a truthful
`PRIMARIES=` Rec.709/D65 header. `ra_xyze` applies von Kries adaptation to Radiance's
equal-energy white, verified in `spec_rgb.c`.

| path | route | behaviour |
|---|---|---|
| **A** | Rec.709 → XYZE (`ra_xyze`) → `pcond -s -c -p Rec.709` | pcond as shipped; scotopic estimate from XYZ (`cielum`); over-bright pixels clipped to white by `clipgamut()` |
| **B** | Rec.709 → Radiance-standard RGB (`ra_xyze -r`) → pcond | this is pcond's *default* space, so the redundant PRIMARIES line is moved to the header history (`pcomb` pass-through, after verifying it is the standard set). pcond then skips `matscan()` and returns its **own unclipped** result; over-bright pixels are scaled to luminance 1 (pcond's clip point) with their chromaticity kept |
| AB (rejected) | A where pcond did not clip, B where it did | per-pixel switch: the temporal sweep shows a +36 % luminance pop for red, +5 % for sodium at the switch frame |
| **LC** (used) | luminance of A, chromaticity of B, every pixel | pcond's own luminance (as shipped, honest XYZE) with pcond's own unclipped colour; no switch |

**LC is a project-specific composition of two outputs of an existing operator.** It is not a
validated model of human vision. What is validated is narrower:
- its luminance is pcond's on every pixel;
- its colour equals pcond's unclipped result;
- it adds no temporal seams (section 3c).

**Checks against pcond itself** (`colorimetry_result.txt`, `pcond_mapping_test.txt`):
- AB equals pcond's own XYZE output on every pixel pcond did not clip: median and p99 relative
  error **0.0000** on
  - the synthetic image (1.44 M px),
  - McKeesPub (2.0 M px),
  - the M1 scene (0.67 M px).
- **LC's luminance equals pcond's on every pixel**: median relative error 0.0000–0.0007, p99
  ≤ 0.5 %, on the same three images. The difference is one extra RGBE write.
- On a coloured log ramp, in both pcond modes, the clipped photopic pixels keep the input
  chromaticity within 2 RGBE quantisation steps (3 for LC), and luminance never exceeds 1.

**A vs B, i.e. Radiance's two scotopic approximations.**
- On the whole image they agree: mean |A−B| is 0.0002 (synthetic) and 0.0026 (McKeesPub).
- They differ on saturated colours in the dark. For the red probe at 0.03 cd/m², A gives 0.057
  and B gives 0.080.
- An RGB renderer cannot settle this by itself, so `scotopic_oracle.py` brackets it with
  existing code: colour-science 0.4.7, five published RGB→spectrum recovery methods × CIE 1951
  V′(λ) / CIE 1924 V(λ).

Relative scotopic efficiency, normalised to white:

| | red probe | blue probe | sodium | warm LED |
|---|---|---|---|---|
| spectral recoveries (Jakob'19, Otsu'18, Meng'15, Mallett'19, Smits'99) | 0.13–0.27 | 2.0–4.9 | 0.48–0.60 | 0.75–0.81 |
| Radiance A (`cielum`) | **0.23** | 2.35 | **0.47** | **0.74** |
| Radiance B (`rgblum`) | 0.34 ✗ | 2.49 | 0.64 ✗ | 0.83 ✗ |

**A lies inside or at the edge of the recovered range. B lies above it for reds and warm
colours, i.e. it weakens the Purkinje shift.** Hence LC takes its luminance from A.

This is a **plausibility check, not an oracle**:
- RGB → spectrum is fundamentally ambiguous (metamers).
- The recovery methods return a smooth, colorimetrically consistent *candidate*, not the
  physical spectrum.

The clean check (gate G7, deliberately not done now) would use **real lamp SPDs** instead of
recovered ones. Options:
- LuxPy's IES TM-30 source sets;
- measured HPS / LPS / LED spectra through the IES/PNNL spectral calculator.

Low-pressure sodium (589 nm) is the textbook case where photopic and scotopic/mesopic ratings
diverge.

## 3b. What pcond actually does on these night scenes

**Linear mode, not histogram compression.** pcond `-s` falls back to linear mapping when its
1°-foveal histogram already fits the display (`mkbrmap()`: "no compression needed").
- On all three test images pcond is in this mode: a CSF-chosen **linear exposure**, plus `-c`,
  plus a clip.
- Sub-pixel lamps barely affect 1° averages.
- In the M1 scene the display saturates at L ≈ **0.13 cd/m²**.

**A pcond `-x` bug.** In linear mode (`-l`, `-e`, or this fallback), the `-x` table overstates
display luminance by exactly **179/Ldmax** (`putmapping()` reuses `scalef`, which already
contains 179/Ldmax). Measured 0.556 against the expected 0.559. In histogram mode the table is
correct (0.997). The AB path does not use `-x` at all. The test guards our reading of it and
will flag it if upstream changes.

## 3c. Temporal continuity sweep (`test_continuity_sweep.py`, `continuity_sweep_result.txt`)

**Setup.**
- A 4×4-pixel source (sodium, warm LED, red, blue) sits in the dark sky of the M1 scene.
- It ramps 0.03 → 30 cd/m² over 61 frames (+12 %/frame), through pcond's clip point
  (0.17–0.3 cd/m²) and on into the photopic range.
- pcond's exposure is identical in all frames.

**Reference: pcond as shipped (A).** Only artefacts *added* by our composition count. Its own
hard knee at display max does not.

**Thresholds.**
- Colour seam: a Δu′v′ step more than 3× its neighbours and above 0.002 (half a JND).
- Luminance pop: a step more than 5 % away from pcond's step.
- Added fall: more than 3 RGBE steps below pcond's step.
- Hue is reported as a u′v′ arc. For these near-grey mesopic colours, 1° of hue is ~0.0007 u′v′,
  i.e. RGBE quantisation noise.

| stage | sodium | warm LED | red | blue |
|---|---|---|---|---|
| **LC (pcond stage)** | ok | ok | ok | ok |
| AB (pcond stage) | Y pop at switch | ok | **+36 % Y pop**, falls | ok |
| display: PBR Neutral on out-of-gamut pixels | −12…16 % Y drop at gamut exit, falls later | Y drop at exit | pops + falls | drop + falls |
| display: Radiance `clipgamut` | ok (synthetic sky); one ~1-JND colour step at onset (scene) | ok | pops/falls later | pops/falls later |

The sweep runs on a synthetic sky in `nix flake check` (pcond-continuity). Only the pcond stage
gates the check; the display stages are reported.

## 4. Gamut: bringing the warm lamp pixels onto the display

Input: the LC output (the table below was measured on AB, which is identical on these pixels). Luminance is ≤ 1 everywhere; the lamp pixels have a channel above 1, and
**all their components are ≥ 0.14** (inside the Rec.709 triangle). `gamut_result.txt`, M1
scene, 1096 lamp pixels, input hue 31°:

| method (all existing) | in-gamut pixels changed (max) | lamp hue error | lamp saturation (input 0.71) | lamp Y |
|---|---|---|---|---|
| per-channel clip (Standard view) | 0 | 22.7° | 0.55 | 0.87 |
| **ACES 1.3 Reference Gamut Compression** (OCIO builtin LMT) | 0 | 22.7° (= clip) | 0.55 | 0.87 |
| **ACES 2.0 SDR output, inverse → forward** (OCIO builtins) | 0 | 22.7° (= clip) | 0.55 | 0.87 |
| Radiance `clipgamut` | 0 | 0.8° | 0.20 | 0.90 |
| **Khronos PBR Neutral, lamp pixels only** | 0 | **0.2°** | **0.67** | 0.63 |
| PBR Neutral on the whole image | 0.038 (its toe) | 0.2° | 0.67 | 0.63 |
| ACES 2.0 view on the whole image | 0.040 (second tone curve) | 1.8° | 0.49 | 0.46 |

Why the standalone ACES tools do nothing here:
- **RGC** compresses chroma *outside* the working gamut (negative components). Our lamps are
  inside the triangle and only exceed 1 in magnitude.
- **The ACES 2.0 inverse output transform** clamps to the display cube by design, so the
  over-range information is gone before the forward pass. ACES 2's JMh gamut compression only
  exists inside the full scene→display transform, and that would re-tone-map pcond's result.

**Khronos PBR Neutral.** Khronos states it does no gamut mapping and assumes Rec.709 input. That
precondition holds for our lamp pixels (all components ≥ 0, inside the triangle). What it does
to them is its designed function: hue-preserving **highlight compression** of values above 1.
The non-standard part is restricting it to the pixels above display white, because its toe would
otherwise shift pcond's darkness.

**Two existing options, each with a measured defect. Neither passes the temporal sweep for all
colours:**
- **stills (M2):** PBR Neutral on the out-of-gamut pixels. Best saturation (0.67), but a 12–16 %
  luminance drop at the moment a pixel leaves gamut, so **not for motion**.
- **motion (M3):** Radiance `clipgamut`. Luminance-continuous for sodium and warm LEDs, which are
  our lamp colours; paler (0.20); not monotonic for saturated red and blue.

A continuous, hue-preserving highlight compressor that can be restricted to part of the image
was not found among the existing tools tested. Writing one is a gate only if M3 motion shows the
`clipgamut` compromise is visible.

## 5. Results on the scene (1920×820, 512 spp)

Images are in [`../docs/research/m1-results/`](../docs/research/m1-results/).

| output | what |
|---|---|
| `1_raw_photometric_100nit` | the scene's own luminance on a 100-nit display: almost black |
| `2_camera_autoexposure_agx` | auto exposure + AgX: grey sky, green field, "dusk" |
| `3_pcond_sc` | pcond as shipped (honest XYZE): dark silhouettes, **white** lamps |
| `4_pcond_sc_LC_pbrneutral_oog` | the same pixels, **warm sodium lamps**, whiter 4000 K LEDs. **Recommended for stills** |
| `5_fogglow_…` | calibrated eye PSF before pcond: every lamp becomes a disc about 0.3–0.5° across |

**Why the discs** (corrected from M1). pcond is in linear mode here, and the display clips at
about 0.13 cd/m².
- The Spencer halo stays above that out to ~0.2°, so it saturates at the same display value as
  the lamp core.
- This is the display's 100:1 range at a dark-adapted linear exposure, not an error in the PSF.
  `-d 1000` only moves Ldmin, which is why it barely helped.
- **Open question for the next gate:** does the Spencer PSF predict the same veiling luminance
  as CIE 146:2002 for this geometry and a chosen observer (age, pigmentation)? For that
  comparison, CIE 146 is an independent glare reference for the *veil*, not a model of the
  dark-adapted eye.

## 6. FROZEN perceptual stack (end of M1.1)

    Cycles EXR (scene-linear Rec.709; 179 lm/W equal-energy-white convention)
      -> m1/pcond_colorimetric.sh LC   (ra_xyze; pcond -s -c; luminance A x chromaticity B)
      -> display: PBR Neutral on out-of-gamut pixels (stills) | Radiance clipgamut (motion)
      Fog Glow: OFF (adapter + test kept; G3' deferred)

It is guarded by `nix flake check` (pcond-mapping, pcond-continuity, fog-glow-psf), pinned to
Blender 5.2.2 and Radiance bcffc2b, and CPU-only. Changes to this stack need a failing test or a
visible defect in a real scene, not curiosity.
