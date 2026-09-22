# M0: existing operators on calibrated HDR (no 3D scene yet)

This milestone runs night-vision tone-mapping operators that already exist on HDR images with known
absolute luminance. Nothing here implements a vision model. The only code is glue: format
conversion, header metadata and contact sheets.

    nix develop                                  # radiance, pfstools, oiiotool, imagemagick, blender …
    m0/make_synthetic_night.py                   # -> m0/data/synthetic_night.exr (test data, cd/m^2)
    m0/run_m0.sh                                 # -> m0/out/*.png, sheet_*.png
    m0/fetch_fairchild.sh                        # real calibrated dusk HDR (research licence, not committed)
    CROPS=0 m0/run_m0.sh m0/data/fairchild_McKeesPub_cdm2.exr 60 m0/out_mckeespub

## Input contract

The input is an EXR in linear Rec.709/D65 whose Y channel (0.2126 R + 0.7152 G + 0.0722 B) is
luminance in cd/m². The second argument is the horizontal field of view in degrees; pcond needs it
for acuity and veiling glare.

## Glue steps

| step | tool | why |
|---|---|---|
| clamp ≥ 0 | oiiotool | real HDR merges contain negatives, and one negative pixel makes pattanaik00 NaN |
| × 1/179 → `.hdr` | oiiotool | Radiance pictures store radiance; pcond multiplies by 179 lm/W |
| `VIEW=`, `PRIMARIES=` headers | `getinfo -a` | pcond otherwise assumes a 40° view and Radiance primaries |
| `.pfm` + `LUMINANCE=ABSOLUTE` | oiiotool, `pfstag` | pfstools 2.2.0 is built without OpenEXR (OpenEXR 2 is gone from nixpkgs) |
| display encoding | `ra_ppm -g 2.2`, `pfsgamma -g 2.2` | each tool's documented path. mantiuk08 output is already display-encoded |

## Synthetic scene luminances

These are order-of-magnitude choices, used only as test data.

| element | cd/m² | note |
|---|---|---|
| sky | 3e-4 (zenith) to 1.5e-3 (horizon) + warm skyglow | moonless rural sky with a distant settlement |
| hills | 2e-4 | barely darker than the sky |
| fields | 1.5e-4 to 5.5e-4, ±35 % fine furrows | acuity probe |
| poplars | 3e-5 | silhouettes |
| Purkinje probe | red and blue patches, both Y = 0.03 | mesopic test |
| road lamps | 4000 × haze transmittance (0.67 … 0.13), one pixel each | sub-pixel luminaires as pixel-averaged luminance, HPS-like colour |
| village lights | 200 to 2500 | warm and cool LED mix |

## Results summary

See [`../docs/research/human-night-vision-landscape.md`](../docs/research/human-night-vision-landscape.md),
sections B and F.

- **`pcond -s -c` meets the M0 acceptance condition.**
- **`pcond -a` / `-v` have artefacts on point-source chains.**
- **Every operator loses the warm hue of the lamps**, because they all clip to white.

### Temporal smoke test (pattanaik00 `-t`)

    oiiotool m0/data/fairchild_McKeesPub_cdm2.exr --resize 320x0 --clamp:min=0 -o /tmp/dark.pfm
    oiiotool /tmp/dark.pfm --mulc 1000 -o /tmp/bright.pfm
    pfsin /tmp/bright.pfm $(printf '/tmp/dark.pfm %.0s' $(seq 19)) \
      | pfstmo_pattanaik00 -t --fps 1 | pfsgamma -g 2.2 | pfsoutpfm /tmp/f%02d.pfm

The mean display value was 0.29 on the bright frame. Over the next 19 dusk frames it drifted from
0.405 to 0.421. The static render of the same dusk frame gives 0.276. The operator runs, but the
direction of the transient has not been validated yet.
