# Track vdp-metrics: ColorVideoVDP and FovVideoVDP

The source ids in [brackets] are defined in `sources.md`.

## IDENTITY
| | ColorVideoVDP | FovVideoVDP |
|---|---|---|
| authors | Mantiuk et al., Cambridge gfxdisp [CV4] | Mantiuk, Denes, Chapiro, Kaplanyan, Rufo, Bachy, Lian, Patney [FV3] |
| version | **0.5.7**: PyPI wheel in the repo flake (`nix develop .#video`), sha256 5e0f0d0a…7583 [CV1]. File-identical to git tag v0.5.7 = `2a268bce8d56e2f3abde46df3927d8a633707a24` [CV2] | **1.2.2**: PyPI sdist sha256 1a4db808…ae9e3. File-identical to git tag v1.2.2 = `4e36c59c231162a8c390601f99993f79cd86a47f` [FV1] |
| licence | **MIT** [CV3] | **CC BY-NC 4.0: non-commercial only**; attribution required; redistribution only under the same non-commercial terms [FV2] |
| paper | ACM TOG 43(4) 2024, doi:10.1145/3658144 | ACM TOG 40(4):49 2021, doi:10.1145/3450626.3459831 |
| what it is | A full-reference **metric**: it predicts the visible difference between a test and a reference video on a specified display, in JOD units. It is **not** a renderer and **not** a model of appearance | same, plus eccentricity (fixation-dependent) sensitivity |

## PURPOSE
The intended use is to ask whether a temporal change the renderer produces, such as a lamp that "breathes" or moves by less than a pixel, is visible on the PHONE_TARGET and DESKTOP_TARGET displays, and how visibility depends on gaze. The metric is an instrument for **display-referred visibility**. It says nothing about physical correctness: a high JOD means "hard to tell apart", never "correct".

## HVS COMPONENTS
| component | ColorVideoVDP | FovVideoVDP |
|---|---|---|
| optics | none explicit. Optical MTF is folded into the CSF; there is no glare or PSF | same |
| glare | none | none |
| adaptation | local adaptation from a Gaussian or Laplacian pyramid band. No time course | local adaptation, clamped to at least 0.1 cd/m² [FV7] |
| rods/cones, mesopic/scotopic | castleCSF (colour, cone-contrast based) [CV4]. The CSF lookup covers 0.005–10000 cd/m² only, so there is **no scotopic range** [CV7] | achromatic (luminance) CSF; no rod pathway |
| acuity | through the spatial CSF, driven by ppd | also falls with eccentricity (cortical magnification) |
| temporal state | sustained and transient temporal channels (0 and 5 Hz CSF omega). No adaptation dynamics | same |
| gaze | none (foveal everywhere) | `fixation_point` per frame, `foveated=True` [FV6] |
| display model | **yes, the core of the method**: peak, contrast or black level, EOTF, ambient reflection [CV5, CV6]; ppd fixed or from geometry | yes: physical geometry, and ppd varies with eccentricity [FV5] |
| spectrum | RGB colorimetry (colour spaces in JSON). Not spectral | luminance only |

## NATIVE ENVIRONMENT
- ColorVideoVDP: `nix develop .#video` (repo flake, Python 3.14.7, torch 2.13.0 on CPU).
- FovVideoVDP: `uv venv --system-site-packages --python <.#video python3> research-cache/vdp-metrics/venv` and `uv pip install --no-deps pyfvvdp==1.2.2`. No other packages were needed: numpy, scipy, torch, ffmpeg-python, imageio and matplotlib all come from nix, and PyEXR is unused.
- Upstream checkouts at the pinned tags: `research-cache/vdp-metrics/{cvvdp-src,fvvdp-src}`.
- FreeImage (needed by both examples to read 16-bit PNGs) was fetched with curl and passed through `IMAGEIO_FREEIMAGE_LIB` [IMG].
- Runs use CPU only, 2 threads, under `nice`.

## NATIVE REPRODUCTION (L4)
Script: `nix develop .#video -c bash tracks/vdp-metrics/run_native_examples.sh`. Stages are selected with `STAGE=cvvdp_py|cvvdp_cli|fvvdp`. The examples are run from inside the authors' checkouts, exactly as their READMEs say. Logs are in `results/native/vdp-metrics/NATIVE_*.log`.

| example | our result | authors' reference | status |
|---|---|---|---|
| cvvdp `examples/ex_simple_image.py` (standard_4k) | noise 9.888, blur **8.514** | comment in the file: noise 8.955, blur 8.514 | blur exact. The noise reference is **stale**: 0.5.6 changed `imnoise` from Gaussian to seeded uniform noise [CV8]. Re-running with the authors' pre-0.5.6 `imnoise`, restored from git (`check_stale_reference.py`), gives **8.952 / 8.959 / 8.960** for 3 seeds, matching 8.955. PASS |
| cvvdp `examples/ex_hdr_images.py` | noise 9.454, blur **8.696** | 9.450, 8.696 | PASS. The noise term is random (`np.random.randn`) |
| cvvdp `examples/ex_simple_video.py` | static noise 9.703, dynamic noise 9.852 | none stated | runs |
| cvvdp CLI (README) `--test example_media/aliasing/ferris-*-*.mp4 --ref ferris-ref.mp4 --display standard_fhd` | bicubic-bicubic 5.519, bicubic-nearest 5.217, nearest-bicubic 5.655, nearest-nearest 5.429 | none stated | runs |
| fvvdp README simple image (`pytorch_examples/ex_simple_image.py`, standard_4k) | noise **9.535** and 9.538 in two runs (unseeded noise), blur **8.693** | 9.537, 8.693 | PASS |
| fvvdp README CLI aliasing (standard_fhd) | 6.4691, 6.3283, 5.9226, 5.8213 | 6.469, 6.328, 5.923, 5.821 | **exact PASS** |
| fvvdp `pytorch_examples/ex_foveated_video.py` (htc_vive_pro, moving gaze) | 9.843 JOD (130 s) | none stated | runs |

**NATIVE verdict: PASS for both.**

## COMMON STIMULUS (L5, label ADAPTED: a metric-plumbing demo)
Script: `tracks/vdp-metrics/l5_s6_visibility.py {cvvdp|fvvdp} results/common/vdp-metrics`. Each tool runs in its own process [BOTH].

- **Question:** is the temporal change in **S6** visible? S6 is an unresolved white source (E = 8.9e-5 lx at the eye) moving 1 stimulus px (1.9′) in 2 s, 48 frames at 24 fps [S6]. The test is S6 as it moves; the reference is S6 frame 1 repeated 48 times.
- **Display formation (ADAPTED; our choice, not the metric's):**
  1. Resample the linear cd/m² frames bilinearly from 32 px/deg to the declared target ppd (73.0 and 48.4) *before* any mapping (lesson from M2.6). The luminance integral of the point is preserved to 0.970 on phone and 0.9999 on desktop.
  2. Crop to the phone's 1920×820 content window; the desktop keeps the full 1548×774.
  3. Apply one fixed exposure so that **the peak pixel of the static frame 1 = display white**, then clip. S6's per-frame peak varies with sub-pixel phase (74.7–114 cd/m² after resampling), so **46 of 48 moving frames clip**. Variant "allframes": the exposure maps the brightest moving frame to white, and nothing clips.
  4. Encode with the sRGB OETF (float16, or 8-bit).
  5. The metric's display model turns the code values back into cd/m². The sky (4e-4 cd/m²) maps to about 5e-6 of white, i.e. to the display black level: 1 cd/m² on the phone, 0.2 cd/m² on the desktop.
  6. Configs: `display_models_cvvdp_targets.json` (cvvdp: every number from `stimuli/display_targets.json` with an explicit `pixels_per_degree`, no default ppd) and `fvvdp_config/display_models.json` (fvvdp: physical geometry of the same targets).

| tool / display model | variant | JOD (10 = no visible difference) |
|---|---|---|
| cvvdp hnp_phone_target (73.0 ppd, 100 cd/m², 100:1) | frame-1 exposure, float / 8-bit | **9.844 / 9.845** |
| cvvdp hnp_phone_target | allframes exposure (no clip) | 9.865 |
| cvvdp hnp_desktop_target (48.4 ppd, 200 cd/m², 1000:1) | frame-1 exposure, float / 8-bit | **9.835 / 9.835** |
| cvvdp hnp_desktop_target_physical_centre_ppd (44.86 ppd) | float | 9.837 |
| cvvdp hnp_desktop_target | allframes exposure | 9.844 |
| cvvdp control: static vs static (phone, desktop) | – | 10.000 / 10.000 |
| fvvdp hnp_phone_target (physical centre ppd 71.8) | fixation **on the source** | **9.807** |
| fvvdp hnp_phone_target | fixation **10° right** of the source | **9.882** |
| fvvdp hnp_desktop_content (44.9 ppd) | fixation on the source | **9.866** |
| fvvdp hnp_desktop_content | fixation 10° right | **9.902** |

Results are in `results/common/vdp-metrics/ADAPTED_S6_{cvvdp,fvvdp}_results.json`, which records every display parameter, exposure, clip count and metric info string, and in `ADAPTED_S6_{phone,desktop}_displayframes_1_24_48_crop.png` (the displayed point at frames 1, 24 and 48, enlarged 12×).

**Reading.** The drift of 1.9′ over 2 s, combined with the sub-pixel changes in peak and shape, is predicted to be only slightly visible: 0.13–0.19 JOD below 10 when foveated. A difference of 1 JOD means 75 % of observers pick the reference, so 0.16 JOD is about 54 %. ColorVideoVDP ranks the phone and desktop nearly the same. 8-bit quantisation and the declared-vs-physical ppd make no difference (≤ 0.003 JOD). Clipping lowers the JOD slightly: with clipping the peak modulation is removed, but the clipped core stays bright. FovVideoVDP gives the expected direction for gaze: fixating 10° away raises the JOD (the change is less visible) from 9.807 to 9.882 on the phone and from 9.866 to 9.902 on the desktop. With fixation on the source it rates the phone (71.8 ppd) change as more visible than the desktop one (44.9 ppd). **This is plumbing only.** The metric sees a photopic 1–200 cd/m² SDR frame, not the night scene. Its CSF has no scotopic branch [CV7], and the result depends entirely on our ad-hoc exposure.

## ASSUMPTIONS
- **Input to both tools:** display-encoded sRGB (BT.709) code values in [0,1]. Absolute cd/m² comes only from the display model: peak, contrast, 0 lux ambient, and the default k_refl of 0.005 (which is irrelevant at 0 lux).
- **Colour:** cvvdp works in RGB (the stimulus is D65 white, so R = G = B); fvvdp uses luminance.
- **Geometry:** from `stimuli/display_targets.json` only. cvvdp uses the declared `px_per_deg_centre` (73.0 and 48.4). fvvdp has to use physical geometry and so gets 71.8 and 44.9 at the centre. The file's values are **mean** ppd over the width, not the centre value [DT]; a cvvdp sensitivity run at 44.86 changed the JOD by +0.003. For the desktop, the fvvdp "display" is the 1548×774 image region at the monitor's pixel pitch, because fvvdp assumes the image fills the display [FV5].
- **Absolute scale:** the exposure is ours (frame-1 peak = white); it is not a tone mapper and not pcond.

## VALIDATION
- The NATIVE examples reproduce the authors' numbers (above), including a stale reference traced to a code change.
- The COMMON runs are only sanity-checked: static vs static gives exactly 10 JOD, and the effect of 8-bit quantisation is negligible.
- There is no ground truth for S6 visibility.

## REUSE
- **ColorVideoVDP:** MIT, already in the flake (`.#video`). Suitable as a **behavioural oracle** for display-referred temporal visibility (e.g. M2.5/M2.6 clips, a "breathing" lamp vs a static one) at the declared display models in `display_models_cvvdp_targets.json`.
- **FovVideoVDP:** **CC BY-NC 4.0**. Fine for this non-commercial research; do not vendor it or ship it in anything commercial. It is not added to the flake; it is installed with uv into research-cache. Its unique value is the fixation and eccentricity dependence.
- Nothing from either tool was copied into `tracks/`; only wrappers, configs and runners were written.

## FAILURES / SURPRISES
- The two packages cannot be imported in one Python process: both define a top-level module `interp` [BOTH].
- cvvdp only accepts a `config_paths` JSON file whose basename **starts with `display_models`**. Our first name (`cvvdp_display_models_targets.json`) was silently ignored, and the run fell back to the built-in file and failed with "display model not found".
- fvvdp `predict()` accepts only uint8, uint16 and float32. cvvdp also accepts float16.
- The fvvdp README examples end with `plt.waitforbuttonpress()`, which hangs headless runs forever. We used `MPLBACKEND=Agg` and unbuffered output.
- FreeImage (for 16-bit PNG) cannot be auto-downloaded behind the proxy (Python's strict TLS check rejects the proxy CA), and nixpkgs has removed it [IMG].
- cvvdp's `ex_simple_image.py` reference comment is stale since 0.5.6 [CV8].
- `stimuli/display_targets.json` labels mean ppd as `px_per_deg_centre` [DT]. We did not change it (the file is frozen).
- Our bilinear resample preserves the luminance integral of an unresolved point to only 0.970 at ×2.28 (phone); it is 0.9999 at ×1.51.
- S6's per-frame peak varies by about 1.5× with sub-pixel phase, although its energy is constant, so a fixed exposure clips most frames.

## BRIGHT POINT SOURCE
1. Where the optical PSF is applied: nowhere. Neither metric applies an optical PSF or glare; the optics are only implicit in the CSF.
2. Before or after adaptation: not applicable. Local adaptation is computed from the displayed image itself, after the display model.
3. Before or after tone reproduction: the metric runs **after** tone reproduction and the display; it compares displayed frames.
4. Energy preserved: not applicable (a metric). Our display formation preserved the integral to 0.97–1.00, and then the clip removes energy by design.
5. Absolute-luminance aware: **yes**, through the display model (cd/m² of the display). The CSF range is 0.005–10000 cd/m² for cvvdp, and fvvdp clamps adaptation at 0.1 cd/m².
6. Does the PSF depend on adaptation, pupil, age, wavelength or field angle: not applicable (no PSF). The CSF depends on luminance and, in fvvdp, on eccentricity. There is no pupil and no age.
7. How an HDR source is shown on an LDR or HDR display: not the metric's job. It takes whatever the pipeline displays. Here the pipeline was a fixed exposure with the point peak at white, clipped.
8. Does the halo change perceived brightness: not modelled; the metric predicts difference visibility, not brightness.
9. Temporal PSF variation: no PSF. Temporal *changes on the display* are what the metric measures (sustained and transient channels).
10. Clip before or after convolution: not applicable. In our L5 display formation, the resample (a kind of convolution) comes before the clip.

## VERDICT
- ColorVideoVDP: **BEHAVIORAL ORACLE** for display-referred visibility of temporal changes at the target displays. RUNNABLE, MIT, in the flake.
- FovVideoVDP: **BEHAVIORAL ORACLE** with gaze and eccentricity. RUNNABLE, CC BY-NC 4.0.
- For both, NATIVE PASS and COMMON (ADAPTED plumbing demo) done.

## Files
- `run_native_examples.sh`: L4 runner.
- `check_stale_reference.py`: traces the stale 8.955 reference.
- `l5_s6_visibility.py`: L5 demo.
- `display_models_cvvdp_targets.json` and `fvvdp_config/display_models.json`: L2 display models.
- `results/native/vdp-metrics/NATIVE_*.log`
- `results/common/vdp-metrics/ADAPTED_S6_*`
