# B0: bright-point-source perception bake-off (v3, roles separated)

**The task, stated as what it is: an inverse perceptual rendering problem.**
Find the display image D such that

    viewer_eye(D)  ≈  target_retina(real_scene)

- `target_retina` is what a model eye puts on the retina when looking at the real lamp and trunk at
  night.
- `viewer_eye` is the real eye of the viewer, looking at the phone under display luminances.

The optics that belong to the scene therefore live in the **target**. The viewer's own optics are
physically present and belong to the **evaluation**. The display image D is the only thing we
choose. B0 measures, for one distant lamp and a dark trunk 0.3° from it, how far each existing
display encoding D is from each retinal target. No winner is chosen.

**Status.** An exploratory perceptual experiment. Every detection probability here is **"P_det
under observer model X"** (HDR-VDP-3 side-by-side, with its local adaptation and CSF), a diagnostic,
not a measured human probability. At night-sky levels every such model is extrapolated.

**Frozen:** the Blender scene and pipeline are not touched. Every display encoding goes through the
same display step, the frozen pcond stack (`b0/display.sh`, PHONE 73 px/deg, Ldmax 100).

    for p in 73 146 292; do nix develop -c python3 b0/make_b0.py $p; done         # v2 stimuli (warm source)
    for p in 73 146; do nix develop -c python3 b0/make_b0.py $p neutral; done     # v3 B0-optics stimuli (neutral)
    # ISET point images, 4x of 73 px/deg (tag, CSV column, narrowband 550, defocus 0):
    REPO=$PWD B0_OUT=$PWD/b0/out/kernels SPD_CSV=$PWD/tracks/mitsuba-spectral/spectra/test_spectra_unitlum.csv \
      B0_ISET_TAG=_550z B0_SPD_COL=5 B0_NARROW550=1 B0_ZERO_DEFOCUS=1 B0_SPD_NAME=550 \
      bash tracks/iset/scripts/run_octave.sh b0/iset_kernel.m    # also _HPSz(3) _LEDz(4) _Ez(5) _BLUEz(6), and without z
    B0_LAYER=ach nix develop -c b0/run_components.sh    # optics on the linear components
    B0_LAYER=ach nix develop -c python3 b0/sweep.py     # 31-step sweep: display, 3 evaluators, adaptation
    B0_LAYER=ach nix develop -c b0/sweep_world.sh       # retinal targets via the evaluator's optics, 146 px/deg
    tracks/temporal-glare-2009/py.sh b0/report_v3.py    # -> results/b0_v3_tables.md, sweep_ach_curves.png
    nix develop -c python3 b0/spectral_layer.py         # B0-spectral
    tracks/temporal-glare-2009/py.sh b0/temporal_inner.py
    nix develop -c python3 b0/cie_ss_check.py           # CIE99 4x vs 8x
    (v2 warm layer: the same without B0_LAYER; v1 nominal and blind set: b0/run_optics.sh, b0/run_display.sh,
     b0/blind.py; do not rerun blind.py, it would reshuffle the key)

## Roles (v3)

A branch is classified by **where its output lives**, not by what school it comes from.

| role | what it produces | branches here | how it is evaluated |
|---|---|---|---|
| **RETINAL_FORWARD** | the retinal image of the real scene: a candidate `target_retina` | ISET `wvf human`; CIE99 GSF and HDR-VDP MTF (both via HDR-VDP 3.0.7) | on the retinal image, **evaluator optics OFF** (its optics are already applied) |
| **DISPLAY_ENCODING** | an image D for the phone | baseline pcond (V0); Spencer via Fog Glow (V4); Temporal Glare kernel (V5) | through the display, with **the viewer's eye at the phone** (EVAL_VIEWER); optics OFF as a diagnostic |
| **OBSERVER_MODEL** | a judge, never an image | HDR-VDP-3 (MTF, local adaptation = Vangorp descendant, CSF, detection) | — |

- **PSF × PSF.** A retinal PSF baked into a display image is blurred a second time by the viewer's
  eye when viewed. Retinal-forward branches shown on the display are therefore kept only as
  informational rows (`display_PSF_x_PSF` in `sweep_ach.json`). They are not candidates for D as
  they stand.
- In v2 the same numbers were in one table. That mixed targets with encodings.

## MATCHED_OBSERVER (what every branch was set to, and what it cannot be set to)

| parameter | ISET `wvf human` | CIE99 (HDR-VDP `otf_cie99`) | HDR-VDP MTF | Spencer / Fog Glow | Temporal Glare demo | HDR-VDP evaluator |
|---|---|---|---|---|---|---|
| pupil | **6 mm (set)** | model-fixed (no pupil in the GSF) | model-fixed (4-exponential fit) | model-fixed (Blender's Spencer kernel) | model-internal: hippus around 6.66 mm (Eq. 2 from the overlay mean), SD 0.11 mm | model-fixed |
| age | not modelled (Thibos mean eye, 21–65 y sample) | **24 (set; donor default)**, pigmentation 0.5 | model-fixed | not modelled | not modelled | 24 (default) |
| eccentricity | **0, on-axis (set)** | 0 (GSF is foveal) | 0 | 0 | 0 | 0 (fixating the lamp region) |
| defocus | **0 (set: Zernike j=4 zeroed)**; other Thibos mean terms kept (astigmatism j=5 −0.17 µm, spherical j=12 +0.094 µm) | n/a | n/a | n/a | model-internal (lens + aperture texture) | n/a |
| display geometry | same: 12° × 6° field, 73 px/deg PHONE, 30 cm, dark room | same | same | same | same | same |
| adaptation | none (optics only) | none | none | none | pupil only | its own local adaptation, per evaluator |
| spectrum | **monochromatic 550 nm (set)** in B0-optics | achromatic | achromatic | achromatic | luminance-weighted kernel (set) | achromatic channel |

**Correction found by matching.** ISET's `wvf human` ships the Thibos mean Zernike set *including
its mean defocus*, c4 = +0.335 µm at 6 mm (≈ 0.26 D). With it, 550 nm was *blurrier* (EE50 1.86′)
than the HPS spectrum (1.03′), because LCA at the sodium lines partly cancels that defocus. The v2
V1 row (HPS, "focus 550 nm") therefore carried a hidden 0.26 D. v3 sets defocus 0.

## B0-optics (achromatic) and B0-spectral: separated

- **B0-optics:** a neutral source of the same photopic luminance (`make_b0.py neutral`, Y unchanged),
  ISET at monochromatic 550 nm, the temporal kernel luminance-weighted on all channels. No colour
  is evaluated. All tables below are this layer.
- **B0-spectral:** only systems that actually take an SPD, here ISET alone. Retinal output only, no
  display (`results/spectral_layer.json`). Thibos mean eye, 6 mm, on-axis. Encircled-energy radii
  and FWHM, in arcmin:

| SPD | defocus 0 (MATCHED): EE50 / 80 / 95 | FWHM | Thibos mean as shipped (c4 +0.335 µm): EE50 / 80 / 95 | FWHM |
|---|---|---|---|---|
| monochromatic 550 nm | 0.92 / 1.66 / 3.70 | 0.84 | 1.86 / 3.66 / 5.96 | 0.70 |
| HPS (CIE HP1) | 1.56 / 2.21 / 3.14 | 1.25 | 1.03 / 2.34 / 4.87 | 1.01 |
| LED warm | 1.38 / 2.30 / 3.75 | 1.37 | 1.20 / 2.94 / 5.71 | 1.01 |
| equal-energy E | 1.30 / 2.47 / 4.51 | 1.09 | 1.45 / 3.64 / 6.69 | 0.90 |
| blue test spectrum | 4.73 / 7.54 / 11.45 | 2.56 | 6.71 / 9.88 / 13.53 | 5.70 |

  Radii are within the 2.5° ISET field. The spectrum moves the core by ~1.5× (and ~5× for blue),
  but the 0.26 D question moves it just as much. The spectral layer is not interpretable
  without fixing the observer first.

## Numerics

- **Illuminance at the eye** (`meta.json`): ×1 = 800 cd / (3000 m)² = **8.89·10⁻⁵ lx**,
  ×10 = 8.89·10⁻⁴, ×100 = 8.89·10⁻³. The README and manifests were right. The "8.9e-5 / 1e-4 / 1e-3"
  was a typo in a chat message only.
- **CIE99 OTF grid:** production 4×. Spot check 8× on a 3° × 3° crop around the source
  (`results/cie_ss_check.json`):
  - energy-weighted difference 1.8 %;
  - peak 1.4 %;
  - largest local difference 4.0 % where L > 1 % of the peak;
  - luminance at 5′ / 15′ / 30′ equal to 0.05 %.
  (v2 used 2×, which differed from 4× by 5 % energy-weighted.)
- **ISET:** 4× vs 8× EE radii within 6 % (v2 record, below).
- **Two routes to the same retinal target agree.**
  - CIE99 donor at 73 px/deg with evaluator optics OFF, vs CIE99 as the evaluator's optics at
    146 px/deg: trunk P_det 0.268 / 0.285 (×0.1) … 0.004 / 0.005 (×100).
  - HDR-VDP MTF: 0.027 / 0.051 (×0.1), 0.005 / 0.009 (×1): a factor ~2 in the last few hundredths.

## Definitions

- **Display plateau (v3):** the equivalent-area diameter of the pixels whose displayed luminance
  above black is ≥ 0.99·Ldmax. It is a property of this display mapping, not a PSF size.
  - v2 used "any channel ≥ 0.98". The v2 numbers are within 0.3–2′, except the widest glare
    (Spencer ×100 62 → 53′, HDR-VDP MTF ×100 75 → 69′).
  - Both fields are in the sweep JSONs.
- **Window-limited (`wl`):** the Temporal Glare demo's PSF lives in a ±0.481° window (57.7′ wide).
  Once the plateau reaches 0.8 of that width, neither the plateau nor the trunk P_det measures the
  model any more: the trunk extends 1.5° beyond the glare. Such cells are marked and are not results.

## Results, B0-optics (achromatic): `results/b0_v3_tables.md`, `results/sweep_ach_curves.png`

#### RETINAL TARGETS (achromatic B0-optics; trunk P_det, HDR-VDP-3 observer model)

| target (observer model X) | route | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | donor optics, evaluator OFF, 73 px/deg | 0.275 | 0.088 | 0.025 | 0.007 |
| HDR-VDP-3 eye MTF | donor optics, evaluator OFF, 73 px/deg | 0.027 | 0.005 | 0.000 | 0.000 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | donor optics, evaluator OFF, 73 px/deg | 0.268 | 0.123 | 0.038 | 0.004 |
| no optics (physical stimulus) | donor optics, evaluator OFF, 73 px/deg | 0.552 | 0.514 | 0.475 | 0.438 |
| HDR-VDP-3 eye MTF | evaluator optics on the physical stimulus, 146 px/deg | 0.051 | 0.009 | 0.000 | 0.000 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | evaluator optics on the physical stimulus, 146 px/deg | 0.285 | 0.132 | 0.041 | 0.005 |

Vangorp L_la at the trunk under each target's retinal image [cd/m², HDR-VDP local adaptation, extrapolated below its fitted 1 cd/m²] (diagnostic under observer model X):

| target | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | 0.000374 | 0.00173 | 0.0142 | 0.139 |
| HDR-VDP-3 eye MTF | 0.00332 | 0.0289 | 0.284 | 2.83 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | 0.000433 | 0.00196 | 0.0149 | 0.142 |
| no optics (physical stimulus) | 4.9e-05 | 4.91e-05 | 4.92e-05 | 4.94e-05 |

#### DISPLAY ENCODINGS (image D on the phone through the frozen pcond stack, Ldmax 100)

| encoding | evaluator | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| no optics (physical stimulus) | viewer's eye at the phone | 0.997 | 0.997 | 0.995 | 0.995 |
| no optics (physical stimulus) | optics OFF (diagnostic) | 0.999 | 0.999 | 0.999 | 0.999 |
| Spencer 1995 via Blender Fog Glow | viewer's eye at the phone | 0.744 | 0.173 | 0.012 | 0.000 |
| Spencer 1995 via Blender Fog Glow | optics OFF (diagnostic) | 0.858 | 0.392 | 0.028 | 0.001 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | viewer's eye at the phone | 0.178 | 0.041 wl | 0.033 wl | 0.030 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | optics OFF (diagnostic) | 0.362 | 0.274 wl | 0.255 wl | 0.244 wl |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 (PSF x PSF, informational) | viewer's eye at the phone | 0.955 | 0.664 | 0.144 | 0.014 |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 (PSF x PSF, informational) | optics OFF (diagnostic) | 0.983 | 0.829 | 0.317 | 0.067 |
| HDR-VDP-3 eye MTF (PSF x PSF, informational) | viewer's eye at the phone | 0.586 | 0.103 | 0.008 | 0.000 |
| HDR-VDP-3 eye MTF (PSF x PSF, informational) | optics OFF (diagnostic) | 0.761 | 0.249 | 0.017 | 0.001 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid (PSF x PSF, informational) | viewer's eye at the phone | 0.967 | 0.877 | 0.517 | 0.098 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid (PSF x PSF, informational) | optics OFF (diagnostic) | 0.989 | 0.959 | 0.793 | 0.236 |

Plateau: equivalent-area diameter of the pixels with displayed luminance above black >= 0.99 Ldmax [arcmin]; `wl` = window-limited (>= 0.8 of the 57.7' temporal window): neither the plateau nor the P_det is a result there:

| encoding | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|
| no optics (physical stimulus) | 1.9 | 1.9 | 3.2 | 3.2 |
| Spencer 1995 via Blender Fog Glow | 8.3 | 20.7 | 44.7 | 71.8 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | 7.1 | 52.7 wl | 57.9 wl | 59.7 wl |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | 6.9 | 10.9 | 19.8 | 41.5 |
| HDR-VDP-3 eye MTF | 11.0 | 26.0 | 53.3 | 87.4 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | 6.7 | 13.4 | 25.1 | 44.9 |

#### GAP: |P_det(viewer_eye(D)) - P_det(target_retina)| (display encodings, EVAL_VIEWER)

| encoding D | target | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| no optics (physical stimulus) | ISET 550 nm (retinal) | 0.722 | 0.909 | 0.970 | 0.988 |
| no optics (physical stimulus) | CIE99 (world, 146 px/deg) | 0.712 | 0.865 | 0.954 | 0.990 |
| no optics (physical stimulus) | HDR-VDP MTF (world, 146 px/deg) | 0.946 | 0.988 | 0.995 | 0.995 |
| Spencer 1995 via Blender Fog Glow | ISET 550 nm (retinal) | 0.469 | 0.085 | 0.013 | 0.007 |
| Spencer 1995 via Blender Fog Glow | CIE99 (world, 146 px/deg) | 0.459 | 0.041 | 0.029 | 0.004 |
| Spencer 1995 via Blender Fog Glow | HDR-VDP MTF (world, 146 px/deg) | 0.693 | 0.164 | 0.012 | 0.000 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | ISET 550 nm (retinal) | 0.097 | 0.047 wl | 0.008 wl | 0.023 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | CIE99 (world, 146 px/deg) | 0.107 | 0.091 wl | 0.008 wl | 0.025 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | HDR-VDP MTF (world, 146 px/deg) | 0.127 | 0.032 wl | 0.033 wl | 0.030 wl |

**Reading.**

- **The frozen display encoding (V0) is the largest gap, and not only because of glare.**
  - Even with no optics at all, the physical stimulus at night luminance gives a trunk
    P_det ≈ 0.5 under the observer model.
  - pcond shows it at 0.997.
  - The mapping of a 4·10⁻⁴ cd/m² scene into photopic display levels alone makes the trunk more
    visible than the night target.
  - Adding glare to D is one lever, not the whole solution.
- **Spencer (V4)** is within 0.09 (0.004–0.085) of the ISET and CIE99 targets from ×1 upward. At ×0.1 it shows
  the trunk far more than the targets do (0.74 vs 0.27–0.28).
  - This is an observation under one observer model, not a validation.
- **Temporal Glare (V5)** is within 0.13 at ×0.1. From ×1 upward it is window-limited, so it is not
  evaluated.
- **Retinal targets:**
  - ISET 550 nm (defocus 0) and CIE99 agree within a factor ~1.5 over the sweep.
  - HDR-VDP's own MTF gives a 10–20× lower trunk P_det.
  - That spread is **target uncertainty**: it is not a range of human visibility.
- **Vangorp L_la at the trunk** is 4·10⁻⁴–0.14 cd/m² for ISET and CIE99 (up to 2.8 for the HDR-VDP MTF),
  mostly far below the model's fitted 1–5000 cd/m². It
  is a diagnostic under the HDR-VDP local-adaptation model applied to each target's retina, and
  nothing more.

## Temporal Glare as an inner dynamic glare sample (`results/temporal_inner.json`, `.png`)

The plateau diameter of the demo is not used once near its window. What the window *can* say was
measured on the 33 **native** float PSF frames (demo times 0.8–9.4 s, median step 0.26 s, so the
spectrum is limited to < 1.9 Hz). The PSF is luminance-weighted, only inside a safe radius of 0.35°,
and each frame is normalised there:

| quantity | value |
|---|---|
| inner radial profile, temporal modulation (max/min − 1) | 0.6 % (0–1′), 1.8 % (1–2′), 3.7 % (2–4′), 3.5 % (4–6′), 3.3 % (6–10′), 2.6 % (10–15′), 6.0 % (15–21′) |
| centre-of-energy wander | 0.002′ rms (inner 0.35°), 0.003′ rms (core 5′): none |
| central deformation | core ellipticity 0.004–0.012, orientation 5–30° |
| core EE50 radius (within 0.35°) | 8.5–8.9′, ±2 % (3.8 % max/min) |
| energy in 2–10′ | ±1.7 % (3.5 % max/min) |
| temporal spectrum peak | 0.24 Hz (both), matching the traced hippus |

**Reading.** In this implementation, the eye's "breathing" is a symmetric ~3–4 % pulsation of the
inner glare at ~0.24 Hz. It does not wander, and its shape barely changes. Anything larger in a
clip is not this donor.

## For the viewer (blind)

`results/blind/A–F.png` and `A–F.mp4` (v1 set, nominal ×1, no trunk, taper + renormalised temporal):
a 1920×820 frame, image 1:1 in the centre, full screen on a phone held landscape at ~30 cm in a dark
room. Decide first, then open `results/BLIND_KEY_open_after_viewing.json` and the `REVEAL_` sheets.

**What the blind choice means.** It is a **human preference / resemblance judgement** ("which looks
most like what I remember"). It says nothing about physiological correctness.
- The set predates v3: warm source, the v2 ISET had hidden 0.26 D defocus, and it mixes retinal
  targets with display encodings.
- It is not rebuilt.
- Its answer is read against the DISPLAY ENCODINGS table, not the retinal one.

---

# Appendix: v2 record (warm source, one mixed table)

Superseded where v3 differs:
- the roles are separated;
- ISET is at defocus 0;
- the CIE99 grid is 4×;
- the plateau is Y ≥ 0.99·Ldmax.

Kept for the record and for the window-sensitivity test.

### Stimulus record (`make_b0.py`, `out/stim*/meta.json`)

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

### Stage ledger (no physiological stage twice)

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

### Variants (all existing implementations)

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

### Provenance corrections (Vangorp)

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

### Terminology

The size numbers below are **white-clipped plateau angular diameters under this display mapping**
(pcond, PHONE, Ldmax 100): the equivalent diameter of the area at display white. They combine:
- the PSF wings;
- the source level;
- the display peak;
- tone mapping;
- clipping.

They are **not PSF sizes**. A physically tiny aberration core (ISET EE50 ≈ 1′) gives a 12′ white
plateau because pcond puts the lamp ~30× above display white.

### Results

#### Continuous sweep (`results/sweep.json`, `results/sweep_curves.png`, `results/sweep_checks.json`)

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

#### Temporal Glare window sensitivity (window-limited)

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

#### Temporal data

- **NATIVE temporal data:** the 33 float PSF frames dumped from the demo at demo times
  0.8–9.6 s (~3.7 frames/s), and the 631 hippus steps traced in `tracks/temporal-glare-2009`.
  Only these may be used for frequency analysis. Hippus is broadband below ~0.6 Hz, peak
  0.24 Hz; PSF energy ±3.8 %.
- **INTERPOLATED 24 fps:** the V5 video in the blind set. Perceptual preview only; linear
  interpolation low-passes the sequence.
- Only the hippus part of Temporal Glare exists in the demo. Blinks, lens/vitreous particles,
  eyelashes and field-luminance/observer-motion dependence are paper-only.

