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
    nix develop -c python3 d0/donors/controls_exposure.py     # CTRL-PHOT, CTRL-KEY exposure + clamp
    d0/donors/icam06/setup.sh && tracks/temporal-glare-2009/py.sh d0/donors/icam06/run_all.py   # E iCAM06 (author code fetched, not redistributed)
    tracks/temporal-glare-2009/py.sh d0/donors/icam06/ladder.py          # D0.1 iCAM06 absolute-level ladder
    python3 d0/donors/aces2/run.py family                                # D0.1 ACES exposure family (run.py venv)
    D0_PFSTOOLS_BUILD=master python3 d0/donors/mantiuk08/run_pfstmo.py master   # D0.1, master pfstools first on PATH
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

Every donor is classed by what its input numbers mean (**`d0/input-semantics.md`**, the D0.1 audit). Results are
readable only within that class.

| donor | input class | status | configs |
|---|---|---|---|
| A pcond V0 (Radiance, `m1/pcond_colorimetric.sh LC` + PBR-oog sRGB) | physical | run unchanged | native_default (SDR100); `-u/-d` for SDR200, BRIGHT500; no HDR |
| B Mantiuk08 (pfstools CLI `pfstmo_mantiuk08`, release 2.2.0; checked against master c860691, 2025) | relative + WHITE_Y anchor | run; native example reproduced; master = 2.2.0 byte for byte | native_default; WHITE_Y auto; WHITE_Y = display peak; WHITE_Y sweep 4e-4…4; DESKTOP; DIM; `--scene-y-adapt auto`; video (IIR, 25 fps); master: `--tone-value max` |
| C ACES 2 (OCIO 2.5.2 built-in `studio-config-v4.0.0_aces-v2.0_ocio-v2.5`) | scene-referred + exposure | run; **matches the CTL reference within one 10-bit code** | **exposure family** EV 0…18 on S0, S1, S3, S4 × SDR100, HDR1000; sweep −4…+20 on S1; EV 0 also on BRIGHT500_PQ and the clip |
| CTRL-PHOT, CTRL-KEY exposure + clamp (`controls_exposure.py`; D1a/D1b before D0.1) | physical clipping / relative key | run | exposure 1; log-average key 0.18 |
| D2 Reinhard02 (`pfstmo_reinhard02`) | relative key | run, defaults | SDR100/200/BRIGHT500 encodings |
| E iCAM06 (authors' V1.3 MATLAB, Octave, trivial shims) | absolute appearance | run on stills; native PeckLake example reproduced | native (max_L 20000); absolute γ 1.2 (Readme) and γ 1.5 (paper); **absolute-level ladder ×10⁰…10⁶** |
| F ITU-R BT.2446 | display-referred HDR | **STANDARD_REFERENCE_ONLY** | needs an HDR rendering first; no trustworthy full implementation |
| G Tariq et al. 2023 | — | **REFERENCE_ONLY** | no code |

## What the donors do: measurements, not a ranking

Full tables: `results/tables/summary.md`. Previews: `results/stills/sheet_*_SDR100.png`. Measurement view across
displays: `results/stills/sheet_S1_scenarios.png`. ACES exposure family: `results/stills/aces2_family_S1.png`.
iCAM06 ladder: `results/stills/icam06_ladder_S1.png`. Clips: `results/video/`. Numbers are for PHONE, DARK,
emitted cd/m². The physical sky of S0/S1 is 2.9·10⁻⁴ cd/m².

**P1: does it read as night?** S1 sky median on SDR100, cd/m²:

| pcond V0 | CTRL-PHOT | CTRL-KEY | Reinhard02 | Mantiuk08 auto | Mantiuk08 anchor | ACES 2, EV 0 / +12 / +14 / +18 | iCAM06 native / absolute |
|---|---|---|---|---|---|---|---|
| 0.32 | 0.1 (= black) | 50 | 30 | 12.5 | 5.0 | 0.1 (black) / 0.2 / 1.6 / 38 | 30 / 27 |

- **Read by input class.**
  - *Physical* inputs: CTRL-PHOT shows literal photometry, which is display black; pcond puts the sky at 0.3 cd/m²
    (3× black).
  - *Absolute appearance*: iCAM06 does have a principled input for the absolute level, and the D0.1 ladder shows
    its machinery responds to it. It still renders the physical night as a dusk at 27 cd/m²; see "iCAM06 ladder"
    below.
  - *Relative / scene-referred* renderers (Mantiuk08, ACES, Reinhard02, CTRL-KEY) take night brightness from an
    **external anchor**: WHITE_Y, exposure, key. That is by design, not a failure to "know the night". Their D0
    numbers are one member of a family per anchor.
- **ACES is an exposure family.** EV 0 (ACES 1.0 = 100 cd/m², the transform's own scale) crushes the night to
  black; EV +12…+14 gives a dark-but-visible sky. "Sky at black" describes our exposure choice, not ACES.

**P2: silhouettes.** Displayed Weber contrast sky→poplar (physical 0.72):
- pcond 0.56, Reinhard02 0.64, CTRL-KEY 0.72, Mantiuk08 auto 0.79 / anchor 0.71, iCAM06 0.89–0.96;
- ACES 0 at EV 0 and ≤ +8 (black), 0.47 (SDR) / 0.91 (HDR1000) at +12;
- 0 for CTRL-PHOT.
- iCAM06 floors each XYZ channel at 1e-4 cd/m² in its bilateral filter (52 % of S0/S1 pixels), which flattens the
  dark ground in its absolute configs.

**P3, P5: sources, plateaus.** S1 SDR100:

| | pcond | CTRL-KEY | Reinhard02 | Mantiuk08 auto | Mantiuk08 anchor | ACES 2 EV 0 / +12 / +16 | iCAM06 native |
|---|---|---|---|---|---|---|---|
| source/sky contrast | 270 | 2 | 3.2 | 8 | 20 | 584 / 499 / 9 | 3.3 |
| display-white plateaus (n / largest ⌀) | 2 / 0.9′ | 338 / 109′ | 1 / 0.9′ | 88 / 39′ | 28 / 1.3′ | 0 / 104 × 23′ / 89 × 47′ | 467 / 96′ |

- The largest plateau is the lamp ribbon merged into one white line where the curve clips many lamps. That is a
  "giant white" failure of CTRL-KEY, iCAM06, Mantiuk08 auto, and ACES once exposed to show the sky.
- pcond, Reinhard02 and Mantiuk08-anchor keep individual lamps at ~1′.
- ACES keeps lamps small only at EV 0 (where everything else is black) and, on HDR1000, at EV +12 (≤ 2.5′).

**P6: warm lamps.** Saturation kept (u′v′ distance from white, displayed / scene):

| ACES 2 EV 0 / +12 | Reinhard02 | pcond | Mantiuk08 (also `--tone-value max`) | CTRL-KEY, iCAM06 |
|---|---|---|---|---|
| 0.60 / 0.02 (SDR); 1.1 / 0.12 (HDR) | 0.76 | 0.35 | 0.001–0.10 | ≈ 0 (clipped to white) |

- ACES's warm lamps at EV 0 exist only because the lamps are the only thing not crushed. At any EV that shows the
  sky, ACES whitens them too.

**P4: nearby dark object.** S3, HDR-VDP-3 P_det diagnostic.
- EVAL_VIEWER: HDR-VDP's observer including its ocular MTF, viewing the phone. EVAL_OFF: the same with the MTF off.
- Everything that lifts the sky keeps the bar next to the lamp detectable (P ≈ 1): CTRL-KEY, Reinhard02, iCAM06
  at every ladder level, pcond, ACES from EV +12.
- CTRL-PHOT and ACES at EV ≤ +8 make it "invisible" only because the whole sky is at display black (P = 0, bar
  Weber ≈ 0). **That is crushing, not glare.**
- **No donor simulates ocular glare.** In one case the bar's detectability dropped with the observer's optics on:
  Mantiuk08's mapping for BRIGHT500/HDR1000 (sky 0.018 cd/m², lamp at display peak). P_det was 0.43–0.67 with
  HDR-VDP's ocular MTF, and 0.98 without it. The operator produced a displayed luminance ratio at which the
  *observer model's* optics hide the bar. It did not render glare.

**P7: temporal.** 2 s clip:
- **No donor creates flicker or tone pumping:**
  - global mean max step ≤ 0.9 %;
  - empirical tone curve steps ≤ 1 % (pcond: 0.6–1 % at the brightest level);
  - one isolated-flash frame (pcond).
- Mantiuk08's tone curves are smoothed (max step 1.1·10⁻³ log₁₀; 2.6·10⁻² without smoothing).
- CTRL-KEY and Reinhard02 re-normalise every frame, but the scene's key barely changes while walking.
- Source-region energy modulation is 0.1–2.8 %. The per-lamp display-grid breathing (M2.6) is not visible in this
  region-sum measure.

**P8: changing the display.** S1 sky median SDR100 → SDR200 → BRIGHT500 → HDR1000:

| donor | sky median |
|---|---|
| pcond | 0.32 → 0.37 → 0.10 |
| Reinhard02 | scales with peak (30 → 61 → 151) |
| CTRL-KEY | scales with peak |
| Mantiuk08 auto | 12.5 → 19.7 → 13.5 → 14.6, with deeper dark regions on high-range displays |
| Mantiuk08 anchor | 5.0 → 5.8 → 2.5 → 2.5 |
| ACES EV 0 / +12 | black on every target / 0.2 (SDR) → 0.14 (HDR1000) |

- Donors that only encode (Reinhard02, CTRL-KEY) put more light on a brighter display.
- Display-aware ones (Mantiuk08, pcond with its range, ACES) use the range differently.

**Real night photograph (S4) and interior (S5).**
- Physical sky 0.69 cd/m² → ACES EV 0 0.13 (EV +8 already 61), CTRL-PHOT 0.69, pcond 9.4, Mantiuk08 auto 26,
  Reinhard02 31, iCAM06 23–31, CTRL-KEY 45.
- ACES would need an exposure about 8–12 stops lower for S4 than for S1. No single EV serves both scenes.

## D0.1: contract audit and three short re-runs

1. **Mantiuk08: which implementation, and upstream.**
   - It was the pfstools **CLI** `pfstmo_mantiuk08`, release 2.2.0, run with `-s ppd=73` (not LuminanceHDR's
     embedded copy).
   - The CLI's `--display-size` exists, and 30 ppd is its documented default. But the operator **never reads it**:
     `optimize_tonecurve` receives `ds` and does not use it, and the frequency bands are built with
     `conditional_density()`'s default `pix_per_deg = 30`. That holds in 2.2.0 **and in current master**.
   - The D0 phrase "hard-wired" was imprecise; the correct statement is "accepted, printed, unused". Verified
     byte-identical PHONE = DESKTOP in both builds.
   - Master (c860691, 2025-09-20, `donors/mantiuk08/pfstools-master.nix`) reproduces 2.2.0 byte for byte.
   - Its new `--tone-value max` changes what the curve is computed on (max RGB instead of luminance). It is
     **not a luminance anchor**, and on S1 it makes lamps whiter, not warmer.
   - `--fps 0` disables the filter; 24 fps is still unsupported.
   - Details: `input-contracts/mantiuk08.md` §9.
2. **iCAM06: absolute-level ladder** (`input-contracts/icam06.md` §D0.1). S1 × 10⁰…10⁶, absolute input, the
   original sub-functions, with the model output saved before the display stage.
   - The level strongly changes the model's output: the model's sky sits at 1 % of its max at night and 0.0008 %
     at daylight.
   - The rod term lifts dark regions; hue goes pink (night) → blue (mesopic) → warm lamps (day).
   - The native display stage (max-Y normalisation + 1–99 % stretch) keeps the displayed sky at 11–28 cd/m² over
     six decades. **The physical night renders lighter than daylight.**
   - Plateaus stay 31–93′, lamp saturation ≤ 0.07, P_det of the bar = 1 at every level.
3. **ACES 2: exposure family** (`input-contracts/aces2.md` §8), EV 0…18, S0, S1, S3, S4 × SDR100, HDR1000.
   - No exposure gives a dark sky, separate lamps and warm lamps at once.
   - HDR1000 at EV +12 is the closest member: sky 0.14 cd/m², silhouettes 0.91, plateaus ≤ 2.5′, lamp saturation
     0.12.
4. **Controls renamed** CTRL-PHOT / CTRL-KEY; "D1" now only names the next round.

## Parameters without an objective value (explicit axes)

These are anchors that relative or scene-referred renderers need *by design*. They are not defects.

- **Mantiuk08 WHITE_Y.** A night scene has no diffuse white. Two defensible anchors differ by 5.4 decades: display
  peak (used here) vs a white surface lit by the night sky, ~4·10⁻⁴ cd/m². The resulting sky ranges from 5 to
  64 cd/m² (sweep). **WHITE_Y is an appearance-design parameter here, not a physical one.**
- **ACES scene exposure.** ACES defines no real-world cd/m² → ACES mapping. EV 0 = the transform's implied scale.
  Across −4…+20 stops S1 goes from all-black to a clipped day-like image; there is no documented night anchor.
- **pcond display range, target peak, ambient** (Mantiuk08 DIM lifts the sky 12.5 → 16.5 cd/m²).
- **iCAM06 surround γ** (Readme 1.2 vs paper 1.5). `max_L` is not an axis in the absolute configs: the ladder
  shows what the level does.

## Limits and incidents

- **pfstools `pfstmo_mantiuk08`** (2.2.0 and master):
  - viewing geometry is accepted but unused (source-verified);
  - only 25/30/60 fps (25 used for the 24-fps clip, labelled ADAPTED);
  - its temporal filter is a 3rd-order IIR, not the paper's FIR.
- **Disk.** Clips were written only for pcond, the exposure controls, Mantiuk08 auto (SDR100), ACES (EV 0) and
  Reinhard02 (SDR100). The other clips' tone curves exist, and their frames can be regenerated (`D0_WRITE_S2`).
- **iCAM06** was run on stills only.
- **Disk incident.** A 4.7 GB unbounded download filled the disk during the round. Five control frames were
  corrupted and regenerated. Containers were restarted once; all runs were redone from the frozen inputs.
- **P_det** is HDR-VDP-3's detection model applied to emitted light: one observer model, not a human
  measurement. Nothing is ranked by it.

**D0 + D0.1 are frozen.** Implementation/documentation mismatch filed for the upstream backlog (draft, not sent): `docs/upstream/pfstools-mantiuk08-display-size/`. The low-light appearance question continues in `d1/README.md`. Not started: D1 (no custom objective, no Spencer/Temporal Glare, no Blender changes).
Open questions: `docs/research/display-rendering-open-questions.md`. Donor matrix:
`docs/research/display-renderer-matrix.md`.
