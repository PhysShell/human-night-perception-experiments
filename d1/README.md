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
- [ ] D1-B still has **no donor with a working low-light colour model** (see below)
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
- **Detail.** No donor models scotopic acuity loss; the only detail loss seen comes from numerical floors.

Next (not started): decide whether D1-B needs an implementation that passes a photopic round-trip, or whether it
stays a documented gap.
