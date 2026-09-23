# Track hcipy: HCIPy atmospheric turbulence (research only)

Nothing from this track goes into the baseline scene. The source ids in [brackets] are defined in `sources.md`.

## IDENTITY
- **HCIPy**, High Contrast Imaging for Python, by E. Por et al. Repository: https://github.com/ehpor/hcipy.
- Pinned version: PyPI `hcipy==0.7.1`. The git tag `v0.7.1` is commit `32f2b4cef99533aa44cfbb08049bd3cbbe2c16a4` (2026-09-02) [HC1, HC2].
- Licence: **MIT**. Reuse and redistribution are allowed with the copyright notice [HC1].
- What it is: an astronomical optics and adaptive-optics simulator. It has Fourier-optics propagators, von Kármán phase screens (infinite extrusion after Assémat 2006), a multi-layer atmosphere with Fresnel propagation between layers (scintillation), wavefront sensors and coronagraphs.
- What it is not: a model of the human visual system, a model of the eye's optics, or a propagator for horizontal paths with spherical waves.

## PURPOSE
The question is whether the atmosphere can make distant lamps "breathe" on the PHONE and DESKTOP targets, and by how much. We split the atmospheric effects into three separate outputs:
- (a) image motion (angle of arrival)
- (b) PSF deformation and seeing
- (c) scintillation

HCIPy's own tutorial setup is used to show that these three can be measured separately and that the tool reproduces textbook theory. Closed-form textbook formulas then give the expected magnitudes for our geometry: lamps at 2.2–14 km and 9 m high, eye at 1.7 m, human pupil of 5–7 mm.

## HVS COMPONENTS
| component | HCIPy |
|---|---|
| optics | Generic pupil and focal-plane Fourier optics. It has no eye model: no ocular aberrations, no Stiles–Crawford effect, no ocular scatter |
| glare | none |
| adaptation | none |
| rods / cones, mesopic / scotopic | none |
| acuity | none. Only the diffraction limit of whatever aperture is given |
| temporal state | Frozen-flow time evolution of phase screens (`layer.t`, `evolve_until`). There is no temporal model of vision |
| gaze | none |
| display model | none |
| spectrum | Monochromatic wavefronts. Polychromatic results need a loop over wavelengths. r0 scales as λ^(6/5) internally through Cn² |

## NATIVE ENVIRONMENT
- The repository's default `nix develop` Python has no matplotlib. A PyPI numpy wheel installed into a venv fails on this NixOS-style store with `libstdc++.so.6: cannot open shared object file`.
- We therefore built a Python environment from the repository's pinned nixpkgs **without editing flake.nix**:
  `nix build --impure --expr '(builtins.getFlake ...).inputs.nixpkgs...python3.withPackages (numpy scipy matplotlib astropy xxhash numexpr asdf importlib-metadata pillow pyyaml imageio tqdm pytest mpmath)' -o research-cache/hcipy/pyenv`
  This gives Python 3.14.7, numpy 2.5.2, scipy 1.18.1 and astropy 8.0.0.
- On top of it: `uv venv --system-site-packages --python research-cache/hcipy/pyenv/bin/python3 research-cache/hcipy/venv` and `uv pip install --no-deps hcipy==0.7.1`.
- Git checkout of the matching tag: `research-cache/hcipy/src`.
- Every run is single-threaded (`OMP_NUM_THREADS=1`) under `nice -n 10`.

## NATIVE REPRODUCTION
1. **Test suite.** `cd research-cache/hcipy/src/tests && ../../venv/bin/python -m pytest --import-mode=importlib test_atmosphere.py`
   - Result: **18 passed, 16 skipped** (the skipped ones are marked slow) in 50 s. Log: `results/native/hcipy/NATIVE_pytest_test_atmosphere.log`.
   - The tests compare total and per-Zernike phase variance with the von Kármán theory, and cover the multi-layer scintillation behaviour and seeing/r0 conversions [HC8].
2. **Official tutorial.** `tracks/hcipy/run_notebook_native.py research-cache/hcipy/src/doc/getting_started/3_atmosphere_adaptive_optics.ipynb results/native/hcipy`
   - The runner executes the notebook cells unchanged, except for one logged API-drift patch: the v0.7.1 notebook still calls `make_focal_grid(8, 16, wavelength=wavelength)`, which 0.7.1 rejects with a TypeError [HC4]. We replaced it with `spatial_resolution=wavelength/D_tel`.
   - All 6 code cells ran. Covered: InfiniteAtmosphericLayer phase, PSF, time evolution to t = 0.1 s, and MultiLayerAtmosphere (Mauna Kea) with Fresnel scintillation.
   - `NATIVE_nb3_reference_vs_run_montage.jpg` puts each figure the authors stored in the notebook (left) next to our run (right). The random realisations differ, but they have the same statistics and appearance.
3. **M2: separate effects from the tutorial setup.** `tracks/hcipy/m2_separate_effects.py results/native/hcipy`, runtime about 2 min. HCIPy does all the optics; the script only measures the results.

| effect | measured (HCIPy) | theory | agreement |
|---|---|---|---|
| (a) image motion, one axis, phase Z-tilt, 200 independent screens | 0.0378″ | von Kármán Z-tilt from HCIPy's own test formula, L0 = 20 m: 0.0379″ | 0.3 % |
| (a) same, PSF centroid (G-tilt) | 0.0311″ | G-tilt is slightly below Z-tilt | consistent |
| (a) Kolmogorov value (L0 = ∞) for comparison | – | 0.114″ | L0 = 20 m with D = 8.2 m removes about 90 % of the tilt variance |
| (b) long-exposure FWHM (ensemble of 200) | 0.301″ | 0.98λ/r0 = 0.440″ (Kolmogorov); ×√(1−2.183(r0/L0)^0.356) = 0.289″ (von Kármán) [TK02] | 4 % |
| (b) short vs long exposure | peak/diffraction 0.033 vs 0.012; a speckled short PSF; the correlated time series moves by about 0.02″ | – | – |
| (c) scintillation σ_I², 5.9 mm pupil pixels, Mauna Kea layers, λ = 2 µm, 60 realisations | 0.0955 | weak-regime plane wave 2.25 k^(7/6) Σ Cn²ᵢ hᵢ^(5/6) = 0.0923 [KK15 eq. 8] | 3.5 % |
| (c) aperture averaging | 0.2 m: 0.026; 1 m: 0.0009 | – | decreases as expected |

   Output files: `NATIVE_m2_separate_effects.json`, `NATIVE_m2_psf_and_image_motion.png`, `NATIVE_m2_scintillation.png`.

   **Verdict of NATIVE: PASS.** The tutorial runs after one documented one-keyword API fix, the tests pass, and three independent effects agree with theory to 0.3–4 %.

## COMMON STIMULUS
Not applicable (M5): HCIPy is not applied to our scene or to `stimuli/pack`.

What we did instead is the M3 analysis: `tracks/hcipy/m3_horizontal_path_analysis.py results/common/hcipy`, labelled **ANALYSIS**. It is not a simulator; it only evaluates cited closed-form formulas. Outputs are `ANALYSIS_m3_horizontal_path_eye.csv` (every Cn² × L × pupil combination) and `ANALYSIS_m3_horizontal_path_eye.png`.

Parameters and their provenance:
- Cn² constant along the path [FG04 p. 12]. Under stable night conditions Cn² is roughly independent of height [KK15, Gurvich]. We ignore the slant from 1.7 m to 9 m.
- Cn² values: 1e-16, 1e-15, 8.4e-15 (SLC Night, h < 18.5 m [FG04 p. 12]), 1e-14 and 1e-13 as the strong upper bound [FG04 p. 11]. Values between 1e-15 and 1e-14 have been measured in the evening on a 2.7 km near-ground path [SV21].
- λ = 550 nm; pupil 5, 6 and 7 mm; inner scale l0 = 1–10 mm [FG04]; outer scale L0 about the height above ground, i.e. 2–10 m [FG04 p. 8].
- Crosswind 0.5–3 m/s. This is an ASSUMPTION, with no source.

**Key output at a 6 mm pupil.** The last three columns are the r0 regime, the isoplanatic angle θ0, and the fluctuation frequency.

| night Cn² (m^-2/3) | L (km) | image motion RMS, one axis (arcmin) | spherical Rytov β0² | σ_I² at the eye (point receiver) | seeing λ/r0 (arcmin) | r0 (mm), D/r0 | θ0 (arcmin) | f ≈ v⊥/√(λL) (Hz) |
|---|---|---|---|---|---|---|---|---|
| 1e-15 (stable) | 2.2 / 14 | 0.009–0.013 / 0.022–0.032 | 0.12 / 3.4 | 0.12 / 1.6 | 0.02 / 0.06 | 101 / 33; ≪ 1 | 0.05 / 0.003 | 14–86 / 6–34 |
| 8.4e-15 (SLC night) | 2.2 / 14 | 0.025–0.037 / 0.063–0.092 | 1.0 / 29 | 0.84 / 1.5 | 0.07 / 0.20 | 28 / 9.3; 0.2 / 0.65 | 0.014 / 0.001 | same |
| 1e-13 (upper bound) | 2.2 / 14 | 0.09–0.13 / 0.22–0.32 | 11.5 / 342 | 1.7 / 1.2 | 0.30 / 0.90 | 6.4 / 2.1; 0.9 / 2.9 | ≤ 0.003 | same |

Comparison with the display: one pixel is 0.82′ on PHONE_TARGET and 1.24′ on DESKTOP_TARGET [stimuli/display_targets.json].

- **(a) Image motion.** RMS is ≤ 0.1′ for realistic night Cn², and ≤ 0.32′ at the strong upper bound. That is ≤ 0.12 px (at most 0.4 px) on PHONE and ≤ 0.08 px (at most 0.26 px) on DESKTOP. It cannot be shown as whole-pixel jitter; only sub-pixel energy redistribution could show it, which is what S6 tests with 1 px in 2 s. The spherical-wave weighting (3/8 of the plane-wave value) is taken from [AP05] and is NOT VERIFIED. The pupil is about the size of the inner scale, so both forms (D-limited and l0-limited) are given [KK15 eq. 18].
- **(b) Scintillation.** Strong. β0² already exceeds 1 at 2–3 km for Cn² ≥ 8e-15, which means moderate to saturated fluctuations, with σ_I² ≈ 0.8–1.7 (RMS intensity 90–130 %). Weak-regime aperture averaging for a 5–7 mm pupil is A ≥ 0.994 [KK15 eq. 21]: the pupil is much smaller than the Fresnel scale √(L/k) of 14–35 mm, so the eye is effectively a point receiver. In the strong regime, however, ρ0 = r0/2.1 falls to 4–13 mm (SLC night) or to 1–3 mm (upper bound), comparable to or smaller than the pupil. There some averaging will occur, which the weak formula does not capture; this is open, and would need the strong-regime aperture-averaging formula from [AP05]. Every lamp twinkles independently because θ0 is much smaller than the lamp separations.
- **(c) Seeing blur.** λ/r0 ≤ 0.2′ for realistic night Cn² and up to 0.9′ at the upper bound. D/r0 < 1 except at the strongest turbulence, so the atmospheric "seeing disc" does not form in a 6 mm pupil. The atmospheric blur is smaller than one display pixel in all but the most extreme case.
- **Time scales.** v⊥/√(λL) is about 6–90 Hz for 0.5–3 m/s, and faster (v⊥/ρ0) in strong turbulence. That is mostly above the 12 Hz Nyquist limit of the 24 fps stimuli. Slow components, from wind gusts and Cn² changes, were not quantified.

**Which effects could be visible on PHONE/DESKTOP.** Only scintillation, as intensity modulation of the point source, is large. Image motion and seeing are sub-pixel at both targets. For the "breathing" question, atmospheric scintillation is a physically large candidate, but most of its power lies above what a 24 fps display can reproduce.

**What HCIPy would need, if it were ever applied (not done):**
1. Spherical-wave geometry. HCIPy's multi-layer model is collimated and plane-wave [HC6]. It would need a point-source initial field and the (z/L)^(5/3) weighting of the screens, or a switch to split-step code with a point source, e.g. WavePy or Schmidt [M4-1, M4-5].
2. Layers placed along a 2–14 km horizontal path, with the `height` parameter used as the distance from the pupil. This is possible with custom `InfiniteAtmosphericLayer`s.
3. Night values of Cn², L0 of 2–10 m, and wind of 0.5–3 m/s instead of the Mauna Kea layers [HC7]. The Mauna Kea defaults are not used here.
4. An inner scale. HCIPy's von Kármán spectrum has none, and l0 matters for scintillation [FG04 p. 11].
5. Sampling. A 6 mm pupil needs screens many Fresnel zones and several L0 wide, sampled finer than ρ0 (a few mm). The grids become very large.

**M4: near-ground horizontal propagation simulators (survey only; nothing was run).** Details are in `sources.md` M4-1..7.

| simulator | what it offers | licence and status |
|---|---|---|
| WavePy (Beck, Bekins, Bos 2016) | Python split-step with **spherical/point sources** and a horizontal Cn² | Apache-2.0 file, but the README says "creators retain all rights". Last commit 2017. ρ0 exponent bug |
| wavepy3 | Python 3 port of WavePy by a third party | Apache-2.0 |
| AOtools | Phase screens (including infinite), atmospheric conversions, angular-spectrum propagation | LGPL-3.0 |
| Schmidt 2010 book code | The reference split-step implementation with point sources (MATLAB, on the book's CD) | No open licence found; treat as all rights reserved |
| Purdue P2S / TurbulenceSim (Chimitt, Chan) | Long-range horizontal *imaging*, 300–1000× faster than split-step | Original: research/evaluation-only licence, patents pending. The GitHub copy we inspected is a third-party fork under CC BY-NC-SA |
| PROPER, LightPipes | Propagation only, no turbulence model for horizontal paths | BSD / MIT |

If a simulator is ever needed, a WavePy-style split-step with a point source is the matching method. We could not verify WavePy's licence status.

## ASSUMPTIONS
- HCIPy works in radians, metres and relative intensity. It has no concept of cd/m², photometry or spectra beyond single wavelengths.
- It uses no RGB, XYZ or spectral colour. Geometry comes from pupil and focal grids in physical units.
- It has no display and no absolute luminance scale. For M3: λ = 550 nm (photopic); scotopic 507 nm would change the numbers by about (550/507)^(7/6) ≈ 1.1 in β0².

## VALIDATION
- HCIPy's own statistics tests pass.
- Our three separate measurements agree with independent theory to 0.3–4 % (see the M2 table).
- The M3 numbers are formula evaluations, not validation.
- None of this validates anything about human perception.

## REUSE
- MIT: code may be reused and redistributed with the licence notice.
- A useful role is as a trusted **SCIENTIFIC ORACLE** for turbulence statistics: phase screens, tilt, and scintillation in collimated geometry.
- It would not be used as a direct renderer for the scene.
- Nothing was copied into `tracks/`; only wrappers were written.

## FAILURES / SURPRISES
- The v0.7.1 tutorial notebook is out of date with the 0.7.1 API (the `make_focal_grid(..., wavelength=)` TypeError) [HC4].
- The tutorial's focal grid (±16 λ/D = ±0.41″ at 1 µm) is smaller than the seeing disc (0.44″ FWHM). Centroid and FWHM measured on it are truncated: our first M2 attempt gave a "seeing" of 0.08″ and a tilt of 0.028″. The measurement grid was widened to ±80 λ/D.
- The finite outer scale matters a lot: L0 = 20 m with D = 8.2 m reduces the tilt variance by about 10×, which is easy to mistake for a bug.
- `MultiLayerAtmosphere(..., scintilation=True)` (the misspelling in the tutorial) is still accepted, with a warning.
- The repository's default devShell cannot run HCIPy (no matplotlib), and PyPI binary wheels do not load on the nix Python. A nixpkgs `python3.withPackages` was needed.
- WavePy, found in the M4 survey, has a sign error in the ρ0 exponent (`wavepy.py:110`) and a licence contradiction [M4-1].

## BRIGHT POINT SOURCE
1. Where the optical PSF is applied: in the pupil or focal plane of a generic telescope, and only for a monochromatic point source at infinity (plane wave).
2. Before or after adaptation: not applicable (no adaptation).
3. Before or after tone reproduction: not applicable (no tone reproduction).
4. Energy preserved: yes. The propagators are unitary: Fraunhofer MFT and Fresnel are normalised, and the intensity integral is conserved up to grid truncation.
5. Absolute-luminance aware: no (relative intensity only).
6. Does the PSF depend on adaptation, pupil, age, wavelength or field angle: it depends on wavelength and pupil (aperture), and field angle only if you build it (anisoplanatism through layer heights). There is no adaptation and no age.
7. How an HDR source is shown on an LDR or HDR display: not applicable.
8. Does the halo change perceived brightness: not applicable. It is an atmospheric PSF, not a perceptual halo.
9. Temporal PSF variation: yes. This is its core feature: frozen-flow evolution of the turbulent PSF and of scintillation. Magnitudes for our scene are in the M3 analysis above.
10. Clip before or after convolution: not applicable. Wave optics is linear, with no clipping.

## VERDICT
**SCIENTIFIC ORACLE** for atmospheric turbulence statistics. NATIVE PASS; the magnitudes for our scene come from the ANALYSIS above. It is not a renderer for our horizontal spherical-wave geometry without substantial custom setup.

## Files
- `tracks/hcipy/run_notebook_native.py`: NATIVE tutorial runner (one logged API patch).
- `tracks/hcipy/m2_separate_effects.py`: M2 measurements from the tutorial setup.
- `tracks/hcipy/m3_horizontal_path_analysis.py`: M3 closed-form analysis for the scene geometry.
- `results/native/hcipy/`: NATIVE_* (runs), REFERENCE_* (the authors' stored figures), and the pytest log.
- `results/common/hcipy/`: ANALYSIS_m3_* (no COMMON stimulus run, per M5).
