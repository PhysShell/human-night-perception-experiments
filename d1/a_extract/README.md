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
