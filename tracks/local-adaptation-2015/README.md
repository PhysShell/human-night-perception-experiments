# Track: local-adaptation-2015 (Vangorp, Myszkowski, Graf, Mantiuk, "A Model of Local Adaptation", ACM TOG 34(6), SIGGRAPH Asia 2015)

> Written by the coordinator. The worker was stopped after ~4 h with no track files: it produced
> the HDR-VDP-3 runs, obtained the paper PDF (`research-cache/local-adaptation-2015/`, source URL
> not recorded), and never obtained the source code. Everything below is cited to that PDF's text
> extraction (`paper.txt`, line numbers of the two-column pdftotext layout) or marked unknown.

## IDENTITY
Vangorp, Myszkowski, Graf, Mantiuk; ACM TOG 34(6), 2015. The project page
https://resources.mpi-inf.mpg.de/LocalAdaptation/ (paper, video, supplement, slides,
Matlab/Octave source according to the round-8 brief) returns **HTTP 403** to this container.
Licence of the code: unknown (not obtained).

## PURPOSE
An empirical model of the **spatial pooling of luminance adaptation**. The processing chain
(paper Fig. 1 caption, paper.txt l.12–16):
- the optical glare of the eye produces the retinal image;
- local adaptation luminance is computed from it;
- a detection map (visibility thresholds) follows.

Applications named: perceptual error bounds for rendering, HDR backlight resolution, visible
dynamic range, afterimages, gaze-dependent tone mapping (abstract).

## HVS COMPONENTS (from the paper)
- **Optics / glare:** the first stage is a glare spread function or OTF. Candidates fitted:
  CIE 135/1-6 (Vos & van den Berg 1999), Deeley 1991 OTF, IJspeert 1993 OTF, and a custom
  parametric OTF (l.598–606). The well-performing models use the Deeley OTF (l.765–768).
- **Adaptation:** local, pooled in a **non-linear (e.g. log) domain** by a Gaussian mixture.
  The best model (#1) has 11 free parameters; the simplest good one (#7) pools in log
  (l.766–770).
- **Pooling extent:** the detection threshold levels off at a pedestal diameter of **~0.5°**.
  That is smaller than the ≥ 1° of ad-hoc models and larger than Wilson's ~0.1° retinal value
  (l.443–448, Fig. 8).
- **Pupil:** no improvement in the predictions from modelling pupil changes (l.596).
- Rods / mesopic, colour, temporal state, gaze: not modelled in the core model (unknown beyond
  the applications section).

## NATIVE ENVIRONMENT / NATIVE REPRODUCTION
Matlab/Octave (per the brief). **BLOCKED:** the source is only on the MPI page (403); no mirror
was found by the worker (none recorded). Not reproduced.

## COMMON STIMULUS
Not run (native not reproduced). The intended stimuli were S0, S5 and S3.

## ASSUMPTIONS
Absolute luminance in cd/m². The experiments ran on an HDR display with pedestals of 5–2500 cd/m²
(l.442–444), i.e. photopic. Our night levels (sky 4·10⁻⁴ cd/m², lamps ~10² cd/m² per pixel)
lie far outside the fitted range except the lamp cores.

## VALIDATION
Psychophysical experiments on an HDR display (Experiments 1–5), model selection with
cross-validation (l.769–770).

## REUSE
Unknown until the code and its licence are obtained.

## BRIGHT POINT SOURCE
1. The GSF/OTF is applied to the physical image first, producing the retinal image (Fig. 1).
2. **Before adaptation:** glare feeds the adaptation signal. That is the architectural point for
   us, and the opposite of Ocean's "visible post-effect".
3. No tone reproduction in the core model; applications use its output.
4. An OTF/GSF is energy-preserving (per the cited models).
5. Absolute cd/m²: yes.
6. The PSF does not depend on pupil in their fit (l.596); age and wavelength unknown.
7. Not a display model.
8. Not addressed (visibility, not brightness).
9. No temporal PSF.
10. No clipping in the model.

A 0.2° disk at 1–10 000 cd/m² is shown in their Fig. 18: the eye cannot adapt to small
highlights (Fig. 1 caption).

## FAILURES / SURPRISES
The worker spent the time on HDR-VDP-3 under Octave and did not document this track. Worth
asking the user to download the MPI package manually.

## VERDICT
**BLOCKED** (code). As a paper: HISTORICAL REFERENCE, and the architectural reference for
"glare → retinal image → local adaptation".
