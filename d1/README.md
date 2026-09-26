# D1: low-light appearance reproduction

**Question.** How do existing low-light *appearance* models turn a physically calibrated night scene into what a
dark-adapted human would perceive? The display viewer stays mesopic/photopic, so the image has to *suggest* that
experience (Jensen et al. 2000). The goal is not `retina(phone) = retina(world)`.

D0 / D0.1 (`d0/README.md`, `d0/input-semantics.md`) closed the display-renderer question. ACES 2, Mantiuk08,
Reinhard02 and the exposure controls stay as **display/production controls** and are not asked to model night
vision.

## Two independent axes. Not combined in D1.

| axis | question | donors | references (behaviour, no runnable code expected) |
|---|---|---|---|
| **D1-A absolute night appearance** | how does physical scene luminance become "it is dark"? | pcond (V0 baseline), Pattanaik et al. 2000 (`pfstmo_pattanaik00`), iCAM06 APPEARANCE stage (model output before its display step) | Ferwerda et al. 1996; Krawczyk et al. 2005 |
| **D1-B low-light colour / detail cues** | what happens to colour and detail in mesopic/scotopic vision (desaturation, Purkinje/blue shift, loss of acuity)? | Kirk & O'Brien 2011 (implementation to be audited), iCAM06 chromatic path | Jensen et al. 2000 "Night rendering"; Krawczyk et al. 2005 |

**Rules.**
- Donors are run natively, one at a time, on the frozen D0 inputs (`d0/work/inputs`, absolute cd/m²).
- Each donor gets an input contract: what its input numbers mean.
- Every run is labelled NATIVE_DEFAULT, DOCUMENTED_TARGET_CONFIG or SENSITIVITY_RUN.
- No new operator. No combination of a D1-A donor with a D1-B donor, and no D1 donor with a D0 display renderer,
  until each has independent outputs and measurements. The only exception is a fixed, documented display control
  that is needed just to *look* at a scene-referred output; it is labelled as a viewing aid.
- The measurements separate the effects:
  - who makes the night darker;
  - who desaturates;
  - who shifts hue;
  - who removes detail;
  - who changes the lamps.

  D1-B donors are measured in the scene domain against their own input (chroma, hue angle, band-limited contrast).
  D1-A donors are measured as emitted light through `d0/display_model.py`.
- No ranking.

## Status

- [x] D1.0 donor audit + native runtime: Kirk & O'Brien 2011 (`d1/kirk2011/`), Pattanaik 2000 (`d1/pattanaik00/`)
- [x] iCAM06_APPEARANCE (`d1/icam06_appearance/`)
- [x] D1.1 pcond `-a`/`-v`/`-h` checked (`d1/pcond_h/`): 1° foveal grid → degree-scale block/ring artefacts on arcminute material; not usable as acuity/glare cue here
- [x] D1-B1 Filament `scotopicAdaptation()` (`d1/filament/`), verbatim: gates pass; Purkinje-direction hue with local level dependence; lamps stay warm; no desaturation (saturated blue at scotopic levels); dark regions brightened ×2–7.5
- [x] D1-B3 absolute-scale calibration (`d1/filament_b3/`, pre-registered): a = 1 fixed, v = κ·L; admissible κ ≈ 1.1–8.3 (κ = 3 adopted); κ = 1 fails G1 by 3 % (blue patch). Kernel transition width 3.2–3.4 decades ≈ the whole CIE mesopic range. Deep-scotopic chromatic plateau remains (extrapolation limit)
- [x] D1-B4 independent chroma-collapse stage (`d1/chroma_b4/`, pre-registered): provisional PASS with one recorded residual: the Wanat-derived local chroma-collapse model (Eq. 26 verified in the authors' preprint; per-pixel radial u′v′ application is a derived hypothesis, not Eq. 25) passes 7/8 gates; G2 stays FAIL (+4e-4 u′v′ rebound on the yellow patch after its hue crosses neutral). pcond `-c` law erases the mesopic tint and most lamp colour; S1 = neutral grey night + warm lamps. B4.1: only the local (per-pixel) luminance drive works; the global mean and the 1° field fail on the lamps. B4 closed
- [x] D1-A0 axis separation (`d1/axis_a/`, pre-registered): PASS: B supplies chromaticity only, the kernel's luminance gain is discarded
- [x] D1-A1 Wanat 2014 global tone curve (our implementation; CSF = HDR-VDP-2.2.2 full CSF, reproduces the paper's Mt = 0.4 %): synthetic kill tests pass (paper behaviour reproduced); on S1 **FAIL** A1-S3: the curve is flat below ~5e-4 cd/m², so the whole night including silhouettes lands on display black (model thresholds at rho = 2 cpd; S1 is below the paper's validated range). Not tuned
- [x] D1-A2-K0 analytic feasibility gate (`d1/axis_a2_k0/`, pre-registered): NOT KILLED (weak). Base-band energy 0.29 < 0.5 at 73 ppd (0.68 at scene 32 ppd); ideal Eq. 17 at rho_N = 1.14 cpd gives Weber 0.48 (tree-side luminance: 0.00; only 6.6 % of edge energy in that band; m < 0 in finer bands). Lead's prediction not confirmed
- [x] D1-A2 literal Wanat 2014 local contrast (`d1/axis_a2/`, pre-registered): **KILL for S1**. Raw Eq. 17 gives m ≈ −75 in the 2–9 cpd bands (subthreshold source contrast → amplified, inverted noise; poplars brighter than sky, Weber −2.1, 53 % edge reversals); clamp m ≥ 0 returns the night to display black (Weber 0.0003, 5.8 % reversals). No tuning
- [x] D1-A3-K0 pcond as luminance-only axis-A donor (`d1/axis_a3_pcond/`, pre-registered): **both -s and -s -c PASS** all gates recombined with frozen B (sky 0.32 cd/m², poplar Weber 0.56–0.59, lamps 82 cd/m², 0 % reversals, B chromaticity exact, 0.3 % above peak); -s -c reproduces V0 luminance (0.9999). Recommended: -s -c (pcond-derived scotopic luminance model). A3a (Ashraf & Mantiuk 2024) not needed for S1 now
- [x] **Axis A FROZEN**: pcond-derived scotopic luminance mapping (`-s -c`, luminance only). PASS = a deterministic luminance donor satisfying D1's necessary conditions on our scenes; not a claim that Ward Larson/Ferwerda reproduce night brightness appearance exactly
- [x] **Axis C** (near-threshold temporal rod noise, Kellnhofer 2015) is **out of scope for D1**: an optional extension. C0 kill-gate first: if the end product is static (sheets/screenshots), KILL C, because the model's key effect is temporal
- [x] D1 acceptance run (`d1/pipeline/`, pre-registered): **NOT accepted; D1 open for 3 failures only**. PASS P-1/P-2/P-5/P-6/P-7 (S1 reproduces A3-K0; S2 no temporal artefact; S3 bar visible). FAIL P-3/P-8/P-9: no gamut handling in the A0 recombination (S5 twilight sky 4.1 % above peak, saturated clipped blue; F1 red/blue non-monotone at the primary ceilings). FAIL P-4: S4 0.937 / S5 0.968 caused by `-c` (the `-s`-only diagnostic gives 1.000); S3_nobar NaN = gate-definition defect. Fixes need their own pre-registration
- [ ] D1 fixes: R1 gamut-aware recombination, R2 P-4 semantics vs `-c`, R3 P-4 on constant fields
- [ ] cross-donor measurements, contact sheets, findings

## D1.0 results: S1, the physical night (sky 2.9·10⁻⁴ cd/m²). Descriptive only; no ranking.

| donor | axis | what the implementation is | darkness (S1 sky) | colour | lamps | detail | time course |
|---|---|---|---|---|---|---|---|
| pcond V0 (D0) | A | Radiance, Ward Larson et al. 1997 | 0.32 cd/m² emitted on SDR100 | scotopic grey blend | kept apart (0.9′), saturation 0.35 | acuity model off in this path | per frame only |
| Pattanaik 2000 (`pfstmo_pattanaik00`, 3rd-party G. Krawczyk; 2.2.0 = master) | A | receptor / bleaching / appearance equations match the paper; **rods driven by photopic Y** (no Purkinje), display-unaware (fixed 25/125/3.9 cd/m² observer) | 8.5 cd/m² on SDR100, **nearly level-independent** (8.5–13 over ×10⁰…10⁶) | rods add grey: colour lost at night, warm lamps only from ×10⁴ | merged: 60 plateaus, largest 84′, saturation 0 | none modelled | dark/light step direction and timing match the paper (native time course). Defects: `-t` start-up transient (goal factor 5 → 1: 8.5 → 44 cd/m² in 0.5 s); explicit rod-bleaching update unstable above 768 cd/m² at 24 fps (NaN → white; source-verified); zero-valued channels → white |
| iCAM06_APPEARANCE | A + B | authors' code, output before the display step | model sky 1.5·10⁻⁴ → 0.11 of p99.9 (lifted ~3 decades) | all non-lamp regions → one weak reddish hue, no Purkinje-direction shift (floor artefact suspected) | desaturated (0.092 → 0.029) | ground detail 0.05 (bilateral floor, not acuity) | still model |
| Kirk & O'Brien 2011 via Y. J. Lee GIMP plug-in (3rd-party, author-hosted, GPL-3) | B | Purkinje core matches Eqs. 10–13 in form; **RGB→LMSR matrix near rank 1 and fails a photopic white round-trip** (white → blue) | core linear below ~1 Td (no darkening) | **implementation defect**: every pixel lands on one cyan | warm lamps → blue | 0.4–1.0 (G-only projection) | still model |

**What D1.0 establishes.**
- **Axis A (darkness).** Of the absolute-input donors, only pcond puts the physical night near display black
  (0.3 cd/m²). Pattanaik (8.5 cd/m²) and iCAM06 (lifted towards the lamps) render the scene *as seen by a
  dark-adapted observer*, i.e. adapted, not dark. That matches their papers' intent: appearance after adaptation.
  So "night brightness" on the display is again not something these models output. It sits in the step from
  "adapted appearance" to "suggest darkness to a photopic viewer", which none of them implements (Jensen et al.
  2000 treat it separately).
- **Axis B (colour).**
  - No runnable implementation reproduces low-light *colour* shifts. Pattanaik and pcond only desaturate.
  - iCAM06's cast is not a Purkinje shift.
  - The only public "Kirk 2011" code fails photopic colour before any night modelling.
  - Kirk 2011, Krawczyk 2005 and Jensen 2000 remain PAPER_REFERENCE for low-light colour.
- **Detail (corrected).** No donor *run in D1.0* showed a convincing spatial-acuity effect. The detail loss that was seen came from numerical floors. However, Radiance `pcond` contains an explicit acuity-loss model (`-a`: defocus of darker regions) and veiling glare (`-v`). The frozen V0 path runs only `-s -c`, and D1.0 did not validate `-a`/`-v`/`-h`. Checked in D1.1.

Update D1.1: D1-B is no longer a gap. the Filament-derived Cao/Kirk kernel (run verbatim; under an absolute-luminance input convention) passes the photopic identity gate and gives a local, level-dependent Purkinje shift (`d1/filament/README.md`). References only: Wanat & Mantiuk 2014, Shin et al. 2004 / Rezagholizadeh et al. 2016 (no public code found).
