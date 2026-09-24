# D0: what existing display renderers do with a calibrated night scene

**Question.** Given a frozen, physically calibrated HDR night scene and a target display with limited
luminance/contrast/gamut, how do existing display-rendering systems map it?

- Each donor is run independently and as natively as practical.
- No new tone mapper, no optimiser, no inverse-eye rendering, no combination of donors.
- **No ranking, no winner.**
- B1 eye models are not used as a renderer (`docs/research/b1-closeout.md`).
- The B0 blind key is untouched.

| role | in D0 |
|---|---|
| physical scene model | frozen Blender/Cycles M2.6 frames + B0 stimulus + two calibrated Fairchild photographs (`d0/make_inputs.py`) |
| eye / reference model | none |
| display renderer | the donors (`d0/donors/`, `d0/input-contracts/`) |
| display model | `d0/display-scenarios.json` + `d0/display_model.py`: ONE parametric decoder for every donor's code values |
| evaluation | `d0/metrics.py`: descriptive measurements. HDR-VDP-3 P_det only as a diagnostic under its own observer model |

## Reproduce

    nix develop -c python3 d0/make_inputs.py                 # frozen inputs -> d0/work/inputs (not committed)
    nix develop -c d0/donors/pcond/run.sh                     # A  pcond V0, unchanged
    d0/donors/mantiuk08/run.sh                                # B  pfstmo_mantiuk08 + D2 pfstmo_reinhard02 (pfstools 2.2.0)
    python3 d0/donors/aces2/run.py                            # C  ACES 2 via OpenColorIO 2.5.2 (creates its venv; CTL check)
    nix develop -c python3 d0/donors/controls_d1.py           # D1 exposure + clamp
    (E iCAM06: authors' V1.3 MATLAB under Octave, see d0/input-contracts/icam06.md; code not redistributed)
    nix develop -c python3 d0/metrics.py                      # -> results/tables/metrics.jsonl, scene_reference.json
    python3 d0/summarize.py                                   # -> results/tables/summary.md, metrics_S*.csv
    tracks/temporal-glare-2009/py.sh d0/contact_sheets.py     # -> results/stills/sheet_*.png

Donor versions, licences and fetch instructions are in each input contract.

## Inputs (frozen; `d0/work/inputs/manifest.json`)

All inputs are linear Rec.709/D65 float EXR, Y in **absolute cd/m²**.

| id | what | notes |
|---|---|---|
| S0 | dark rural still: M2.6 frame 1, haze pass only (no lamp spheres), 1920 × 820 | Cycles output × 179 (Radiance 179 lm/W convention, `m1/README.md` §1). Sky median 2.9·10⁻⁴, scene median 7·10⁻⁵ cd/m² |
| S1 | the same + the distant lamp ribbon | lamps up to 302 cd/m² per display pixel |
| S2 | 2 s walking clip, 48 frames, 24 fps (M2.6 target-first frames) | |
| S3 | B0 warm point source ×10 (8.9·10⁻⁴ lx at the eye) + black bar 0.3° away, bar/no-bar pair | P4 diagnostic |
| S4 | Fairchild HDRPS "Golden Gate (2)": a real calibrated night photograph | licence: non-commercial research, derived files not committed |
| S5 | Fairchild "McKees Pub" ×6.25: a lit interior at night | mixed-luminance control. **No daytime scene**: markfairchild.org now answers new downloads with a JavaScript bot check |

- **Geometry.** S0–S2 are a 60° render shown at 73 px/deg (~26°), so the scene's angles are not the display's.
  S3 is 1:1 visual angle. S4/S5 are shown 1:1 at 1024 px.

## Display scenarios (`display-scenarios.json`: parametric, not the viewer's hardware)

- **Geometry:** PHONE 73 px/deg, DESKTOP 48.4 px/deg.
- **Luminance:**
  - SDR100 (sRGB, 100 / 0.1 cd/m²)
  - SDR200 (γ 2.2, 200 / 0.2)
  - BRIGHT500 (γ 2.2, 500 / 0.005)
  - BRIGHT500_PQ (PQ, 500 / 0.005; added for ACES)
  - HDR1000 (PQ Rec.2020, 1000 / 0.005)
- **Ambient:** DARK 0 lx (the night-viewing case), DIM 50 lx with reflectivity 0.01.
- **Output contract.** Every donor delivers 16-bit PNG code values in the scenario encoding. `display_model.py`
  turns them into emitted cd/m², so every donor is judged under the same display model.

## Donors and status

| donor | status | configs (NATIVE_DEFAULT / DOCUMENTED_TARGET_CONFIG / SENSITIVITY_RUN) |
|---|---|---|
| A pcond V0 (Radiance, `m1/pcond_colorimetric.sh LC` + PBR-oog sRGB) | run unchanged | native_default (SDR100); `-u/-d` for SDR200, BRIGHT500; no HDR |
| B Mantiuk08 (pfstools 2.2.0 `pfstmo_mantiuk08`) | run; native example reproduced | native_default; WHITE_Y auto; WHITE_Y = display peak; WHITE_Y sweep 4e-4…4; DESKTOP; DIM; `--scene-y-adapt auto`; video (IIR smoothing, 25 fps) |
| C ACES 2 (OCIO 2.5.2 built-in `studio-config-v4.0.0_aces-v2.0_ocio-v2.5`) | run; **matches the CTL reference within one 10-bit code** | fixed mapping ACES 1.0 = 100 cd/m² on SDR100, BRIGHT500_PQ, HDR1000; exposure sweep −4…+20 stops |
| D1 exposure + clamp | run | d1a photometric (exposure 1), d1b log-average key 0.18 |
| D2 Reinhard02 (`pfstmo_reinhard02`) | run, defaults | SDR100/200/BRIGHT500 encodings |
| E iCAM06 (authors' V1.3 MATLAB, Octave, trivial shims) | run on stills; native PeckLake example reproduced | native (max_L 20000); absolute input γ 1.2 (Readme) and γ 1.5 (paper) |
| F ITU-R BT.2446 | **STANDARD_REFERENCE_ONLY** | display-referred HDR→SDR, needs an HDR rendering first; no trustworthy full implementation |
| G Tariq et al. 2023 | **REFERENCE_ONLY** | no code |

## What the donors do: measurements, not a ranking

Full tables: `results/tables/summary.md`. Previews: `results/stills/sheet_*_SDR100.png`. Measurement view across
displays: `results/stills/sheet_S1_scenarios.png`. Clips: `results/video/`. Numbers are for PHONE, DARK, emitted
cd/m². The physical sky of S0/S1 is 2.9·10⁻⁴ cd/m².

**P1: does it read as night?** S1 sky median on SDR100, cd/m²:

| pcond V0 | D1a | D1b | Reinhard02 | Mantiuk08 auto | Mantiuk08 anchor | ACES 2 | iCAM06 native / abs γ1.2 |
|---|---|---|---|---|---|---|---|
| 0.32 | 0.1 (= black) | 50 | 30 | 12.5 | 5.0 | 0.1 (= black) | 30 / 27 |

- Two groups:
  - **Crushing to the display's black:** D1a and ACES 2 at its documented mapping. 99.7 % of pixels sit at black;
    only lamps remain.
  - **Lifting the night into a grey/brown dusk:** D1b, Reinhard02, iCAM06, and Mantiuk08 with automatic WHITE_Y.
- pcond V0 sits between them (sky 0.3 cd/m², 3× black).
- ACES needs about +12–14 stops before the sky leaves black. The scene median reaches ACES 0.18 near +18 stops. It has
  no notion of an observer adapted to 4·10⁻⁴ cd/m².

**P2: silhouettes.** Displayed Weber contrast sky→poplar (physical 0.72):
- pcond 0.56, Reinhard02 0.64, D1b 0.72, Mantiuk08 auto 0.79 / anchor 0.71, iCAM06 0.89–0.96;
- 0 where everything is black (D1a, ACES).
- iCAM06 floors luminance at 1e-4 cd/m² in its bilateral filter (52 % of S0/S1 pixels), which flattens the dark
  ground in its absolute configs.

**P3, P5: sources, plateaus.** S1 SDR100:

| | pcond | D1b | Reinhard02 | Mantiuk08 auto | Mantiuk08 anchor | ACES 2 | iCAM06 native |
|---|---|---|---|---|---|---|---|
| source/sky contrast | 270 | 2 | 3.2 | 8 | 20 | 584 (the sky is black) | 3.3 |
| display-white plateaus (n / largest ⌀) | 2 / 0.9′ | 338 / 109′ | 1 / 0.9′ | 88 / 39′ | 28 / 1.3′ | 0 | 467 / 96′ |

- The largest plateau is the lamp ribbon merged into one white line where the curve clips many lamps. That is a
  "giant white" failure of D1b, iCAM06 and Mantiuk08 auto.
- pcond, Reinhard02, Mantiuk08-anchor and ACES keep individual lamps below or at ~1′.

**P6: warm lamps.** Saturation kept (u′v′ distance from white, displayed / scene):

| ACES 2 | Reinhard02 | pcond | Mantiuk08 | D1b, iCAM06 |
|---|---|---|---|---|
| 0.60 (SDR), 1.1 (HDR) | 0.76 | 0.35 | 0.001–0.10 | ≈ 0 (clipped to white) |

**P4: nearby dark object.** S3, HDR-VDP-3 P_det diagnostic; EVAL_VIEWER = the viewer's eye at the phone.
- Everything that lifts the sky (D1b, Reinhard02, iCAM06, pcond) keeps the bar next to the lamp detectable
  (P ≈ 1).
- D1a and ACES make it "invisible" only because the whole sky is at display black (P = 0, bar Weber 0). **That is
  crushing, not glare.**
- **Mantiuk08 on BRIGHT500/HDR1000 is the only case where the bar's detectability drops under the viewer's own
  eye** (EVAL_VIEWER 0.43–0.67, EVAL_OFF 0.98). There the sky is 0.018 cd/m² and the lamp reaches peak: the real
  display's glare in the real eye does it.

**P7: temporal.** 2 s clip:
- **No donor creates flicker or tone pumping:**
  - global mean max step ≤ 0.9 %;
  - empirical tone curve steps ≤ 1 % (pcond: 0.6–1 % at the brightest level);
  - one isolated-flash frame (pcond).
- Mantiuk08's tone curves are smoothed (max step 1.1·10⁻³ log₁₀; 2.6·10⁻² without smoothing).
- D1b and Reinhard02 re-normalise every frame, but the scene's key barely changes while walking.
- Source-region energy modulation is 0.1–2.8 %. The per-lamp display-grid breathing (M2.6) is not visible in this
  region-sum measure.

**P8: changing the display.** S1 sky median SDR100 → SDR200 → BRIGHT500 → HDR1000:

| donor | sky median |
|---|---|
| pcond | 0.32 → 0.37 → 0.10 |
| Reinhard02 | scales with peak (30 → 61 → 151) |
| D1b | scales with peak |
| Mantiuk08 auto | 12.5 → 19.7 → 13.5 → 14.6, with deeper dark regions on high-range displays |
| Mantiuk08 anchor | 5.0 → 5.8 → 2.5 → 2.5 |
| ACES | black on every target; lamp peak 74 → 213 → 291 cd/m² |

- Donors that only encode (Reinhard02, D1b) put more light on a brighter display.
- Display-aware ones (Mantiuk08, pcond with its range, ACES) use the range differently.

**Real night photograph (S4) and interior (S5).**
- All donors behave as on S1 in kind.
- Physical sky 0.69 cd/m² → ACES 0.13, D1a 0.69, pcond 9.4, Mantiuk08 auto 26, Reinhard02 31, iCAM06 23–31, D1b 45.
- On S5 there is no "night special-casing" failure beyond the same brightening/crushing split.

## Parameters without an objective value (explicit axes)

- **Mantiuk08 WHITE_Y.** A night scene has no diffuse white. Two defensible anchors differ by 5.4 decades: display
  peak (used here) vs a white surface lit by the night sky, ~4·10⁻⁴ cd/m². The resulting sky ranges from 5 to
  64 cd/m² (sweep). **WHITE_Y is an appearance-design parameter here, not a physical one.**
- **ACES scene exposure.** The ACES documentation fixes 1.0 = 100 cd/m² only as a convention. Across −4…+20 stops,
  S1 goes from all-black to a clipped day-like image. There is no documented night anchor.
- **pcond display range, target peak, ambient** (Mantiuk08 DIM lifts the sky 12.5 → 16.5 cd/m²).
- **iCAM06 max_L / absolute scaling and surround γ** (Readme 1.2 vs paper 1.5).

## Limits and incidents

- **pfstools 2.2.0 `pfstmo_mantiuk08`:**
  - ignores the viewing geometry (hard-wired 30 px/deg; PHONE = DESKTOP, byte-identical);
  - accepts only 25/30/60 fps (25 used for the 24-fps clip, labelled ADAPTED);
  - its temporal filter is a 3rd-order IIR, not the paper's.
- **Disk.** Clips were written only for pcond, D1, Mantiuk08 auto (SDR100), ACES and Reinhard02 (SDR100). The
  other clips' tone curves exist; their frames can be regenerated (`D0_WRITE_S2`).
- **iCAM06** was run on stills only.
- **Disk incident.** A 4.7 GB unbounded download filled the disk during the round; five D1 frames were corrupted
  and regenerated. Containers were restarted once; all runs were redone from the frozen inputs.
- **P_det** is HDR-VDP-3's detection model applied to emitted light, one observer model. It is not a human
  measurement, and nothing is ranked by it.

**D0 is complete; it stops here.** Not started: D1 (no custom objective, no Spencer/Temporal Glare, no Blender
changes). Open questions: `docs/research/display-rendering-open-questions.md`. Donor matrix:
`docs/research/display-renderer-matrix.md`.
