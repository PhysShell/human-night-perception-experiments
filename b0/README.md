# B0: bright-point-source perception bake-off (v2, after methodology review)

**Question.** For the same physical light, how do different schools represent it on the same
phone display? The light is one distant warm road lamp, unresolved. And what does each do to a
dark object right next to it?

**Status.** An exploratory perceptual experiment. **Not** "six equally comparable models of the
human eye". No winner is chosen; the blind set (`results/blind/`) is for the viewer.

**Frozen:** the Blender scene and pipeline are not touched. Every variant goes through the
**same** display step, the frozen pcond stack (`b0/display.sh`), so only the optics differ.

    for p in 73 146 292; do nix develop -c python3 b0/make_b0.py $p; done           # stimuli + components
    REPO=$PWD B0_OUT=$PWD/b0/out/optics SPD_CSV=$PWD/tracks/mitsuba-spectral/spectra/test_spectra_unitlum.csv \
      bash tracks/iset/scripts/run_octave.sh b0/iset_kernel.m                        # ISET point image (4x)
    nix develop -c b0/run_components.sh      # optics on the linear components (8 variants)
    nix develop -c python3 b0/sweep.py       # 31-step source sweep: display, visibility, adaptation
    nix develop -c b0/sweep_world.sh         # reference observer models on the physical stimulus
    tracks/temporal-glare-2009/py.sh b0/plot_sweep.py
    nix develop -c python3 b0/convergence.py
    (v1 nominal set and blind set: b0/run_optics.sh, b0/run_display.sh, b0/blind.py; do not rerun blind.py,
     it would reshuffle the key)

## Stimulus record (`make_b0.py`, `out/stim*/meta.json`)

| quantity | value |
|---|---|
| source | 800 cd luminaire at 3000 m. Illuminance **at the eye E = I/d² = 8.9·10⁻⁵ lx** (×1). The sweep covers 0.1×–100× = 8.9·10⁻⁶ … 8.9·10⁻³ lx |
| angular subtense | 0.57′ (0.5 m luminaire): unresolved |
| atmospheric T | 1 (not applied) |
| colour / spectrum | RGB variants: Rec.709 1 : 0.45 : 0.08 (sodium-like). ISET: CIE HP1 HPS SPD |
| pupil | not part of the stimulus. Each eye model uses its own: ISET 6 mm; HDR-VDP its own pupil model |
| background | night sky 4·10⁻⁴ cd/m² |
| probe | black bar ("trunk") 0.15° × 3°, near edge 0.3° from the lamp |
| field | 12° × 6° |
| **grids** | **PHONE display chain: 73 px/deg** (the display's pixels). **REAL_SCENE_REFERENCE chain: 146 px/deg**. The world has no pixel grid, so it was refined until the evaluator converged: 73 / 146 / 292 px/deg give trunk P_det 0.146 / 0.148 / 0.141 (CIE99 observer) and 0.0118 / 0.0121 / 0.0116 (HDR-VDP observer) |

All optics used here are linear, so stimuli and retinal images are built exactly from components:
`R(sky ± bar) + k · R(lamp)`. For HDR-VDP's OTFs, the lamp component is computed on a 0.01 cd/m²
pedestal and the pedestal subtracted, because HDR-VDP clamps its OTF output at ≥ 10⁻⁵ cd/m² and
that floor would otherwise scale with k.

## Stage ledger (no physiological stage twice)

| chain | DONOR stages | EVALUATOR stages (HDR-VDP-3) |
|---|---|---|
| display, `EVAL_OFF` | optics = the variant (below); adaptation = none | optics **OFF** (`mtf none`); local adaptation (HDR-VDP's descendant of Vangorp #7) + CSF + detection |
| display, `EVAL_VIEWER` | optics = the variant; adaptation = none | optics = **the viewer's own eye at the phone** (HDR-VDP MTF); local adaptation + CSF + detection |
| REAL_SCENE_REFERENCE | optics = none | optics = CIE99 **or** HDR-VDP MTF (two **reference observer models**); local adaptation + CSF + detection |
| Vangorp oracle | the variant's retinal image | `hdrvdp_local_adapt` only |

- **EVAL_VIEWER does not count the same eye twice.** The donor models the eye *in the scene*;
  the evaluator's optics model the viewer's eye looking at the phone, which physically exists.
  It is reported separately from EVAL_OFF, which isolates the donor chain.
- **The two reference observers disagree by 5–20× across the sweep.** That is
  **reference-model uncertainty, not a range of "real" visibility**. HDR-VDP-2's authors fitted
  their own MTF precisely because CIE99 did not fit all their data.

## Variants (all existing implementations)

| id | school | implementation | notes |
|---|---|---|---|
| V0_none | no eye optics (the M2.6 state) | — | |
| V1_iset | aberration core | ISETBio/ISETCam `wvf human`: **Thibos 2009 mean eye, 6 mm, HPS SPD, on-axis, focus 550 nm** | one configuration, not "the human PSF". Scene at 4× (292 px/deg), area-binned. **Convergence:** EE radii 50/80/95 % = 1.03/2.34/4.87′ (4×) vs 0.97/2.40/5.06′ (8×); FWHM of the sub-pixel core 1.01 vs 0.86′; at 73 px/deg the 3×3 energy is 0.611 vs 0.611. Kernel field ±1.24°: far wings truncated, visible as a faint square at ×10/×100 |
| V2_hdrvdpmtf | eye MTF fitted for a visibility metric | HDR-VDP 3.0.7 `hdrvdp_mtf('hdrvdp')` | OTF on a 2× grid, binned (no Nyquist cross). Loses 0.9 % of energy (the donor's DC gain) |
| V3_cie99 | CIE disability-glare veil | HDR-VDP 3.0.7 `hdrvdp_otf_cie99`: CIE 135/1 (Vos & van den Berg 1999) GSF, age 24, pigmentation 0.5 | Octave needs `b0/octave_shim/dirac.m`; the round-8 HDR-VDP `mtf cie` run had failed silently for this reason. **2× vs 4× grid:** 5 % energy-weighted, 4 % peak, ≤ 12 % local difference = the numerical uncertainty of V3. CIE 146:2002 is a later edition, not this file |
| V4_spencer | Spencer 1995 static glare | our calibrated Blender Fog Glow (`m1/fog_glow.py`) | 97.9 % of energy kept |
| V5_temporal | ocular dynamics (hippus) | Temporal Glare co-author demo float PSF (Frisvad), rebinned to 73 px/deg | **window-limited**: the demo PSF lives in a ±0.5° FFT window and is still ~10⁻³ of peak at its edge. Three treatments are reported (below). Blind set = taper + renormalised |
| — | Vangorp 2015 local adaptation | HDR-VDP 3.0.7 `hdrvdp_local_adapt` | oracle only; see provenance |
| — | Tariq 2023 perceptual TM | no code | not run |

## Provenance corrections (Vangorp)

- **HDR-VDP-3 ships a local-adaptation model *derived from* Vangorp #7, with a different
  parameter.** Their σ = 10^−0.781367° = **0.165°**; the paper's model #7 has **σ = 0.131°**
  (paper Table 2 / text, `research-cache/local-adaptation-2015/paper.txt` l.735–736, 786–788). No
  comment in the source explains the difference (re-fit, FWHM/σ conversion, or re-parameterisation).
  **Provenance check open.**
- **Model #1.** "Cannot handle luminance levels < 1 cd/m²" is **the HDR-VDP implementation's
  comment and decision** (model #1 is present but disabled with `if(0)`), **not a conclusion of
  the paper**. The paper ranks model #1 best by fit, and reports that its support gets wider at
  lower luminance, consistent with adaptation moving post-receptoral (Dunn et al. 2007,
  l.778–786). It only avoids extrapolating its custom non-linearity below the minimum
  experimental level of 0.1 cd/m² (footnote 3, l.912–915).
- **The model is fitted on photopic stimuli, 1–5000 cd/m²** (l.102–103). Mesopic is future work
  (l.990–992). **Our night sky (4·10⁻⁴ cd/m²) is an extrapolation for any version.**

## Terminology

The size numbers below are **white-clipped plateau angular diameters under this display mapping**
(pcond, PHONE, Ldmax 100): the equivalent diameter of the area at display white. They combine:
- the PSF wings;
- the source level;
- the display peak;
- tone mapping;
- clipping.

They are **not PSF sizes**. A physically tiny aberration core (ISET EE50 ≈ 1′) gives a 12′ white
plateau because pcond puts the lamp ~30× above display white.

## Results

### Continuous sweep (`results/sweep.json`, `results/sweep_curves.png`, `results/sweep_checks.json`)

31 log steps, 8.9·10⁻⁶ … 8.9·10⁻³ lx at the eye.

**Smoothness checks, all curves:**
- plateau and Vangorp adaptation are monotone non-decreasing;
- trunk P_det is monotone non-increasing (tolerance 0.02);
- no discontinuities; the largest P_det step between neighbours is 0.08.

**Knee:** only the temporal variants. Their plateau jumps 13–15′ within one step around
5·10⁻⁵–2·10⁻⁴ lx, then saturates at the window (55–67′).

At ×1 / ×10 / ×100 (plateau ′ ; P_det EVAL_OFF ; P_det EVAL_VIEWER ; Vangorp L_la at trunk, cd/m²):

| variant | ×1 | ×10 | ×100 |
|---|---|---|---|
| V0 none | 1.9 ; 0.999 ; 0.997 ; 4.9e-5 | 3.2 ; 0.999 ; 0.995 ; 4.9e-5 | 3.2 ; 0.999 ; 0.996 ; 4.9e-5 |
| V1 ISET | 12.1 ; 0.95 ; 0.90 ; 1.6e-3 | 19.6 ; 0.62 ; 0.38 ; 0.012 | 34.2 ; 0.12 ; 0.047 ; 0.12 |
| V2 HDR-VDP MTF | 20.7 ; 0.42 ; 0.18 ; 0.029 | 43.6 ; 0.034 ; 0.015 ; 0.28 | 74.7 ; 0.002 ; 0.001 ; 2.8 |
| V3 CIE99 | 11.3 ; 0.98 ; 0.92 ; 2.0e-3 | 21.6 ; 0.86 ; 0.68 ; 0.015 | 38.3 ; 0.40 ; 0.16 ; 0.14 |
| V4 Spencer | 16.5 ; 0.55 ; 0.30 ; 0.020 | 35.9 ; 0.054 ; 0.022 ; 0.20 | 61.5 ; 0.002 ; 0.001 ; 2.0 |
| V5 temporal (taper, renorm) | 46.7 ; 0.26 ; 0.043 ; 0.031 | 57.2 ; 0.23 ; 0.033 ; 0.16 | 59.5 ; 0.22 ; 0.031 ; 0.84 |

Reference observer models on the physical stimulus (146 px/deg), trunk P_det:

| observer | 8.9·10⁻⁶ lx | ~7·10⁻⁵ lx (≈ ×0.8) | ~1.4·10⁻⁴ lx (≈ ×1.6) | 8.9·10⁻³ lx |
|---|---|---|---|---|
| CIE99 | 0.30 | 0.16 | 0.12 | 0.007 |
| HDR-VDP MTF | 0.059 | 0.015 | 0.007 | 0 |

**Reading:**
- **V0 (the current state)** keeps the trunk next to the lamp visible (P ≈ 1) at every level;
  both reference observers predict it becoming hard to see as the lamp brightens.
- **Narrow cores (V1 ISET, V3 CIE99)** stay far above both references until ~10⁻³ lx.
- **Wide glare (V2, V4)** falls into the reference range from ~10⁻⁴ lx.
  - Under EVAL_VIEWER, V4 (Spencer) follows the CIE99 observer curve closely over the whole
    range.
  - This is an observation under one reference model, not a validation.
- **V5 (temporal)** never hides the trunk completely (P ≈ 0.2 with the evaluator's optics off).
  Its glare ends at the 0.5° window, while the trunk extends 1.5° beyond it.

### Temporal Glare window sensitivity (window-limited)

| treatment | energy kept in the window | plateau ×1 / ×100 | P_det EVAL_OFF ×1 / ×100 | P_det EVAL_VIEWER ×1 / ×100 |
|---|---|---|---|---|
| square (the demo's window as is, normalised over it) | 100 % | 42 / 67′ | 0.15 / 0.13 | 0.021 / 0.014 |
| taper 0.4–0.5°, renormalised (blind set) | 100 % | 47 / 60′ | 0.26 / 0.22 | 0.043 / 0.031 |
| taper, not renormalised | 85 % | 43 / 59′ | 0.20 / 0.17 | 0.034 / 0.023 |

- Renormalising the taper moves the energy cut beyond 0.4° back inside the window. That makes
  the plateau slightly larger at ×1, and the in-window glare brighter.
- All three are limited by the demo's ±0.5° field, which is still ~10⁻³ of peak at the edge.
  The demo's field is fixed, so **a 0.75° or 1° window is not available from this donor**.
  V5 is labelled **ADAPTED, window-limited**.

### Temporal data

- **NATIVE temporal data:** the 33 float PSF frames dumped from the demo at demo times
  0.8–9.6 s (~3.7 frames/s), and the 631 hippus steps traced in `tracks/temporal-glare-2009`.
  Only these may be used for frequency analysis. Hippus is broadband below ~0.6 Hz, peak
  0.24 Hz; PSF energy ±3.8 %.
- **INTERPOLATED 24 fps:** the V5 video in the blind set. Perceptual preview only; linear
  interpolation low-passes the sequence.
- Only the hippus part of Temporal Glare exists in the demo. Blinks, lens/vitreous particles,
  eyelashes and field-luminance/observer-motion dependence are paper-only.

## For the viewer (blind)

`results/blind/A–F.png` and `A–F.mp4` (v1 set, nominal ×1, no trunk, taper + renormalised
temporal): a 1920×820 frame, image 1:1 in the centre, full screen on a phone held landscape at
~30 cm in a dark room. Decide first, then open `results/BLIND_KEY_open_after_viewing.json` and the
`REVEAL_` sheets. The v2 changes (components, pedestal, bar position ±1 px) do not change the
no-trunk ×1 images the blind set shows.
