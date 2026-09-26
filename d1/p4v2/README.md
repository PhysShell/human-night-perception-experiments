# D1-P4v2 + R3: the luminance-order gate against pcond's own L_eff

Pre-registered in `PREREG.md` (commit `9adb50b`, before the code). `tracks/temporal-glare-2009/py.sh d1/p4v2/run.py`
→ `results.json`. Frozen pipeline: A = extracted pcond `-s -c` luminance; B = Cao/Kirk plus the Wanat-derived chroma
collapse; display = Y-priority. Y_out is taken from the float code.

## Result: **PASS on every image; S3_nobar N/A + R3-flat PASS. All predictions held.**

| image | P4-G1 max \|Y_out − Y_expected\|/Y | resolvable pairs | inversions | verdict | old P-4 Spearman vs photopic Y (diag) | raw inversion rate vs bare L_eff (diag) | k p1–p99 |
|---|---|---|---|---|---|---|---|
| S0 | 1.0·10⁻⁷ | 2.0·10⁸ | 0 | PASS | 0.987 | 0 | 0.99994 |
| S1 | 1.0·10⁻⁷ | 2.0·10⁸ | 0 | PASS | 0.987 | 5·10⁻⁹ | 0.99994 |
| S3_bar | 1.0·10⁻⁷ | 2.1·10⁶ | 0 | PASS | 1.000 | 0 | 0.99994 |
| S3_nobar | 1.0·10⁻⁷ | **0** | – | **N/A + R3-flat PASS** (1 distinct L_eff; 383 672 px, output range 0) | NaN | – | 0.99994 |
| S4 | 1.0·10⁻⁷ | 2.0·10⁸ | 0 | PASS | **0.937** | 2.3·10⁻⁴ | 0.992–1.001 |
| S5 | 1.0·10⁻⁷ | 2.0·10⁸ | 0 | PASS | **0.968** | 2.3·10⁻⁴ | 0.991–1.020 |
| F1 | 9.9·10⁻⁸ | 1.7·10⁸ | 0 | PASS | 0.989 | 3.1·10⁻³ | 0.935–1.025 |
| S2 (48 frames) | ≤ 1.0·10⁻⁷ | ≥ 2.0·10⁸ each | 0 | PASS | – | – | – |

**Reading.**
- **Old P-4 was a semantic mismatch, not an artefact.** The old failures (S4 0.937, S5 0.968) sit on scenes that,
  measured against pcond's own effective luminance, have **zero** reordering downstream of A. The old gate measured the
  `-c` Purkinje reorder, which is intended.
- **The G1 residual is the coefficient sum, not the pipeline.** The 1.0·10⁻⁷ is the Rec.709 luminance coefficient sum
  (1.0000001) seen in DR v2. After A, nothing but the display range clamp touches Y: not B, not the display
  projection, not encode/decode.
- **The raw bare-L_eff inversions quantify pcond's `matscan` von Kries reorder**, which is frozen A behaviour. It is
  0.31 % of pairs on F1 (saturated patches) and 0.023 % on S4/S5, and ≈ 0 on the scotopic scenes (k ≈ 1: the colour is
  already grey).
- **Global switches.** `-c` was active (DO_COLOR not cleared) on every image. All stills ran pcond's DO_LINEAR
  fall-back; F1 was histogram-mapped.

**Adopted for the final acceptance:** P-4 := P4-G1 + P4-G2, with R3 (N/A plus R3-flat) on degenerate references.
