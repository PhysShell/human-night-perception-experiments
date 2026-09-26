# D1-B1: Filament `scotopicAdaptation()` (Cao 2008 / Kirk & O'Brien 2011 lineage)

**Classification: `Filament/Cao-Kirk production approximation`, run VERBATIM. Gates G1–G2 pass. It is not a
reference implementation of Kirk & O'Brien 2011.**

## Provenance
- Source: google/filament, `filament/src/details/ColorGrading.cpp`, `static float3 scotopicAdaptation(float3 v,
  float nightAdaptation)`, commit `ef1a133d6777299ad971a0f9612adf4aad281f46` (2026-09-25). File sha256
  `dd047e80…4c3`. Licence Apache-2.0.
- The in-code references are:
  - Cao et al. 2008, "Rod contributions to color perception: linear with rod contrast";
  - Kirk & O'Brien 2011;
  - J. Patry, "Real-Time Samurai Cinema", SIGGRAPH 2021;
  - Rezagholizadeh & Clark 2013 (log-luminance shift).
- `setup.sh` sparse-clones the pinned commit, verifies the file hash, and extracts the function text **unedited**
  (first/last line match). It compiles it with Filament's own header-only math library (`libs/math/include`) and
  `driver.cpp`, using g++ 15.3.0 (nixpkgs registry, not the repo pin). The `constexpr` matrix construction
  (column order, `inverse`, `transpose`) is therefore Filament's, not a port.
- **What the code says about itself:**
  - k = {0.2, 0.2, 0.3} is "manually tuned for our needs". It follows Kirk & O'Brien's constant values rather than
    Cao's illuminance-dependent ones.
  - `nightAdaptation` ∈ [0, 1] is an artistic control: a linear multiplier on the rod term.
  - The RGB→LMSR matrix is the integral of receptor sensitivities × D65 × Rec.709 primaries, from Filament's
    `tools/rgb-to-lmsr`.

## Input contract
- **Input.** Filament's post-exposure scene-linear Rec.709. The function multiplies it by 380 ("+11.4 EV",
  Patry / Rezagholizadeh & Clark). Filament defines **no cd/m² anchor**.
- **Scale in D1.** `v = linear Rec.709 in cd/m² × s`, with s = 1 as the primary convention (input read as
  cd/m²). s is an explicit axis: G4 shows s = 0.01, 1 and 100. Changing s by 10× shifts the whole level response
  by exactly one decade.
- **Output.** Linear Rec.709 in the same units. There is no display step and no dynamic-range control.

## Gates (no night scene; `gates.py` → `gates.json`, `gates.png`)

| gate | result |
|---|---|
| G1 `nightAdaptation = 0` → identity | **pass**: max error 1.3·10⁻⁶ of the colour's largest channel; white 1 cd/m² → (1, 1, 1). *Criterion revised after the first run:* the per-channel relative error (3.6·10⁻³) occurs only on channels ~10⁻⁶ of the colour's maximum (float32 round-off through the 3×3 inverse) |
| G2 a = 0…1 | **pass**: finite everywhere, black → black, output exactly linear in a (max 2nd difference 9·10⁻⁷) |
| G3 patches × 100…10⁻⁴ cd/m² at a = 1 | no NaN, no negative RGB. Below ~0.01–0.1 cd/m² **every patch converges to one blue hue** (≈ −100° about D65), including red, green and a warm lamp. Chroma does not fall: it converges to 0.14–0.18, and a white becomes chroma 0.15 |
| G4 level dependence of a neutral (s = 1) | the shift is **built into the function** through Cao's gain g = (1 + 0.33/m·(q + k·q_R))^−½, even at fixed a = 1: \|Δu′v′\| ≈ 0.155 below 10⁻³ cd/m², ≈ 0.10 at 0.01, 0.02 at 1, < 0.003 above 100. Luminance also rises, up to ×8.9 for a neutral at scotopic levels ("peak luminance sensitivity increase" in the code comment) |

## Scenes (s = 1; `run_scenes.py` → `scenes.json`, `sheet_S1.png` with one viewing aid for all panels)

| S1 (sky 2.9·10⁻⁴ cd/m²) | a = 0 | 0.25 | 0.5 | 1 |
|---|---|---|---|---|
| sky: Y ×, chroma, hue | ×1.00, 0.005, 58° | ×2.05, 0.105, −102° | ×3.11, 0.130, −102° | ×5.22, 0.148, −102° |
| ground: Y ×, chroma | ×1.00, 0.017 | ×2.63, 0.117 | ×4.27, 0.139 | ×7.53, 0.153 |
| lamps (to 300 cd/m²): Y ×, chroma, hue | ×1.00, 0.092, 45° | ×1.01, 0.087, 43° | ×1.02, 0.081, 41° | ×1.05, 0.071, 36° |
| sky→poplar Weber (0.72 in) | 0.72 | 0.71 | 0.71 | 0.71 |
| detail energy out/in, sky / ground | 1 / 1 | 0.84 / 1.01 | 0.80 / 1.01 | 0.77 / 1.02 |

S4 (real photograph, sky 0.69 cd/m²), a = 1: sky Y ×1.14, chroma 0.061 → 0.078; lamp chroma 0.058 → 0.054.

## What it does, effect by effect (no ranking)
- **Hue: Purkinje direction, correct.** Dark regions move to blue. Bright lamps keep their warm hue, because the
  effect falls with *local* luminance through g. This is the local dependence that the D1.0 donors lacked.
- **Desaturation: none. The opposite happens.** At scotopic levels the output becomes a *saturated* blue. Scotopic
  vision is essentially achromatic, so at full strength the function goes well beyond a perceptual night.
  Presumably this is why Filament exposes `nightAdaptation` as an artistic control.
- **Luminance: coupled.** Dark regions are brightened ×2–7.5 in the scene domain (rod contribution). The donor is
  therefore not a pure axis-B transform. Axis A has to account for it, or measure it separately.
- **Detail: none.** No spatial processing; the DoG changes come from colour/luminance only.
- **Silhouettes: kept.**

## Open design point for D1-B3 (driving the strength from physical luminance)
- The function already depends on level through g, once the input scale s is fixed.
- Driving `nightAdaptation` from a CIE-mesopic adaptation coefficient as well (a = f(L_adapt)) would **count the
  level twice**.
- The two consistent options are:
  1. a = 1 (Cao/Kirk as written), with s = the documented cd/m² anchor and CIE only as a cross-check of where the
     transition lies. With s = 1 the half-effect sits near 0.01–0.03 cd/m², inside the CIE mesopic range.
  2. The input fixed at the adaptation state that CIE's m defines, with a as the only control.
- To decide before any S1 "final" run.
