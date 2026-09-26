# D1.1: pcond's human-vision bundle (`-h` = `-a -v -s -c`)

**Why.** D1.0 said that "no donor models acuity loss". That was wrong as a statement about the donors: Radiance
`pcond` documents
- `-a`: "defocus darker regions … to simulate human visual acuity loss";
- `-v`: "veiling glare … internal scattering";
- `-h`: the bundle of `-a -v -s -c`.

The frozen V0 path runs only `-s -c`. This run checks the rest.

**Setup.**
- `d1/pcond_h/run.sh` runs the **same frozen D0 display path** (`m1/pcond_colorimetric.sh LC` → PBR-oog sRGB,
  SDR100) with three flag sets:
  - V0 = `-s -c`
  - acuity = `-s -c -a`
  - h = `-s -c -a -v`
- Scenes: S0, S1 and the S3 pair.
- V0 reproduces D0 donor A pixel for pixel (`oiiotool --diff` PASS).
- `measure.py` computes the D0 metrics on emitted light and band-pass detail energy relative to V0 →
  `results.json`.
- Sheets: `sheet_crops.png` (full path) and `sheet_paths.png` (single pcond runs, paths A and B separately).

## Results

| | V0 | acuity (`-a`) | h (`-a -v`) |
|---|---|---|---|
| S0 sky / dark median, cd/m² | 0.32 / 0.14 | 0.32 / 0.22 | 0.32 / 0.22 |
| S0 silhouette Weber | 0.56 | **0.08** | 0.08 |
| S1 halo around lamps (ring mean / sky) | 3.2 | **98** | 45 |
| S1 lamp saturation kept | 0.35 | 0.24 | 0.27 |
| S3 bar P_det, viewer / MTF off | 1.00 / 1.00 | 0.09 / 0.26 | 0.03 / 0.04 |
| S3 bar displayed Weber | 0.75 | −6.1 (bar brighter than the sky beside it) | −0.04 |

**What the images show** (`sheet_crops.png`, `sheet_paths.png`).
- **`-a`:**
  - lamps become blocky white rectangles tens of arcminutes wide;
  - horizontal bands appear under the lamp ribbon;
  - the poplars dissolve (silhouette 0.56 → 0.08);
  - the S3 point source becomes a ~1–2° irregular blob that covers the bar.
- **`-v`:** a grey veil of several degrees with a **dark hole about 1° across** around the source.

**Cause: pcond's 1° foveal grid** (Radiance source, `src/px/pcond.h`, `pcond3.c`, `pcond4.c`).
- Local adaptation, veil and acuity are computed on a "foveal" sample image with `FOVDIA = 1°` per sample (S3:
  about 12 × 6 samples).
- The veil at each sample sums all *other* samples (`if (x == px && y == py) continue;`). So the 1° cell that
  contains the source gets no veil from it, which is the dark hole.
- The acuity defocus is driven per sample, which gives the degree-sized blocks.
- The same artefacts appear in single pcond runs (path A and path B separately), so this is **not** the LC
  composition.

**Reading.**
- pcond `-a` and `-v` are genuine models, but they are resolved at **1°**.
- Our questions P3 (lamps), P4 (the bar at 0.3°) and P5 (no giant disks) are at **arcminute** scale. There, `-a`
  and `-v` produce degree-scale block and ring artefacts, not acuity loss or veiling glare.
- The P_det drop at S3 is caused by those artefacts; it is not a glare result.
- The limitation is spatial discretisation, not a wrong model: a 1°-step representation is fundamentally incompatible with arcminute-scale target phenomena. pcond `-h` is therefore **unsuitable for P3–P5 at our angular scales**, not an invalid acuity/glare model in general. V0 (`-s -c`) stays the pcond
  reference.
- A defensible acuity cue for night scenes still needs a donor that works at the display's pixel scale.

No ranking; pcond sources: Radiance 6.0-unstable-2026-08-19 (`nix/radiance.nix`).
