# Track `iset`: ISET3d + ISETBio + ISETCam (+ isetvalidate)

## IDENTITY
- **ISETCam** https://github.com/ISET/isetcam @ `b66ecb6` (2026-09-16). Base library: scene, optical image (oi), wavefront optics, sensor. MIT.
- **ISETBio** https://github.com/isetbio/isetbio @ `af1cf15` (2026-09-23). Human front end: lens and macular pigment, cone mosaic (`cMosaic`), outer segment photocurrent, eye movements, RGC work. Needs ISETCam on the path (README, "As of May 27, 2024"). MIT.
- **ISET3d** https://github.com/ISET/iset3d @ `177300f` (2026-08-22). MATLAB front end that writes PBRT-v4 scenes and runs them in Docker. This repo is the former **iset3d-tiny**: `ISET/iset3d-tiny` resolves to the same HEAD commit, and the iset3d README History says "May 29, 2024 - This repository was called iset3d-tiny in the past". MIT.
- **iset3d-v4** https://github.com/ISET/iset3d-v4 @ `d6a6492` (2025-03-14) is **deprecated**. Its README says "We are now using ISET3d-tiny exclusively" and that scene data moved to https://purl.stanford.edu/cb706yg0989. I cloned it only to read the README and then deleted the clone (4.4 GB).
- **isetvalidate** is at https://github.com/ISET/isetvalidate @ `14a1eef` (2026-07-22). `isetbio/isetvalidate` is not public: git asks for credentials. The ISETBio README points to `ISET/isetvalidate`.
- **Recommended combination (E1):** ISETCam `main` + ISETBio `main` + ISET3d `master` (the former tiny repo) + ISET/isetvalidate `main`, plus the UnitTestToolbox (isetvalidate README). The repos are rolling and publish no release tags; exact commits are in `clone_heads.txt`.

## PURPOSE
Scientific simulation of the human visual front end from spectral radiance: optics, then retinal irradiance, then cone and rod absorptions, then photocurrent. ISET3d adds ray-traced 3D scenes and a PBRT `humaneye` camera for schematic eyes (Navarro, Le Grand, Arizona). It is **not** a display renderer or a tone mapper.

## HVS COMPONENTS (E7, with files)
- **Optics, default human.** `oiCreate('wvf human', pupilMM, zCoefs, wave)` (isetcam/opticalimage/oiCreate.m:297-316) uses the Thibos et al. 2009 mean Zernike coefficients for 3, 4.5, 6 and 7.5 mm pupils. It picks the next measured pupil at or above the request and rejects pupils above 7.5 mm (isetcam/opticalimage/optics/opticsCreate.m:197-256). The data are Thibos VirtualEyes, isetcam/data/optics/thibosvirtualeyes/IASstats{30,45,60,75}.mat, whose licence is research-only (license.txt). Also available: Marimont-Wandell `'human mw'`, and eccentricity-varying Polans2015, Artal2012 and Thibos2002 ensembles for cMosaic (isetbio/cones/cmosaic/@cMosaic/oiEnsembleGenerate.m:69).
- **Longitudinal chromatic aberration.** The human LCA formula is in isetcam/opticalimage/wavefront/wvfLCAFromWavelengthDifference.m (Thibos et al. 1992 sign convention). The default in-focus wavelength is 550 nm. Transverse chromatic aberration comes only through Zernike tilt terms.
- **Pupil.** Size is a user parameter. There is **no** luminance-driven pupil model in the oi path.
- **Lens and macular pigment.** `Lens` (isetbio/opticalimage/@Lens/Lens.m) is attached in oiCreate. `Macular` lives in the cone mosaic.
- **Wide-angle scatter and glare.** **Not in the oi pipeline.** The Thibos wavefront PSF has a finite support (about 12 arcmin in E9) and no intraocular straylight term. `isetcam/human/ijspeert.m` implements the IJspeert 1993 PSF, which includes age and pigmentation scatter, but it is only called by example scripts (isetcam/examples/optics/s_opticsImageFormation.m:439, isetbio/examples/human/s_humanLSF.m:124), not by oiCompute. No CIE glare spread function exists in either repo.
- **Cones.** `cMosaic` handles eccentricity-varying L/M/S cone mosaics with apertures, macular pigment and optional rod-intrusion aperture shrinkage (cMosaic.m:41, 70-73). `coneMosaicRect` is the older rectangular mosaic.
- **Rods.** There is a rod spectral sensitivity (isetcam/data/human/ieRodSpectralSensitivity.m, `rods.mat`), a scotopic luminance function (isetcam/color/ieScotopicLuminanceFromEnergy.m) and rod **absorption** calculations (isetbio/examples/human/s_humanRodAbsorptions.m, isetvalidate/isetbio/calibration/v_ibio_calibrationRods.m). The examples build a monochrome "rod" sensor or a single-type coneMosaicRect. **I found no rod mosaic class, rod photocurrent or rod-cone interaction model.** `osBioPhys` is the Rieke cone phototransduction cascade (isetbio/cones/outersegment/@osBioPhys/osBioPhys.m).
- **Mesopic and scotopic vision.** Only as rod absorptions and scotopic photometry. There is no mesopic combination rule.
- **Acuity.** Emerges from optics plus the cone mosaic (and RGC models under development). There is no separate acuity model.
- **Temporal response.** `osLinear` and `osBioPhys` give photocurrent over time with adaptation (v_ibio_coneAdaptation passes). Fixational eye movements are in isetbio/eyemovement. The optics are static: there is no temporal PSF.
- **Gaze.** Only fixational eye movements. There is no gaze or saccade planning.
- **Display model.** ISETCam `displayCreate` (for example, OLED/LCD SPDs) converts RGB images into spectral scenes. It is not a model of the viewer's display.
- **Spectrum.** Fully spectral, 400-700 nm at 10 nm by default (configurable).

## NATIVE ENVIRONMENT (E2)
- **MATLAB.** The developer skill files name R2025b and R2026a (isetcam/.github/skills/matlab-environment-setup/SKILL.md:45, matlab-evaluation/SKILL.md:42). The code uses App Designer windows (`sceneWindow_App`, `oiWindow_App`), graphics-object dot syntax, `tiledlayout` (R2019b+) and classdef `matlab.mixin.Copyable`. The toolboxes it calls include Image Processing (`imresize`), Computer Vision (`insertShape` in wvfAperture.m:151) and Statistics (`poissrnd`). No minimum version is stated.
- **ISET3d.** Needs MATLAB and **Docker**. PBRT-v4 always runs in a container; the CPU image is `digitalprodev/pbrt-v4-cpu` and the GPU image is `vistalab/pbrt-v4-gpu` (iset3d/docs/setting-up-iset3d.md). The PBRT fork is https://github.com/ISET/pbrt-v4. The `humaneye` camera is CPU-only in practice (iset3d/docs/sceneEye-gpu.md). Scenes are downloaded from the Stanford Digital Repository.
- **Here.** There is no MATLAB. The Docker CLI 29.3.1 is installed but no daemon is running (`/var/run/docker.sock` is missing). The PBRT image pull (several GB) would also break the disk budget. I used **GNU Octave 11.3.0** from the repo-pinned nixpkgs with the Octave-Forge packages that ISETCam's own `ieInit.m` loads under Octave (lines 50-58: general, image, io, optiminterp, signal, statistics). Build it with `scripts/build_octave_env.sh`; no flake edit is needed.

## NATIVE REPRODUCTION (E4-E6)
Command, per script: `tracks/iset/scripts/run_octave.sh <script.m> <log>`. For the whole set: `tracks/iset/scripts/run_batch.sh`. Logs are in `results/native/iset/logs/`, with a table in `results/native/iset/RESULTS_INDEX.csv`.

Octave needs GUI and startup shims (`scripts/octave_shim/`). They contain no computation:
- `ieInit`: the upstream script defines a local function after its first use, and Octave fails with "'localCalledFromUnitTest' undefined near line 42".
- `ieNewGraphWin` and `ieFigure`: figure dot syntax.
- `sceneWindow`, `oiWindow` and `sensorWindow`: App Designer windows.
- `tiledlayout` and `nexttile`.
- `contains`: MATLAB builtin missing in Octave.

| script | result |
|---|---|
| isetbio `t_wvfHuman.m` (official tutorial) | **PASS** (runs to end) |
| isetbio `s_humanOptics.m` (human OTF, Thibos vs Marimont-Wandell) | **PASS** |
| isetvalidate `v_icam_oiWVF` (OTF identity asserts) | **PASS** |
| isetvalidate `v_icam_wvfWaveDefocus` | **PASS** |
| isetvalidate `v_ibio_calibrationRods` (assert within 5% of 7.5e5 R*/rod/s) | **PASS**: 772,461 R*/s |
| isetvalidate `v_ibio_calibrationPugh` | **PASS** |
| isetvalidate `v_ibio_coneAdaptation` (osBioPhys) | **PASS** |
| isetcam `t_oiIntroduction` (official ISETCam tutorial) | FAIL at oiPlot.m:200 (graphics dot syntax) |
| `v_icam_opticsWVF`, `t_humanLineSpreadOI`, `s_humanLSF` | FAIL in plotting (oiPlot.m:200, imageMultiview.m:118) |
| `t_osFoveaPeriphery`, `v_ibio_pigments` (cMosaic / photoPigment) | BLOCKED: "class not found: matlab.mixin.Copyable" |
| `v_icam_opticsFlare` | BLOCKED: `insertShape` (Computer Vision Toolbox) |
| `v_ibio_photonNoise` | FAIL: "poissrnd: LAMBDA must not be complex" (Octave `ifft2` leaves about 1e-8 relative imaginary residue) |

**Status: PARTIAL PASS.** The wavefront-optics, oi, rod/cone calibration and cone-adaptation computations reproduce their own validation asserts under Octave. Everything that uses `cMosaic` or classdef is **BLOCKED (MATLAB licence)**, as is the full ISET3d/PBRT path (MATLAB plus a Docker daemon). I spent about 40 minutes on Octave compatibility.

## COMMON STIMULUS
S0 is an isolated D65 point source: 800 cd at 3 km, E = 8.9e-5 lx, on a 4e-4 cd/m^2 sky, at 32 px/deg.
- `c1_prepare.py` cuts a 64x64 px crop from `S0_Y.pfm` and checks energy: the crop integral gives 8.8889e-5 lx, matching meta.json.
- `c2_common_S0.m` turns the crop into an ISETCam scene. The D65 SPD is scaled per pixel to the stimulus cd/m^2 with `sceneAdjustLuminance` (absolute), and the field of view is 2 deg. It then runs unmodified `oiCreate('wvf human',{3,7})` and `oiCompute`.
- `c3_report_S0.py` makes the report.

Results (`results/common/iset/COMMON_S0_*`): at 32 px/deg the optics leave the footprint almost unchanged. The source pixel holds 0.250 of the energy in the stimulus, 0.245 on the retina at 3 mm and 0.245 at 7 mm. The 3x3 block holds 0.9999 in the stimulus and 0.988 on the retina at both pupils. Peak-to-background ratio is 1.87e5 in the stimulus and 1.74e5 / 1.77e5 on the retina. **The Thibos-mean-eye model creates no visible halo at display resolution.** Viewing geometry (PHONE/DESKTOP targets) is not used, because ISETBio outputs a retinal image, not a display image.

## ASSUMPTIONS
- Input is spectral radiance in absolute units (W or quanta per sr per m^2 per nm). Scenes can be scaled to cd/m^2 with `sceneAdjustLuminance`.
- The output oi is spectral irradiance in photons, and `oiGet 'illuminance'` gives lux.
- Geometry comes from the scene field of view in degrees and 300 um/deg on the retina (opticsCreate.m:224).
- The PSF is shift-invariant over the field, except in the cMosaic ensembles.
- For COMMON I assumed the pack's white is D65 (stated in the pack), 3 mm and 7 mm pupils (no pupil model), and focus at 550 nm.

## VALIDATION
The upstream isetvalidate numeric asserts listed above pass. E8/E9 are **ADAPTED**: unmodified functions, my spectra, under Octave.
- **E9** (`ADAPTED_e9_psf_vs_wavelength_pupil.png`, plot of the model's own `wvfGet(...,'psf')`): the PSF is sharpest at 550 nm and widens strongly at 450 and 500 nm (LCA defocus). At 6 and 7 mm the 450 nm PSF stays above 1e-1 of peak out to about 10 arcmin.
- **E8** (`ADAPTED_e8_point_source_metrics.csv`), photopic EE90:
  - LPS: 1.2-1.7'
  - HPS (CIE HP1): 1.5-1.9'
  - warm LED (CIE LED-B1): 2.0-2.2'
  - equal energy: 2.0-2.4'
  - BLUE (460 nm): 4.1-5.2'
- **E8, scotopic (V'-weighted) EE90:** about 3.2-3.6' for HPS and LED at 6 mm. The rod-weighted image of a point is about twice as wide because short-wavelength light is defocused when focus is set at 550 nm. The model does not include night-myopia refocusing.
- Sampling limits: the scene is 0.5 arcmin/px, so values below about 0.5' are quantised. The 4.5 mm and 6 mm results are nearly identical because both use the 6 mm Thibos coefficients.

## REUSE
- **Code:** MIT (ISETCam, ISETBio, ISET3d). The Thibos VirtualEyes data are for research use only; commercial users must contact Indiana University (isetcam/data/optics/thibosvirtualeyes/license.txt). isetvalidate has a LICENSE file (MIT header).
- **Recommended role:** a spectral oracle for "retinal image of a point source vs wavelength, pupil and spectrum" and for rod/cone absorption counts. For those questions it should be run in MATLAB. This track copies no upstream code; the shims are new wrappers.

## FAILURES / SURPRISES
- ISETCam contains explicit Octave hooks (ieInit.m:50-58), but its own `ieInit` still fails under Octave (local function ordering).
- The computational oi and wvf core works in Octave. The plotting layer does not (MATLAB graphics objects), and neither does anything classdef-based, including the whole cMosaic retina.
- Octave FFT convolution leaves about 1e-8 imaginary parts in oi photons. That is harmless for my analysis (I take the real part) but breaks `poissrnd` in `oiPhotonNoise`.
- iset3d-v4 is 4.4 GB and deprecated. The current iset3d is the renamed iset3d-tiny.
- **ISETBio models no straylight in its default optics**, even though an IJspeert function ships in the repo.

## BRIGHT POINT SOURCE
1. **Where the PSF is applied:** in `oiCompute`, on the spectral scene radiance, per wavelength (OTF multiplication), before any receptor stage.
2. **Before or after adaptation:** before. Adaptation happens only later, in the outer segment (osBioPhys/osLinear).
3. **Before or after tone reproduction:** there is no tone reproduction. ISET simulates the retina, not a display image.
4. **Energy preserved:** yes. The OTF is normalised at DC; in COMMON S0, 99.8% of the energy is inside 9x9 px. The lens transmittance removes energy spectrally, as it should.
5. **Absolute-luminance aware:** yes. Photons are in absolute units, and rod/cone absorptions scale with them.
6. **What the PSF depends on:** pupil yes (a parameter, not driven by adaptation level); wavelength yes (LCA plus diffraction); age only through the IJspeert example function and Lens density, not in the default path; field angle only in cMosaic's Polans/Artal ensembles; adaptation level no.
7. **How an HDR source is shown on a display:** not applicable. ISET produces retinal images; `oiShowImage` is only a gamma preview.
8. **Does the halo change perceived brightness:** not modelled, since there is no perception or brightness stage. The default optics produce no wide halo in any case.
9. **Temporal PSF variation:** no. The optics are static. Fixational eye movements and cone photocurrent dynamics exist but do not change the PSF, and there is no pupil hippus or microfluctuation of accommodation. **Nothing in ISET makes a light "breathe".**
10. **Clip before or after convolution:** no clipping anywhere in the oi path. Floating point runs throughout.

## VERDICT
**SCIENTIFIC ORACLE.** The spectral human optics (Thibos mean eye with LCA, pupil and lens) and the rod/cone absorption calibration are runnable here under Octave, and their own validation asserts pass. The cone mosaic, the full tutorials and ISET3d are BLOCKED (MATLAB licence plus a Docker daemon).
