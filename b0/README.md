# B0: bright-point-source perception bake-off, v1

**Question.** For the same physical light (one distant warm road lamp, unresolved) on the same
phone display, how do the different schools represent it?
- eye optics: core only, aberrations, CIE disability-glare veil, Spencer glare;
- ocular dynamics: temporal glare / hippus;
- local adaptation: Vangorp 2015, used as an oracle.

What does each do to the lamp's look and to a dark object right next to it? **No winner is
chosen here**; the blind set in `results/blind/` is for the viewer, whose memory of the real
scene is the perceptual target no oracle has.

**Frozen:** the Blender scene and pipeline are not touched. Every variant goes through the
**same** display step, the frozen pcond stack (`b0/display.sh`), so only the optics differ.

    nix develop -c python3 b0/make_b0.py                                       # stimuli
    REPO=$PWD B0_OUT=$PWD/b0/out/optics SPD_CSV=$PWD/tracks/mitsuba-spectral/spectra/test_spectra_unitlum.csv \
      bash tracks/iset/scripts/run_octave.sh b0/iset_kernel.m                  # ISET point image (Octave)
    TAPER=1 nix develop -c b0/run_optics.sh                                    # six optics variants + Vangorp maps
    TAPER=1 nix develop -c b0/run_display.sh                                   # display step, metrics, visibility
    nix develop -c python3 b0/blind.py                                         # blind set (key in results/)

## Stimulus (`make_b0.py`)

- **Display density and field.** Made directly at the PHONE target density: 73 px/deg, the
  image formed at the display resolution per M2.6. The field is 12° × 6° (876 × 438 px).
- **Background:** night sky, 4·10⁻⁴ cd/m².
- **Lamp:** one warm unresolved source, the scene's luminaire (800 cd at 3 km, E = 8.9·10⁻⁵ lx
  at the eye), plus ×10 and ×100 variants.
- **Paired image with a silhouette:** a black bar 0.15° × 3° whose near edge is 0.3° from the
  lamp (a poplar trunk).

## Variants (all existing implementations; `run_optics.sh`)

| id | school | implementation | notes |
|---|---|---|---|
| V0_none | no eye optics (the M2.6 state) | — | the reference "physical" image |
| V1_iset | eye optics, aberration core | ISETBio/ISETCam `wvf human`: **Thibos 2009 mean eye, 6 mm pupil, HPS spectrum, on-axis, focus 550 nm** | unmodified oiCreate/oiCompute under Octave; scene at 4× (292 px/deg) then area-binned (a 1-px point gave sinc "cross" tails). **One configuration, not "the human PSF"** |
| V2_hdrvdpmtf | eye MTF fitted for a visibility metric | HDR-VDP 3.0.7 `hdrvdp_mtf('hdrvdp')` | loses 0.9 % of energy (the donor's MTF) |
| V3_cie99 | CIE disability-glare veil | HDR-VDP 3.0.7 `hdrvdp_otf_cie99`: CIE 135/1 (Vos & van den Berg 1999) GSF, age 24, pigmentation 0.5 | needs `b0/octave_shim/dirac.m` under Octave (MATLAB symbolic function; zero where it is evaluated). CIE 146:2002 is the later edition, not this file |
| V4_spencer | Spencer 1995 static glare | our calibrated Blender Fog Glow adapter (`m1/fog_glow.py`, tested to Spencer Eq. 5) | applied to radiance (retinal stage), then the display step |
| V5_temporal | ocular dynamics (hippus) | the Temporal Glare co-author demo's float PSF frames (Frisvad), rebinned to 73 px/deg | **ADAPTED:** circular cosine taper 0.4–0.5° (the demo's ±0.5° FFT window showed as a square at our exposure); time interpolation to 24 fps; per-frame unit energy |
| — | Vangorp 2015 local adaptation | HDR-VDP 3.0.7 `hdrvdp_local_adapt` (model #7) | **oracle**, not an image: the adaptation luminance at the lamp, at the silhouette, in the far sky, for each variant's retinal image |
| — | Tariq 2023 perceptual TM | no code | **not run** (would need a reimplementation) |

## Measurements (`measure.py`, `results/metrics.csv`, `results/radial_profiles_k*.png`)

Per variant, source ×1/×10/×100 and phone peak Ldmax 50/100/200 (×0.5/×1/×2):
- peak display luminance;
- core size (equivalent diameter of the half-maximum area);
- white-core area;
- radial halo profile, and halo radius (where the profile falls to 2× background);
- displayed energy above background;
- Vangorp adaptation luminance.

**Dark-target visibility** (`results/bar_visibility.json`): HDR-VDP-3 side-by-side P_det,
silhouette vs none.
- **Displayed:** each variant's displayed images, on PHONE, with the viewer's eye MTF.
- **"World" reference:** the physical stimuli seen by HDR-VDP-3's eye, once with the CIE99 GSF
  and once with its own MTF.
- The world reference **depends on which eye-optics model is used**; both are given.
- Visibility matching is pcond's own design goal (Ward 1997): a displayed silhouette should be
  about as visible as in the world.

No perceived-brightness oracle exists here. Spencer 1995 and Ritschel 2009 report that halos,
and dynamic halos more so, raise perceived brightness; that is for the viewer to judge.

## Artefacts found and removed (all from sampling, none from the models)

- **ISET, a cross.** A single 73 px/deg pixel used as the point gave sinc tails along the axes
  (on-axis 8.8·10⁻⁶ vs diagonal 9·10⁻⁹ of peak). Fixed by computing the scene 4× finer and
  area-binning; after the fix, axis and diagonal agree (7.9 vs 7.3·10⁻⁶).
- **HDR-VDP OTFs (CIE99 and its MTF), a dashed cross through the lamp.** The OTFs are not zero
  at the output Nyquist frequency. Fixed by evaluating them on a 2× grid and binning; 2× and 4×
  are identical.
- **Temporal Glare, a square.** The demo's PSF lives in a ±0.5° FFT window and is still ~10⁻³ of
  its peak at the edge (22 % of its energy beyond 0.41°). At pcond's exposure the window shows as
  a square. Replaced by a circular cosine taper over 0.4–0.5° for all runs (ADAPTED). Run-1
  numbers without the taper are kept in `results/*_run1_*.json`.
- **Remaining limitation, ISET ×10/×100:** its computation field (2° scene, kernel ±1.24°)
  truncates the far wings, which shows as a faint square at high source levels
  (REVEAL sheet). At ×1, the blind set, it is not visible.
- **Octave compatibility:** HDR-VDP's CIE99 OTF calls MATLAB's symbolic `dirac`
  (`b0/octave_shim/dirac.m`). The earlier round-8 HDR-VDP run with `mtf cie` had silently
  failed for this reason (its `run.json` ended at `"results":{`).

## Results (source ×1 = 800 cd at 3 km unless noted; PHONE, Ldmax 100)

| variant | white core on the display | core Ø (half max) | halo radius (2× bg) | displayed energy above bg | Vangorp adaptation at lamp / at silhouette (cd/m²) |
|---|---|---|---|---|---|
| V0 none | 4 px (3 arcmin²) | 1.9′ | 1.4′ | 3.0·10⁻⁵ | 3.5·10⁻⁴ / 4.9·10⁻⁵ |
| V1 ISET | 171 px (116 arcmin²) | 13.9′ | 14.8′ | 1.7·10⁻³ | 0.023 / 0.0018 |
| V2 HDR-VDP MTF | 500 px (338 arcmin²) | 25.8′ | 44′ | 8.1·10⁻³ | 0.24 / 0.032 |
| V3 CIE99 | 148 px (100 arcmin²) | 13.4′ | 17′ | 1.8·10⁻³ | 0.027 / 0.0022 |
| V4 Spencer | 316 px (213 arcmin²) | 20.6′ | 44′ | 6.2·10⁻³ | 0.14 / 0.022 |
| V5 temporal (tapered) | 2538 px (1715 arcmin²) | 52.5′ | 32′ | 1.8·10⁻² | 0.44 / 0.039 |

(sky: 4·10⁻⁴ cd/m²)

**Size and brightness.**
- Every eye-optics variant makes the lamp's *displayed* spot far bigger than the optics' core,
  because pcond puts the lamp ~30× above display white and so any tail above ~3 % of the peak
  clips.
- Even ISET's aberration-only PSF (no straylight) gives a 14′ white spot.
- ×10 and ×100 grow every spot (REVEAL sheet). Only V0 stays a 2×2 core.

**Dark silhouette 0.3° from the lamp: HDR-VDP-3 detection probability** (`results/bar_visibility_table.txt`)

| | ×1 | ×10 | ×100 |
|---|---|---|---|
| world, CIE99 eye | 0.15 | 0.05 | 0.007 |
| world, HDR-VDP eye | 0.012 | 0.001 | 0 |
| V0 none | **0.997** | 0.995 | 0.996 |
| V1 ISET | 0.90 | 0.41 | 0.05 |
| V2 HDR-VDP MTF | 0.19 | 0.015 | 0.001 |
| V3 CIE99 | 0.92 | 0.69 | 0.18 |
| V4 Spencer | 0.31 | 0.023 | 0.001 |
| V5 temporal | 0.045 | 0.034 | 0.032 |

- **The current state (V0) shows a trunk next to a lamp that the eye in the world would almost
  certainly not see** (0.997 vs 0.01–0.15).
- The world reference itself depends on the eye-optics model used as the oracle: 0.15 vs 0.012.
- Variants within that range at ×1: V2, V4 and V5. V1 and V3 stay far above it until ×100.
- Phone peak ×0.5/×2 barely changes visibility (pcond rescales; `bar_visibility.json`), but
  changes the white-core size by 10–30 %.

**Temporal.** Only V5 changes over time (the hippus halo pulsation, < 0.6 Hz). Whether the eye
reads it is for the blind viewing.

## For the viewer (blind)

`results/blind/A–F.png` and `A–F.mp4`: a 1920×820 frame, image 1:1 in the centre. Open full
screen on a phone held landscape at ~30 cm in a dark room (= PHONE_TARGET). `overview_…png` has
the six crops side by side. Decide first, then open `results/BLIND_KEY_open_after_viewing.json`
and the `REVEAL_` sheets.
