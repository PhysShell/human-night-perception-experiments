# D1-AX: axis-A luminance extracted from pcond before its gamut clip

Pre-registered in `PREREG.md` (commit `922aa88`, before the extraction code).

    nix develop -c d1/a_extract/build_mat.sh     # verbatim Radiance harnesses: matscan matrix, clipgamut(greypoint)
    nix develop -c d1/a_extract/run_ax.sh        # frozen axis-A commands + kept inX.hdr, pcond -x map, -s control run
    tracks/temporal-glare-2009/py.sh d1/a_extract/extract.py

## Run 1 (`results_run1.json`): FAIL (C2, C3 on every still); F1 part PASS

| check | F1 | stills |
|---|---|---|
| C0 `-x` does not change pcond's output | bit-identical | bit-identical (all 6) |
| C1 F reconstruction | cumf[100] = 1 + 7·10⁻⁷, steps ≥ −7·10⁻⁷ | n/a (see below) |
| C2 unclipped identity | all 139 776 inactive-clip pixels ✓, neutrals ✓ | **0 %** |
| C3 full chain (verbatim clipgamut) | every patch ✓, 100 % of pixels | **≤ 0.6 %** |
| **G1 F1 monotone** | **PASS: all 7 colours, blue included** (old Y_A: blue not monotone) | |
| G2 S1 gates (requested Y) | | PASS (sky 0.49, lamps/sky 2711, Weber 0.69, 0 reversals, halo 0.89) |

**What failed.**
- **Every still ran in pcond's DO_LINEAR mode.** Their outputs carry an `EXPOSURE=` header, which only the linear
  branch writes (`pcond.c`). F1 is the only image that was histogram-mapped.
- Cause (`mkbrmap()`, `pcond3.c`): with `-s` the histogram is trimmed to the human-contrast-sensitivity ceiling. When
  the trimmed histogram falls below `CVRATIO` of the original, it returns −1 ("no compression needed!") and pcond
  falls back to the linear operator with the Ward (1994) contrast-based scale factor (`htcontrs`).
- My linear branch read the units wrongly: Y = (dlum/wlum)·L_eff/Ldmax.
- From the source, the linear branch writes dlum = scalef·inpexp·179·wlum (`putmapping`, cielum). pcond scales the
  colour by scalef (after `scalef /= WHTEFFICACY`). So Y_out = (dlum/wlum)·L_eff/**179**.
- The measured new/old ratio is 1.795–1.797 on every still, i.e. 179/100 × 1.003–1.004. The residual 0.3 % is below
  the pre-registered RGBE tolerance of max/128.
- As pre-registered, C3 decided this reading of the units, and it failed. Per the outcome rule this run is a
  **FAIL**. The correction is pre-registered separately (`PREREG_v2.md`) before re-running.

**Finding independent of the bug.**
- On S0/S1/S3/S4/S5, the frozen axis A ("pcond `-s -c`") is effectively a **single global linear exposure** chosen by
  pcond's contrast-sensitivity criterion, plus `-c` and `clipgamut`. It is not a histogram tone curve.
- The histogram adjustment (Ward Larson et al. 1997) is active only on F1.
- This is pcond's own documented fall-back; it does not change the frozen model, only how it should be described.

## Run v2 (`PREREG_v2.md`, commit `d31cbc0`; `results.json`): **PASS**. Axis-A extraction FROZEN as Y_A^new

| check | result |
|---|---|
| C0 non-interference | bit-identical, all 7 images |
| C1 F reconstruction (F1, the only mapped image) | cumf[100] − 1 = 7·10⁻⁷ |
| C2 unclipped identity | 100 % of clip-inactive pixels on every image; all F1 neutral and inactive patches |
| **C3 full chain** | **100 % of pixels on every image, clipped ones included**. The verbatim `clipgamut(greypoint(rgb_pre))` reproduces pcond's output within the RGBE bound |
| **G1 F1 monotone** | **PASS, all 7 colours** |
| G2 S1 (requested Y) | sky 0.318 cd/m², lamps/sky 2335, poplar Weber 0.593, reversals 0, halo 0.91 |

- **Stills.** New/old ratio (median) 1.0028–1.0036, as predicted: the RGBE truncation bias of pcond's output. Fraction
  differing by > 1 %: S0 0.0006 %, S1 0.30 %, S4 0.12 %, **S5 4.7 %**. These are the pixels pcond's `clipgamut`
  had altered: the S1 lamp cores and the S5 twilight sky.
- **Requested above peak (Y_A^new > 1).** S1 0.30 %, S4 0.065 %, S5 0.095 %.
- **Requested (Y_A^new, u′v′_B) outside SDR100.** S1 0.32 %, **S5 4.35 %**. This is the input to the display-realisation
  PREREG.
- **Von Kries luminance factor** (Y_A^new / F(L_eff)): 0.935–1.025 on F1 (p1–p99), 0.991–1.020 on S5, ≈ 1 on the
  night scenes (scotopic grey). The sensitivity Y′ = F(L_eff) is also monotone on F1.

F1, requested display luminance 0.1 + 99.9·Y (cd/m²), source 0.316 → 100 cd/m² (`F1_curves.png`):

| colour | old (after `clipgamut`) | new (pre-gamut) |
|---|---|---|
| neutral | 6.5 8.9 13.4 23.6 47.7 91.0 | 6.5 9.0 13.4 23.6 47.9 91.4 |
| red | 4.2 6.5 11.4 23.8 34.3 **38.8** | 4.2 6.5 11.5 23.6 48.1 92.5 |
| blue | 8.7 12.7 **17.7 12.2 13.8 13.9** | 8.7 12.8 17.9 24.5 49.9 91.2 |
| green | 6.6 9.1 13.6 23.7 47.8 80.2 | 6.7 9.1 13.7 23.8 48.0 91.1 |

**Conclusion.**
- The diagnosis "`clipgamut` is the whole cause of the F1 non-monotonicity" is confirmed.
- In the photopic range pcond's own chain gives every colour essentially the same Y at the same source luminance, as
  a photopic mapping should. Below that, the `-c` scotopic weighting orders colours by scotopic efficiency (blue
  above red), and that ordering is monotone in L.
- **Frozen axis A (D1)**, i.e. the model plus how its luminance is read:
  - model: Radiance `pcond -s -c` (unchanged);
  - luminance: **the Rec.709 luminance of pcond's pre-gamut output**, reproduced exactly from L_eff (post-`scotscan`),
    pcond's own tone map (`-x`, or the linear fall-back), and `matscan`'s matrix.
- On our real scenes pcond runs its linear fall-back (the Ward 1994 contrast-based scale factor), so there the model
  is a single global exposure plus the scotopic `-c` step.

**Next** (each with its own PREREG):
1. display realisation: chroma-priority Y_out = min(Y_A, Y_max(u′v′_B)) as primary, with R1 Y-priority as control;
2. P-4 v2 (reference L_eff) plus R3;
3. the final corpus acceptance.
