# D1-A2-K0: analytic feasibility gate for Wanat 2014 local contrast on S1

Pre-registered in `PREREG.md` (commit `47898d7`, before running).

    tracks/temporal-glare-2009/py.sh d1/axis_a2_k0/k0.py   # -> results.json

**Verdict under the pre-registered rules: NOT KILLED. Full A2 is allowed.** The project lead's pre-run prediction
("published A2 will likely not restore the silhouette gate") is **not confirmed by K0**. The pass is weak (see the
caveats).

## Numbers
**Silhouette** (luminance-defined, the two large poplars):
- L_tree = 5.6·10⁻⁵ and L_sky = 2.88·10⁻⁴ cd/m², so G_src = 0.355 (Weber 0.805).
- ROI 51 731 px.

**K0-1 band-energy census** (Rppd = 73, N = 5 per Eq. 15):

| band | ρ Eq. 15 (cpd) | DoG peak (cpd) | energy fraction |
|---|---|---|---|
| k1 | 18.3 | 36.5 | 0.040 |
| k2 | 9.1 | 11.2 | 0.018 |
| k3 | 4.6 | 5.6 | 0.022 |
| k4 | 2.3 | 2.8 | 0.040 |
| k5 | 1.14 | 1.39 | 0.066 |
| **base (A1)** | < 1.14 | — | **0.293** (< 0.5 → K0-1 not triggered) |

At the scene angle (Rppd = 32, sensitivity): N = 3, base fraction **0.684**. There the K0-1 rule *would* kill.
The display geometry decides.

**K0-2 ideal Eq. 17.** Displayed Weber if the whole G_src sat in one band at ρ, with L_tgt = 0.1 cd/m² (the A1 base
band):

| L_src \ ρ (cpd) | 0.25 | 0.5 | 1 | **1.14 (ρ_N)** | 2 | 2.28 |
|---|---|---|---|---|---|---|
| √(sky·tree) (pre-registered) | 0.42 | 0.57 | 0.53 | **0.48** | 0 | 0 |
| sky | 0.62 | 0.67 | 0.66 | 0.63 | 0.05 | 0 |
| tree | 0 | 0.29 | 0.20 | **0.00** | 0 | 0 |

K0-2 is not triggered (0.48 ≥ 0.1). K0-3 is not triggered (≥ 0.1 is reached at ρ ≥ ρ_N).

## Caveats (why this PASS is weak)
1. **The energy census under-counts.** Band and base fractions sum to 0.48, not 1, because DoG bands of a step
   edge are correlated (cross terms). The pre-registered measure is kept, but it understates every component,
   the base included.
2. **K0-2 depends strongly on which pixel luminance sets the threshold.** Eq. 17 uses per-pixel source luminance.
   At ρ_N, the tree side gives G̃ = 0 and the sky side 0.63. The real edge lies in between; the pre-registered
   geometric mean gives 0.48.
3. **"Ideal" is an upper bound.**
   - Only 6.6 % of the ROI energy is in the one band where G̃ is positive.
   - In the bands at ≥ 2.3 cpd, G̃ is negative. Eq. 17 then gives m < 0: contrast inversion or removal. The
     paper does not say how m < 0 is handled.
   - A realistic A2 will therefore produce a low-frequency, low-contrast silhouette from band 5 alone, with the
     finer edge content suppressed. Whether it reaches Weber 0.1 is not decidable analytically.
4. **The regime** (Kellnhofer et al. 2015). S1's sky (2.9·10⁻⁴) and poplars (5.6·10⁻⁵ cd/m²) lie below
   ~10⁻³ cd/m², near the absolute threshold, where perception becomes stochastic. A deterministic Weber target is
   an incomplete description there, whatever A2 gives.

## Next (needs its own pre-registration; not started)
**A2, published Wanat local contrast** (§4.1.2), with the choices the paper leaves open fixed in advance:
- the handling of m_k < 0: primary = as written (no clamp); sensitivity = m_k clamped at 0;
- the local-contrast estimator σ (Eq. 14);
- the same A1-S3 gate (Weber ≥ 0.1) measured on the rendered, displayed image, plus A1-S1/S2/S4.

**A3 (near-threshold branch: Kellnhofer 2015, Ferwerda 1996) stays open regardless.** Caveat 4 applies even if A2
passes.
