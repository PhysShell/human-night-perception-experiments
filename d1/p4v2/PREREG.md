# D1-P4v2 + R3 pre-registration: luminance-order gate against pcond's own L_eff; N/A plus a flat guard on degenerate input

Committed **before** the code exists. It replaces acceptance gate P-4 (Spearman vs photopic Y).
- That gate failed on S4 (0.937) and S5 (0.968) because `-c` deliberately reorders spectrally different colours. On
  S3_nobar it was undefined (NaN).
- The old P-4 history stays FAIL.
- Everything evaluated here is frozen: A = extracted pcond `-s -c` luminance (`d1/a_extract/`); B = Cao/Kirk κ = 3
  plus the Wanat-derived local chroma collapse; display = Y-priority (`d1/display_r/`, v2).

## Quantities (per pixel, from the frozen extraction; its actual branches are used)
- **L_eff**: pcond's effective luminance after `scotscan`. If pcond cleared DO_COLOR for the image, L_eff = photopic
  L_p (`colour_active` in the extraction). If it ran DO_LINEAR, F is its linear map.
- **F(L_eff)** = Y_map, pcond's tone-map output.
- **k** = Y_A / Y_map: the luminance factor of `matscan`'s von Kries step, part of the frozen A. This is not a free
  parameter. So Y_A = F(L_eff)·k.
- **Y_out** = the final emitted luminance of the frozen pipeline, taken from the float code before 16-bit
  quantisation, as in every gate so far, and decoded through `d0/display_model.py`.
- **Y_expected** = clamp(0.1 + 99.9·F(L_eff)·k, 0.1, 100).

**Tolerance.** The only tolerance used is the one already frozen for Y in the display stage: **10⁻⁶ relative**
(Y-priority S-1). No new constant.

## Gates
| id | criterion |
|---|---|
| **P4-G1 functional** | \|Y_out − Y_expected\| ≤ 10⁻⁶·Y_expected on every pixel of every still, F1 and all 48 S2 frames. An end-to-end self-check: after A, nothing (B, display, encode/decode) changes Y except the display range clamp |
| **P4-G2 ordering** | on a 20 000-pixel subsample (seed 0), all ordered pairs (i, j) with F(L_eff,i) < F(L_eff,j) that are **resolvable**: F(L_eff,j)/F(L_eff,i) > (k_i/k_j)·(1 + 10⁻⁶). Inversion: Y_out,i > Y_out,j·(1 + 10⁻⁶). Floor/ceiling ties are never inversions (strict inequality). **Inversion rate = 0**. Every still, F1, all S2 frames |
| **R3 degenerate reference** | if the subsample contains **no** resolvable pair, P-4 = **N/A** (neither PASS nor FAIL) and R3-flat runs instead |
| **R3-flat** | the pipeline creates no luminance structure absent from the reference: over all pixels whose L_eff equals the subsample's (single) value, max Y_out / min Y_out − 1 ≤ 10⁻⁶, and P4-G1 holds on the whole image |

Why resolvable pairs are defined this way: pcond's chain is Y_A = F(L_eff)·k with F monotone. A pair whose F ratio
exceeds its k ratio can be reordered only by something downstream of A, which is what P-4 exists to catch. Closer
pairs of different chromaticity may be reordered by pcond's own `matscan`, which is frozen A behaviour. Their count is
reported.

## Reported (diagnostic, no gate)
- Old P-4: Spearman(photopic Y, Y_out). This shows the size of the Purkinje/`-c` reorder.
- Raw inversion rate against bare L_eff (no k allowance): the size of the `matscan` von Kries reorder.
- Fraction of resolvable pairs; the k range; the DO_COLOR/DO_LINEAR branch per image.

## Decision
- **Any inversion on a resolvable pair, or any P4-G1 violation:** a real FAIL of the frozen pipeline. The component is
  located (B, display or encoding) and it is **not** a metric problem. No re-tuning here; the fix gets its own
  PREREG.
- **All pass (with N/A allowed only via R3):** P-4 v2 and R3 are adopted for the final acceptance.

## Predictions (recorded before running)
- S4 and S5 pass P4-G1/G2: the old 0.937/0.968 was the expected `-c` reorder.
- **S3_nobar → N/A plus R3-flat PASS.** The old Spearman was NaN because the photopic subsample was constant; L_eff is
  expected to be constant there as well.
- S0, S1, S3_bar, F1 and all S2 frames PASS.
- The raw inversion rate against bare L_eff is > 0 on F1 and S5 (k spread) and ≈ 0 on the scotopic scenes (k ≈ 1).

## Then
The final corpus acceptance with everything frozen:
- A = extracted pcond `-s -c` luminance;
- B = Cao/Kirk plus the Wanat-derived local chroma collapse;
- display = Y-priority minimum-chroma projection;
- P-4 = P-4 v2 plus R3.

It is a separate PREREG committed before that run; it contains no new investigation.
