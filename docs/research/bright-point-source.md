# The unresolved bright point source: how each system represents it (round 8)

**The problem.** A distant road lamp has an angular size below 0.1′. It delivers ~9·10⁻⁵ lx at
the eye (800 cd at 3 km) against a night sky of 4·10⁻⁴ cd/m². After pcond it is ~30× above
display white. It should not look like:
- a square pixel (M2.5, fixed in M2.6 by forming the image at the display first);
- an arbitrary bloom sprite;
- a huge clipped white disc (M1, calibrated Spencer PSF at a 100:1 display).

Each track answered the same ten questions; the details are in each `tracks/<donor>/README.md`,
section BRIGHT POINT SOURCE. Answers are from code/doc/paper per the track's `sources.md`.
"n/a" = not applicable, "?" = undocumented.

| system | 1 where the PSF is applied | 2 vs adaptation | 3 vs tone reproduction | 4 energy | 5 absolute | 6 PSF depends on | 7 HDR source on the display | 8 halo raises brightness? | 9 temporal PSF | 10 clip vs convolve |
|---|---|---|---|---|---|---|---|---|---|---|
| **Spencer 1995** (paper) | radiometric image | varies with adaptation state | before | preserved | yes | adaptation, pupil, wavelength, age | convolve, then tone map | **yes** (7-subject experiment) | no | convolve, then clip |
| **Ward 1997 / `pcond -v`** (baseline, OFF) | 1° grid veil (θ⁻²) | added before, raises adaptation | before | ~preserved | yes | none | veil + histogram mapping | not tested | no | veil before clip; **no sub-degree halo** |
| **Pattanaik 1998** (paper) | Westheimer + Spencer PSF at 130 px/deg | before gain control | before | preserved | yes | adaptation | multiscale model | ? | no | before |
| **Krawczyk 2005** (thesis) | Gaussian pyramid level on adaptation-scaled luminance (Deeley) | after adaptation | before the local sigmoid | not preserved (added) | yes | pupil of the adapting luminance | sigmoid, then 8 bit | claimed via Spencer, not tested | no | clip only at quantisation |
| **Ritschel 2009 temporal glare** (paper + co-author demo) | paper: whole HDR image; demo: bright-pixel overlay | only via pupil size | before gamma | **not** preserved (∝D^1.1 in demo) | nominal | pupil (hippus), wavelength | gamma, then clip | **yes**: dynamic > static > none (paper p. 190) | **yes**: hippus; paper also particles, lashes, blinks | paper: float; demo: 8-bit source |
| **Vangorp 2015 local adaptation** (paper; code BLOCKED) | GSF/OTF (Deeley / CIE 135) on the physical image → retinal image | **before: glare feeds adaptation** | no TM in the model | preserved | yes | not pupil (their fit) | n/a | n/a (visibility, not brightness) | no | no clipping |
| **Jacobs 2015 GazeHDR** (paper + author video) | **no PSF** | n/a | n/a | n/a | yes | n/a | Naka–Rushton compression → source saturates; gaze-locked afterimage | afterimages: no significant gain (p = 0.449) | no | n/a |
| **Tariq 2023 perceptually adaptive TM** | **no PSF** | n/a | n/a | not preserved (saturates) | yes | n/a | global curve; lamp barely affects it (pixel-average pooling) | no halo | parameter smoothing only | n/a |
| **ISETBio/ISETCam** (Octave, partly run) | oiCompute on spectral radiance | before (outer segment) | no tone mapping | preserved | yes | pupil, wavelength (field angle only in cMosaic) | n/a (retina, no display) | n/a | **no** | no clipping |
| **VisSimFramework** (code audit) | compute pass, HDR or LDR phase | HDR mode: before | HDR mode: before; demo default after | ~preserved (1 % tail dropped) | no | pupil, wavelength, field angle, focus | fp16 → ACES → clip | n/a | no | HDR mode: convolve then clip; **demo default clips first** |
| **VSS Stuttgart** (run) | none for the normal eye | none | after tone mapping | blur yes, "bloom" adds energy | no | none | 8-bit in and out | n/a | no | clip first |
| **OpenVisSim** (audit) | none (LDR bright-pass bloom) | none | after | not preserved | no | none | LDR | n/a | no | clip first |
| **Ocean** (docs) | pixels > 10× image mean, XYZ buffer | after the adaptation gains | glare, then Drago (order partly undocumented) | ? | partly | photopic / mesopic / scotopic, age, dispersion | glare + Drago | not addressed | no | threshold before convolution |
| **Speos** (docs, blog) | luminance-map post-process | ? | ? | ? | yes | age (weak source) | adaptation + white point | ? | no; but Monte Carlo noise makes glare "sparkle" | ? |
| **HCIPy** (atmosphere) | telescope pupil/focal plane | n/a | n/a | preserved | no | wavelength, aperture | n/a | n/a | **yes**, atmospheric | n/a |
| **Mitsuba 3** | none (reconstruction filter only) | n/a | n/a | preserved | if units given | n/a | clipped when writing PNG | n/a | no | clip at output |

## What the rows say

1. **Every model that treats the eye as an optical system puts the PSF on the physical
   (scene/retinal) radiance, before tone reproduction, and preserves energy.** This holds for
   Spencer, Pattanaik, ISET, and VisSimFramework in HDR mode. Every system that clips first is
   an LDR effect (VSS, OpenVisSim, VisSimFramework's demo default, Ritschel's demo). So the
   order is not in dispute: **convolve radiance, then map to the display.** Our baseline
   already did that in M1; the result was a 0.3–0.5° disc.
2. **Nobody has solved the step after that.** Once the halo is in the radiance, a 100:1
   display clips everything above white. Spencer's own answer is perceptual: the halo is there
   *so that* the source reads brighter than white (his 7-subject test; Ritschel repeats it for
   temporal glare). The systems then differ:
   - Ocean gates the PSF to pixels above 10× the mean;
   - Speos and Ocean use adaptation plus a white point;
   - GazeHDR and Tariq 2023 let the source saturate with no halo.

   **So the "huge disc vs square pixel" choice is not settled by any donor; it is a display
   design decision.**
3. **The eye's own optics are small for a point at night.** ISET (Thibos aberrations, 3–7 mm
   pupil) puts 98.8 % of a point's energy in a 3 × 3 block at 32 px/deg: encircled energy
   1.2–2.4′ for warm sources, ~5′ for blue. The big halo in Spencer and Vos is the **wide-angle
   straylight** term (θ⁻²), not the aberration core. So "the lamp looks like a small bright
   point with a faint wide veil" is what the optics predict. The 2 × 2-pixel core at 74 px/deg
   from M2.6 is already about optics-sized (1.6′).
4. **"Breathing" candidates, measured:**
   - **Eye:** Ritschel's pupil hippus is a 3–5 % halo pulsation below ~0.6 Hz with 0.07 px
     centroid motion (co-author demo). Small, and its perceptual weight is only claimed for
     bright sources.
   - **Atmosphere** (HCIPy + textbook formulas, our geometry, 6 mm pupil): image motion
     0.01–0.09′, seeing ≤ 0.2′, both sub-pixel. **Scintillation is large**: σ_I² 0.1–1.7,
     often saturated beyond 3 km, the pupil averages almost nothing, at 6–90 Hz. That is mostly
     above what a 24 fps clip can show.
   - **Display:** the M2.6 residual. Clipped cores on the display grid modulate ~11 % as they
     move.
   - Of the three, **only scintillation is physically large for distant lamps**. A two-formula
     caveat applies (NOT VERIFIED in tracks/hcipy/sources.md).
5. **ColorVideoVDP and FovVideoVDP** rate a point moving 1 px in 2 s at 9.8–9.9 JOD against a
   static frame on both targets. The display-grid modulation of a single point is near the
   visibility threshold on PHONE and DESKTOP.
