# D1-B3 pre-registration: absolute-scale calibration of the Filament-derived Cao/Kirk kernel

Committed **before** the κ sweep is run. Prior knowledge that must be disclosed:
- D1.1 G4 already showed the neutral-patch curve at κ = 1, 0.01 and 100 (`d1/filament/gates.json`).
- At κ = 1: |Δu′v′| 0.156 (plateau, L ≤ 10⁻³), 0.10 at 0.01, 0.021 at 1, 0.0024 at 100 cd/m².
- κ shifts that curve along log L without changing its shape. These thresholds were written knowing this.

**Name of the object under test.** "Filament-derived Cao/Kirk kernel under an absolute-luminance input
convention": `scotopicAdaptation(κ·L_rgb, a = 1)`, with L_rgb linear Rec.709 in cd/m². This is **not** "how
Filament models cd/m²". Filament feeds the function exposure-adjusted renderer values.

**Fixed.** a = 1. No CIE-m → a mapping. CIE 191:2010 / 257:2026 is used only as an external envelope: the mesopic
range is 0.005–5 cd/m².

**Sweep.**
- κ ∈ {0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100}.
- Patch luminance L ∈ 10⁻⁴…10² cd/m², 61 log steps.
- Patches: D65 neutral, red, green, blue, cyan, warm lamp (1, 0.55, 0.2), yellow.

**Effect measures per patch and L** (output vs input of the same patch):
- E = |Δu′v′| (primary);
- Y_out / Y_in;
- Δhue (° about D65);
- output chroma;
- ΔE*uv, CIELUV with white = D65 at Y_n = Y_in;
- rod-induced RGB increment |out − in| / |in|.

**Definitions (per patch, per κ).**
- E_plat = E at L = 10⁻⁴ (the low-level plateau).
- L50, L10 = the luminances where E falls to 50 % and 10 % of E_plat (log interpolation). L90 is defined likewise.
- width = log10(L10 / L90).

**Gates.** All apply per κ; "all patches" means every patch except where a gate says "neutral".

| gate | criterion |
|---|---|
| B3-G1 photopic suppression | E(5 cd/m²) ≤ 0.10 · E(0.005 cd/m²), for all patches |
| B3-G2 mesopic activity, smooth | neutral: L50 ∈ [0.005, 5] cd/m² **and** width ≥ 1 decade (not a step) |
| B3-G3 ordering | E(0.005) > E(0.05) > E(0.5) > E(5), strictly, for all patches |
| B3-G4 highlight preservation | warm lamp: E at 200 cd/m² ≤ 0.10 · E of the neutral at 0.01 cd/m² |
| B3-G5 scene consistency | on S1 at the same κ: median E over lamp pixels ≤ 0.25 · median E over sky pixels |
| no-transition-escape | L50 (neutral) ∉ [10⁻⁶, 10⁻⁴] and ∉ [100, 500]; implied by G2, listed for clarity |

**Outcome rule.**
- **κ admissible** if it passes G1–G5.
- **At least one admissible κ:** report the admissible interval. If κ = 1 lies inside, record it as an *empirical
  coincidence*, not as a property of Filament.
- **No admissible κ:** the kernel's intrinsic luminance response is inconsistent with the target physical scale.
  No CIE-m patch is added; the next step is Kirk / Wanat / Shin as references (Wanat/Mantiuk possibly D2).
- **Expected from the κ-shift property** (stated before running): G2, G4 and G5 are satisfiable by choosing κ.
  G1 is **not** satisfiable by κ, because it tests the curve's width (a fall to 10 % within 3 decades). G3 holds
  for every κ if the curve is monotone.
