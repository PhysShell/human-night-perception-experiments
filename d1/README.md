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

- [ ] D1.0 donor audit + native runtime: Kirk & O'Brien 2011 (`d1/kirk2011/`), Pattanaik 2000 (`d1/pattanaik00/`)
- [ ] iCAM06_APPEARANCE outputs (from the D0.1 ladder driver) as a D1-A donor
- [ ] measurements, contact sheets, findings
