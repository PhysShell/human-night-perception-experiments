# Track `vissimframework` — Csoba & Kunkli, VisSimFramework (wavefront-aberration PSFs, tiled PSF splatting)

## IDENTITY
- Repository: https://github.com/csobaistvan/VisSimFramework, commit `274ca986d695da1694975213b82e90bdab3d8dde`
  (2024-07-28), cloned to `research-cache/vissimframework/VisSimFramework` (gitignored; `.git` removed afterwards to save disk).
- Author: István Csoba (PhD framework, Univ. Debrecen), with Roland Kunkli on the papers.
- License: BSD-2-Clause, `LICENSE` ("Copyright 2017-2024 István Csoba"). Redistribution allowed with notice.
  Bundled third-party code keeps its own terms: modified Optometrika (MATLAB ray tracer,
  `Assets/Scripts/Matlab/EyeReconstruction`, see README "Code organization"), HDR-VDP 3.0.6
  (`Assets/Scripts/Matlab/hdrvdp-3.0.6`). Third-party libraries and most assets are NOT in the repo
  (SharePoint links in README, see FAILURES).
- Papers (titles/DOIs from the repo README, "Related publications"):
  1. Csoba & Kunkli, *Efficient Rendering of Ocular Wavefront Aberrations using Tiled Point-Spread Function
     Splatting*, Computer Graphics Forum 40(6):182-199, 2021, doi:10.1111/cgf.14267 (PDF not reachable: Wiley 403).
  2. Csoba & Kunkli, *Fast, GPU-based Computation of Large Point-Spread Function Sets for the Human Eye using the
     Extended Nijboer-Zernike Approach*, IEEE CITDS 2022, pp. 69-73, doi:10.1109/CITDS54976.2022.9914232 (not fetched).
  3. Csoba & Kunkli, *Rendering algorithms for aberrated human vision simulation* (survey), Visual Computing for
     Industry, Biomedicine, and Art 6:5, 2023, doi:10.1186/s42492-023-00132-9 (open access, fetched).
  4. Csoba & Kunkli, *Fast rendering of central and peripheral human visual aberrations across the entire visual
     field with interactive personalization*, The Visual Computer 40:3709-3731, 2024, doi:10.1007/s00371-023-03060-0
     (open access, fetched).

## PURPOSE
Research test bed for real-time simulation of **optical aberrations of the eye** (defocus, astigmatism,
higher-order Zernike terms, keratoconus, peripheral/off-axis aberrations) by physically computed,
depth- and field-dependent PSFs, applied to a rendered 3D scene (G-buffer colour + depth) by tiled
PSF splatting. It is an optics renderer (PSF donor), not a perception/adaptation model.

## HVS COMPONENTS
| component | present? | where (file:line) |
|---|---|---|
| optics (wavefront → PSF) | YES, the core. Zernike wavefront → PSF via Extended Nijboer-Zernike (ENZ), CPU and GPU backends | `Source/Scene/Components/Aberration/WavefrontAberration.cpp` (namespace `Vnm` from l.1703; `computePsfEntryParameters` l.2463; `optimizePsf` crop+normalize l.2854-2872); GPU: `Assets/Shaders/OpenGL/Aberration/PsfStack/compute_psf_cs.glsl`, `compute_vnm_cs.glsl`, `compute_vnm_inner_cs.glsl` |
| eye model (for off-axis) | YES: parametric schematic eye after Escudero-Sanz & Navarro, reconstructed from on-axis Zernike data by patternsearch (MATLAB) or neural nets (TensorFlow C API) | `Assets/Scripts/Matlab/EyeReconstruction/EyeParametric.m` l.3; `EyeReconstruction.m`; `compute_aberrations.m`; `Source/Core/LibraryExtensions/TensorFlowEx.h` |
| pupil | YES: aperture diameter parameter (`Ap` in .abp files; camera `aperture` default 5.0 mm; variable-pupil PSF cache 2-7 mm) | `Source/Scene/Components/Rendering/Camera.cpp` l.545-549; `TiledSplatBlur.cpp` l.2801-2818; PSF cache interpolation `Assets/Shaders/OpenGL/Aberration/TiledSplatBlur/PSF/diopter_based_off_axis.glsl` l.528-553 |
| accommodation / focus | YES: focus distance (default 8 m), variable focus PSF cache 0.125-6.125 dpt | `Camera.cpp` l.553-557; `TiledSplatBlur.cpp` l.2820-2837 |
| chromatic | partial: PSFs at 3 wavelengths, default {612, 549, 464} nm "sRGB primaries" (one per RGB channel); `WavefrontAberration.cpp` l.2379 comment: "TODO: shouldn't this actually depend on wavelength?" for the object-depth focal shift | `WavefrontAberration.h` l.202; `.abp` reference wavelength `Wa = 587.56` |
| field angle / peripheral variation | YES (OffAxis mode): PSF grid over incident angles, e.g. ±45° × ±25° (31×21) for 50° fovy | `TiledSplatBlur.cpp` l.2773-2799; shader `sphericalCoordinates` `TiledSplatBlur/common.glsl` l.370-388; layouts `PSF/diopter_based_off_axis.glsl`, `PSF/diopter_based_on_axis.glsl`, `PSF/radius_based.glsl` |
| glare / intraocular scatter | NO. No scatter, Stiles-Crawford or veiling-glare term found (grep for scatter/glare/Stiles in `Source/Scene/Components/Aberration` and the Matlab eye code). PSFs are **cropped to 99 % of their energy** (`m_cropThresholdSum = 0.99`, `TiledSplatBlur.cpp` l.2738; `cropSum` `WavefrontAberration.cpp` l.1976-1989) — any wide halo is removed by design | |
| adaptation | only a generic game-engine tone mapper with exponential temporal auto-exposure (`ToneMap` component, `Source/Demo/Demo.cpp` l.295-349: AutoKey, Exponential adaptation rate 2.0, ACES operator) — not an HVS adaptation model | `Assets/Shaders/OpenGL/PostProcessing/ToneMap/tonemap_fs.glsl` |
| rods/cones, mesopic/scotopic | NO | |
| acuity | only implicitly via PSF (diffraction + aberrations); no neural sampling | |
| temporal state | tone mapper adaptation only; PSFs do not vary in time except when pupil/focus parameters are animated (key-frame system) | |
| gaze | no eye tracking; off-axis PSFs are indexed by screen position relative to the camera axis (fixation = screen centre) | `TiledSplatBlur/common.glsl` l.370-388 |
| display model | NO (output is the framework's LDR swap chain; sRGB encode + saturate in tone mapper) | `tonemap_fs.glsl` l.34 |
| spectrum | 3 wavelengths per RGB channel; no spectral rendering | |

## NATIVE ENVIRONMENT
Windows + Visual Studio 2019 (v16.6.3), Premake5 (`premake5 --matlab_root=... vs2019`), OpenGL 4.3 compute
shaders (tested on NVIDIA TITAN Xp), MATLAB R2020b with Optimization / Global Optimization / Parallel Computing /
Image Processing toolboxes, Python 3.8 + TensorFlow 2.5 for the networks, third-party binaries from a SharePoint
archive (repo README, "Requirements").

## NATIVE REPRODUCTION
- Exact example: the "healthy" default aberration (`-aberration healthy`, `Assets/Aberrations/healthy.abp`:
  `Ap = 5.0`, `Wa = 587.56`, `Z[0,0] = 1` i.e. piston only = diffraction-limited 5 mm pupil) with the
  TiledSplatBlur demo (`TiledSplatBlur::demoSetup`, `TiledSplatBlur.cpp` l.2662-2844) in the Sponza/San Miguel scenes.
- Command (as documented): `premake5 vs2019` → build in VS/MSBuild → run with defaults.
- Result: **BLOCKED** — no Windows, no Visual Studio/MSBuild, no OpenGL 4.3 GPU, no MATLAB here; third-party
  libraries/assets are on SharePoint (URLs in README) and not in the repo. Per track instructions the framework
  was not ported to Linux.
- NATIVE references captured instead (published by the authors in the repo, BSD-2-Clause):
  `results/native/vissimframework/NATIVE_published_sanmiguel_healthy_offaxis.png`,
  `NATIVE_published_sponza_healthy_offaxis.png`, `NATIVE_published_sanmiguelupper4_myopia06_7mm.png`
  (copied from `Docs/`, see `results/native/vissimframework/INDEX.md`). The healthy images show strong peripheral
  (off-axis) blur with a sharp centre; they contain no bright point source and no HDR highlight, so they say
  nothing about halo/glare.

### Smallest normal-eye configuration (F5)
Command-line defaults (all from `Config::registerConfigAttribute` calls):
`-aberration healthy` (`WavefrontAberration.cpp` l.5772-5778), `-fov 60` (`Camera.cpp` l.537-541),
`-aperture 5.0` mm (`Camera.cpp` l.545-549), `-focus 8.0` m (`Camera.cpp` l.553-557),
`-tsb_axis_method OnAxis`, `-tsb_focus_distance Fixed`, `-tsb_aperture_diameter Fixed`, `-tsb_tile_size 8`
(`TiledSplatBlur.cpp` l.2613-2659). demoSetup then fixes: object distances 0.125-8.125 dpt in 33 steps (on-axis),
3 wavelengths, F11 PSF texture, FrontToBack accumulation, AreaSquare/AlphaBlend weights, `m_maxCoC = 80` px (l.2700),
`m_cropThresholdSum = 0.99`, **`m_inputDynamicRange = LDR`** (l.2687). `healthy.abp` contains only piston, so the
"healthy" eye is an aberration-free diffraction-limited eye plus defocus from object depth vs focus distance; in
OffAxis mode the off-axis aberrations come from the reconstructed Navarro-type schematic eye.

## COMMON STIMULUS
Not run: NATIVE is BLOCKED (rule 1). What it would need: a G-buffer (linear colour + depth) — the framework
also accepts an image via `GroundTruthAberration` (`Asset::loadImage`, `GroundTruthAberration.cpp` l.195) with an
`InputDynamicRange` switch (HDR/LDR). S0-S7 would be compatible in principle only as HDR inputs at a known FOV
(fovy from `stimuli/display_targets.json`).

## ASSUMPTIONS
- Units: scene-referred linear RGB from its own deferred renderer; no cd/m^2 calibration anywhere; the tone
  mapper auto-exposes (key 0.115, `Demo.cpp` l.302). Absolute luminance does not enter the PSF.
- Colour: RGB, each channel convolved with the PSF of one wavelength (612/549/464 nm).
- Geometry: camera fovy (default 60°) + render resolution define pixel → angle; PSF sizes are converted to pixels
  from diffraction units and the angular pixel size (`computePsfSampling`, `WavefrontAberration.cpp` l.2419-2426).
- Display: none modelled; sRGB OETF + `saturate` at tone mapping.

## VALIDATION
Papers compare against their own dense per-pixel ground truth (`GroundTruthAberrationComponent`) with PSNR
(`Assets/Scripts/Matlab/compute_psnr.m`) and against earlier vision-simulation algorithms (TVC 2024 abstract,
`research-cache/vissimframework/papers/tvc2024.txt` l.1-36). No psychophysical validation of appearance; no
validation of bright sources or glare.

## REUSE
- PSF donor (CODE DONOR): the ENZ PSF computation (Zernike → PSF, pupil/focus/wavelength/field-angle grid) is the
  most complete open eye-PSF code among the donors; BSD-2 allows reuse. Needs MATLAB only for eye reconstruction;
  the ENZ/PSF part is C++/GLSL.
- Not reusable as-is for glare: the 99 % energy crop and the ≤80 px max CoC remove exactly the wide PSF skirt that
  produces a visible halo around an unresolved lamp.
- Architecture idea: splat PSFs per fragment in HDR before tone mapping (the HDR callback exists).

## FAILURES / SURPRISES
- BLOCKED build (Windows/VS/OpenGL 4.3/MATLAB). Third-party binaries/assets only via SharePoint:
  `https://unidebhu-my.sharepoint.com/:u:/g/personal/csoba_istvan_inf_unideb_hu/Ecw5NQRdltNFk61E1H1JeUcBk9uBU2ag_JIXCnueOzNNrA?e=kkEVpQ`
  (libraries), `.../EfvMCe3XCvtAk8HdAQ77ewQBxnNT_fHhjlzVPuccnBIj5A?e=JhYbjB` (assets),
  `.../EcuEr51d8B9NtXwCWWNZVY0BbLkt1UJShSuw973eTIX4LA?e=IEEIEy` (datasets) — not attempted (not needed, build blocked anyway).
- CGF 2021 paper PDF: `https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/cgf.14267` → HTTP 403 (Wiley bot wall). BLOCKED.
- Surprise 1: the shipped demo convolves **LDR** (post-tone-map, post-`saturate`, sRGB-encoded) colour, not radiance
  (`TiledSplatBlur.cpp` l.2687; same for `GroundTruthAberration.cpp` l.2592).
- Surprise 2: accumulation is front-to-back alpha compositing with the PSF value as alpha, then division by the total
  weight (`convolution_cs.glsl` l.312-316, l.394-396) — occlusion-aware, not a linear energy-conserving convolution.
- Surprise 3: PSF weights are clamped to [0,1] per sample (`PSF/common.glsl` l.555-561 `saturate(scaleWeight(saturate(weight)...))`).

## BRIGHT POINT SOURCE
1. Where the PSF is applied: in a compute pass over the G-buffer colour, registered either after "Effects (HDR) [Begin]"
   (HDR mode) or after "Effects (LDR) [Begin]" (LDR mode) — `TiledSplatBlur.cpp` l.11-16; selection by
   `m_inputDynamicRange` (l.1908-1920). Input read in `fragment_buffer_build_cs.glsl` l.19 (`gbufferAlbedo`).
2. Before/after adaptation: HDR mode = before the tone mapper's auto-exposure; LDR mode (the shipped demo default) = after.
3. Before/after tone reproduction: same as 2 — the demo default is AFTER tone mapping (`TiledSplatBlur.cpp` l.2687).
4. Energy preserved: PSFs are normalized to sum 1 after cropping to 99 % energy (`WavefrontAberration.cpp` l.2863-2872),
   so ~1 % tail energy is redistributed into the core; FrontToBack alpha accumulation + normalization
   (`convolution_cs.glsl` l.312-316, 394-396) is not strictly energy preserving; `Sum` mode exists (l.326-330).
5. Absolute-luminance aware: NO (scene units arbitrary; tone mapper auto-exposes).
6. PSF depends on: pupil diameter YES (2-7 mm), wavelength YES (3 λ), field angle YES (OffAxis), focus/object depth YES,
   age NO (only via user-supplied aberrations), adaptation level NO (pupil is a free parameter, not driven by luminance).
7. HDR source on LDR display: HDR mode — fp16 G-buffer (`Demo.cpp` l.116 `F16`; fragment colour packed with
   `packHalf2x16`, `TiledSplatBlur/common.glsl` l.233-238) is convolved, then the tone mapper (ACES, auto exposure)
   and `saturate(linearToSrgb())` clip (`tonemap_fs.glsl` l.30-34). LDR mode — clipped sRGB values are convolved.
8. Halo changes perceived brightness: not modelled (no perceptual brightness model).
9. Temporal PSF variation: none intrinsic (no fluctuation of accommodation/pupil); PSFs change only when parameters change.
10. Clip before or after convolution: HDR mode → convolution BEFORE clip (clip at `tonemap_fs.glsl` l.34 comes after);
    shipped LDR demo → clip (and sRGB encoding) BEFORE convolution. The HDR path needs the user to switch
    "Input Dynamic Range" in the GUI (`TiledSplatBlur.cpp` l.2559).

## VERDICT
**CODE DONOR** (PSF generation: Zernike/ENZ, pupil, focus, wavelength, field angle; BSD-2). Build BLOCKED here, no
native run, no COMMON output. Not a glare/adaptation/night-vision model.
