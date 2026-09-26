# D1 final acceptance: the frozen A + B + display pipeline on the whole corpus. **ACCEPTED**

Pre-registered in `PREREG.md` (commit `a581d84`, before the run). Code `run.py`; results `acceptance.json`; P-7 from
`d0/metrics.py` (config `d1_pipeline/final`). P-9 sheet: `sheet_final.png` (old frozen vs final; S0, S1, poplar crop,
lamp ribbon, S3 bar, F1). The S4/S5 sheet is Fairchild-derived and not committed (`d0/work/sheets/`).

    nix develop -c d1/a_extract/run_ax.sh; nix develop -c d1/display_r/run_s2_ax.sh
    tracks/temporal-glare-2009/py.sh d1/final/run.py; tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline

| gate | result | values |
|---|---|---|
| P-1 numerics | **PASS** | finite on every still, F1 and all 48 S2 frames |
| P-2a in-gamut B preserved | **PASS** | output = recombination exactly; \|Δu′v′\| ≤ 3.7·10⁻¹⁶ |
| P-2b projected pixels | **PASS** | ΔY/Y ≤ 1.0·10⁻⁷; hue exact where defined; chroma never increases; t maximal |
| P-3 clipping | **PASS** | every channel in [0.1, 100] everywhere (above-peak 0; was S5 4.1 %) |
| P-4 order (v2 + R3) | **PASS** | 0 inversions on 2.1·10⁶–2.0·10⁸ resolvable pairs per image (S2 too); S3_nobar **N/A + R3-flat PASS** |
| P-5 S1 | **PASS** | sky 0.318 cd/m², lamps/sky 315, poplar Weber 0.593, reversals 0, halo 0.91 |
| P-6 S3 | **PASS** | displayed bar Weber 0.753 |
| P-7 S2 | **PASS** | mean max step 0.071 %, sky step 0, isolated flashes 0 |
| P-8 F1 | **PASS** | monotone for all 7 colours; no channel above peak at any level |
| P-9 new artefact classes (visual) | **PASS** | no halo, banding, reversal, fringing, blocking or posterisation. F1 saturated patches desaturate smoothly towards white above their primaries' ceilings |

**Known, documented outcomes (declared in the PREREG as not new artefact classes).**
- **S1 lamp cores whiten.** pcond requests Y ≥ 90 cd/m² there, and SDR100 can only emit white at its peak. Y-priority
  keeps Y, so the core loses its colour. The shoulders keep full colour and Y (`d1/display_r/`).
- **S5 twilight sky stays saturated blue.** This is in-gamut chromaticity of the frozen B. The clipping is gone.

**Prediction check.** All gate values reproduce the pre-registered prediction (DR v2 / P4v2 numbers) exactly.

## What D1 delivers
A **composite** low-light appearance pipeline, not a single physiological model, for rendering a physically calibrated
night scene (absolute cd/m²) on a limited display (SDR100 dark):
- **A, luminance.** Radiance `pcond -s -c`, read before its gamut clip.
  - On our real scenes this is pcond's linear fall-back (Ward 1994 contrast-based exposure) plus the `-c` scotopic
    luminous response.
  - PASS here means "a deterministic luminance donor satisfying D1's necessary conditions on our scenes". It is not a
    claim that it reproduces night brightness appearance exactly.
- **B, chromaticity.**
  - The Filament-derived Cao/Kirk kernel (Purkinje-direction shift), a = 1, κ = 3.
  - The Wanat-derived local chroma collapse, t = L/(L + 0.108) per pixel.
- **Display.** Y-priority minimum-chroma projection into SDR100.
- **Out of scope:**
  - axis C (Kellnhofer 2015 temporal rod noise; optional, with a C0 kill-gate: static end product → KILL);
  - local contrast (Wanat A2, killed);
  - acuity;
  - glare.

**Open residuals, not D1 failures.**
1. **Lamp-core colour at peak.** Any chroma-first alternative needs its own PREREG and must pass F1 monotonicity. The
   plain C-priority variant failed it.
2. **Saturation of the S5 sky**, if judged too strong: a question for axis B, not the display.
3. **The mesopic calibration of B**, currently the CIE envelope only.
