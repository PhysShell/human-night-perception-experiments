# D1-B4.1: local vs global vs adaptation-field luminance for the Wanat-derived chroma law

Pre-registered in `PREREG.md` (commit `4ee5bfa`, before running). No parameter is fitted. The B4 stage functions
are imported unchanged.

    tracks/temporal-glare-2009/py.sh d1/chroma_b4_1/run.py   # -> results.json

| S1 (mean L = 0.011 cd/m²) | local (B4) | global (scene mean, Wanat's variable) | field (1° Gaussian) |
|---|---|---|---|
| lamp chroma kept (≥ 0.9) | **0.93** | 0.095 | 0.50 |
| sky chroma (≤ 0.01) | **0.0004** | 0.013 | 0.0004 |
| poplar chroma | 0.0001 | 0.013 | **0.056** |
| B4-G8 thresholds | **PASS** | FAIL | FAIL |

- **S0** (mean 2.2·10⁻⁴): every variant collapses all regions (≤ 0.0007).
- **S4** (real photo, mean 0.39): lamps keep 0.99 / 0.78 / 0.85 of their chroma (local / global / field). Sky
  chroma is 0.061 / 0.056 / 0.061. The sky is already blue in the input (hue −110°), so no Purkinje reading is
  possible there.
- Uniform patches are identical across variants by construction, so B4's patch results (mesopic tint, G1–G7) carry
  over.

**Reading.**
- **global** fails exactly as predicted. One value per image (t = 0.095 at S1's mean) cannot both collapse a
  2.9·10⁻⁴ cd/m² sky and keep 300 cd/m² lamps. The literal transfer of Wanat's independent variable (mean image
  luminance, measured on displayed images of moderate dynamic range) to a scene-referred HDR night scene is
  unsuitable. This is a useful negative result.
- **field** fails on the lamps: sub-degree sources inside a dark 1° field get t ≈ 0.5. It also shows an effect not
  predicted in the pre-registration: dark poplars next to the lamp ribbon pick up a blue tint (chroma 0.056),
  because lamp light enters their adaptation field.
- **local** is the only variant that keeps the architecture's behaviour, with the chroma law following the
  pixel's own luminance. B4 therefore keeps the local form.
- It is recorded as a derived hypothesis, not as Wanat's measured variable.
