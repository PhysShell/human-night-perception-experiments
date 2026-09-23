# Track: hdrvdp3 (HDR-VDP 3.0.7, Mantiuk et al.)

> Written by the coordinator from the worker's scripts and result files (the worker was stopped
> before writing this README). All numbers are from `results/native/hdrvdp3/*.json` and
> `results/common/hdrvdp3/*/run.json`.

## IDENTITY
HDR-VDP 3.0.7 (`hdrvdp_version.m`: 3.07) from https://sourceforge.net/projects/hdrvdp/files/hdrvdp/
(fetched by `fetch_donor.sh`, checksummed in `research-cache/hdrvdp3/donor_manifest.sha256`).
Unmodified source in `research-cache/hdrvdp3/src/hdrvdp-3.0.7`. Licence: see the donor's
licence file (not re-checked by the coordinator).

## PURPOSE
A calibrated visible-difference and quality metric for HDR images. **A metric, not a renderer.**

## HVS COMPONENTS
Optical MTF (`'hdrvdp'` or `'cie'` glare option), age parameter, local adaptation, contrast
sensitivity, side-by-side and flicker tasks, explicit display geometry and photometry.

## NATIVE ENVIRONMENT
GNU Octave 11.3.0 (nix). MEX parts built by `build_mex.sh`. Graphics are unavailable (headless),
so example scripts stop at their plotting step ("no graphics toolkits are available!") after
computing the metric.

## NATIVE REPRODUCTION (PASS)
| example (unmodified) | result |
|---|---|
| `hdrvdp3.m` header example (luminance ramp 0.1–1000 cd/m² + 5 % noise) | claim "noise more visible in the brighter part" reproduced: P 0.04 in 0.1–1 cd/m², 0.97 in 100–1000 cd/m² |
| `examples/example_octave.m` | side-by-side Q_JOD 8.83 (8-bit read) / 8.25 (16-bit); flicker 7.65 / 7.19 |
| `examples/display_quality.m` | Q_JOD 7.23; Q vs ppd 120→7.5: 9.53, 9.13, 8.35, 7.76, 6.31 |
| `examples/impairment_detection_{hdr,sdr}.m`, `compare_hdr_vs_tonemapped.m` | run; values in the JSON files |

No published reference numbers were compared (the examples print values; "reproduce" = the
shipped examples run and the documented qualitative claim holds).

## COMMON (metric plumbing, `run_hdrvdp.sh`: explicit PHONE/DESKTOP from stimuli/display_targets.json)
| comparison | target | display | result |
|---|---|---|---|
| S1 (warm point) vs S0 (white point), equal luminance | PHONE, DESKTOP | clip / none | Q_JOD 10.0, P_det ≤ 0.02 |
| S7v frame 2 vs S7 (2nd frame of the walk) | PHONE, DESKTOP; also `mtf cie`, age 24 | clip / none | Q_JOD 10.0, P_det ~0 |

**Reading:**
- The S0/S1 pair differs only in chromaticity at equal luminance. HDR-VDP-3's detection is
  luminance-based, so it reports no difference **by construction**; it is not evidence that
  the colour difference is invisible. Use ColorVideoVDP for colour.
- One frame of the walk is below threshold, as expected.

## BRIGHT POINT SOURCE
1. Optical MTF/glare inside the metric, on the displayed luminance.
2. Before its adaptation stage.
3. It does not tone map.
4. MTF energy-preserving.
5. Absolute cd/m² through the display model.
6. `'cie'` glare option with age.
7. Our wrapper: physical clip at peak + black level (not a tone mapper).
8. Not modelled.
9. Flicker task only (temporal difference between two images).
10. The wrapper clips to the display, then the metric applies its optics.

## VERDICT
**SCIENTIFIC ORACLE** (visibility of differences on a declared display), runnable under Octave.
