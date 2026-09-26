# D1-A2: literal Wanat & Mantiuk 2014 local contrast on S1: KILL

Pre-registered in `PREREG.md` (commit `3022af8`, before any code). This is one strict run as in the paper, on the
frozen A1 curve and frozen B chromaticity, PHONE 73 ppd, SDR100 DARK.

    tracks/temporal-glare-2009/py.sh d1/axis_a2/run.py   # -> results.json, sheet_S1.png

## Result: raw FAIL and clamp FAIL, so **KILL Wanat A2 for S1** (pre-registered decision tree)

| gate | raw (m as written) | clamp m ≥ 0 (sensitivity only) |
|---|---|---|
| A2-S1 sky ≤ 2 cd/m² | 0.100 ✓ | 0.100 ✓ |
| A2-S2 lamps / sky ≥ 10 | 827 ✓ | 827 ✓ |
| **A2-S3 silhouette Weber ≥ 0.1** | **−2.14 ✗** (poplars brighter than the sky) | **0.0003 ✗** |
| A2-S4 B untouched | Δu′v′ 3·10⁻⁸ ✓ | 3·10⁻¹⁶ ✓ |
| **A2-AR1 poplar darker than the ring** | **✗** | ✓ |
| **A2-AR2 edge reversals ≤ 5 %** | **53 % ✗** | **5.8 % ✗** |
| A2-AR3 halo within 1.5× | ✓ | ✓ |
| pixels outside the display range | 47 % | 51 % |

(The D0 fragmentary tree mask gives the same reading: −2.51 / 0.0003.)

**m_k diagnostics (raw).**

| band (cpd) | 18.25 | 9.13 | 4.56 | 2.28 | 1.14 |
|---|---|---|---|---|---|
| σ (Eq. 14, px) | 2 | 4 | 8 | 16 | 32 |
| pixels with m < 0 | 0 % | 99.6 % | 99.2 % | 96.3 % | 82.8 % |
| share of Σ\|P_k\| with m < 0 | 0 | 0.83 | 0.71 | 0.44 | 0.11 |
| median m | 1.0 | −75.7 | −74.4 | −30.7 | −7.2 |

## Mechanism
- Eq. 17 is additive (Kulikowski): m = (c − Gt_src + Gt_tgt)/c.
- On S1 the source thresholds are huge (≈ 1.65 near the Mt cap for Y ≲ 10⁻⁴ cd/m²; 0.3–0.6 at the sky level). The
  target thresholds at the display's 0.1 cd/m² base are small. The local RMS contrast c of the dark regions is tiny
  (it is mostly Monte-Carlo render noise).
- So c − Gt_src + Gt_tgt is strongly negative and dividing by a small c gives **m ≈ −75**. The pixels are
  subthreshold in the source, and the model "restores" them as amplified, sign-inverted content.
- The result is bright inverted poplar outlines and render noise amplified across the sky and ground
  (`sheet_S1.png`).
- The 18.25 cpd band is left at m = 1, because both thresholds sit at the Mt cap there.
- Clamping m ≥ 0 removes the inversion but also the whole contribution. The silhouettes return to display black,
  and 5.8 % edge reversals remain from the few surviving positive bands.
- The additive principle is exactly what breaks: the model has no defined behaviour for source contrast *below*
  the source threshold, and Eq. 17 extrapolates it into inversion. The pre-registration predicted AR2 as the most
  likely failure; the magnitude was not predicted.

## Next (per the decision tree; not started)
- **No parameter tuning of Wanat.** The clamped variant is not adopted: it failed as well.
- **A3a = Ashraf & Mantiuk 2024.** The hybrid additive + multiplicative supra-threshold contrast-matching function
  revisits exactly the additive principle that fails here. Its lowest measured level, 0.02 cd/m², is still about
  two decades above S1's sky, so it is no certificate for starlight.
- **Then Kellnhofer 2015 / Ferwerda 1996** for < 10⁻³ cd/m², where a deterministic contrast target is incomplete
  (stochastic near-threshold vision).
