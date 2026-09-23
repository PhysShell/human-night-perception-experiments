# temporal-glare-2009 — Ritschel, Ihrke, Frisvad, Coppens, Myszkowski, Seidel, "Temporal Glare" (EG 2009)

## IDENTITY
- Paper: T. Ritschel, M. Ihrke, J. R. Frisvad, J. Coppens, K. Myszkowski, H.-P. Seidel, *Temporal Glare:
  Real-Time Dynamic Simulation of the Scattering in the Human Eye*, Computer Graphics Forum 28(2) (Proc.
  Eurographics 2009), pp. 183-192, doi:10.1111/j.1467-8659.2009.01357.x. Author copy retrieved from co-author
  Frisvad's DTU page (sources.md T1). Page numbers below are the journal page numbers printed on the PDF.
- Project page https://resources.mpi-inf.mpg.de/hdr/temporalglare/ with the 600-/120-frame PNG glare
  billboard sequences and HQ AVI/MPEG video: **BLOCKED** (HTTP 403; Wayback copy exists but web.archive.org is
  blocked by the egress policy; the author's YouTube upload https://www.youtube.com/watch?v=5ewKMOodT1Y refuses
  anonymous download). The user can fetch these manually.
- **Author code found and run instead** (sources.md T6, T8): J. R. Frisvad's (co-author) `glare_demo`
  (C++/OpenGL/GLSL, 2009-2014, "a partial implementation of the glare method described in the paper":
  human aperture model, Fresnel diffraction, chromatic blur, convolution, pupillary hippus) and his Matlab
  `hippus.m` (Eq. 1). No licence text ("Copyright (c) DTU Informatics 2009") -> treated as all rights
  reserved: kept only in research-cache/, nothing of it copied into tracks/.

## PURPOSE
Real-time simulation of *dynamic* glare (bloom/veil, ciliary corona, lenticular halo) for bright sources in
HDR images/animation, to raise perceived brightness on LDR displays (abstract, p. 183; study p. 190).

## HVS COMPONENTS (paper) and what the runnable demo actually contains
| component | paper (page, eq.) | glare_demo (glare.cpp line) |
|---|---|---|
| optics: aperture diffraction | Fresnel diffraction of a pupil-plane aperture image, L_i = K F{P E}, K = 1/(lambda d)^2, E = exp(i pi (x^2+y^2)/(lambda d)) (p. 187, Eq. 3; App. A p. 192) | yes: aperture drawn in a 512^2 texture (N = 10 mm), complex E multiplied in the shader, GPU FFT; **shows the amplitude \|F\|, not \|F\|^2** (FFT.cpp display1_frag `length(ffts.rg)`) |
| cornea | static large sparse particles, 25-30 % of scatter (p. 185) | 200 static points (l. 45) |
| pupil + hippus | h(t,p) = p + noise(t/p) (p_max/p) sqrt(1 - p/p_max), p_max 9 mm, 3-octave value noise (p. 185, Eq. 1); mean p = 4.9 - 3 tanh(0.4 (log L_v + 1)) (Moon & Spencer, Eq. 2) with L_v the "time-damped average screen intensity" (p. 186) | yes: Eq. 1 with Perlin-type noise x `contrast` (l. 84-105, 89, 390, 393); L_v = mean of the 8-bit overlay PNG |
| lens: fibre grating -> lenticular halo; nucleus particles; accommodation micro-fluctuation motion (<0.6 Hz and 1.3-2.1 Hz components, 17x17 mass-spring deformation, 750 particles, 200 gratings) | p. 186, Fig. 4 | static grating of 200 radial lines + 400 static nucleus points (l. 46-47); **no lens motion** |
| vitreous | particles in a damped rigid body driven by random saccade forces, projected to the pupil plane (single-plane approximation) (pp. 186-188) | **absent** |
| eyelashes / blinking / squinting | animated bitmaps (p. 187) | **absent** |
| retina | approximated by fewer, larger particles (p. 187) | implicit (particle sizes) |
| wavelength | chromatic blur: F_lambda2(x) = F_lambda1(lambda1/lambda2 x), n = 32 samples 380-770 nm, XYZ, E computed once at 575 nm (p. 188) | 89 samples 390-830 nm of Stockman-Sharpe cone-based "RGB" (spectrum2rgb.h), lambda1 = 492 nm, extra gain x2 on G and B (l. 509-511) |
| adaptation | only through pupil size (Eq. 2) | same, from the overlay mean |
| rods/cones, mesopic, acuity, gaze | no | no |
| temporal state | hippus, lens + vitreous particle motion, blinking (Table 1 p. 185) | hippus only |
| display | "gamma mapping (gamma = 2.2)" after convolution (p. 190) | divide by max_intensity (includes 1/pupil area in glare view, l. 531), pow(x, 0.4545) (l. 165), 8-bit window |
| spectrum | XYZ from 32 spectral samples | cone-fundamental-based RGB, treated as display RGB |

## NATIVE ENVIRONMENT
Windows, Visual Studio 2010+ project, GLUT + GLEW, OpenGL 2.1 GLSL, NVIDIA GPU (paper: GeForce 8800 GTX,
p. 190; demo reference screenshot https://people.compute.dtu.dk/jerf/code/images/glare_demo.png shows 115.9 fps
PSF view, 63.8 fps glare view). Here: Linux, nixpkgs gcc 15 + freeglut 3.8 + glew 2.3 + Mesa 26.2 llvmpipe
(software) under Xvfb; Octave (nixpkgs) + gnuplot for hippus.m.

## NATIVE REPRODUCTION — **PASS** (qualitative; see caveats)
Commands (repo root):
```
tracks/temporal-glare-2009/build_glare_demo.sh                 # unmodified sources + 1 documented portability rename
tracks/temporal-glare-2009/run_glare_demo_native.sh research-cache/temporal-glare-2009/native_glare glare 240 0.4
tracks/temporal-glare-2009/run_glare_demo_native.sh research-cache/temporal-glare-2009/native_psf psf 540 0.4
tracks/temporal-glare-2009/trace_glare_demo_psf.sh research-cache/temporal-glare-2009/trace_psf 90
tracks/temporal-glare-2009/dump_psf_floats.sh research-cache/temporal-glare-2009/trace_psf 48   # stopped at 27 min, 36 dumps
nix shell --inputs-from . nixpkgs#octave nixpkgs#gnuplot -c octave --no-gui -q tracks/temporal-glare-2009/run_hippus_native.m
tracks/temporal-glare-2009/py.sh tracks/temporal-glare-2009/analyze_native.py
```
Example (B6): the demo's own bundled example (candle.png + overlay.png, 512x512) exactly as shipped, i.e. the
PSF applied to the bright pixels of the authors' own example scene as intended.
Two things were needed to make the author code run correctly on Linux/Mesa, both documented in the scripts:
1. **Portability rename**: Convolution.cpp names two GLSL samplers `input`/`output`, reserved words that Mesa
   rejects (NVIDIA 2009 accepted them) -> renamed to `in_tex`/`out_tex` in a research-cache copy (6 shader
   lines + 3 glGetUniformLocation strings; nothing numerical touched).
2. **Author bug made deterministic, not patched**: `FFT::FFT()` compiles the dimension-0 butterfly display lists
   (`init_display_lists(i)`, FFT.cpp l. 181) before `size[1]` is assigned (l. 169), i.e. with an
   uninitialised quad height. With glibc it is 0 and the PSF is black (found with apitrace + a probe that links
   the unmodified FFT.cpp: harness/fft_probe.cpp). On MSVC 2009 the garbage happened to be large. Running with
   `GLIBC_TUNABLES=glibc.malloc.tcache_count=0:glibc.malloc.perturb=1` fills fresh heap with 0xFE -> height
   4.28e9 -> full-viewport quads, as the author intended.
Result: `results/native/temporal-glare-2009/NATIVE_glare_demo_candle_glare_and_psf_views.png` reproduces the
author's screenshot qualitatively (veil + corona needles + coloured lenticular halo around the candle; radial
needles and halo ring in PSF view). Not bit-comparable (8-bit, different GPU, the screenshot shows one instant of a
time-varying process). Speed: 4.4 fps (glare view) / 10.7 fps (PSF view) on llvmpipe vs 64/116 fps reference.
`hippus.m` under Octave (`NATIVE_hippus_matlab_octave.png`) reproduces the author's `hippus_matlab.svg`
qualitatively (same 5 mean levels 8.5/7.2/6.0/4.5/4.0 mm, amplitude growing as p shrinks); individual curves
differ because Octave's `rng(t,'twister')` stream is not MATLAB's.

### B3/B4 measurements (NATIVE; `NATIVE_metrics.json`, `NATIVE_psf_float_metrics.csv`, plots)
The published PNG sequences were not obtainable, so the same measurements were made on the demo's own output:
(a) the per-step hippus pupil diameter extracted from an apitrace of the run (631 steps x 20 ms = 12.6 s sim),
(b) 33 float RGB32F PSF frames (fbo before the tone pass, sim t = 0.8-9.4 s, every 13 steps = 0.26 s) dumped
with `glretrace -D` (non-invasive), (c) 1275 + 568 8-bit window grabs.
- resolution/normalisation: PSF 512x512 RGB32F, demo RGB; 8-bit grabs 512x512 sRGB-like (pow 0.4545),
  0.3 % (PSF view) / 1.7 % (glare view) of pixels clipped at 255. Derived angular scale 532 px/deg from code
  constants (N = 10 mm/512 px, d = 20.32 mm, lambda1 = N/d, glare_scale 1.5; the code comment calls lambda1
  "micrometers" while it is used as nm -> scale is DERIVED, uncertain); window = +-0.48 deg.
- temporal: pupil mean 6.66 mm (Eq. 2 value 6.63 mm from overlay mean L = 0.0023 "cd/m^2"), SD 0.11 mm,
  range 6.37-6.87 mm; no period: broadband 1/f-like spectrum, peak 0.24 Hz, median 0.32 Hz, 90 % of power
  < 0.63 Hz; autocorrelation 1/e lag 0.74 s; halves differ (SD 0.06 vs 0.14 mm) -> weakly stationary at
  best over 12 s. Octave hippus.m: SD 0.04-0.20 mm, p-p 0.18-1.07 mm, larger for small pupils.
- per-frame energy: PSF sum varies 3.8 % p-p, correlates with pupil area (r = 0.995), log-slope vs D 1.13;
  PSF peak varies 2.6 % p-p, anti-correlated (slope -0.78). In the glare view the demo multiplies by pupil
  area (l. 531) -> displayed glare energy scales ~D^3.1 (inferred from code + measured slope).
- radial profile: core HWHM 3 px (0.34 arcmin); encircled energy 3 % within 0.006 deg, 13 % within 0.019 deg,
  39 % within 0.19 deg, 90 % within 0.48 deg (window); 15 % beyond r = 240 px (FFT wrap-around, heavy tails
  because the demo shows \|F\|). Lenticular halo bump at r = 175-184 px = 0.33-0.35 deg (paper-scale halos are
  ~3-4 deg; the demo's 200 fibres over a 10 mm aperture give a ~0.2-0.35 deg ring); halo prominence 1.17-1.21,
  correlated with pupil D (r = 0.99).
- centre-of-energy motion: < 0.07 px (none); no translation.
- temporal variation per radius (relative SD over frames): core 0.6 %, 0.1 deg 4.5 %, halo 3.5 %, edge 3.2 %.
- colour: demo-RGB energy R:G:B = 1.17 : 1 : 0.55 for a "white" source; R/G rises to 1.36 at 0.02 deg and B/G
  falls to 0.42 at the halo (red-shifted halo edge, chromatic scaling).
- energy conservation: not enforced (PSF energy ~ D^1.13 in PSF view; ~D^3.1 in glare view; paper Eq. 3 would
  give intensity ~ area). The demo's grabs: display energy SD 3.3 %, corner-veil SD 7-8 %.

### B5 classification of the dynamic effect
| candidate | paper | demo |
|---|---|---|
| intensity modulation | yes, through pupil area in Eq. 3 (K, open area) | yes (PSF energy 3.8 % p-p; glare view ~23 % p-p, inferred D^3.1) |
| PSF deformation | yes: hippus scales the diffraction pattern (~1/D); particle motion changes needle pattern | yes, radial rescaling + halo prominence change only |
| translation | no (vitreous rotation moves needles, not the centroid) | none measured (< 0.07 px) |
| streak (needle) variation | yes: lens particle motion + vitreous (p. 186-187) and "superimposed needles fluctuate incoherently" (p. 189) | no (particles static) |
| pupil | yes (hippus, Eq. 1-2) | yes (the only dynamics) |
| lens fibres | static grating (halo); lens deformation moves particles, not fibres | static |
| vitreous | yes, saccade-driven damped rotation | no |
| eyelashes/blink/squint | yes (animated bitmaps) | no |
| tear film | not modelled | no |
So the demo reproduces only the "pulsation" component (paper p. 185-186: "The visual effect due to the
pupillary hippus is a sort of pulsation of the glare pattern"); the paper's fluid needle motion (lens/vitreous)
and blinking are paper-only. The dynamics are ocular-internal, independent of the atmosphere.

## COMMON STIMULUS (B7) — ADAPTED (the published PNG sequence being BLOCKED)
`tracks/temporal-glare-2009/compose_common.py` uses the 33 NATIVE float PSF frames as a billboard on
S0 (white) and S1 (HPS-like) without pcond. ADAPTED choices (also in `ADAPTED_summary.json`):
PSF scale 532 px/deg (derived) -> flux-conserving area rebin to 32 px/deg (the whole demo PSF, +-0.48 deg,
becomes a ~31 px wide kernel on a 35x35 px grid); each frame and channel normalised to unit sum (energy- and colour-conserving
billboard; the demo's own +-2 % energy change is deliberately not applied); source = stimulus minus median sky
inside a 9x9 window, convolved with the kernel; display = PHONE_TARGET (73 px/deg, 100 cd/m^2 peak) with
value = clip(Y/100) per channel, sRGB OETF, bilinear 32->73 px/deg; time base 20 ms/step, frames held 0.26 s.
Results (`results/common/temporal-glare-2009/`): MP4s, montages, luminance-over-time plots/CSV.
- the source pixel falls from 74.7 to 11.8 cd/m^2 (only 11.7 % of the energy stays in the central 32-px/deg
  pixel), so nothing clips on the 100 cd/m^2 phone; the "2x2 clipped white core" of the baseline becomes a soft
  core with a faint 0.28 cd/m^2 halo ring at 0.33 deg (700x the 4e-4 sky) and a hard square edge at +-0.5 deg
  (the demo's PSF window, a limitation of the donor output).
- temporal: peak 0.33 % p-p, ring 4-5 % p-p over 8.6 s; slow (sub-Hz) -> after energy normalisation the
  "breathing" is a small redistribution between core and halo, far below the display's 8-bit step at the core.

## ASSUMPTIONS
Paper: field luminance in cd/m^2 (Eq. 2) but approximated by "time-damped average screen intensity" (p. 186);
HDR RGB input for the convolution; no viewing geometry stated for the PSF; display via gamma 2.2 (p. 190);
study viewing distance 1 m, images ~10 deg (p. 190). Demo: 8-bit PNG image + 8-bit bright-pixel overlay (the
source is LDR-coded; `image_intensity` = 10 is a fixed gain), overlay mean treated as cd/m^2 for the pupil.

## VALIDATION
Paper p. 190: 2AFC with 10 subjects, dynamic glare judged brighter than static (chi^2 = 72.2, p < .01) and
than control (chi^2 = 145.8); attractiveness/realism scene-dependent; brightness matching with 4 subjects
shows a boost for static and dynamic glare (F(2,4) = 8.22, p < .05), dynamic vs static not significant. No
physical validation of the PSF; hippus curve tuned "qualitatively" to Fry 1991 (hippus.m header).

## REUSE
Runnable author demo (source available, no licence -> may be run and cited, not redistributed; ask the author
for reuse). Useful as a CODE/BEHAVIOUR donor for "pupil-driven pulsation", not for absolute photometry:
the PSF is an amplitude image, has a non-physical angular scale and window, and LDR input.

## FAILURES / SURPRISES
- The published billboard PNG sequences, AVI/MPEG and the YouTube video are unreachable from here (403,
  egress policy, bot check).
- Author FFT bug (uninitialised `size[1]`) silently produces a black PSF on glibc; reserved GLSL identifiers
  break on Mesa.
- The demo displays the Fourier amplitude, not intensity (Eq. 3 squares it) -> much heavier tails.
- Derived halo radius ~0.33 deg, i.e. ~10x smaller than the lenticular halo described in the literature.
- In glare view the veil brightness scales ~D^3 with the pupil (display normalisation multiplies by area).

## BRIGHT POINT SOURCE
1. Paper: RGB PSF convolved with the whole HDR image (p. 189, "Convolution"); demo: with the bright-pixel overlay only, then the LDR image is added.
2. The PSF depends on the adaptation state only through pupil size (Eq. 2 from field luminance); there is no photoreceptor adaptation stage, glare is applied to scene-referred values.
3. Before tone reproduction (gamma 2.2, p. 190; demo: divide + pow 0.4545 after convolution).
4. Paper: K = 1/(lambda d)^2 with unit incident amplitude -> energy ~ open pupil area, not normalised to the source; demo: not conserved (sum ~D^1.13, glare view ~D^3.1).
5. Paper: nominally cd/m^2 for Eq. 2 only, but uses screen intensity; demo: no (8-bit overlay).
6. Pupil (adaptation, hippus) and wavelength (chromatic scaling) yes; age no; field angle no (shift-invariant convolution).
7. HDR result gamma-mapped (gamma 2.2) and clipped to LDR; glare is the device that conveys brightness; no HDR display path.
8. Yes: psychophysics p. 190 (dynamic > static > none for brightness).
9. Yes: hippus, lens-particle micro-fluctuations (<0.6 Hz, 1.3-2.1 Hz), vitreous damped rotation, blinking (paper); demo: hippus only, broadband < ~0.6 Hz, pupil SD ~0.1 mm at p = 6.6 mm.
10. Paper: convolution on float HDR (no clipping before); demo: source enters as an 8-bit overlay (clipped/LDR-coded before convolution), result clipped after.

## VERDICT
**BEHAVIORAL ORACLE** (runnable co-author demo reproduces its reference behaviour; model-level scientific claims
come from the paper; not a photometric/absolute glare model). Published PNG sequences: BLOCKED.
