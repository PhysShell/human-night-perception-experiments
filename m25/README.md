# M2.5: a slow look at the frozen scene (video, no new physics)

> **Superseded in part by [M2.6](../m26/README.md).** The 960-px clips here were formed at 16 px/deg
> and the phone copies were upscaled nearest-neighbour. Hence the square lamps and most of the
> 20–30 % "breathing", which came from the render grid, not the air. Clips for viewing: render at
> ≥ 32 px/deg, resample the scene radiance to the device, then pcond.

**Question.** Does the distant ribbon already feel "alive" from the observer's own motion
(sub-pixel motion, occlusion by the poplars, atmosphere), before any scintillation (M3)?

**Scope.**
- The scene is the frozen M2 scene, clear atmosphere (V = 40 km, single scattering).
- The stack is the frozen M1.1 stack, motion variant: LC → Radiance `clipgamut`.
- No scintillation, no Fog Glow, no new physics.

    nix develop -c m25/run_m25.sh            # clips A and B, ~3 h on 4 cores, + invariants, tracks, videos
    nix develop .#video -c m25/cvvdp.sh TEST.mp4 REF.mp4 OUTDIR    # ColorVideoVDP diagnostic
    nix flake check                          # incl. m25-decomposition, m25-golden-clip

| clip | observer | length |
|---|---|---|
| **A** | standing still | 10 s (one frame, repeated: fixed seed, nothing in the scene moves) |
| **B** | walking sideways at 1 m/s, eye height 1.7 m | 10 s, 24 fps, 240 frames; frame 1 = A |

Viewing condition (declared, as for FLIP in T2):
- pcond's own display: Ldmax 100 cd/m², dynamic range 100:1 (pcond defaults), dark room;
- the 960 × 410 clip fills the camera's 60° horizontal field of view, i.e. 16 px/deg.

## 1. Why a video needs a different render than a still

A still at 512 spp hides a problem that motion exposes. Each lamp covers ~0.1–3 % of a
pixel, so only a handful of camera samples hit it. pcond's exposure (1390 here) makes
even 1 % of a lamp's energy visible: one sample hit in a neighbouring pixel is worth
~27 cd/m² on the display. In motion, which samples hit changes from frame to frame. **Monte
Carlo noise on the lamps would read as twinkling**: exactly the effect M3 is supposed to
judge, produced by the renderer instead of the air.

Fix: the frame is rendered as **two passes whose sum is the one-pass render**. This uses only
stock Cycles plus an OIIO resize.

| pass | contents | sampling |
|---|---|---|
| `haze` | everything except the camera-visible lamp spheres: sky, ground, poplars, spot-lit ground and haze | 32 spp, fixed seed |
| `lamps` | only the lamp spheres, seen through a purely absorbing medium with the same total extinction (the unscattered camera ray is all a sphere contributes, since it is visible to camera rays only) | see below |
| `occluders` | test aid only: white poplars on black | 16 spp |

The lamps pass, step by step:
1. **Enlarged, same intensity.** Each sphere is enlarged to 0.7 px across at its distance,
   with its radiance lowered by the same area. The intensity in cd is unchanged, and an
   unresolved source is defined by intensity alone.
2. **See-through.** Emission comes from the front face only, and the sphere lets light
   through. Where the road recedes, enlarged spheres overlap on screen; opaque ones hid each
   other and lost up to 80 % of the far bins.
3. **No ground.** The flat ground never hides a lamp from eye height, but it cut enlarged
   distant low lamps in half (−10 %).
4. **4× resolution, 1-px box filter, 256 spp (4096 per output pixel).** Fixed seed, no
   adaptive sampling: adaptive sampling made filter-tail pixels blink between "stopped with 0
   hits" and "one hit".
5. **Resample** to the output with Cycles' own pixel filter. Cycles builds its Blackman–Harris
   table over 2 × `filter_width` (film.cpp), so a window 3 output pixels wide
   (`m25/resample.py`). The filter tails then come from many well-sampled pixels, not from
   rare hits.
6. **Band only.** Only the image band that holds lamps over the whole camera path is rendered
   (+6 px), so the lamps pass costs ~13 s per frame.

**Equivalence gate (`m25-decomposition`, golden view)** (`decomposition_result.txt`):
- haze pass = one-pass render away from the lamps (median 0.9992);
- lamps pass / true-radius lamps (16k spp, two seeds) = **1.001** in total;
- every 20-column bin within tolerance;
- peak-row energy share (spot shape) 0.756 vs Cycles' 0.798.

The one-pass render cannot be the lamp reference itself: at 320 px it gives each lamp a couple
of hits.

## 2. Display in motion

Every frame goes through `m1/pcond_colorimetric.sh LC`, then `clipgamut`, then the sRGB
Standard view, then lossless x264 RGB (`display_clip.sh`).

**pcond adapts per frame.** Its linear-mode exposure comes from each frame's histogram, so a
changing exposure would be a global flicker no eye makes. It is logged per frame and must stay
within 1 %.

## 3. Invariants (`check_clip.py`), run on every clip

- finite;
- pcond linear mode and constant exposure;
- lamp energy (away from the frame edges): no single-frame blink > 0.5 % (steps from lamps leaving the frame or passing behind poplars are reported, not failed);
- no single-frame **blink** > 20 % (luminance) or > 0.004 u′v′ in windows around lamps, on the
  pcond stage and the display, except at poplar edges;
- displayed ribbon band ≤ 2 % per frame.

A lamp seen through a moving gap between trees does blink physically. Those blinks are
counted, not failed.

**Negative control.** The same pilot with the old adaptive lamps pass **fails**: blinks of
71 % against ≤ 3.4 % now.

## 4. How visible is the render noise? (ColorVideoVDP, diagnostic)

The same 12-frame pilot was rendered with two seeds (`m25/cvvdp.sh`):

| comparison | JOD (10 = identical) |
|---|---|
| seed 0 vs seed 1, moving | 9.721 |
| haze from seed 1 + lamps from seed 0, vs seed 0 | 9.721 (the lamps pass adds no visible noise) |
| seed 0 vs seed 1, **static** (frame 1 repeated) | 9.724 |
| seed 0 vs seed 1 with Cycles OIDN on the haze pass | 9.946, but band energy −25 % vs 512 spp → **rejected** |

**Reading.**
- The visible seed difference (~0.28 JOD) sits in the spot-lit ground and haze right under the
  near lamps (heat map). It is the same whether the camera moves or not, so it is a **frozen
  spatial noise pattern, not temporal noise**. With a fixed seed and a slow camera, motion adds
  no visible noise.
- Any "life" in clip B therefore does not come from the renderer.
- For M3, a scintillation effect must stand clearly above this level (≈ 0.28 JOD) to count.

## 5. Results (`B_walk_check.txt`, `B_walk_modulation.txt`, videos in `docs/m25-results/`)

**Invariants: clip B (240 frames) passes on both displays.**

| invariant | clip B |
|---|---|
| pcond | linear mode on every frame; exposure 1389.9–1390.4 (0.036 %): no adaptation flicker |
| lamp energy (away from the frame edges) | largest single-frame blink 0.10 %; largest step 1.22 % |
| blinks, pcond stage | ≤ 8.4 % |
| blinks, display | ≤ 15.5 % |
| displayed ribbon band | ≤ 0.45 % per frame |

- The lamp-energy steps are near lamps leaving the frame at the left edge (frames 113–115 and
  137–139) and a lamp coming out from behind a poplar. A first version gated every step at 1 %
  and failed on exactly these legitimate events; it now fails on blinks only.
- PBR display only: 7 frames have a blink of more than 20 % at a poplar edge (allowed).
- The negative control (adaptive lamps pass) still fails.

**What motion does to each lamp** (`analyse_clip.py`). 26 isolated lamps at 2.7–3.3 km were
tracked; they move 2.5–3.4 px over the clip. Energy in a 7×7 window around each:

| stage | modulation over 10 s (median / p90 / max) | dominant frequency |
|---|---|---|
| scene (lamps pass) | 4.5 / 5.1 / 5.5 % | 0.4 Hz |
| pcond stage | 20.8 / 26.4 / 27.5 % | 0.4 Hz |
| display, clipgamut | 21.5 / 29.3 / 30.1 % | 0.4 Hz |
| display, PBR out-of-gamut | 24.4 / 31.2 / 32.7 % | 0.4 Hz |

**Reading.**
- **Scene.** The physics (I·T/d²) does not change over 10 m of walking. The 4.5 % is the pixel
  filter's grid ripple: a 3-px Blackman–Harris window summed over the pixel grid varies by up
  to 6.5 % with sub-pixel phase. Cycles has this property itself, and the lamps pass
  reproduces it.
- **Display.** A lamp's core is far above display white (pcond clips it), so its visible
  energy is set by how many of its pixels are clipped. That depends on where the lamp sits on
  the pixel grid.
- **So a walking observer sees every lamp "breathe" by ~20–30 % at ~0.4 Hz**, the rate at
  which it crosses pixels. Nearer lamps move faster, so different lamps breathe out of phase.
- This comes from the display and its 16 px/deg grid, not from the air. A finer grid (the
  1920-px render) halves the period, and a real eye has no pixel grid. It is still a real
  stimulus on a screen.
- **The second source of life is occlusion.** Lamps pass behind poplar edges and gaps; in the
  clipgamut display these blinks are counted separately and allowed.

**Colour.**
- The motion display (clipgamut) makes the lamp cores almost white; the known compromise from
  M1 §4 is visible here.
- The stills display (PBR Neutral on out-of-gamut pixels) keeps them warm.
- In this clip it also passes every invariant: display blinks are the same ≤ 15.5 %, and its
  modulation is only slightly higher (24 % vs 21 %).
- The 12–16 % gamut-exit drop seen in the synthetic ramp does not show up as a blink here.
  **Candidate for the motion display, pending the viewer's judgement.**

**Not done.** ColorVideoVDP between A and B is not meaningful: the content moves, and the
metric compares images that should match. It was used for what it can answer: render noise
visibility (§4).

## 6. For the M3 decision

- The observer's own motion already gives a slow, out-of-phase breathing of the ribbon
  (display grid) and occlusion blinks at the poplars.
- Stationary, clip A shows none of it.
- Scintillation (M3) would add a fast (several Hz), random, per-lamp flicker. That is a
  different stimulus from this 0.4 Hz one, and it would matter in the stationary case
  especially.
- **Decision criteria:**
  - does clip A feel dead compared with the memory?
  - does clip B's breathing read as natural, or as a display artefact?
- Any scintillation must stand above the render-noise level (≈ 0.28 JOD, §4).
