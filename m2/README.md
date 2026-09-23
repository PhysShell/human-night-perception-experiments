# M2: 14 km of air between the lamps and the eye (stock Cycles only)

**Scope.** Atmospheric extinction and haze around the distant lights, added to the M1 scene. The
frozen M1.1 perceptual stack is not modified. Excluded: Fog Glow, turbulence and scintillation,
weather systems and art assets.

    nix develop
    blender -b --factory-startup --python m2/calibrate_volume.py -- m2/out/vcal && python3 m2/check_volume.py
    m2/render_all.sh          # vacuum / clear / mild / moderate, 960x410, 512 spp, ~14 min each on 4 cores
    m2/run_m2.sh              # unchanged M1.1 stack (LC + PBR Neutral out-of-gamut, stills) + comparison

Results are in `compare_result.txt` and `sky_noise_result.txt`; images in
[`../docs/research/m2-results/`](../docs/research/m2-results/).

## 1. What Cycles offers, and what it does

- **Volume Coefficients node (Blender 5.x).**
  - Absorption, scattering and emission coefficients per RGB channel, in 1/m.
  - Phase functions: Henyey–Greenstein, Fournier–Forand, Draine, Rayleigh, Mie.
  - Mie here is Jendersie & d'Eon's approximation for 0–50 µm **water droplets**, i.e. mist and
    fog, not sub-micron haze.
- **Calibration** (`calibrate_volume.py`, a 1 m emitter at 1 km):
  - absorption follows Beer–Lambert **per channel to 0.1 %**, e.g. σ = (0.5, 1, 2)·10⁻³ →
    T = (0.6068, 0.3682, 0.1356) against (0.6065, 0.3679, 0.1353);
  - with scattering (σ_s = 10⁻³, HG g = 0.7), the direct term matches (0.370 against 0.368), and
    a forward-scattered aureole carries 2.5 % of the source within 2°;
  - a spot light with a 180° cone has intensity P/(4π), like a point light (`m1/calibrate.py`,
    c2b).

## 2. The three atmospheres (`atmospheres.py`)

**Parameters.** Textbook optics turned into coefficients, not a new model:
- a homogeneous boundary layer from the ground to 1 km;
- σ₅₅₀ = 3.912/V (Koschmieder);
- Rayleigh σ₅₅₀ = 1.16·10⁻⁵ m⁻¹ with λ⁻⁴ and a Rayleigh phase;
- continental aerosol for the rest: Ångström α = 1.3, single-scattering albedo 0.9, HG g = 0.7;
- RGB taken at 610/550/465 nm.

These are typical values, not site data for East Kazakhstan.

| case | V | extinction R/G/B [1/m] | T at 14 km (R/G/B) |
|---|---|---|---|
| clear dry night | 40 km | 0.83 / 0.98 / 1.30 ·10⁻⁴ | 0.31 / 0.25 / 0.16 |
| mild haze | 15 km | 2.25 / 2.61 / 3.33 ·10⁻⁴ | 0.043 / 0.026 / 0.009 |
| moderately hazy | 7 km | 4.86 / 5.59 / 7.03 ·10⁻⁴ | 0.001 / 0 / 0 |

## 3. Scene changes needed once there is a medium

- **No baked extinction.** M1 folded V = 25 km into the lamp intensities; the medium now does it.
- **Split lamps.** Lamps in M2 are split into two parts with the same energy. This is a
  rendering technique; it changes no physics.
  - The eye sees the M1 emissive sphere (800 cd towards the observer), visible to **camera rays
    only**.
  - The lamp lights the ground and haze through a **spot light, 180° cone pointing down**. That
    is a full cut-off luminaire, with no light above the horizontal.
  - Two failures before this:
    - With ~500 mesh emitters inside a scattering volume, the haze glow was Monte Carlo noise.
      At 128 spp, the sky's p99 was 3.9× its median; with split lamps it is **1.24×**.
    - A "lower-hemisphere" emitting sphere still emits upward near its equator, which produced
      an **artificial light dome**.
- **vacuum case** = the same lamps, no medium, no baked extinction. It is the reference for
  transmittance. The M1 scene itself (`none`) is unchanged.
- **Path guiding** (Open PGL) cut the sky-noise tail by only 3–5 % for +21 % time, so it is off.

## 4. Results, through the unchanged M1.1 stack (`compare_result.txt`)

**Lamp transmittance** is measured on background-subtracted lamp **energy** per 20-column bin,
not on peak pixels. A lamp covers ~2 % of a pixel, and the pixel filter shares it differently
between renders.

| case | T 2–4 km (Beer–Lambert @3 km) | T 9–14 km (@11.5 km) | fitted σ vs input |
|---|---|---|---|
| clear | 0.757 (0.746) | 0.323 (0.325) | 8.9·10⁻⁵ vs 9.8·10⁻⁵ |
| mild | 0.477 (0.457) | 0.025 (0.050) | 2.3·10⁻⁴ vs 2.6·10⁻⁴ (fit ≤ 6 km) |
| moderate | 0.204 (0.187) | 0.0004 (0.0016) | n/a (measurable only < 3 km) |

- Near values are a few percent above Beer–Lambert: that is forward-scattered light landing in
  the measurement window.
- Beyond about τ = 2, only a handful of camera samples per pixel reach a sub-pixel lamp at
  512 spp. The values stay unbiased as sums but are very noisy, which is why the fits are
  restricted.

**Lamp colour** (u′v′ hue / chroma, scene → after pcond):
- The distant lamps redden, because blue has the highest extinction. Far lamps go from hue 47.1°
  (vacuum) to 43.4° (clear) and 37.3° (mild).
- After pcond, **far** lamps lose chroma as they dim into the mesopic range. That is `-c`,
  pcond's mesopic colour loss: 0.081 → 0.055 → 0.018, and grey in moderate.

**Ribbon** (vertical extent of the glow on the display):
- The ribbon **widens from ~6′ (vacuum) to 13–15′ near** in haze, from haze lit from below along
  the road.
- The lamps stay tiny points on it (`m2_ribbon_crop.jpg`).
- In mild and moderate haze the far end of the ribbon fades out.

**Silhouettes**, 512 spp, single scattering: poplar contrast on the display falls from 1.00 to
0.83 / 0.67 / 0.50, and the sky darkens to 0.75× / 0.47× / 0.23× of the authored value.

## 5. Open issue: single vs multiple scattering (not fixed; next decision)

**Cycles defaults to `volume_bounces = 0`, i.e. single scattering.**
- In a hazy boundary layer lit by the sky, that loses the multiply scattered skylight. The sky
  near the horizon darkens, and nearby trees drown in their own airlight with nothing behind them.
- Test: moderate, 64 spp (`m2_moderate_single_vs_multiple_scattering_64spp.jpg`).
  - **8 bounces:** sky 9·10⁻⁵ → 2.3·10⁻⁴ cd/m², poplar contrast 0.16 → **0.61** in scene
    luminance, which is much more plausible.
  - But multiply scattered **lamp** light arrives as fireflies: sky p99.9 is 100× its median.
- **Options, not implemented:**
  - many more samples (hours per frame on CPU; a GPU is the natural place);
  - Cycles' indirect clamp (biased, loses energy);
  - a thin or clear atmosphere where single scattering is adequate (clear: sky 0.75×, poplars 0.83).

**Recommended for the art scene** unless this is resolved: **clear to mild** haze with single
scattering. Its extinction, reddening and ribbon softening are all verified above.

## 6. What M2 shows about the original impression

- Tiny physical sources, long paths through a calibrated medium and pcond's mesopic response
  together already give:
  - a **warm luminous ribbon** made of points;
  - softened from below by lit haze;
  - reddening and fading with distance;
  - over dark silhouettes.
- Nothing in it is a post-process bloom.
- **Still missing is temporal "breathing".** Whether it needs scintillation (M3, HCIPy/AOtools
  time series, far lamps only) should be decided by watching a slow camera move over the clear
  or mild scene first.
