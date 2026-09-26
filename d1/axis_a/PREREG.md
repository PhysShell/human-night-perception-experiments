# D1-A0 / D1-A1 pre-registration: axis separation, then Wanat 2014 global tone curve only

Committed **before** any A0/A1 code is written. B (the Cao/Kirk kernel, κ = 3, a = 1, plus the Wanat-derived local
chroma collapse) is frozen.

## Architecture under test
- **B** supplies chromaticity only.
- **A** supplies display luminance only.
- `display RGB = chromaticity_B at exactly Y_display_A`.
- The kernel's luminance gain (×2–7.5 in dark regions) is **discarded**, not compensated.

## D1-A0: axis separation (cheap falsifier)
- `x_A0 = out_B · (Y_physical / Y(out_B))` per pixel (for Y(out_B) > 0).
- **Kill** if any of these fails on the B4 patches (all L) and on S1:
  - |Δ u′v′ chroma| ≤ 10⁻⁹;
  - |Δ hue| ≤ 10⁻⁶° where chroma ≥ 0.002;
  - |Y(x_A0)/Y_physical − 1| ≤ 10⁻⁹.
- If it is killed, the luminance gain is not separable from the colour mechanism, and this architecture is dropped.
- **Expected: PASS.** A per-pixel scalar does not change chromaticity.

## D1-A1: Wanat & Mantiuk 2014, global contrast retargeting only (§4.1.1, Eqs. 5–11)
- **Implementation (ours; no public code exists).** Minimise over a piecewise-linear T on l = log10 Y:
  - ∫ [ (G − Gt(l)) − (T′(l)·G − Gt(T(l))) ]² + τ (l − T(l))² dl
  - subject to T′ ≥ 0, T(lmin) ≥ dmin, T(lmax) ≤ dmax (log10 cd/m²).
  - S(l) = 1 (no saliency; the paper's own choice for video/display-referred use).
  - G = 0.4, ρ = 2 cpd, τ = 10⁻⁴.
  - Gt = G(Mt) = ½ log10((1 + Mt)/(1 − Mt)), with Mt = 1 / (8.6 · CSF(ρ, La)) and La = the luminance itself.
  - 30 nodes. Solved with SLSQP on node values (the paper uses iterative QP; the problem is the same).
- **CSF, identified before running.** HDR-VDP-2.2.2 full CSF = `ncsf(ρ, L) · MTF(ρ) · sA(L)`, tables from
  `hdrvdp_parse_options.m` of the official 2.2.2 zip (sha256 b651bc47…6820).
  - Check: 8.6 · CSF(2 cpd, 100 cd/m²) = 244.6, i.e. Mt = 0.409 %; the paper says 0.4 %.
  - Rejected: ncsf only (8.3 %), ncsf·MTF (12.3 %), and the HDR-VDP-3.0.7 table refitted in 2020 (12.6 %).
  - Below 0.002 cd/m² the ncsf parameters are clamped (the table ends there), as in HDR-VDP: an extrapolation.
- **Mt ≥ 1 rule (declared).** Mt is capped at 0.999 (Gt ≈ 1.65), meaning "invisible". This happens below
  ~1.5·10⁻⁴ cd/m².
- **Target display (frozen, not fitted).** SDR100 DARK from `d0/display-scenarios.json`: dmin = 0.1, dmax = 100
  cd/m².

### Kill-first synthetic tests (run before any scene; if any fails: A1 KILL, no scene render)
| id | test | criterion |
|---|---|---|
| K0a native: same luminance | source [10⁻³, 10²] → target [10⁻³, 10²] | T ≈ identity: max \|T(l) − l\| ≤ 0.05 log10 |
| K0b native: 100 → 1 (paper Fig. 7 text: "less steep for bright tones and more steep for dark tones") | source [10⁻³, 10²] → target [10⁻⁵, 1] | mean slope over source [10, 100] < 1 **and** < mean slope over source [10⁻³, 10⁻²] |
| K0c native: 100 → 1000 ("little change in shape") | source [10⁻³, 10²] → target [10⁻², 10³] | slope within [0.85, 1.15] over source [10⁻², 10] |
| K1 our case | source [10⁻⁴, 10²] → SDR100 | T monotone; T(lmin) ≥ log10 0.1 and T(lmax) ≤ log10 100 (± 10⁻⁶) |
| K2 no decade crushing in the visible range | same | every full source decade within [10⁻³, 10²] has mean slope ≥ 0.1 |
| K3 night contrast reduced relative to bright | same | mean slope over source [10⁻³, 10⁻²] < mean slope over source [1, 10²] |

### Scene tests (only if K0–K3 pass). S1, frozen B, SDR100 DARK.
- Source range: lmin = log10 max(Y_p0.1, 10⁻⁵) and lmax = log10 Y_max of the physical S1.
- Pixels outside the range are clamped to it.

| id | criterion |
|---|---|
| A1-S1 night stays dark | S1 sky median display luminance ≤ 2 cd/m² (SDR100 midtone ≈ 18) |
| A1-S2 lamps ordered and salient | median lamp / median sky display luminance ≥ 10, and T monotone (lamp order kept) |
| A1-S3 silhouettes | displayed Weber (sky → poplars) ≥ 0.1 |
| A1-S4 B untouched | for pixels with no channel clipped at dmax: \|Δ u′v′\| between display RGB and B's chromaticity ≤ 10⁻⁶. Clipped fraction reported |
| A1-S5 no scene knob | no parameter depends on S1 other than lmin/lmax, which are defined above |

**Controls, no gate:** D0 emitted-light values of pcond V0 and Mantiuk08 (WHITE_Y auto) on S1 SDR100, from
`d0/results/tables/metrics.jsonl`.

**Not in scope.** Local contrast (Laplacian pyramid, §4.1.2) and saliency. A2 opens only for a demonstrated
residual such as low-contrast texture visibility.

**Expectations, stated before running.**
- A0 passes.
- K0a–K0c pass if the implementation is right. They are the check of our code against the paper's stated
  behaviour.
- At S1 levels the model's thresholds are near G = 0.4 (Gt(3·10⁻⁴) = 0.34). A3 (silhouettes) is therefore the
  uncertain scene gate.
