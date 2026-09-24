# Display-renderer matrix (D0)

What each existing display-rendering system *is* and *does* with our frozen, calibrated night scenes.
- Not a ranking.
- Measured behaviour: `d0/README.md` and `d0/results/tables/`.
- Input semantics per donor: `d0/input-contracts/`.

The roles are kept apart:

| role | what it is in D0 |
|---|---|
| physical scene model | the frozen Blender/Cycles scene (absolute cd/m²), plus two calibrated Fairchild photographs |
| eye / reference model | none inside any renderer here. B1 is a separate reference and is not used |
| display renderer | the donors below |
| display model | `d0/display-scenarios.json` + `d0/display_model.py`: one parametric decoder for every donor |
| evaluation metric | `d0/metrics.py`: descriptive only. HDR-VDP P_det is a diagnostic under its own observer model |

| | A pcond (V0) | B Mantiuk08 | C ACES 2 | D1 exposure + clamp | D2 Reinhard02 | E iCAM06 | F BT.2446 | G Tariq 2023 |
|---|---|---|---|---|---|---|---|---|
| **primary purpose** | visibility-matched tone reproduction: human sensitivity, colour loss | minimise visible contrast distortion on a given display | scene-referred → display rendering for cinema/TV mastering | control: literal photometry / naive auto-exposure | control: photographic global curve | image appearance across media and luminance levels | broadcast HDR→SDR conversion | perceptual contrast preservation under display limits (real time) |
| **input semantics** | absolute (Radiance units, 179 lm/W); scene HFOV | log-luminance *differences*: absolute level ignored (models an eye adapted to 1000 cd/m²), except through `--white-y` / an undocumented scene-adapt option | scene-referred relative (ACES2065-1); **absolute level = our exposure choice** (fixed: ACES 1.0 = 100 cd/m²) | absolute cd/m² (d1a); key-normalised (d1b) | relative (key-normalised), with a 1e-5 guard in input units | absolute cd/m² (its own max_L parameter), or scaled per its Readme | **display-referred** HDR (BT.2100 PQ/HLG), *not* scene-referred | — |
| **display awareness** | its own Ldmax + dynamic range (`-u`, `-d`) | full display model: LUT or gamma, peak, black, ambient reflection | target peak + limiting gamut + EOTF (fixed output transforms) | peak/black via exposure and clamp only | none (encoding only) | none (output stretched to the display range) | fixed 1000 → 100 cd/m² | — |
| target peak aware? | yes (`-u`) | yes | yes (100 / 500 / 1000 nits; no 200-nit SDR, no 500-nit SDR) | d1b yes; d1a clamp only | no | no | fixed | (paper: yes) |
| black-level aware? | yes (range) | yes | partly (per target) | clamp only | no | no | — | (paper: yes) |
| ambient aware? | no | **yes** (reflection model) | no (fixed dim-surround constants) | no | no | surround parameter only | no | (paper: ?) |
| viewing geometry aware? | scene HFOV (not the display) | the manual says yes; **pfstools 2.2.0 hard-wires 30 px/deg** (PHONE = DESKTOP, identical output) | no | no | no | no | no | (paper: yes) |
| temporal? | per frame, no smoothing | **yes**: tone-curve smoothing (3rd-order IIR in the code; 24 fps not accepted, 25 used) | per pixel (stateless) | d1b per-frame exposure, no smoothing | no (`--temporal-coherent` off by default) | no | per pixel | yes (paper) |
| colour appearance model? | scotopic colour loss (pcond `-c`) | no (luminance only, colour ratios kept) | **yes**: JMh from a simplified Hellwig 2022 CAM | no | no | **yes** (iCAM06: IPT, local adaptation) | colour correction (Method A, Table 3) | no |
| open source? | yes (Radiance) | yes (pfstools, LGPL / GPL-2+ headers) | yes (ACES Apache-2.0; OCIO BSD-3) | ours (trivial) | yes (pfstools) | authors' MATLAB, **no licence stated** (not redistributed) | libplacebo `bt2446a` (curve only, GPU); AviSynth HDRTools (A, C) | **no code found** |
| native implementation run? | yes, unchanged (frozen stack) | yes; native example reproduced (Debevec memorial) | yes, OCIO 2.5.2 built-in config; **matches CTL reference within one 10-bit code** | — | yes | yes; native PeckLake example reproduced | **no** (STANDARD_REFERENCE_ONLY) | **no** (REFERENCE_ONLY) |
| parameter uncertainty (explicit axes) | Ldmax / range per scenario | **WHITE_Y** (no diffuse white at night: an appearance-design parameter), display LUT, ambient | **scene exposure** (swept −4…+20 stops) | exposure rule | key a | max_L / absolute scaling, surround γ (Readme 1.2 vs paper 1.5) | — | — |
| observed failure modes on our night scenes | see `d0/README.md` | see `d0/README.md` | see `d0/README.md` | see `d0/README.md` | see `d0/README.md` | see `d0/README.md` | — | — |

**Sources:**
- Mantiuk, Daly & Kerofsky 2008 (ACM TOG 27(3)); pfstools 2.2.0.
- ACES 2 (aces-aswf/aces-core @069b0bc, aces-output @6d8f907; CTL @e280b6c); OpenColorIO 2.5.2 built-in
  `studio-config-v4.0.0_aces-v2.0_ocio-v2.5`.
- Reinhard et al. 2002.
- Kuang, Johnson & Fairchild 2007 (iCAM06 V1.3, RIT MCSL).
- ITU-R Report BT.2446-1 (2021).
- Tariq et al., SIGGRAPH Asia 2023.
- Ward Larson, Rushmeier & Piatko 1997 (pcond).
