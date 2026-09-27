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
