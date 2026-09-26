# D1-B4 pre-registration: an independent scotopic chroma-collapse stage

Committed **before** any B4 code is run. Nothing below is tuned after looking at S1.

## Frozen upstream
- The Filament-derived Cao/Kirk kernel, a = 1, κ = 3 (D1-B3; no re-calibration): f = scotopicAdaptation(3·L_rgb)/3.
- B4 acts on f only. The kernel's hue shift and its luminance boost are *not* touched. The luminance boost remains
  an axis-A matter, reported but not corrected here.

## The chroma stage (the same for every candidate; only the weight law differs)
- For each pixel: Y_f = Rec.709 luminance of f.
- The output is `out = Y_f·(1,1,1) + w·(f − Y_f·(1,1,1))`, mixing towards the D65 white of the same luminance in
  linear Rec.709.
- This preserves Y exactly and preserves the u′v′ hue angle exactly: an additive mixture lies on the straight line
  to white.
- It cannot create negative RGB when f ≥ 0 and 0 ≤ w ≤ 1.
- **Target.** The ratio of u′v′ chroma (distance from D65) out/f equals the candidate's target saturation t(L). w
  is found per pixel by bisection; the u′v′ distance is monotone in w along the line.
- **L = the pixel's physical input luminance in cd/m²**, not Y_f, which is boosted and κ-scaled.
- **Sensitivity variant, reported only.** w = t(L) directly (linear-RGB weight).

## Candidates

| id | t(L) | role | source status |
|---|---|---|---|
| none | 1 | baseline: current Filament | — |
| pcond_c | clip((L − 5.62·10⁻³)/(5.62 − 5.62·10⁻³), 0, 1) | legacy / aggressive reference | **verified** in Radiance `src/px/pcond3.c` `scotscan()` and `pcond.h` (BotMesopic 5.62e-3, TopMesopic 5.62). Only its colour weight is used: pcond itself also replaces luminance with scotopic luminance, which is not taken here |
| wanat14 | L / (L + 0.108) | main psychophysical candidate | Wanat & Mantiuk 2014, TOG 33(4), saturation-matching fit against a 200 cd/m² reference. **NOT VERIFIED HERE**: the paper is not reachable from this container (ACM closed, author pages 404, Bangor repository 403). The constant is taken from the project lead's reading and must be checked against the paper before B4 conclusions are called final |

Shin et al. 2004 / Rezagholizadeh et al. 2016 are a qualitative reference only (chroma → neutral with falling
luminance, hue-dependent; bluish stimuli may keep or gain lightness).

## Test material
- Patches: neutral, red, green, blue, cyan, warm lamp (1, 0.55, 0.2), yellow.
- L = 10⁻⁴…10² cd/m² (61 log steps), plus 200 cd/m².
- S1.

## Gates (per candidate)

| gate | criterion |
|---|---|
| B4-G1 photopic identity | L ≥ 100 cd/m²: chroma_out / chroma_f ≥ 0.99, all patches |
| B4-G2 monotone collapse | chromatic patches (not neutral): chroma_out does not increase as L decreases, for L ≤ 5 cd/m² (tolerance 10⁻⁴) |
| B4-G3 scotopic collapse | L ≤ 10⁻³ cd/m²: chroma_out ≤ 0.01 (u′v′), all patches including neutral |
| B4-G4 Purkinje hue kept | \|hue_out − hue_f\| ≤ 0.5° wherever chroma_out ≥ 0.002 |
| B4-G5 luminance kept | \|Y_out / Y_f − 1\| ≤ 10⁻⁴ |
| B4-G6 numerics | finite, no negative RGB |
| **B4-G7 negative gate: the Purkinje shift is not erased** | neutral at 0.1 cd/m²: Δu′v′(out, input) ≥ 0.3 · Δu′v′(f, input). The mesopic tint must survive; "grayscale from the original" fails |
| B4-G8 scene | S1: median over lamp pixels of chroma_out / chroma_f ≥ 0.9, **and** median sky chroma_out ≤ 0.01 |

**Outcome.**
- A candidate that passes G1–G8 is supported *as a chroma law on this material*. No combined renderer is claimed.
- **Expectations, stated before running:**
  - none fails G3 and G8 (sky);
  - pcond_c fails G7, because its weight at 0.1 cd/m² is ≈ 0.017;
  - wanat14 is expected to pass. G2 is the uncertain gate, because Filament's own chroma rises at low L for some
    patches.

**Post-run note (not a change to the gates above).** The constant was later verified in the authors' preprint (Eq. 26, k3 = 0.108; see README). The candidate is renamed "Wanat-derived local chroma-collapse model".
