# Track `mitsuba-spectral`: Mitsuba 3, used as a spectral research oracle

## IDENTITY
- **Mitsuba 3** https://github.com/mitsuba-renderer/mitsuba3 @ `de4fde8` (2026-09-23). PyPI `mitsuba` **3.9.1**, `drjit` 1.5.0. Licence: BSD-3-style with an "Enhancements" clause (mitsuba3/LICENSE).
- **Tutorials** https://github.com/mitsuba-renderer/mitsuba-tutorials @ `22db0a7`.
- **Photometry tools** (PyPI): LuxPy 1.12.5 (GPLv3) and colour-science 0.4.7 (BSD-3).

## PURPOSE
Mitsuba is a retargetable, differentiable physically based renderer with true spectral variants. In this project it serves only as a **spectral oracle**: it checks what a narrow sodium line, a warm LED or a neutral source does in radiometric and photometric (photopic and scotopic) terms. It is **not** a Blender replacement, and I did not port the scene.

## HVS COMPONENTS
None. Mitsuba has no optics of the eye, glare, adaptation, rods/cones, mesopic model, acuity, temporal state, gaze or display model.
- **Spectrum:** yes. Spectral transport over 360-830 nm (include/mitsuba/core/spectrum.h:123-125).
- **Sensor output:** CIE 1931 XYZ/RGB via hdrfilm (hdrfilm.cpp:221-227), or arbitrary spectral response functions via `specfilm`. The SRFs can be V(λ) and V'(λ), so the film can directly output photopic and scotopic radiance (specfilm.cpp:178-250).
- **Camera:** pinhole/perspective or thin lens (defocus). There is no eye model.
- **PostProcess:** an abstract interface for bloom-like filters exists (include/mitsuba/render/postprocess.h), but no concrete bloom plugin ships.

## NATIVE ENVIRONMENT
- Setup: `uv venv research-cache/mitsuba-spectral/venv --python /usr/local/bin/python3` (CPython 3.11, Ubuntu 24.04, glibc 2.39), then `uv pip install mitsuba luxpy colour-science matplotlib "numpy<2.3"`.
- The manylinux wheel ran directly. No nix-ld or steam-run was needed, because the container is Ubuntu, not NixOS.
- Only CPU was used (no GPU).
- The pip wheel ships `scalar_rgb, scalar_spectral, scalar_spectral_polarized, llvm_ad_{rgb,mono,mono_polarized,spectral,spectral_polarized}, cuda_ad_*`. **`llvm_spectral` is not in the wheel** (variants.rst; `set_variant('llvm_spectral')` raises "unsupported variant"). I used `llvm_ad_spectral` as the llvm spectral example.
- numpy 2.4 breaks `import luxpy` (TypeError in `blackbody` during import), so numpy is pinned to 2.2.6.

## NATIVE REPRODUCTION
- **Example:** the official quickstart (`mitsuba-tutorials/quickstart/mitsuba_quickstart.ipynb`) on `scenes/cbox.xml` at 256 spp. The code is unchanged except for the variant.
- **Command:** `research-cache/mitsuba-spectral/venv/bin/python tracks/mitsuba-spectral/scripts/n2_native_quickstart.py research-cache/mitsuba-spectral/mitsuba-tutorials results/native/mitsuba-spectral`
- **Result: PASS.** The three variants render the Cornell box: llvm_ad_rgb in 1.0 s, **scalar_spectral in 40 s** and **llvm_ad_spectral in 0.4 s**. Outputs are `NATIVE_cbox_*.{exr,png}` and `NATIVE_cbox_stats.json`.
- **Checks:** the spectral and RGB channel means agree within 3.2%, and scalar_spectral and llvm_ad_spectral agree within 0.2%. The tutorial ships no numeric reference image, so the cross-variant agreement is the only reference check.

## COMMON STIMULUS
**Not applicable.** The pack is a rendered linear RGB image, and Mitsuba is a renderer, not an image-to-image model (see `results/common/mitsuba-spectral/NOT_APPLICABLE.txt`).

## ASSUMPTIONS
- **Units.** Mitsuba is unitless unless the user supplies physical units. The test spectra (`spectra/test_spectra_unitlum.csv`, from `scripts/make_spectra.py`) are in W m^-2 sr^-1 nm^-1, normalised to 1 cd/m^2.
- **Test spectra:**
  - LPS: constructed Na D doublet, 588.995 / 589.592 nm, 2:1, FWHM 1 nm.
  - HPS: CIE HP1.
  - LED_warm: CIE LED-B1.
  - E: equal energy.
  - BLUE: constructed Gaussian at 460 nm, FWHM 20 nm.
- **Geometry:** scene units are metres.
- **Standard observers:** CIE 1931 2° (from colour-science) and CIE 1951 V'(λ) with K'm = 1700 lm/W.

## VALIDATION (N3-N5)
### N3/N4: unit conventions, verified by rendering
`scripts/n4_emitters.py`, variant llvm_ad_spectral, 256 spp. Output: `ADAPTED_n4_emitter_units.json`.
- **specfilm channel = ∫ SRF(λ) L(λ) dλ (unnormalised).** Y × 683 gives
  - LPS 1.015
  - HPS 1.0003
  - LED 1.0002
  - E 1.00005
  - BLUE 0.9992 cd/m^2

  The expected value is 1. The **specfilm V' channel** gives S/P = 0.2241 / 0.5565 / 1.2134 / 2.2611 / 22.22. The independent colour-science integrals give 0.2242 / 0.5591 / 1.2136 / 2.2611 / 22.21.
- **hdrfilm `xyz`:** Y = ∫ L ȳ dλ / 106.75, so cd/m^2 = Y × 683 × 106.75. Measured values: 0.996 / 0.999 / 1.000 / 1.000 / 1.011.
- **Point emitter** `intensity` is in W sr^-1 nm^-1. A white Lambertian plane 1 m away gives L = ρI/(πd^2): 0.309 to 0.319 cd/m^2 against an expected 0.3183. The point light itself does not appear in the image (it is a delta light), so **a visible lamp must be a small area emitter.**
- **Narrow lines are expensive.** For the 1 nm-wide LPS lines, the per-pixel relative standard deviation of Y is **29% at 256 spp**, against 0.4-3.4% for the broadband spectra (HPS 2.9%, BLUE 3.4%). The sensor samples wavelengths from the film response, not from the emitter spectrum. The estimate is unbiased (mean 1.015) but needs about 100x more samples for line sources.

### N5: photometry
`scripts/n5_photometry.py`, results in `ADAPTED_n5_photometry.{csv,json}`.

| spectrum | S/P (luxpy) | x, y | CCT | Duv |
|---|---|---|---|---|
| LPS | 0.225 | 0.5704, 0.4290 | 1772 K | +0.007 |
| HPS (HP1) | 0.560 | 0.5328, 0.4152 | 1962 K | |
| LED-B1 | 1.214 | 0.4559, 0.4079 | 2735 K | |
| E | 2.261 | 0.3333, 0.3333 | | |
| BLUE | 22.2 | 0.143, 0.033 | not meaningful | |

- **Mesopic, LuxPy (FLAGGED):** `get_cie_mesopic_adaptation`, which claims CIE 191:2010, **fails the S/P=1 invariant**. For Lp = 0.01 it returns Lmes = 0.245 instead of 0.01, and for S/P = 22 its iteration diverges. The cause is the missing Lp factor at `luxpy/spectrum/basics/spectral.py:975`. Its mesopic numbers must not be used.
- **Mesopic, colour-science:** only a coarse MOVE/LRC table lookup, sourced from Wikipedia. Its Lmes/Lp ratios are:

  | Lp (cd/m^2) | LPS | HPS | LED-B1 | E | BLUE |
  |---|---|---|---|---|---|
  | ≤0.03 | 0.22 | 0.56 | 1.16 | 1.92 | 16.5 |
  | 0.1-0.3 | 0.66 | 0.81 | 1.08 | 1.45 | 8.6 |
  | 1-5 | 0.88 | 0.93 | 1.03 | 1.19 | 4.1 |

  Treat these as indicative only. **No validated CIE 191 implementation was found in these tools**, and I did not write one (no reimplementation).

## REUSE
- The Python API is BSD-3-style, and PyPI wheels install without a compiler.
- Best reused as a spectral/photometric unit checker (specfilm with V and V' bands).
- LuxPy is GPLv3, so do not vendor it.

## FAILURES / SURPRISES
- The wheel has no `llvm_spectral` variant.
- LuxPy's CIE 191 bug (above), and LuxPy's incompatibility with numpy 2.4.
- LPS-like line spectra are very noisy under standard spectral sampling.
- A directly viewed point light is invisible in Mitsuba (delta emitter).

## BRIGHT POINT SOURCE
1. **Where the optical PSF is applied:** there is no eye PSF. The only spreading comes from the film reconstruction filter (rfilter, default Gaussian) and optional thin-lens defocus.
2. **Before or after adaptation:** not applicable.
3. **Before or after tone reproduction:** not applicable. The EXR output is linear with no tone mapping.
4. **Energy preserved:** yes. Monte Carlo transport is unbiased, and the rfilter is normalised.
5. **Absolute-luminance aware:** only if the user supplies physical units. Verified above: specfilm × 683 gives cd/m^2.
6. **What the PSF depends on:** not applicable (no eye PSF).
7. **How an HDR source is shown on a display:** not applicable. The output is float EXR; PNG export clips.
8. **Does the halo change perceived brightness:** not applicable.
9. **Temporal PSF variation:** no.
10. **Clip before or after convolution:** no clipping in the EXR/film. Clipping happens only when writing 8-bit PNG, after reconstruction filtering.

## VERDICT
**SCIENTIFIC ORACLE**, for spectral radiometry and photometry only (units, S/P, XYZ of lamp spectra). It says nothing about human night perception.
