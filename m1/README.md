# M1: a Blender-rendered, calibrated night scene through existing tools only

    nix develop
    blender -b --factory-startup --python m1/calibrate.py -- m1/out/calib   # radiometric check renders
    python3 m1/check_calibration.py m1/out/calib                            # -> m1/calibration_result.txt
    blender -b --factory-startup --python m1/scene.py -- m1/out/scene.exr 512
    m1/run_m1.sh m1/out/scene.exr 60 m1/out/results

    # Fog Glow check on a single pixel
    blender -b --factory-startup --python m1/fog_glow.py -- m1/out/point.exr m1/out/point_glare.exr 60
    python3 m1/check_fog_glow.py m1/out/point.exr m1/out/point_glare.exr 60  # -> m1/fog_glow_check.txt

No vision algorithm, tone mapper or glare kernel was written. What we wrote:

| file | what | kind |
|---|---|---|
| `calibrate.py`, `check_calibration.py` | closed-form radiometry checks of Cycles | test |
| `scene.py` | minimal scene (ground, poplars, lamps) with photometric light authoring | scene data |
| `fog_glow.py` | drives Blender's stock Glare node headless, with settings derived from its source | configuration |
| `check_fog_glow.py` | compares Fog Glow output against the published Spencer '95 formula | test |
| `pcond_keep_hue.sh` | Radiance `pcond` + `tabfunc` + `pcomb` + `pcond -l`, i.e. Radiance tools only | glue |
| `run_m1.sh` | conversions, OCIO display views, per-pixel select, contact sheets | glue |

## 1. Calibration: Blender linear → cd/m²

Result: [`calibration_result.txt`](calibration_result.txt). Cycles 5.2.2 CPU is radiometrically
exact in its own units. Every case below matches the closed-form value to within 0.2 %:

- **Sun.** Strength E [W/m²] on a Lambertian surface gives radiance ρE/π.
- **Point light.** Power P gives intensity **P/(4π) W/sr**.
- **World background.** Strength B (with Color = 1) gives radiance B. The node's *default colour
  is 0.05 grey*, which silently divides the sky by 20.
- **Emission shader.** Strength S gives radiance S.
- **Sub-pixel emissive sphere at 500 m.** Σ L·Ω over the pixels = I/d² (energy is conserved
  through sub-pixel sampling). This is what makes the distant lamp chain trustworthy.
- ⚠ **Point lights are not camera-visible.** Visible lamps must be emissive meshes.

Since Cycles has no photometric units, "linear → cd/m²" comes down to **one declared constant**:

> **K = 179 lm per Blender-watt** (Radiance's `WHTEFFICACY`). All lights are authored
> photometrically and divided by K: sky 4e-4 cd/m², lamp intensity 800 cd, and so on.
> The Cycles EXR is then *directly* a Radiance picture, and **cd/m² = 179 · Y**.

K is a convention. It cancels as long as authoring and interpretation use the same value. It is
**not** the lamp's physical luminous efficacy.

## 2. Fog Glow: what Blender 5.2.2 really does

These findings come from reading `node_composite_glare.cc` and `fog_glow_kernel.cc`.

- **Kernel.** Spencer et al. 1995, Eq. 5 photopic:
  `0.384·f0 + 0.478·f1 + 0.138·f2`, with θ in degrees. It is normalised to sum 1 and applied as
  an FFT convolution with zero padding.
- **FOV.** `FOV_k = lerp(180°, 10°, Size^(1/3))`. This is **not** the camera. The kernel then
  uses **deg/px = FOV_k / max(width, height)**.
  - So **Size = ((180 − FOV)/170)³** makes the kernel match the camera's FOV along the larger
    image dimension. For a 60° camera that is Size = 0.3517. Cameras narrower than 10° cannot be
    represented.
- **Threshold = 0** turns the adaptive smooth clamp into exactly max(0, x), so every pixel
  scatters, as it does in the eye.
- **Quality High.** Medium or Low downsample the highlights 2× or 4× first.
- **Use the `Glare` output socket.** The `Image` socket is `input + glare`, which double-counts
  the unscattered core. The `Glare` socket alone is PSF ⊛ image.

**Single-pixel test** ([`fog_glow_check.txt`](fog_glow_check.txt)):
- The profile matches Spencer Eq. 5 within **±1 % from 0.09° to 3°**, and within −3 % at 10°.
  At 20° (near the frame edge) it is +24 %.
- Energy out/in = 0.984; the rest leaves the frame.
- The centre pixel keeps 53 % of a point source (0.031°/px).

**Limits:**
- Photopic PSF only. Spencer also gives a scotopic/large-pupil variant, which Blender does not
  implement.
- No age or pupil parameters.

## 3. Warm lamp colour without a custom tone mapper

**Where the colour dies.** This comes from reading the Radiance source, not guessing.

- Sub-pixel lamps lie above the top of pcond's 1°-foveal histogram. `mapscan()` pushes them
  10³–10⁴× above display max but keeps their RGB ratios.
- They turn white only in `matscan()` → `clipgamut()`, whose "brightness above max" branch returns
  pure white.
- `matscan()` runs whenever the picture has a `PRIMARIES=` header, because `inprims != outprims`
  compares **pointers**.

**Reuse route** (`pcond_keep_hue.sh`, Radiance tools only):
1. Run `pcond -s -c -x map` on an input **without** `PRIMARIES`, so the colour survives.
2. With `tabfunc` + `pcomb`, rescale **only the pixels pcond pushed above display max** to the
   display luminance that pcond's own `-x` curve assigns them. On the synthetic test that is
   exactly 383 pixels; all others are bit-identical to pcond.
3. Choose one way to bring the out-of-gamut pixels into gamut:
   - `pcond -l -e 1` with a PRIMARIES header runs Radiance's own `clipgamut()`. This keeps hue
     and luminance, but desaturates toward grey.
   - **Khronos PBR Neutral** (the view in Blender's OCIO config), applied **only** to pixels
     outside the display gamut.

Measured on the synthetic test (input hue 31°):

| path | lamp hue | lamp saturation | darkness (field / sky) |
|---|---|---|---|
| Radiance `clipgamut` | 29–30° | 0.16 (pale) | unchanged |
| PBR Neutral, out-of-gamut pixels only | 31–32° | 0.56 | unchanged |
| PBR Neutral on the whole image | 31–32° | 0.56 | **crushed 50×** (its toe subtracts up to 0.04) |
| ACES 2.0 SDR on the whole image | 32–33° | 0.35 | **crushed** (it applies a second tone curve) |
| per-channel clip (Standard view) | 50° (turns yellow) | 0.45 | unchanged |

So ACES 2 and PBR Neutral are both hue-preserving, but neither can follow pcond across the whole
frame. PBR Neutral restricted to the out-of-gamut pixels keeps the lamps warm and leaves pcond's
darkness untouched.

## 4. Results on the scene (1920×820, 512 spp, 7 min on 4 CPU cores)

Images are in [`../docs/research/m1-results/`](../docs/research/m1-results/).

| output | what |
|---|---|
| `1_raw_photometric_100nit` | the scene's own luminance on a 100-nit display: almost everything is black |
| `2_camera_autoexposure_agx` | the usual render: auto exposure + AgX. Grey sky, green field, "dusk" |
| `3_pcond_sc` | dark silhouettes, salient ribbon, **white** lamps |
| `4_pcond_sc_keephue_pbrneutral_oog` | the same darkness, **warm** lamps. **Recommended M1 path** |
| `4_pcond_sc_keephue_radiance_clipgamut` | warm but pale lamps |
| `5_fogglow_…` | calibrated eye PSF before pcond: every lamp becomes a white disc about 0.3–0.5° across |

**Why Fog Glow is off by default.** The PSF itself is right: it matches Spencer to within 1 %.
The problem is how pcond's histogram operator hands out display range. Lamp and halo pixels are
rare, so everything from about 0.2 cd/m² (halo) to about 300 cd/m² (core) lands on display max,
and the halo becomes as bright as its source. Before turning it on, check the PSF magnitude
against CIE 146 for a dark-adapted eye.
