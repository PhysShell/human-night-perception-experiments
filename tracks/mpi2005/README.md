# mpi2005 — Krawczyk, Myszkowski, Seidel, "Perceptual Effects in Real-time Tone Mapping" (SCCG 2005)

## IDENTITY
- Paper: G. Krawczyk, K. Myszkowski, H.-P. Seidel, *Perceptual effects in real-time tone mapping*,
  Proc. 21st Spring Conference on Computer Graphics (SCCG 2005), pp. 195-202, doi:10.1145/1090122.1090154
  (1st Best Paper Award, per the author's alumni page). Project page
  https://resources.mpi-inf.mpg.de/hdr/peffects/ (paper `krawczyk05sccg.pdf`, slides `krawczyk05sccg_slides.pdf`).
- **The SCCG PDF itself could not be retrieved** (HTTP 403 from resources.mpi-inf.mpg.de both from the container
  and from WebFetch; ACM DL paywalled; Semantic Scholar lists no open-access PDF; the old
  `domino.mpi-inf.mpg.de/.../$FILE/krawczyk05sccg.pdf` mirror returns 503). Status: **BLOCKED** for the paper, slides and
  any demo video.
- Substitute primary source used here, by the same first author: G. Krawczyk, *Perception-inspired Tone Mapping*,
  PhD thesis, Saarland University / MPI Informatik, 2007, **Chapter 4 "Real-time Tone Mapping for HDR Video"**
  (printed pp. 39-54 = PDF pp. 51-66), downloaded from
  https://people.mpi-inf.mpg.de/alumni/d4/2014/krawczyk/phd/krawczyk07phd_final.pdf
  (sha256 d00196fd5d87ca91eedb16211c7e4386e02992cd26ec776d20a176e34f20cc4a, 7 793 901 B; identical bytes at
  https://d-nb.info/1004355556/34). Chapter 4 is the journal-length version of the SCCG paper (same model,
  same constants, performance table, Figure 4.9 pipeline). Equation numbers below are the thesis numbers
  (4.n); third-party code that cites the SCCG paper uses the same numbers without the "4." prefix
  (Stride cites "p. 3, Equation 5" for the adaptation and "p. 4, Equation 11" for the key; stuntrally cites
  "Equ(7)" for rod sensitivity and "Equ(12)" for tau), which is consistent with SCCG Eq. n = thesis Eq. 4.n.
  This mapping is an inference from those comments, not verified against the SCCG PDF.

## PURPOSE
Real-time (GPU, 2005) local tone mapping of HDR video (Reinhard et al. 2002 photographic operator with
Gaussian-pyramid dodging & burning) extended with luminance-dependent perceptual effects: temporal luminance
adaptation, scotopic (rod) desaturation with blue shift, loss of visual acuity, and veiling glare. Key idea:
reuse the tone mapper's Gaussian pyramid levels as the blur kernels for acuity and glare (thesis p. 46,
Fig. 4.7), so the effects cost almost nothing.

## HVS COMPONENTS
| component | present? | how (thesis page, eq.) |
|---|---|---|
| optics / glare | yes, simplified | veiling luminance from the Deeley et al. 1991 ocular transfer function OTF(rho,d) = exp(-(rho/(20.9-2.1d))^(1.3-0.07d)) (p. 46, eq. 4.10), **approximated by one Gaussian pyramid level** chosen per frame from the adapting luminance (p. 46-47, Fig. 4.7; p. 50). Glare added as Y_glare = Y_gmap (1 - 0.9/(0.9+Y_gmap)) (p. 50, eq. 4.14) |
| pupil | yes (inside glare only) | d(Y) = 4.9 - 3 tanh(0.4 log10 Y + 1) (p. 46, eq. 4.10, second line; note: the bracket differs from Moon & Spencer's 4.9 - 3 tanh(0.4(log L + 1)) used by Ritschel 2009 Eq. 2) |
| adaptation (temporal) | yes | exponential filter of the log-average luminance, Y_a,new = Y_a + (Y - Y_a)(1 - exp(-T/tau)) (p. 43, eq. 4.5), tau_rods = 0.4 s, tau_cones = 0.1 s (p. 44, eq. 4.6), tau interpolated by rod sensitivity (p. 48, eq. 4.12); dark adaptation deliberately symmetric/fast (p. 44) |
| rods / cones, mesopic / scotopic | yes | sigma(Y) = 0.04/(0.04+Y) (p. 44, eq. 4.7, after Hunt 1995); per-pixel mix of colour and monochrome with blue-shift weights (1.05, 0.97, 1.27) (p. 50, eq. 4.15) |
| acuity | yes | Ward et al. 1997 fit RF(Y) = 17.25 arctan(1.4 log10 Y + 0.35) + 25.72 cpd (p. 44, eq. 4.8); Gaussian s = (width/fov)/(1.86 RF) (p. 45, eq. 4.9); 45 px/deg assumed for a 15" 1024x768 LCD at 0.5 m (p. 45) |
| tone reproduction | yes | Y_r = alpha Y / Y_bar (4.1), L = Y_r/(1+Y_r) (4.2), local L = Y_r/(1+V) (4.3), pyramid g(x,y,s) with s0 = 1/(2 sqrt 2), x1.6 per scale, 8 scales (p. 42-43, eq. 4.4); auto key alpha = 1.03 - 2/(2+log10(Y_bar+1)) (p. 48, eq. 4.11); final L = (Y_acuity + Y_glare)/(1+V) (p. 50, eq. 4.13) |
| temporal state | adaptation only | no temporal glare/PSF dynamics |
| gaze | no | |
| display model | minimal | output RGB in [0,1] quantised to 8 bit by the OpenGL driver (p. 41); 45 px/deg viewing assumption only for acuity |
| spectrum | no | RGB; luminance from CIE XYZ transform (p. 41) |

## NATIVE ENVIRONMENT
GPU fragment programs + pixel buffers on an NVIDIA GeForce 6800GT (p. 52), plugged into the MPI HDR video
player (Mantiuk et al. 2004 HDR MPEG). **No source code or binary of the SCCG/thesis pipeline was found**:
- author pages (people.mpi-inf.mpg.de alumni page, LinkedIn link only), MPI resources page (403), GitHub
  code/repository search for "peffects", "Krawczyk" + tone mapping: no author repository;
- pfstools (GPL) contains Krawczyk's port of Reinhard 2002 (`src/tmo/reinhard02/tmo_reinhard02.cpp`, header:
  "Port to PFS tools library by Grzegorz Krawczyk"), i.e. only the underlying tone-mapping stage, CPU, without
  the perceptual effects;
- `ASolot/temporal-glare` and all engine code below are third-party re-implementations of single formulas.

## NATIVE REPRODUCTION
**BLOCKED / not possible**: no runnable original code exists publicly; implementing the missing stages is out
of scope (RULES: no reimplementation). Exact blocked URLs: https://resources.mpi-inf.mpg.de/hdr/peffects/ ,
https://resources.mpi-inf.mpg.de/hdr/peffects/krawczyk05sccg.pdf , https://resources.mpi-inf.mpg.de/hdr/peffects/krawczyk05sccg_slides.pdf
(all HTTP 403), http://domino.mpi-inf.mpg.de/intranet/ag4/ag4publ.nsf/2a3e8aac13d8697cc125675300686237/a48310c4fdbe1ea6c1256fe9004d4776/$FILE/krawczyk05sccg.pdf (HTTP 503).

## COMMON STIMULUS
Not run (no native code). Nothing in results/common/mpi2005/.

## PIPELINE (A4, reconstructed from thesis Fig. 4.9, pp. 48-50)
```
HDR RGB frame (float, cd/m^2 expected, 1e-4..1e8; p. 41)
  -> Y (CIE XYZ luminance)                                    p. 41
  -> log-average Y_bar (GPU down-sampling, Goodnight 2003)     p. 49
  -> TEMPORAL ADAPTATION Y_a (eq. 4.5, tau from eq. 4.12/4.7)  pp. 43-44, 48
  -> key alpha(Y_a) (eq. 4.11); relative luminance Y_r = alpha Y / Y_a (eq. 4.1)   pp. 42, 48
  -> Gaussian pyramid of Y_r, 8 scales, separable, down-sampled (eq. 4.4, Fig. 4.10)  pp. 42-43, 49-50
       per scale, per pixel update of 3 "perceptual data" maps (one RGB texture):
         V         local adaptation (Reinhard 2002 scale selection)            [TONE REPRODUCTION]
         Y_acuity  scale chosen per pixel from RF(Y) (eq. 4.8-4.9, LUT)        [NEURAL / ACUITY]
         Y_gmap    scale chosen per frame from Y_a via OTF(rho, d(Y_a)) (4.10) [RETINAL OPTICS]
  -> Y_glare = Y_gmap (1 - 0.9/(0.9 + Y_gmap)) (eq. 4.14)       p. 50
  -> L = (Y_acuity + Y_glare) / (1 + V) (eq. 4.13)              p. 50   [LOCAL MAPPING]
  -> RGB: colour part L(1-sigma)/Y * RGB + blue-shifted grey (1.05,0.97,1.27) L sigma (eq. 4.15, sigma eq. 4.7) [ROD/CONE]
  -> [0,1] float -> 8-bit by the OpenGL driver -> display (no display model)   p. 41
```
So the order is: input -> temporal adaptation -> (key, relative luminance) -> {acuity loss, glare, local
adaptation computed in parallel on the same pyramid} -> local compression -> scotopic colour -> display.
Acuity and glare are both applied to the **adaptation-scaled relative luminance**, inside the numerator of the
local operator, i.e. before the compressive division and before display quantisation.

## A5: stage -> mechanism
| stage | class |
|---|---|
| temporal adaptation of Y_bar (4.5, 4.6, 4.12) | neural response (photoreceptor/post-receptoral adaptation time course), crude |
| pupil d(Y) inside 4.10 | retinal optics (aperture) |
| veiling glare (4.10, 4.14) | retinal optics (intraocular scatter), Gaussian surrogate |
| acuity loss (4.8, 4.9) | neural (rod-pooling / resolution limit), applied as optical-like blur |
| scotopic desaturation + blue shift (4.7, 4.15) | neural response (rod vs cone), appearance |
| key value (4.11), sigmoid & dodging-burning (4.1-4.3, 4.13) | tone reproduction |
| 8-bit quantisation | display |

## ASSUMPTIONS
cd/m^2 calibrated input required for the effects (p. 41: "should be calibrated to cd/m^2", Appendix A
calibration); RGB (not spectral); viewing geometry fixed at 45 px/deg (p. 45); absolute scale matters for
sigma, RF, d(Y) and alpha; display = generic [0,1] 8-bit, no peak luminance or contrast model.

## VALIDATION
None quantitative in the thesis chapter: visual examples (Fig. 4.11) and timings (Table 4.1, p. 53). The key
formula 4.11 is explicitly empirical ("matter of experience", p. 47-48). Glare brightness benefit is argued
by citing Spencer et al. 1995 (p. 40), not measured.

## REUSE (A3) — descendants in open source (formula-level only, third-party)
| where | lines | what | notes |
|---|---|---|---|
| RBDOOM-3-BFG tag `1.1.0-preview3` (7728dc3a) `neo/renderer/tr_backend_draw.cpp` | 4366-4368 | `hdrKey = 1.03 - ( 2.0 / ( 2.0 + ( hdrAverageLuminance + 1.0f ) ) )`, comment "calculation from: Perceptual Effects in Real-time Tone Mapping - Krawczyk et al." | inside `#if 0 // RB: this never worked :/`; **log10 missing** vs eq. 4.11 |
| RBDOOM-3-BFG `1.2.0-preview1` `neo/renderer/RenderBackend.cpp` | 4364-4365 | same | same, disabled |
| RBDOOM-3-BFG `v1.3.0` (b4e0366c), `v1.4.0` (f81a8c1d) `neo/renderer/RenderBackend.cpp` | 4689-4690 (disabled block 4686-4696) | same | adaptation used instead is the Quake-style `1 - 0.98^(30 dt)` (v1.4.0 line 4668), fixed key `r_hdrKey` |
| RBDOOM-3-BFG `v1.5.0`, `v1.6.0`, master ea29c006 | — | formula removed; `r_hdrKey` default "0.015" (master `neo/renderer/RenderSystem_init.cpp:268`) | |
| TEKUUM-D3 (R. Beckebans) 5791f0bc `renderer/tr_backend_draw.cpp` | 4385-4386 | active: `1.03 - 2.0 / ( 2.0 + log10f( hdrAverageLuminance + 1.0f ) )` | GPL v3 (file header) |
| ET: Legacy b93c534c `src/renderer2/tr_backend.c` | 2761-2762 | active, log10f | GPL v3; XreaL lineage (also ET-XreaL, KingpinQ3, OpenWolf ...) |
| Stride engine ecf78116 `sources/engine/Stride.Rendering/Rendering/Images/ColorTransforms/ToneMap/ToneMap.cs` | 203-204, 211-213 | temporal adaptation (cites "p. 3, Equation 5") and auto key (cites "p. 4, Equation 11") | MIT; adaptation rate is a user parameter, not tau(sigma) |
| stuntrally 9a7efa5a `data/compositor/hdr/hdr.hlsl` | 104-116 | sigma (cites "Equ(7)") as `0.4/(0.04+L)` (**0.4 instead of 0.04**), tau lerp(0.01,0.04) (cites "Equ(12)"), adaptation ("Equ(5)") | same code in delta3d `examples/data/shaders/hdr/luminance_adapted_fp.glsl` 43-62 |
| tizian/tonemapper dd9f7c86 `src/main.cpp` | 323-325 | key alpha per eq. 11 on the log-mean | license file not found at repo root (not verified) |
| CRYENGINE (MergHQ mirror) 8b63f61c `Engine/Shaders/HWScripts/CryFX/HDRPostProcess.cfx` | 289-290 | "Krawczyk scene key estimation adjusted": `1.03 - 2/(2+log2(L+1))` (**log2**) | CRYENGINE licence, not open source in the OSI sense |
Only the **auto-key formula (4.11)** and occasionally the **adaptation filter (4.5)/(4.7)/(4.12)** survive; nobody
re-uses the pyramid-shared acuity/glare mechanism. Several copies deviate (missing log10, log2, 0.4 vs 0.04).

## FAILURES / SURPRISES
- The widely cited RBDOOM-3-BFG "Krawczyk key" never ran: it is compiled out and lacks the log10.
- The pupil formula in eq. 4.10 has the bracket in a different place than Moon & Spencer (1944) as quoted by
  Ritschel et al. 2009 Eq. 2; which one the SCCG PDF prints is unknown (PDF blocked).
- Glare model is a single Gaussian level, i.e. no ciliary corona, no halo, no wavelength dependence.

## BRIGHT POINT SOURCE
1. PSF applied to the adaptation-normalised relative luminance Y_r (via the pyramid level chosen from Y_a), p. 49-50.
2. After (temporal) adaptation normalisation (eq. 4.1 uses Y_a).
3. Before tone reproduction: Y_glare is added in the numerator of the local operator (eq. 4.13).
4. No: glare is added on top of the unblurred/acuity-blurred image and not removed from the source (4.13-4.14); energy is added, not redistributed.
5. Yes, requires cd/m^2 (p. 41) for sigma, RF, d(Y), alpha.
6. Glare width depends on adaptation luminance via pupil d(Y_a) only; not age, wavelength or field angle.
7. Compressive local sigmoid L = (...)/(1+V) to [0,1], 8-bit quantised; unresolved source saturates to white core with a Gaussian veil; no HDR display path.
8. Claimed (cites Spencer 1995, p. 40) but not tested.
9. No temporal PSF variation except the slow change of the chosen scale with Y_a (tau 0.1-0.4 s).
10. No clipping before blurring (float pipeline); clipping only at the final [0,1] -> 8-bit step.

## VERDICT
**HISTORICAL REFERENCE** (paper BLOCKED; thesis chapter used as documented substitute; no code; descendants
reuse only the key/adaptation formulas).
