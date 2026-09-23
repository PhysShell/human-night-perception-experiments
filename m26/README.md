# M2.6: sampling density (16 / 32 / 64 px/deg) and where the display is formed

**Question** (after M2.5): the lamps looked like small squares, and each lamp's displayed
energy "breathed" by 20–30 % while the observer walked. How much of that is the render's pixel
grid, i.e. does it change with sampling density?

**Setup.**
- The first 2 s (48 frames) of clip B: walk 1 m/s, clear, the same scene, path and frozen
  stack.
- Rendered at 16 / 32 / 64 px/deg of the 60° view (960 / 1920 / 3840 px wide).
  - 16 px/deg = the M2.5 frames.
  - 32 and 64 render the near half of the ribbon at full density (`M26_CROP`) and take the
    rest from the 16 px/deg frames (`composite.py`). pcond's exposure is the same on every
    frame at every density (1389.9–1390.4), so the composite does not move the adaptation.
- One target display for all three: a phone in landscape, the 1920 × 820 clip full width
  (~14 cm) at 30 cm, i.e. ~26° wide and **74 px/deg**; pcond's 100 cd/m², 100:1, dark room
  (`display_models_m26.json`).
- Resampling uses Blackman–Harris (`to_target.py`), never nearest-neighbour.
- The display is PBR Neutral on out-of-gamut pixels (warm lamps).

    nix develop -c m26/run_m26.sh                 # ~2.5 h (renders 32 and 64 once), ORDER=target
    ORDER=render nix develop -c m26/run_m26.sh    # the first, wrong order (kept for the record)

## Result 1: the order of operations decides whether density converges

| order | 16 vs 64 | 32 vs 64 | lamps at 64 px/deg |
|---|---|---|---|
| **render → pcond → resample to the display** (as first run) | 7.26 JOD | **9.14 JOD** | dimmer, less warm, no pixel reaches white |
| **render → resample scene radiance to the display → pcond** | 7.42 JOD | **9.75 JOD** | same as 32 |

- pcond's clip (the display's 100:1 range) must act on the pixels the display actually has.
  Clipping at the render pixel throws away more of each lamp's energy the finer the render, so
  it cannot converge.
- A display pixel is the physical emitter. It shows the scene integrated over its own area,
  and only then does the display's range limit apply.
- With the right order, **32 vs 64 px/deg = 9.75 JOD**, the same as two seeds of the same
  render (9.72, M2.5 §4).
- **Result: render at ≥ 32 px/deg of the scene (the 1920-px M1 resolution), form the image at
  the target display, then apply pcond. 16 px/deg is not enough (7.4 JOD).** M2.5's 960-px
  clips were formed at their own 960-px "display" and then shown 2× nearest-neighbour on a
  phone. That is where the squares came from.

## Result 2: what remains is the display's own grid (`density_result_target_first.txt`)

At the target, tracked isolated lamps at 2.6–3.3 km, 2 s:

| render density | white core on the display | displayed energy modulation (median / p90) |
|---|---|---|
| 16 px/deg | 14 px (a 7′ blob of the scene) | 5.9 / 9.2 % |
| 32 px/deg | 4 px (2 × 2 display pixels) | 10.5 / 26.4 % |
| 64 px/deg | 4 px (2 × 2 display pixels) | 10.9 / 26.9 % |

- **Squares are gone.** At 32/64 px/deg a lamp is a 2 × 2-pixel white core on a 74 px/deg
  display, ~1.6′ on the retina, i.e. at the eye's resolution limit: a point, not a square.
- **The breathing does not go away with render density.** It converges to ~11 % median over
  2 s (M2.5 had ~20–28 % over 10 s at 960 px).
  - It is the **target display's** grid: an unresolved source whose core is far above white
    lights 1–4 display pixels depending on its sub-pixel phase.
  - Any pixel display does this. Only a spread larger than a pixel before the range limit
    would remove it: optics (the eye's PSF) or a display with more range.
  - 16 px/deg looks calmer only because the 2× upsampling blurs every lamp into a 7′ blob.
- **Haze noise.** At 32 px/deg the spot-lit ground under the lamps shows as fine grain (32 spp
  per display pixel). At 64 px/deg it averages out (4 × 32 spp); CVVDP counts this as part of
  the 0.25 JOD.

## Consequences

- Clips for viewing are rendered at ≥ 32 px/deg and formed at the viewing device's resolution
  before pcond. The M2.5 phone copies (960 → nearest ×2) are diagnostic only.
- The "breathing" of M2.5 was mostly the render grid (the 960-px display plus nearest ×2). The
  residual ~11 % is the grid of any real display.
- That residual is not atmosphere and should not be kept as "life". Whether it is visible at
  74 px/deg needs the eye's optics:
  - the calibrated Spencer PSF (M1 Fog Glow adapter, frozen OFF) spreads the core over
    several display pixels;
  - but at the display's 100:1 range the full PSF became 0.3–0.5° discs in M1.
  - That trade-off, not scintillation, is the next question.
