# D1-B4.1 pre-registration: which luminance drives the Wanat-derived chroma law?

Committed **before** running. This is a sensitivity check, not a new model, and it fits no parameters.

**Why.** Wanat & Mantiuk 2014 fitted s(Y) = Y/(Y + 0.108) (Eq. 26) against the **mean luminance of an image**.
B4 applied it to the **per-pixel** physical luminance.

**Fixed.**
- Upstream: the Cao/Kirk kernel, a = 1, κ = 3.
- The B4 chroma stage: radial u′v′ attenuation to t, preserving Y and hue.
- t = L_drive / (L_drive + 0.108).
- Only L_drive changes.

| variant | L_drive |
|---|---|
| local | the pixel's physical luminance L(x, y) (= B4) |
| global | the arithmetic mean of the scene's physical luminance, one value per image (the paper's independent variable) |
| field | the Gaussian-weighted arithmetic mean of the physical luminance with σ = 1° of *scene* visual angle (S1/S0: 32 px, S4: 32 px, from the manifest). Declared once, not tuned |

**Scenes.** S1, S0 and S4 (S4: numbers only; images not committed, Fairchild licence). Uniform patches are
identical for all three variants by construction, because local = field = global on a uniform field. The patch
results of B4 (including the mesopic Purkinje tint) therefore carry over unchanged. This is stated rather than
re-measured.

**Measured.**
- S1: median lamp chroma out/kernel, median sky chroma, median ground chroma.
- S4: sky chroma and hue, lamp chroma ratio.
- S0: sky and ground chroma.

**Criteria** (the B4-G8 thresholds, re-used unchanged): S1 lamps ≥ 0.9 **and** S1 sky ≤ 0.01.

**Expectations, stated before running.**
- global fails on S1. One value for the whole scene sits between the dark sky and the lamps, so it neither
  collapses the sky nor keeps the lamps.
- field keeps the sky collapsed. It probably desaturates the lamps too, because they are sub-degree sources inside
  a dark 1° field.
- local passes, as in B4.
- If local is the only variant that passes, the literal transfer of Wanat's independent variable (mean image
  luminance) to a scene-referred HDR image with a large local dynamic range is shown to be unsuitable. That is a
  useful negative result.
