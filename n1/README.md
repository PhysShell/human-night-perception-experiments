# N1: a complete night scene (hero shot) through the frozen D1 baseline

Pre-registered: `PREREG.md` (`5e0dffe`) plus addendum 1 (`9912b59`). D1 is untouched (`d1/verify_manifest.sh` OK
before the run).

    B=/nix/store/…-blender-5.2.2/bin/blender   # flake nixpkgs pin
    $B -b --factory-startup --python n1/scene/scene.py -- probes a n1/work 4096
    $B -b --factory-startup --python n1/scene/scene.py -- hero a n1/work 512 1.0
    tracks/temporal-glare-2009/py.sh n1/probes.py a        # -> probes.json, renders/raw/n1_1a_preview.png

- Illuminance probes: a 0.6 m albedo-1 Lambertian patch with a tiny orthographic camera above it (E = π·L).
- Luminance probes: 7 × 7 px medians in the hero frame.
- M2: Cycles light-path passes.
- Hero EXR: `n1/work/hero_a.exr` (sha256 2e6a836627a8d614…, gitignored).

## N1.1a: moon + sky only. **L1 PASS, L2 PASS** (after correction round 1)

| quantity | authored / expected | measured |
|---|---|---|
| open-field illuminance | moon 0.020 + sky π·10⁻³ = 0.0231 lx | **0.02313 lx** (two probes) |
| moon-shadow illuminance under a poplar | sky only, minus occlusion | 0.0029 lx (8× below open) |
| sky luminance | 1.0·10⁻³ cd/m² | 1.000·10⁻³ |
| open-field luminance | ρE/π = 5.9·10⁻⁴ | 5.89·10⁻⁴ (ratio 0.9998) |
| barn front / west wall (not moonlit) | sky + bounce | 3.1 / 3.2·10⁻⁴ |
| puddle (reflects sky) | below the sky | 5.0·10⁻⁴ |
| lane at 38 m (asphalt, grazing sheen) | – | 1.3·10⁻³ (brighter than the sky: rough-glossy sky reflection at 87°, Principled asphalt; reported, not gated) |

- The Cycles calibration in Blender 5.2 holds: sun irradiance and world radiance come out exactly as authored.
- L1 lists exactly one light (moon), no emissive material, and the world at 10⁻³ cd/m².

**Measurement errors (not rounds).** The first sky probe (bearing −10°) landed on a poplar, giving 6·10⁻⁵ cd/m². The
second was out of frame. It now sits at bearing +1°, elevation 9°.

**Correction round 1 of 3 (materials; cause read from the M2 passes first).**
- First run: field luminance was 1.9 × ρE/π, and **brighter than the sky** (1.12 vs 1.00·10⁻³). The passes gave
  diffuse 5.4·10⁻⁴ ≈ ρE/π, plus **glossy 5.8·10⁻⁴**: the Principled BSDF's Fresnel layer (IOR 1.5) at 86° grazing,
  reflecting sky and moon.
- A mown grass canopy is not a smooth dielectric sheet, so field, poplar foliage and hills are now Lambertian
  (`Specular IOR Level` 0). This lowers a non-physical sheen; nothing is brightened. The asphalt keeps its specular.

**Geometry correction (my coordinates vs the pre-registered N1.0 description, not a lighting change).**
- The poplar row at 76 m had its crowns cut off by the top of the frame. It moved to 125 m (height 16–22 m, tops ≤ 10°),
  so the whole silhouettes stand against the sky.

## The "almost vanishing" region → addendum 2 (geometry): **N1.1a complete**
With the first layout the moon's shadows were only slivers in the frame (1.7 m eye height; the shadows 80–130 m
away, pointing back-left). This was reported under stop condition 5. The user chose option A, frozen in addendum 2:
- barn at x 7–17, y 22–32;
- lamp head (4.5, 30, 5.9), pole at x = 6.3;
- puddle at the lamp mirror point (1.0, 6.6).

The user's three checks:
1. **The barn shadow is in the frame.** Ground below half the open-field luminance covers 8.7 % of the frame (17 % of
   the lower half): a band across the lane and the field edge.
2. **Inside it** (3, 16): 0.0031 lx, **7.6× darker** than the open field (luminance ×4.6 on the shadowed asphalt).
   The same order as the tree shadow (8×).
3. **Outside it, unchanged.** Open field 0.02308 vs 0.02313 lx, luminance 5.88 vs 5.89·10⁻⁴, sky 1.000·10⁻³, tree
   shadow identical, **L1 + L2 PASS**. The field probe right beside the barn rose 1.3 % (bounce off its wall).

Consequences predicted in addendum 2 and confirmed:
- the puddle is moonlit and now reflects the pole;
- the barn is cropped by the right and top edges;
- the lamp foot (4.5, 30) lies just outside the shadow (0.0227 lx moon + sky); lamp_y−10 (4.5, 20) is inside
  (0.0029 lx).

## N1.1b: + the one luminaire. **L1 PASS, L4 PASS, L3 FAIL as written** (stopped and reported: stop condition 3)

| gate | measured | verdict |
|---|---|---|
| L1 | lights = moon + luminaire spot; emissive = lamp disc only; world 10⁻³ | PASS |
| L4 disc | 8051.6 cd/m² vs I₀/A = 8051.7 (ratio 0.99999) | PASS |
| L4 under lamp | 17.50 lx vs I₀/h² = 16.35 (+7.0 %; 16.52 = +1.0 % with the barn's bounce excluded, below) | PASS |
| L3 under lamp | 17.5 lx (band 5–30) | pass |
| L3 at 30 m | y+30: 5·10⁻⁵ lx; y−30: 4·10⁻⁶; **x−30 (towards the field): 2.9·10⁻³ lx = 15 % of the moon's 0.0199** (limit 10 %) | **FAIL** |

**M2 attribution** (diagnostic render only: the barn walls and roof made invisible to diffuse rays via
`N1_DIAG_NO_BARN_BOUNCE`; the scene itself is unchanged).

| probe | lamp-only E | without barn bounce |
|---|---|---|
| under lamp | 17.50 | 16.52 |
| 5 m | 5.21 | 5.03 |
| 10 m (both directions) | 1.28 / 1.31 | 1.26 / 1.26 |
| 20 m towards the camera | 2.6·10⁻³ | 4·10⁻⁵ |
| **30 m towards the field** | **2.9·10⁻³** | **1·10⁻⁵** |

**Reading.** The luminaire's own optics are clean. Its spill at 30 m is 10⁻⁵ lx, 0.05 % of the moon. The whole L3
excess is **light bounced off the barn's west wall**:
- the wall is plaster, albedo 0.45, 2.5 m from the lamp (addendum-2 geometry), and at 1.1 cd/m² it is the brightest
  surface in the scene;
- it re-emits Lambertian light across the field at grazing incidence.

That is real physics of a lamp beside a pale wall, not bad optics. But the gate, as written ("the lamp's own ground
illuminance, step 2 minus step 1"), counts it, so it is recorded as FAIL.

**Second finding (no gate): the Blender 5.2 spot's angular profile.**
- Measured I(θ)/I₀ (lamp-only, barn bounce excluded): 1.0 at 0°, 0.69 at 40°, 0.59 at 60°.
- My uniform-cone model (Cycles ≥ 4.0 smoothstep mask, no cosine) predicted 1.0 / 1.0 / 0.95.
- So the delivered flux is ≈ 1500 lm, not the authored 2000 lm. The nadir intensity, the disc and L4 are exact; the
  claim "2000 lm" is not met.

**Preview** (`renders/raw/n1_1b_preview.png`).
- The pool sits on the lane and field edge; the barn wall is the brightest element.
- The lamp pool fills much of the barn-shadow band (barn_shadow probe 1.3·10⁻⁴ → 2.0·10⁻² cd/m²). The remaining dark
  regions are the lower-left field and the tree shadows.
- The puddle reflects the lamp arm and pole.
- The bounce light on the left field is visibly noisy at 512 spp. The production render (N1.2) needs a higher sample
  count; the count is fixed after N1.1.

## N1.1b after addendum 3 (lamp at (4.5, 45, 5.9), puddle at (1.0, 10.1)): **L1, L3, L4 PASS**. All predictions held
Stage a was re-rendered, because the puddle moved: L1 + L2 PASS; field 0.02308 lx; barn shadow 0.00305 lx; dark
ground 8.4 % of the frame.

| check | measured | verdict |
|---|---|---|
| L1 | moon + luminaire spot; emissive = lamp disc only | PASS |
| L3 under lamp | 16.52 lx (band 5–30) | PASS |
| L3 at 30 m (y+30, y−30, x−30) | 1·10⁻⁶ / 3·10⁻⁶ / 2·10⁻⁶ lx (limit 2.0·10⁻³) | **PASS**: the wall bounce is gone (was 2.9·10⁻³) |
| L4 disc | 8051.6 vs 8051.7 cd/m² | PASS |
| L4 under lamp | 16.52 vs I₀/h² = 16.35 (+1.0 %) | PASS |
| dark ground (< 0.5 × moonlit field) | **7.8 %** with the lamp on vs 8.4 % moon-only (it was 0.6 % with the lamp at y = 30) | the barn shadow survives |
| lamp-lit ground (> 10 × moonlit field) | 0.9 % of the frame: the pool at 29–61 m is a thin band from eye height | reported |
| barn-shadow probe luminance | 1.29·10⁻⁴ cd/m², unchanged from moon-only | – |

**Lamp-only profile** (clean, no barn bounce):

| distance from lamp | E (lx) |
|---|---|
| 0 m | 16.5 |
| 5 m | 5.03 |
| 10 m | 1.26 |
| 15 m | 0.015 |
| 20 m | 2·10⁻⁵ |

The effective flux is ≈ 1500 lm, as described in addendum 3.

**Preview.**
- Near to far: the moonlit near lane with the puddle (reflecting the lamp head and pole) → the dark barn-shadow band →
  the warm pool with the lamp → the moonlit field and the poplar silhouettes.
- The barn's west wall is lit only at its far end (1.5·10⁻³ cd/m²).
- The shadow band shows Monte Carlo speckle from the lamp's indirect light at 512 spp. The N1.2 production sample
  count must remove it.

**N1.1c (barn window).** The pre-registered window on the barn's front wall (x 11.4–12.6, y = 22) lies at bearing
27–30°, **outside the frame** (right edge at +20°) with the addendum-2 barn. It cannot be tested in this hero view.
It goes to the user: skip it, or re-place it (another addendum).

## N1.2 step 1: sample-count calibration. **No spp frozen: stopped per addendum 4 (2048 → 4096 still fails)**
Hero stage b, raw linear, same seed. The metric is the median of the 8 × 8-block median changes N → 2N, per crop
(`noise.json`).

| crop | 512→1024 | 1024→2048 | 2048→4096 |
|---|---|---|---|
| barn shadow (3, 16) | 0.24 % | 0.74 % | **4.32 %** |
| shadow/pool boundary (4.5, 28) | **5.61 %** | **6.47 %** | **8.01 %** |
| warm pool (4.5, 43) | 0.28 % | 0.28 % | 0.15 % |
| puddle (1.0, 10.1) | 0.05 % | 0.07 % | 0.11 % |
| moonlit dark field (−6, 14) | 0.00 % | 0.00 % | 0.00 % |

**Cause: a firefly regime, not a metric artefact.**
- In the barn shadow the only light besides sky and bounce is the lamp's **indirect** light, and it arrives through
  rare high-value paths.
- Shadow-crop pixels: mean 1.86 → 1.88 → 1.98 → 1.99·10⁻⁴ cd/m² (converging); median 1.29 → 1.29 → 1.30 →
  1.37·10⁻⁴ (still climbing towards the mean as more pixels collect a hit).
- Per-pixel coefficient of variation: 2.57 / 1.67 / 1.39 / 0.94 (≈ 1/√N from 1024 on).
- The block medians therefore drift with N instead of settling. At the observed rate, the per-pixel scatter reaches
  ~0.1 only at ≈ 4·10⁵ spp (≈ 2 days of CPU for one frame).
- Everything lit directly (pool, puddle, moonlit field) converges at 512.

## N1.2 addendum 5: one OIDN run. **PASS**
- `n1/denoise_render.py`: the frozen `scene.py` (hash-checked, byte-unchanged), 4096 spp, Cycles OIDN with Albedo and
  Normal, Accurate prefilter, High quality, CPU.
- Stored passes: Noisy Image, Denoising Albedo, Normal, Specular Albedo, Roughness, Depth.
- **Precondition: the Noisy Image is bit-identical** to the earlier 4096 Combined (max abs difference 0.0).
- Results in `oidn_gate.json`.

| crop | mean noisy → denoised | deviation (gate ≤ 2 %) | median | pixel CoV |
|---|---|---|---|---|
| barn shadow | 1.996 → 1.982·10⁻⁴ | **−0.74 %** | 1.37 → 1.97·10⁻⁴ | 0.96 → **0.05** |
| shadow/pool boundary | 8.115 → 8.109·10⁻³ | **−0.07 %** | 5.9 → 3.9·10⁻⁴ | 1.76 → 1.76 |
| warm pool | 0.1988 → 0.1990 | **+0.11 %** | 0.192 → 0.192 | 0.76 → 0.76 |
| puddle | 1.053 → 1.056·10⁻³ | **+0.35 %** | 5.4 → 5.4·10⁻⁴ | 1.72 → 1.70 |
| moonlit field | 5.906 → 5.908·10⁻⁴ | **+0.02 %** | 5.89 → 5.91·10⁻⁴ | 0.02 → 0.00 |
| whole frame | | −0.18 % | | |

**Reading.**
- Energy is preserved everywhere, so the M2.5 risk (−25 %) did not recur here.
- The barn shadow's fireflies are gone: its median rose to its mean, and the pixel CoV dropped from 0.96 to 0.05.
- In the boundary, pool and puddle crops, the CoV is structure (a light edge, the pool, a reflection), not noise, and
  it is unchanged.
- The boundary crop's median fell (5.9 → 3.9·10⁻⁴): its shadow half lost its hit pixels, while the mean is kept to
  0.07 %.

**The single N1 hero input** (denoised Combined, sha256 `3ce7fab2…` in Cycles units, `0e4a3803…` ×179 in cd/m²):
- `n1/work/hero_final_rgb.exr` for the comparator;
- `n1/work/hero_cdm2.exr` for A-only, B-only, raw, V0 and D1.
- Source multilayer `oidn4096/hero_b.exr`, sha256 `8a51bfb5…`.

## N1.2 steps 2–5: single EXR → comparator (fixed first) → D1 + variants + V0 → blind sheet
- **Comparator** (`comparator.json`, commit `b79ba55`, made before any D1 hero output): Blender 5.2 factory AgX,
  sRGB, no look, **+12 stops**.
- **D1 on the hero** (`variants.json`):
  - the extraction reproduces real pcond **bit-exactly** (C0); C2 and C3 at 100 %;
  - `-c` is active, and pcond takes its linear fall-back (as on the corpus);
  - the final D1 display gates (G1–G3, S-1…S-3) PASS; channels in [0.110, 100].
  - D1's C0 self-check needed the frozen `d1/pipeline/axis_a.sh` output for the hero; it was run.
  - A name collision in `n1/variants.py` (my camera `project` shadowed D1's `project()`) crashed the first attempt
    before any output was written. It was fixed.
- `d1/verify_manifest.sh` OK before and after.
- **Blind sheet** `renders/blind/sheet.png` (and `X.png`, `Y.png`, `Z.png`):
  - D1 final, the plain Blender comparator and V0 pcond, in a seed-0 permutation;
  - all re-encoded to identical 8-bit PNG.
  - **Key sha256 `173b6e88bb5a56cec32a93b740b3b23b772bc6baeba37f19cef6ca65c65b351e`** (`n1/work/blind_key.json`, revealed after the verdict).
  - My own reading, written before the verdict: sha256 `ecfd7371d78e0bb8518f1359fddfa76545ee4c2aaca47c57fbf6a18688772dda` (`n1/work/my_reading.txt`).
  - The diagnostic raw / A-only / B-only / final sheet is withheld until after the verdict: it would reveal which
    blind image is D1.

## N1 hero result: **ACCEPTED under the pre-registered gates (V1–V7 PASS)**. One classified D1 residual
The user's blind verdict (`blind_verdict.md`, commit `40451c8`, recorded before the reveal): V1–V6 PASS for all three
images; order as night **X > Y > Z**.

**Key revealed** (`blind_key.json`; its sha256 `173b6e88…` matches the pre-committed hash):
- **X = V0 pcond**;
- **Y = D1 final**;
- **Z = plain Blender AgX +12**.
- My pre-verdict reading (`my_reading.txt`, sha256 `ecfd7371…` matches) had guessed Z as the comparator and ranked
  Z > X > Y as a picture.

**V7** (D1 not judged worse than the plain exposure): **PASS**. D1 (Y) ranks above the plain exposure (Z) as night.
**V3** is lifted from PENDING: PASS.

**The finding the gates don't show: on this hero D1 does not beat the old V0 (X > Y).**
- Luminance is the same in both: pcond `-s -c`, linear fall-back. The only difference is colour.
- The diagnostic sheet (`renders/diagnostic_sheet.png`) and the pool-flank chromaticity (display Y 5–60 cd/m²,
  below the peak) locate it:

| version | u′v′ chroma from D65 | hue |
|---|---|---|
| raw (scene colour) | 0.075 | 53° (warm orange) |
| A-only | 0.073 | 50° |
| **B-only** | **0.008** | **6°** |
| **final (D1)** | **0.012** | **19°** |
| V0 pcond | 0.001 | (neutral) |
| plain Blender | 0.046 | 50° |

- **Axis B** collapses the 3000 K pool's chroma ×6–9 and rotates its hue from orange (~50°) towards red (6–19°): the
  "warmer/fleshier", pinkish pool the user saw in Y.
- V0 simply neutralises it (pcond `-c` plus clipgamut), and the user judged that slightly more coherent.
- The pool centre is white in every D1 variant: the known Y-priority peak whitening.

**Classification** (addendum 4):
- **D1 known residual, axis B.** It belongs to the documented B limitations (`d1/MANIFEST.md`: the mesopic calibration
  of B is an envelope only; B4-G2, a warm/yellow hue driven across neutral).
- It is **not a new D1 failure**, and the gates pass. D1 is not changed here.
- **Candidate D2 question** (only if wanted, via `d2/TEMPLATE.md`): *D2-B2: at mesopic pool levels, does B push warm
  practical light through neutral to pink?*

**Status (user decision after the reveal):**
- N1.2 hero **ACCEPTED** and frozen (`3ea5c40`).
- D1 vs plain Blender: **D1 wins**. D1 vs V0: **V0 wins on this hero**.
- The cause is isolated: the axis-B warm-mesopic hue residual.
- **Next: the D2-B2 cheap falsifier** (`d2/b2/PREREG.md`) **before N1.5.**

**D2-B2 result** (`d2/b2/README.md`): **KILL**. The pinkish pool is the Cao/Kirk rod-intrusion term itself. With the
kernel's rod term off, the rotation vanishes exactly; with it on, the hero flank rotates −31.9°. So it is not a
defect under the frozen model. The residual is an official limitation, and **N1.5 proceeds with the current D1.**
