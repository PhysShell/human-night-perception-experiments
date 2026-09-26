# D1-B4: an independent scotopic chroma-collapse stage on top of the Cao/Kirk kernel

**Pre-registered** in `PREREG.md`, committed in `6d38a90` before `run.py` existed.
- Upstream (frozen from B3): the Filament-derived Cao/Kirk kernel, a = 1, κ = 3.
- The stage: `out = Y_f·white + w·(f − Y_f·white)`.
  - It mixes towards the Rec.709 white of the same luminance, so Y and u′v′ hue are preserved exactly.
  - w is solved so that u′v′ chroma out/f = t(L), where L is the pixel's physical input luminance.

    d1/filament/setup.sh
    tracks/temporal-glare-2009/py.sh d1/chroma_b4/run.py     # -> results.json, gates.json, curves.png, sheet_S1.png

**One measurement correction after the first run, disclosed.**
- The white point in `run.py` was the rounded u′v′ (0.1978, 0.4683). The exact white of Rec.709 (1, 1, 1) is
  (0.197840, 0.468336), about 4·10⁻⁵ away.
- That offset alone produced ~1° hue "errors" at chroma ≈ 0.002, and B4-G4 failed for pcond_c and wanat14.
- The constant is now computed from the matrix. No gate, law or parameter changed. The first run's gates are kept
  in `.cache/gates_run1_rounded_white.json`.
- Earlier D1 hue/chroma tables (`d1/filament/`) used the same rounded white. Their effect is ≤ 4·10⁻⁵ in u′v′,
  negligible for the chroma ≥ 0.005 reported there. B3's E = |Δu′v′| is a difference and is unaffected.

## Results (corrected white)

| candidate | G1 photopic identity (≥ 0.99) | G2 monotone collapse (≤ 10⁻⁴) | G3 chroma ≤ 0.01 at L ≤ 10⁻³ | G4 hue kept (≤ 0.5°) | G5 Y kept | G6 numerics | G7 Purkinje not erased (≥ 0.3) | G8 S1 lamps ≥ 0.9, sky ≤ 0.01 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| none | 1.000 ✓ | 7.4·10⁻³ ✗ | 0.200 ✗ | 0 ✓ | ✓ | ✓ | 1.00 ✓ | 1.00, **0.139 ✗** | not supported (as expected) |
| pcond_c | 1.000 ✓ | 4·10⁻⁶ ✓ | 0.000 ✓ | 0 ✓ | ✓ | ✓ | **0.017 ✗** | **0.27 ✗**, 0.000 | not supported (G7 as expected; G8 lamps also) |
| **wanat14** | 0.9989 ✓ | **4.2·10⁻⁴ ✗** (yellow only) | 0.0018 ✓ | 0 ✓ | ✓ | ✓ | 0.48 ✓ | 0.93 ✓, 0.0004 ✓ | **passes 7 of 8; fails G2 on one patch** |

**What the results show.**
1. **wanat14 does what the architecture needs.**
   - It is photopic identity above ~100 cd/m² (≥ 0.999).
   - The chroma collapses below the CIE scotopic boundary (≤ 0.0018 at 10⁻³ cd/m²).
   - The Cao/Kirk hue and luminance are untouched.
   - The mesopic Purkinje tint survives: a neutral reaches u′v′ chroma ≈ 0.017 around 0.15 cd/m², and 48 % of
     the kernel's shift remains at 0.1 cd/m².
   - On S1 it keeps 93 % of the lamps' chroma while the sky goes to 0.0004.
   - All of this follows from absolute luminance alone, with no lamp mask.
2. **Its one failure is real and specific.**
   - For the yellow patch, the kernel rotates the hue through neutral towards blue. Its chroma passes through a
     minimum (≈ 0.010 near 0.013–0.016 cd/m²) and then grows again as a blue.
   - wanat14's t(L) damps but does not fully cancel that regrowth: +4·10⁻⁴ u′v′, about a tenth of a JND.
   - The pre-registered gate is not relaxed: it is a FAIL.
   - It shows an interaction the gate did not anticipate. A hue rotation *through* neutral makes "chroma never
     rises as L falls" stricter than the physiology may require (Shin et al. report hue-dependent paths).
3. **pcond_c's law is too aggressive for this architecture.**
   - Linear in L, it has already removed 98 % of the chroma at 0.1 cd/m². That erases the mesopic tint (G7), as
     expected.
   - It also removes 73 % of the S1 lamps' chroma, because the median lamp pixel is ~1.5 cd/m² after pixel
     averaging.
   - It stays a legacy reference.
4. **What S1 now looks like** (`sheet_S1.png`, one viewing aid for all panels): a neutral grey night with warm
   lamps.
   - The Purkinje tint is invisible on S1, simply because nothing in the scene lies in the mesopic range. The sky
     is 2.9·10⁻⁴ and the ground is lower still.
   - The kernel's **luminance boost** of dark regions (×2–7.5 at κ = 1; see B1/B3) is still present. It is an
     axis-A effect that B4 deliberately leaves alone.

**Open before any B4 conclusion is final.**
- Verify `s(L) = L/(L + 0.108)` and its conditions (saturation measure, reference level) in Wanat & Mantiuk 2014.
  The paper was not reachable from this container.
- Decide on the G2 FAIL. Two options, both requiring a *new* pre-registration, not an edit of this one:
  - accept it as a physiologically plausible hue-path effect;
  - require the chroma stage to handle hue paths through neutral.
