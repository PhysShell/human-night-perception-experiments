# M1 / M1.1: a Blender-rendered, calibrated night scene through existing tools only

    nix develop
    nix flake check                                              # regression tests (pcond mapping, Fog Glow PSF)
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
| `pcond_colorimetric.sh` | Rec.709 → Radiance via `ra_xyze`, `pcond -s -c`, per-pixel select of pcond outputs | glue |
| `fog_glow.py` | drives Blender's stock Glare node headless (version-pinned adapter) | configuration |
| `test_pcond_mapping.py`, `test_fog_glow.sh` (+ `check_fog_glow.py`) | regression tests, run by `nix flake check` | test |
| `check_colorimetry.py`, `run_colorimetry.sh`, `scotopic_oracle.py`, `gamut_compare.py` | M1.1 comparisons | test |
| `run_m1.sh` | conversions, OCIO display views, contact sheets | glue |
| `pcond_keep_hue.sh` | **deprecated** M1 route (Rec.709 data relabelled as Radiance RGB), kept as the "old" baseline | — |

Result files committed next to the scripts: `calibration_result.txt`, `fog_glow_check.txt`,
`pcond_mapping_test.txt`, `colorimetry_result.txt`, `scotopic_oracle_result.txt`,
`gamut_result.txt`.

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
| **AB** (used) | A where pcond did not clip, B where it did | pcond's XYZ scotopic behaviour for everything visible, colour kept only on clipped lamp pixels |

**Oracle checks** (`colorimetry_result.txt`, `pcond_mapping_test.txt`):
- AB equals pcond's own XYZE output on every pixel pcond did not clip: median and p99 relative
  error **0.0000** on
  - the synthetic image (1.44 M px),
  - McKeesPub (2.0 M px),
  - the M1 scene (0.67 M px).
- On a coloured log ramp, both pcond modes, the clipped photopic pixels keep the input
  chromaticity within 2 RGBE quantisation steps, and luminance never exceeds 1.

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

**A lies inside or at the edge of the spectral range. B overestimates reds and warm colours,
which weakens the Purkinje shift.** Hence AB. Spectral truth remains gate G7 (Mitsuba/PBRT),
not needed now.

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

## 4. Gamut: bringing the warm lamp pixels onto the display

Input: the AB output. Luminance is ≤ 1 everywhere; the lamp pixels have a channel above 1, and
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

**Kept with this explicit caveat.** Radiance `clipgamut` is the fallback if the restriction is
ever unacceptable: same hue, paler lamps.

## 5. Results on the scene (1920×820, 512 spp)

Images are in [`../docs/research/m1-results/`](../docs/research/m1-results/).

| output | what |
|---|---|
| `1_raw_photometric_100nit` | the scene's own luminance on a 100-nit display: almost black |
| `2_camera_autoexposure_agx` | auto exposure + AgX: grey sky, green field, "dusk" |
| `3_pcond_sc` | pcond as shipped (honest XYZE): dark silhouettes, **white** lamps |
| `4_pcond_sc_AB_pbrneutral_oog` | the same pixels, **warm sodium lamps**, whiter 4000 K LEDs. **Recommended** |
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
