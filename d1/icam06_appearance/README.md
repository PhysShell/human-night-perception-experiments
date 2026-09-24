# D1 donor: iCAM06_APPEARANCE

**What it is.** iCAM06 V1.3's image-appearance output `XYZ_tm`, taken **before** the authors' display step
(`iCAM06_disp`).
- Input: absolute (`max_L = 0`), p = 0.7, γ = 1.2 (dark surround).
- Produced by the D0.1 driver `d0/donors/icam06/icam06_ladder.m`, which calls the original sub-functions in the
  order of `iCAM06_HDR.m`.
- Provenance, shims and the rendered counterpart: `d0/input-contracts/icam06.md`. The absolute-level ladder is in
  §D0.1 there.

**Units.** `XYZ_tm` is in the model's own response units, not cd/m². Only within-image ratios and chromaticities
are read. Measurements are made in the scene domain against the donor's own input; there is no display step.

    d0/donors/icam06/setup.sh
    tracks/temporal-glare-2009/py.sh d1/icam06_appearance/run.py   # -> .cache/<scene>_XYZ_tm.exr, results.json

## S1 (physical night, sky 2.9·10⁻⁴ cd/m²): in → out

| region | Y / image p99.9 | chroma (u′v′ from D65) | hue angle about D65 |
|---|---|---|---|
| sky | 1.5·10⁻⁴ → 0.11 | 0.005 → 0.020 | 58° → 14° |
| poplars | 4.2·10⁻⁵ → 0.032 | 0.058 → 0.020 | 52° → 11° |
| ground | 1.8·10⁻⁵ → 0.050 | 0.017 → 0.021 | 94° → 15° |
| lamps | 0.79 → 0.81 | 0.092 → 0.029 | 45° → 27° |

- Sky→poplar Weber contrast: 0.72 → 0.71.
- Band-pass detail energy (DoG 1 vs 4 px, log domain), out/in: sky 0.62, ground 0.05.

## What this donor does to the physical night (D1-A / D1-B effects, separated)

- **Brightness / range (D1-A).** It lifts the dark scene by about three decades relative to its highlights: the
  sky goes from 1.5·10⁻⁴ to 0.11 of p99.9. That is the rod-response term: it compresses the scene towards the lamps
  instead of keeping it dark.
- **Silhouettes.** Kept (0.71).
- **Colour (D1-B).**
  - Everything that is not a lamp converges on one weak chroma (≈ 0.02) and one hue (11–15°: reddish-pink), whatever
    its input colour.
  - Lamps lose two thirds of their chroma.
  - There is **no blue (Purkinje-direction) shift** at this level.
  - A cast that is identical across regions suggests the per-channel 1e-4 floor in `fastbilateralfilter.m`
    (sub-floor pixels become equal-energy grey). **Hypothesis, not verified**; see `d0/input-contracts/icam06.md`.
    In the D0.1 ladder the bluish cast appears only at ×10²–10⁴ (mesopic).
- **Detail (D1-B).** Detail on the ground (the input is below 1e-4 cd/m² there) almost vanishes (0.05). That comes
  from the same floor flattening the log base layer. It is not an acuity model.
- **Real night photograph S4** (sky 0.69 cd/m², above the floor): sky chroma 0.061 → 0.007 (desaturation), hue
  −110° → −16°; lamp chroma 0.058 → 0.038.

No ranking. The rendered counterpart (iCAM06_RENDERED) is a D0 display renderer.
