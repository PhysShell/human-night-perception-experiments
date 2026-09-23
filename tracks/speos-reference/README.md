# Track speos-reference: Ansys Speos, Human Vision (Virtual Human Vision Lab)

## IDENTITY

- Ansys Speos (Ansys, now part of Synopsys) is a commercial optical simulator. "Human Vision" is a
  **post-processing viewer** for Speos luminance maps (*.xmp):
  - the stand-alone **Virtual Human Vision Lab** (VHV Lab) [S1];
  - the **Live Preview** "Human Vision" display modes [S5];
  - the "Human Vision" functions of the Virtual Reality Lab [S6].
- The current public help is Release 2026 R1 (v261) at ansyshelp.ansys.com [S1].
- **Several key pages are login-only and BLOCKED:** "Vision Parameters", "Using Vision Parameters",
  "Parameters of Vision Parameters", "Look At", "Simulation Parameters", and VR Lab "Human Vision",
  "Using Human Vision" and "Parameters of Human Vision". Each shows "The information contained in that
  page are private. To access the private content, log into the Ansys Help." [S2]. This holds in v261,
  v252 and v242; the v232 and older paths do not exist.

## PURPOSE

"The human eye has a great dynamic to detect levels of luminance going from 10⁻⁶ cd/m² to 10⁸ cd/m².
... a monitor has a dynamic lower than one hundred. With Virtual Human Vision Lab, you can reproduce
visual appearance of modeled scenes on this media. Virtual Human Vision Lab restores contrasts
perceived by an observer placed in the scene." [S1]

## HVS COMPONENTS (I2: feature matrix)

| Feature | What public documentation says | Source |
|---|---|---|
| Adaptation, Local | "defines the accommodation on a fixed value of the luminance map"; a user-entered luminance (dialog shows e.g. 1234 cd/m²) | S5, S3 Fig. 10 |
| Adaptation, Dynamic Adaptation 2019 | "enables the adaptation of the human eye. It models the fact that the eye adapts locally as the viewer scans the different areas of the luminance map"; the dialog shows a greyed, computed luminance | S5, S3 Fig. 10 |
| Automatic adaptation (Live Preview) | "base the adaptation on the maximum value of the result", or set a custom value | S5 |
| Visibility threshold | "All luminance map fields having luminance lower than the detection threshold of the human eye are not displayed. This threshold depends on the luminance to which the eye is adapted." | S1 |
| Photopic / mesopic / scotopic | scotopic below ~0.001 cd/m² (no colour); photopic above ~5 cd/m² (rods saturate); mesopic "between 0.005 cd/m² and 5 cd/m²". Vision mode "is estimated to starting from the values of the displayed luminance map"; in mesopic, colours appear "first red color, then orange, green and last blue" as luminance rises | S1, S4 |
| Vision-mode evaluation basis | Average value / **Maximum value** / Each point of the xmp; maximum recommended for night driving | S3 Fig. 11 |
| Glare | "Glare is the contrast lowering effect of stray light ... forms a veil of luminance ... light sources located in periphery of the visual field are diffused by various diopters constituting the human eye, like by the aqueous humor"; models **Vos, 1984** and **Holladay, 1926** | S7, S3 |
| Temporal adaptation | "Time adaptation": an AVI from previous adaptation L0 (cd/m²) to the current map. Dark adaptation "can take until thirty minutes" (time compressed, real time shown); light adaptation "takes few seconds"; "only uses the dynamic adaptation mode" | S8 |
| Observer | age, glare, eye deficiencies, observation conditions (from a CADFEM brochure via search listing; brochure PDF 403) | S10 |
| Acuity, depth of field | named in marketing: "emulating physiological properties of the human eye like the glare, depth of field, acuity and temporal adaptation" | S9 |
| Display model | Monitor preferences: primaries, gamma (fitted, SMPTE 2084, or custom 18-point) and **White Point Luminance**. The "1:1 scale" option saturates everything above the white point. HDR10 / SIM2 / JVC HDR are supported; with SIM2 in VR Lab "it is not possible to activate Human Vision functions as Glare". "Virtual Human Vision Lab takes into account the luminance of the used screen." | S11, S1 |
| Spectrum | XMP maps may be spectral or colorimetric; colour management with gamut clipping or "maintain lightness and hue" | S5, S3 |
| Gaze | none (the Dynamic 2019 model scans the map; no tracker) | S5 |
| Legibility / visibility, UGR | separate analysis tools | S1 |

## I3: recommended order of operations (as documented)

This is the workflow order from S3, the Ansys blog by Mike Grove, 2023-02-28.

1. **Sensor**:
   - "A 'smooth' result is a minimum of 1920 pixels ... for the longer side of the sensor";
   - "around 4,000 pixels" if zooming;
   - square pixels;
   - for radiance sensors, frame close to the object and far from the eye.
2. Meshing tolerances.
3. Direct and inverse simulation choice. Run length by design phase (rays or passes).
4. Separate simulations per lamp function, combined with map union.
5. Post-processing:
   1. **colour management** ("maintain lightness and hue" for tail and stop lamps);
   2. **adaptation** (Dynamic Adaptation 2019 for wide FOV, Local for narrow FOV);
   3. **glare** (Vos 1984);
   4. **vision-mode evaluation on the maximum value**.

The internal processing order of the VHV Lab algorithms (glare before or after adaptation or tone
reproduction) is **not public**: those pages are login-only [S2]. **UNKNOWN.**

## I4: default / recommended glare model and why

- The dialog screenshot shows the Glare Effect enabled with **Vos, 1984** selected [S3 Fig. 10].
- "The Holladay, 1926 glare effect setting offers a faster, simpler calculation; however, given
  computing capabilities today, Vos, 1984 is our recommended setting" [S3].
- "If you're short on time, use Holladay, 1926 instead to show brightness in a realistic manner" [S3].

## I5: what Speos says about resolution, noise, glare, adaptation, FOV and night driving

- **Resolution**: a minimum of 1920 px on the long side, about 4000 px for zooming. "If you're
  viewing results with 1080-pixel resolution on a 4K monitor, there's going to be noticeable
  pixelation" [S3].
- **Noise and glare**: "If your model has noise (e.g., pixels with high luminance), Vos, 1984 may
  generate an undesired sparkling effect. To negate this effect, you should always include an
  environmental light source, even if it's a low level of light. In parallel, increasing the number
  of rays will also help eliminate noise." [S3]
- **Adaptation versus FOV**: "The dynamic adaptation 2019 type setting is best practice when your
  sensor has a wide field of view (similar to our actual eyes) so the overall luminance is properly
  considered. When the sensor has a narrow field of view, local adaptation is preferred ... since the
  reduced field of view contains only a fraction of the overall luminance a real eye would see." [S3]
- **Night driving**: "Maximum value is best for nighttime driving conditions or other low luminance
  scenarios because average value can be low, resulting in mesopic or scotopic vision." [S3]
- **Display**: set the White Point Luminance to the real maximum of the screen. With 1:1 scale,
  "all information from the map that is above 100cd/m2 is saturated to white" (for a 100 cd/m²
  white point) [S11].

## I6: public videos showing Human Vision output

These were found and recorded; **not downloaded, not watched, no timestamps measured**. That is
deliberately left for manual viewing.

- "ANSYS SPEOS l ARRK Rear Light in Human Vision", channel ANSYS OPTICAL SOLUTIONS (@optis),
  https://www.youtube.com/watch?v=pMXg0_1FY3A (oEmbed metadata) [S12].
- "Control panel lighting simulation - Ansys Speos Demo", Ozen Engineering,
  https://www.youtube.com/watch?v=7yw3OKuYPDM [S12].
- The webinar "Relying on What You See: Luminance Matching and Human Vision" is registration-gated
  and was **not** accessed [S9].
- The CADFEM video page "Consider human vision with Ansys SPEOS" returns 403.
- Still images available: S3 Figures 10–12 (dialog screenshots and a result image) at
  https://images.ansys.com/is/image/ansys/{preferred-adaption-glare-settings, vision-mode-evalution,
  example-simulation-results} (cached in research-cache/speos-reference/).

## NATIVE ENVIRONMENT / NATIVE REPRODUCTION

- **BLOCKED.** Speos is commercial, licensed software.
- The detailed parameter pages require an Ansys Help login.
- The optics.ansys.com knowledge-base articles return HTTP 403 to curl and WebFetch:
  - https://optics.ansys.com/hc/en-us/articles/30535212484115-Simulation-Parameters-for-Visualisation-Best-Practices
  - https://optics.ansys.com/hc/en-us/articles/8314838263699-Planar-OLED-Human-Vision
  Their content is known only via search snippets that match S3 text.

## COMMON STIMULUS

Not run.

## ASSUMPTIONS

- Absolute luminance maps in cd/m² (XMP), optionally spectral.
- Display photometry from the Monitor preferences (white point luminance, gamma, primaries).
- Viewing geometry: the sensor FOV matters for adaptation choice [S3]. No px/deg parameter for glare
  is public.

## VALIDATION

None public. The blog and webinar are vendor best practice, not validation.

## REUSE

Proprietary. Short quotations only, for research notes.

## FAILURES / SURPRISES

- **Vendor-documented: Monte-Carlo hot pixels + Vos glare = "sparkling".** The glare step treats a
  single noisy high-luminance pixel as a real source and spreads it into a visible veil. The vendor
  fix is an ambient source (raising adaptation) and more rays.
- This is directly relevant to our case: an unresolved lamp *is* a few very bright pixels. With any
  PSF glare, pixel-level noise and sub-pixel phase would make the halo "breathe" from frame to frame.
  This is an artefact mechanism, not a physiological one.
- Holladay 1926 is a veiling-luminance (disability glare) formula, and Speos offers it as a faster
  alternative. How Speos turns it into an image is not public.

## BRIGHT POINT SOURCE

1. Where the PSF is applied: in the VHV Lab / Live Preview post-process on the luminance map (Vos
   1984 or Holladay 1926 veil) [S3, S7]. The exact step is unknown.
2. Before/after adaptation: **unknown** (pages private).
3. Before/after tone reproduction: **unknown**.
4. Energy preserved: **unknown**.
5. Absolute-luminance aware: **yes**. cd/m² maps; vision mode is derived from map values; monitor
   white point in cd/m².
6. PSF dependence: an age parameter is reported (S10, weak). Pupil, wavelength and field angle are
   unknown. The vision mode (photopic/mesopic/scotopic) is set from the map's average, maximum or
   per-point value.
7. HDR source on a display: adaptation (local fixed value or Dynamic 2019) plus the monitor white
   point. Optional 1:1 scale saturates values above the white point. HDR10 is supported in VR Lab.
8. Halo and perceived brightness: not documented.
9. Temporal PSF variation: none documented. Only the time-adaptation AVI.
   - Temporal *artefact*: MC noise makes Vos glare "sparkle" (vendor statement).
10. Clip before or after convolution: unknown.

## VERDICT

**BEHAVIORAL ORACLE** (documentation and best-practice level). No pixels can be obtained here. Its
useful content for us:
- Vos 1984 is the recommended PSF;
- the explicit warning that PSF glare turns per-pixel noise into sparkles;
- adaptation choice depends on FOV;
- vision mode for night scenes is set from the maximum.
