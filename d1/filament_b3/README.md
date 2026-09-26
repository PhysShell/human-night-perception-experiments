# D1-B3: absolute-scale calibration of the Filament-derived Cao/Kirk kernel

**Object tested.** The Filament-derived Cao/Kirk kernel under an absolute-luminance input convention:
`scotopicAdaptation(κ·L_rgb, a = 1)`, run verbatim (`d1/filament/`), with L_rgb in cd/m². Filament itself feeds
the function exposure-adjusted renderer values, so no result here says "how Filament models cd/m²". The only free
scalar is κ.

**Pre-registered** in `PREREG.md`, committed in `dff6db1` before `sweep.py` ran. CIE's mesopic range
(0.005–5 cd/m²) is used only as an envelope; there is no CIE-m → a mapping.

    d1/filament/setup.sh
    tracks/temporal-glare-2009/py.sh d1/filament_b3/sweep.py      # pre-registered grid -> results.json, gates.json, curves.png
    tracks/temporal-glare-2009/py.sh d1/filament_b3/boundary.py   # POST-HOC fine search of the interval ends -> boundary.json

## Result on the pre-registered grid

| κ | B3-G1 worst E(5)/E(0.005) ≤ 0.10 | B3-G2 neutral L50 ∈ [0.005, 5], width ≥ 1 dec | G3 ordering | G4 lamp@200 / neutral@0.01 ≤ 0.10 | G5 S1 lamp/sky E ≤ 0.25 | admissible |
|---|---|---|---|---|---|---|
| 0.01 | 0.48 ✗ | 2.9, — ✗ | ✓ | 0.114 ✗ | 0.72 ✗ | no |
| 0.03 | 0.34 ✗ | 0.98, 3.4 ✓ | ✓ | 0.070 ✓ | 0.51 ✗ | no |
| 0.1 | 0.23 ✗ | 0.30, 3.4 ✓ | ✓ | 0.042 ✓ | 0.33 ✗ | no |
| 0.3 | 0.15 ✗ | 0.10, 3.3 ✓ | ✓ | 0.027 ✓ | 0.21 ✓ | no |
| **1** | **0.103 ✗** (blue patch; neutral 0.089) | 0.032, 3.3 ✓ | ✓ | 0.018 ✓ | 0.13 ✓ | **no, by 3 % on one patch** |
| **3** | 0.074 ✓ | 0.012, 3.2 ✓ | ✓ | 0.014 ✓ | 0.080 ✓ | **yes** |
| 10 | 0.055 ✓ | 0.0044 ✗ | ✓ | 0.011 ✓ | 0.051 ✓ | no |
| 30 | 0.045 ✓ | 0.0021 ✗ | ✓ | 0.010 ✓ | 0.035 ✓ | no |
| 100 | 0.039 ✓ | 0.0012 ✗ | ✓ | 0.009 ✓ | 0.026 ✓ | no |

**Admissible interval.** A post-hoc fine search with the same G1/G2 definitions gives **κ ≈ 1.09–8.3**, i.e. less
than one decade. G3–G5 pass over the whole interval.

## Reading

1. **A consistent physical scale exists, but only just.**
   - The kernel's own transition (neutral, 90 % → 10 % of its plateau) is **3.2–3.4 decades** wide. That is as
     wide as the whole CIE mesopic range (3 decades).
   - So it fits inside the envelope only when it is placed almost exactly on it:
     - below κ ≈ 1.1 too much effect remains at 5 cd/m² (G1);
     - above κ ≈ 8.3 the transition midpoint drops under 0.005 cd/m² (G2).
2. **κ = 1 (input read directly as cd/m²) is just outside.** It fails G1 by 3 %, on the blue patch only (neutral
   0.089, others ≤ 0.099).
   - This is an **empirical near-coincidence**. It is not evidence that Filament's +11.4 EV constant was meant for
     cd/m².
   - D1 adopts **κ = 3** (the admissible grid point) as the documented convention for further runs, with the
     interval 1.1–8.3 as its stated uncertainty.
3. **Highlight preservation holds at every admissible κ.** A 200 cd/m² warm lamp receives ≤ 1.4 % of the shift of a
   0.01 cd/m² neutral; on S1, lamp pixels receive 8 % of the sky's shift at κ = 3.
4. **My pre-registered expectation was wrong in one respect.** I had stated that G1 could not be satisfied by κ,
   because it tests the curve's width. In fact E(5)/E(0.005) also depends on *where* the two CIE points fall on the
   curve, which κ controls. It falls from 0.48 to 0.04 over the grid. The width argument explains why the window is
   narrow, not why it is empty.
5. **What calibration cannot fix (unchanged from D1.1).**
   - Below ~0.005 cd/m² the kernel saturates on a *chromatic* blue plateau (neutral Δu′v′ ≈ 0.155) and brightens the
     input: a blue patch is ×27 at 10⁻⁴ cd/m², κ = 1.
   - Scotopic vision is essentially achromatic. Cao et al. 2008 measured rod–cone interaction at 2–100 Td, in the
     mesopic regime.
   - So the kernel **cannot by itself model the transition into fully scotopic, achromatic vision**. This is an
     extrapolation limit, not a defect of the kernel.
   - S1's sky (2.9·10⁻⁴ cd/m²) lies in that extrapolated region at every admissible κ.

## Next (not started)
- Scotopic desaturation (chroma → 0 below ~0.005 cd/m²) without destroying the mesopic hue shift found here.
- Reference behaviour: pcond `-c`'s chroma attenuation, examined as a function on its own.
- Not a merged renderer.
