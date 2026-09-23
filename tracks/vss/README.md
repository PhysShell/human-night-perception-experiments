# Track `vss` — University of Stuttgart VISUS "Visual System Simulator" (Rust, wgpu)

## IDENTITY
- Repository: https://github.com/UniStuttgart-VISUS/visual-system-simulator, branch `wgpu`, commit
  `22055373eccf4b50220df8f6f57751851ed34e8c` (2026-08-05, "Unify run.ps1"), cloned to
  `research-cache/vss/visual-system-simulator` (gitignored). The default branch `main` (`17cd907`, 2023-03-08) is the
  older gfx-rs/OpenGL/glutin version; the actively maintained wgpu branch was used as instructed (its README documents
  a headless `render` subcommand).
- License: Apache-2.0 (`LICENSE`, `vss/Cargo.toml` `license = "Apache-2.0"`), © 2017 University of Stuttgart. Reuse and
  redistribution allowed with notice.
- Paper: Schulz, Rodrigues, Amann, Baumgartner, Mielke, Baumann, Sedlmair, Weiskopf, *A Framework for Pervasive Visual
  Deficiency Simulation*, IEEE VR 2019, doi:10.1109/VR44988.2019.9044164; author PDF
  https://www.vis.uni-stuttgart.de/documentcenter/staff/sedlmaml/papers/schulz2019deficiencySim.pdf (fetched to
  `research-cache/vss/papers/schulz2019.pdf`; the visvar.github.io mirror returns 404).

## PURPOSE
Cross-platform real-time **visual deficiency simulator** (cataract, myopia/hyperopia/presbyopia/astigmatism,
nyctalopia, colour-vision deficiencies, AMD, glaucoma, strabismus) for images, video, camera and XR (README
"Features"; catalog articles in `vss-catalog/articles/`). Its normal-eye configuration is the identity.

## HVS COMPONENTS (G3/G4)
Pipeline per eye (`vss-desktop/src/flow.rs` l.395-407): Upload → EyeControl → **Cataract** → **Lens** → **Retina** →
PeacockCB → VarianceMeasure → MetricOverlay → Display → Download. Intermediate colour is Rgba32Float
(`vss/src/node/slot.rs` l.12) but inputs are 8-bit.

| component | normal eye? | impairment? | where / what |
|---|---|---|---|
| lens / refraction (optics) | inactive by default (`active = 0` unless presbyopia or refraction enabled, `vss/src/node/lens/mod.rs` l.293-341) | myopia/hyperopia/presbyopia/astigmatism | GPU ray tracer through 4 spherical/ellipsoidal surfaces (inner/outer lens, inner/outer cornea) with refractive indices and radii "obtained via machine learning, using a particle swarm optimisation algorithm" (`lens/lens_model.wgsl` l.1-33); accommodation by depth-dependent lens radii (l.35-75); defocus emulated by scaling the anterior-chamber index with exponents 0.08/0.12 marked "TODO factor" (`lens/mod.wgsl` l.342-351); colour = mean of 8 ray samples (`samplecount` 4) through the depth map (`lens/mod.wgsl` l.353-406, l.249-314). Diopters mapped by `(value/50-1)*3` (`lens/mod.rs` l.309). No diffraction, no aberration polynomials, no PSF, no chromatic dispersion. Paper: parameters "not always physiologically plausible" (`schulz2019.txt` l.327-329) |
| cornea | default flat corneal map | corneal map deflections | `lens/mod.wgsl` l.109-116 (`CORNEA_MAP_FACTOR` 0.2) |
| scattering / cataract | off by default | cataract | not physical scattering: separable 9-tap Gaussian blur (`common.wgsl` l.1-60, `BLUR_SIZE = 9`) + "bloom" `color * (1 + Y*c)` with Y = 0.299R+0.587G+0.114B (`common.wgsl` l.145-182) + contrast reduction toward the max channel (`cataract/mod.wgsl` l.15-40, l.97-150); parameters scaled ×0.01 (`cataract/mod.rs` l.175-190) |
| retina / receptors | identity (`track_error = -1` when no map feature is on, `retina/mod.rs` l.439-446; `retina_map/mod.rs` l.161-168) | glaucoma, AMD, colour deficiency, achromatopsia, nyctalopia | retina map = cube map RGBA, RGB = L/M/S cone "health", A = rods (README "Retina Map"; `retina_map/mod.rs` l.237-260 min-merge). Optional receptor-density map from digitized Østerberg (1935) cone/rod densities (`retina_map/osterberg.rs`, `receptor_density.rs`; source digitization `doc/receptor-density/osterberg-digitized.csv`) — but only used as a mask, not as sampling |
| nyctalopia ("night blindness") | NO | yes | `applyNyctalopia` (`retina/mod.wgsl` l.191-220): if `5·Y < 1` then `color = a·color + (1-a)·5Y·color`, a = rod value from map; severity map `nyctalopia.rs` l.9-19 sets a = 1 - severity. An ad-hoc darkening of dark pixels of an sRGB image — **not** a scotopic/mesopic model, no luminance units, no adaptation |
| colour vision | NO (identity) | protan/deutan/tritan/achromat | retina: fixed 3×3 matrices blended by receptor weights (`retina/mod.wgsl` l.108-189); PeacockCB: "modified version of https://raw.githubusercontent.com/jkulesza/peacock/master/python/peacock.py" (`peacock/mod.wgsl` l.1) |
| glare | NO | only as "bloom" inside cataract/achromatopsia (`retina/mod.wgsl` l.68-106) | multiplicative brightness boost of each pixel, no spatial spread beyond the 9-tap blur |
| adaptation, mesopic/scotopic, temporal state | NO | NO | none; hemeralopia preset is explicitly "an illustrative approximation ... cannot represent adaptation" (`vss-catalog/articles/hemeralopia/hemeralopia.md` l.18-20) |
| acuity | NO | via blur maps | |
| gaze | yes (EyeControl node, mouse/gaze → retina map projection `gaze_inv_proj`, `retina/mod.wgsl` l.239-252) | | |
| display model | NO | | display pass copies texture (`display/mod.wgsl` l.63-68) |
| spectrum | NO (8-bit sRGB RGB) | | |

## NATIVE ENVIRONMENT
Rust (edition 2021, wgpu 29, winit, egui) via `./run.ps1 desktop start` = `cargo run -p vss-desktop --release`
(`vss-desktop/run.ps1`); a GPU with Vulkan/Metal/DX12/GL. Here: cargo 1.98.0 / rustc 1.98.1 from the pinned nixpkgs,
**no GPU** → Mesa 26.2.3 lavapipe (llvmpipe, software Vulkan 1.4) from the pinned nixpkgs via `VK_ICD_FILENAMES`.
Build needed extra system inputs only: cmake + X11 headers (`libx11`, `xorgproto`) for the `openxr-sys` build script
(first attempt failed: "xlib backend selected, but BUILD_WITH_XLIB_HEADERS either disabled or unavailable",
then "X11/Xlib.h: No such file or directory"; fixed via CPATH/CMAKE_INCLUDE_PATH, no source change).
Scripts: `tracks/vss/build.sh`, `tracks/vss/env.sh`.

## NATIVE REPRODUCTION (G1, G2)
- Build: `tracks/vss/build.sh` → `Finished release profile in 5m 24s` (third attempt; log
  `research-cache/vss/logs/build3.log`). Binary kept at `research-cache/vss/bin/vss-desktop`; `target/` deleted to save disk.
- Examples: bundled presets on bundled assets with the headless batch renderer, e.g.
  `vss-desktop render --force --config vss-catalog/presets/dysadaptation/dysadaptation-nyctalopia-severe.json
  --output 'results/native/vss/NATIVE_{stem}.{config}.{extension}' assets/shanghai-night.png`
  (all runs: `tracks/vss/run_native.sh`; ~1-3 s per 1920×1080 image on lavapipe, `results/native/vss/native_run.log`).
  Runs: normal (no config) on marketplace, marketplace.rgbd, shanghai-night; nyctalopia severe (+ from-map) on
  shanghai-night and marketplace; cataract mild/severe; myopia severe (rgbd depth input).
- Result: **PASS with a defect**. Every preset renders and produces its intended effect (myopia: depth-dependent
  defocus blur; cataract: blur + washed-out contrast; nyctalopia: darkened/desaturated dark regions). Defect found:
  the headless `render` path writes the Display pass into an `Rgba8UnormSrgb` target (`vss-desktop/src/cmd/render.rs`
  l.222) while inputs are uploaded as linear `Rgba8Unorm` without decoding (`vss/src/node/rgb_buffer/upload.rs` l.223),
  so every output equals sRGB-OETF(expected): input 0.2118 → output 0.4980 = sRGB(0.2118) (`oiiotool --diff`,
  `native_run.log`). The interactive surface path strips the sRGB suffix (`vss/src/surface.rs` l.42), so this is
  specific to batch rendering. Undoing that single extra encode (`tracks/vss/undo_extra_srgb.py`, format conversion only;
  outputs labelled ADAPTED) makes the normal-eye output identical to the input within ±1 8-bit code
  (`results/native/vss/identity_check.txt`: mean 0.19 / 0.17 codes, max 1).
- The published nyctalopia teaser (`doc/teaser-nyctalopia.jpg`, 2019, copied as `NATIVE_published_teaser-nyctalopia.jpg`)
  came from the old OpenGL version with unknown settings (peripheral blur + vignette); the current presets do not
  reproduce it pixel-wise — qualitative reference only.

## COMMON STIMULUS (G6)
- Input: VSS decodes images with `image::...to_rgba8()` (`upload.rs` l.133-141) — display-referred 8-bit only, no HDR/EXR
  path. The compatible form of S7 is therefore the frozen baseline's LDR display image
  `results/baseline/S7/S7_BASELINE.png` (pcond LC → sRGB, 1920×820, 32 px/deg; label of the input: BASELINE).
- Configuration: neutral/normal = no config (all simulation nodes default/off). No disease parameter touched.
- Geometry: VSS's normal-eye path has no viewing-geometry input (lens inactive, retina identity), so
  `stimuli/display_targets.json` values cannot be applied — not applicable, no silent default used.
- Command: `tracks/vss/run_common.sh`. Output: `results/common/vss/COMMON_S7_BASELINE.vss.png` (raw, with the extra
  sRGB encode) and `ADAPTED_S7_BASELINE.vss.srgbfix.png`.
- Result: after the encode fix, identical to the input within 1 code (mean 0.002 codes, 0.35 % of pixels differ by 1;
  `results/common/vss/identity_check.txt`). The 2×2 clipped lamp cores are passed through unchanged: **VSS's normal eye
  adds nothing** (no PSF, no glare, no adaptation) to the bright-point problem.

## ASSUMPTIONS
- Input: 8-bit sRGB (camera/image/video), treated as linear numbers in shaders (Y = 0.299R+0.587G+0.114B on sRGB codes,
  `common.wgsl` l.145-149). No cd/m², no absolute scale; paper: "we hope that HDR images might help to better represent
  sources of light in image space, which is important for glare effects" (`schulz2019.txt` l.338-340).
- Geometry: lens model in mm with a fixed image plane and a hard-coded 1920×1080 resolution in `getTargetLocation`
  ("TODO why is the resolution hardcoded ?", `lens/mod.wgsl` l.123-124); depth range 200-5000 mm defaults (`lens/mod.rs` l.79-80).
- Display: none.

## VALIDATION
None quantitative. Paper: "We left it open to future work to fully validate our simulation with real users ... we partially
succeeded in validating our simulation results through reference literature" (`schulz2019.txt` l.305-313).

## REUSE (G5)
- Renderer: no (LDR, impairment-oriented, identity for the normal eye).
- PSF donor: no (ray-sample averaging of 8 taps with PSO-fitted pseudo-parameters, no diffraction/aberrations/scatter).
- Rod-cone donor: no model — only the digitized Østerberg density table (`retina_map/osterberg.rs`, CSV in
  `doc/receptor-density/`) is a reusable data item (Apache-2.0; original source Østerberg 1935).
- Impairment reference: yes — a maintained, runnable, headless impairment simulator (cataract, refractive error,
  nyctalopia, CVD, AMD, glaucoma) useful as a behavioural contrast case, not as normal night vision.
- Infrastructure ideas: node graph per eye, gaze-driven retina cube map, headless `render` batch CLI.

## FAILURES / SURPRISES
- Batch `render` double sRGB encoding (above). Upstream issue candidate; not patched here.
- WGSL `switch` has no fall-through, but the comment/diagram in `lens/mod.wgsl` l.355-363 assumes cumulative cases;
  with the default `samplecount = 4` only the 8 rays of `case 4` are cast (`sampleCount += 8.0`), not 17.
- Build needs X11 headers because `openxr-sys` compiles the OpenXR loader even for headless use.
- Nix eval-cache "database is busy" warnings are harmless (parallel workers).

## BRIGHT POINT SOURCE
1. Where the optical PSF is applied: nowhere for the normal eye (lens node inactive). With refractive error: an 8-ray
   average in the Lens pass on the 8-bit input (`lens/mod.wgsl` l.353-406).
2. Before/after adaptation: no adaptation exists.
3. Before/after tone reproduction: after — input is already a tone-mapped/clipped 8-bit image.
4. Energy preserved: blur kernels are normalized averages (yes for blur); cataract/achromatopsia "bloom" multiplies by
   `1 + Y·c` (adds energy); nyctalopia removes energy.
5. Absolute-luminance aware: no.
6. PSF depends on adaptation/pupil/age/wavelength/field angle: none (defocus depends on depth vs near/far point only).
7. HDR source on LDR display: not handled; clipped 8-bit input in, 8-bit out (S7 lamps stay 2×2 white cores).
8. Halo changes perceived brightness: no halo for the normal eye; "bloom" in impairment modes brightens pixels in place.
9. Temporal PSF variation: none.
10. Clip before or after convolution: clip BEFORE (8-bit input).

## VERDICT
**NOT RELEVANT** for the normal-eye night/bright-point question (runs natively, but its neutral configuration is
the identity and all optics/glare/"night" effects are ad-hoc impairment filters on 8-bit sRGB). Secondary role:
runnable impairment reference (behavioural contrast only); Østerberg density table is a small data donor.
