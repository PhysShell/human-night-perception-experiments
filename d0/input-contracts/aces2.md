# Input contract: ACES 2.0 Output Transforms (donor `aces2`)

Script: `d0/donors/aces2/run.py`. Outputs: `d0/work/out/aces2/`, with every run listed in `runs.json`.
Native-repro evidence: `d0/results/tables/aces2_native_repro.json` and `d0/results/stills/aces2/native_*.png`.
Neutral response table: `d0/results/tables/aces2_neutral_curve.json`.

## 1. Donor as run

| item | value |
|---|---|
| implementation | OpenColorIO **2.5.2** (PyPI wheel `opencolorio==2.5.2`, BSD-3-Clause), built-in ACES 2.0 fixed-function ops |
| config | built-in `ocio://studio-config-v4.0.0_aces-v2.0_ocio-v2.5`: "Academy Color Encoding System - Studio Config [COLORSPACES v4.0.0] [ACES v2.0] [OCIO v2.5]". It ships inside the OCIO library, so there is nothing else to fetch. |
| how to fetch | `python3 d0/donors/aces2/run.py setup` creates `d0/work/aces2_tmp/venv` (`pip install opencolorio==2.5.2 OpenEXR numpy`, about 150 MB) |
| reference | official ACES 2.0 CTL: `aces-aswf/aces-core` @069b0bc (lib), `aces-aswf/aces-output` @6d8f907 (transforms), both Apache-2.0, run by `ctlrender` built from `ampas/CTL` @e280b6c (`run.py build_ctl`, transient) |
| docs | https://docs.acescentral.com/system-components/output-transforms/ |

The ACES 2.0 Output Transform is a Rendering Transform in JMh, based on a simplified Hellwig 2022 CAM. It applies a tonescale, chroma compression and gamut compression, and it is parameterised by the target peak luminance and the limiting gamut. It works on each pixel on its own, with no spatial processing. It knows nothing about temporal state, viewing geometry or ambient light. Its CAM viewing conditions are fixed constants in the CTL (`Lib.Academy.OutputTransform.ctl`): `ref_luminance = 100`, `L_A = 100 cd/m^2`, `Y_b = 20`, and a *dim* surround. **ACES has no notion of a viewer adapted to a 4e-4 cd/m^2 night sky.** No parameter adapts the rendering to scotopic or mesopic viewing, or to the absolute scene level.

## 2. Colour conversion (fixed, OCIO's own)

The input is linear Rec.709/D65 RGB in absolute cd/m^2, with Y = 0.2126 R + 0.7152 G + 0.0722 B. It is converted by the config's own colourspace transform, `Linear Rec.709 (sRGB)` -> `ACES2065-1`. This is a single 3x3 matrix that includes the D65 -> ACES-white (~D60) chromatic adaptation used by the config:

```
AP0 = [[0.43963, 0.38299, 0.17738],
       [0.08978, 0.81344, 0.09678],
       [0.01754, 0.11155, 0.87091]] . RGB709
```

A neutral Rec.709 input (1,1,1) becomes AP0 (1,1,1). ACES Y is therefore Y709 × the scale below. The whole chain is one OCIO processor: `config.getProcessor("Linear Rec.709 (sRGB)", display, view)`.

## 3. Scene normalization (a separate degree of freedom)

ACES2065-1 is **scene-referred relative exposure**, not absolute photometry. In the ACES convention a correctly exposed 18 % grey card has the value 0.18. The system does not define which absolute luminance that corresponds to, because the "correct exposure" belongs to the camera or the colourist. Exposure is therefore an explicit experimental axis. It is applied as a scalar multiply before OCIO, which commutes with the 3x3 matrix, and it is kept apart from the output transform.

**Fixed documented mapping (DOCUMENTED_TARGET_CONFIG): ACES value 1.0 = 100 cd/m^2, that is `ACES = Y_abs / 100 cd/m^2` (EV 0).**

The justification comes only from the ACES 2.0 reference implementation, not from how the night looks. The ACES 2.0 output transform converts ACES RGB to JMh with the CAM reference white fixed at `ref_luminance = 100` (`cam_nl_Y_reference = 100`, `XYZ_w = ref_luminance · RGB_TO_XYZ(1,1,1)`, `L_A = 100 cd/m^2`). The tonescale also normalises "1.0" to `n_r = 100` nits (`Lib.Academy.Tonescale.ctl`: "normalized white in nits (what 1.0 should be)"). ACES 1.0 therefore enters the model as a 100 cd/m^2 stimulus, and this mapping keeps the transform's own implied photometric scale. As a consequence, 18 cd/m^2 maps to ACES 0.18, the tonescale's grey anchor. That grey is shown at about 10 cd/m^2 on SDR100, 14.5 on HDR1000 and 13.2 on the 500-nit output. The same mapping is used for every scene and target. It is not tuned by eye.

**Controlled exposure sweep (SENSITIVITY_RUN):** S1, SDR100 only, EV = −4, −2, 0, … , +20 (2-stop steps), so `ACES = Y_abs · 2^EV / 100`. The range goes past the suggested +8 because S1 is still visually unchanged at +8: 52 % of pixels are exactly code 0, and the median displayed luminance is 0. At about +18 EV the scene median (7e-5 cd/m^2) reaches roughly ACES 0.18. At EV 0 and above, the lamp cores saturate towards the 100-nit peak. The sweep isolates exposure, while the output transform (100-nit Rec.709) stays fixed.

## 4. Targets (display scenarios -> ACES 2.0 outputs)

| scenario (`d0/display-scenarios.json`) | ACES 2.0 output (OCIO display / view) | peak | limiting gamut | encoding |
|---|---|---|---|---|
| SDR100 | `sRGB - Display` / `ACES 2.0 - SDR 100 nits (Rec.709)` (CTL `Output.Academy.Rec709-D65_100nit_in_Rec709-D65_sRGB-Piecewise`) | 100 | Rec.709 D65 | sRGB piecewise, Rec.709 primaries |
| HDR1000 | `Rec.2100-PQ - Display` / `ACES 2.0 - HDR 1000 nits (P3 D65)` (CTL `Output.Academy.P3-D65_1000nit_in_Rec2100-D65_ST2084`) | 1000 | P3 D65 | ST 2084 PQ, Rec.2020 primaries |
| **BRIGHT500_PQ** (not the SDR BRIGHT500 scenario) | `Rec.2100-PQ - Display` / `ACES 2.0 - HDR 500 nits (P3 D65)` (CTL `Output.Academy.P3-D65_500nit_in_Rec2100-D65_ST2084`) | 500 | P3 D65 | ST 2084 PQ, Rec.2020 primaries |
| SDR200 | **none**: ACES 2.0 has no 200-nit SDR output transform | – | – | – |
| BRIGHT500 (SDR, gamma 2.2) | **none**: ACES 2.0 has no 500-nit SDR output. We did not build one. The PQ 500-nit output above is labelled separately. | – | – | – |

The config also offers `Gamma 2.2 Rec.709` and `Rec.1886 Rec.709` displays for the 100-nit SDR view. We use the sRGB-piecewise display because the SDR100 scenario specifies sRGB encoding. Every SDR output is rendered for 100 nits: the rendering targets 100 cd/m^2 whatever the encoding.

## 5. Output contract

Outputs are 16-bit RGB PNG code values, `round(clip(v, 0, 1) · 65535)`. SDR100 uses the sRGB piecewise curve with Rec.709 primaries. HDR outputs use absolute PQ (code 1.0 = 10000 cd/m^2) with Rec.2020 primaries. Code 0 is display black: ACES 2.0 maps scene 0 to display 0. Paths are `d0/work/out/aces2/<config>/<scene>__PHONE_<LUM>_DARK.png`, and S2 goes to `.../S2__PHONE_<LUM>_DARK/frame_####.png`. OCIO applies no black-level or ambient model. The common display model (`d0/display_model.py`) supplies both.

Geometry and ambient are labels only. The transform is per-pixel and does not depend on geometry or ambient, so the PHONE/DARK outputs are identical for DESKTOP or DIM.

## 6. What happens to the night scene at the documented mapping

These are neutral values from `aces2_neutral_curve.json`, given as unquantised display luminance in cd/m^2:

| scene Y (cd/m^2) | ACES | SDR100 | HDR1000 | 500 PQ |
|---|---|---|---|---|
| 7e-5 (median) | 7e-7 | 2e-11 | ~0 | ~0 |
| 4e-4 (sky) | 4e-6 | 1.3e-9 | ~0 | ~0 |
| 0.1 | 1e-3 | 4e-4 | 5e-4 | 5e-4 |
| 1 | 0.01 | 0.07 | 0.09 | 0.08 |
| 18 | 0.18 | 10 | 14.5 | 13.2 |
| 300 (lamp cores) | 3 | 73 | 288 | 210 |

The ACES tonescale toe (a Michaelis-Menten / Daniele curve with flare `t_1`) sends everything below about 0.03 cd/m^2 of scene luminance to less than 1 16-bit code. The sky and the whole landscape become display black (16-bit code 0) on all three targets, and only the lamps and their glare remain. This is the transform working as designed for a scene-referred exposure that the scene's absolute level does not normalise. The exposure sweep documents how the result depends on that separate choice.

## 7. Native reproduction (D0-C1)

OCIO 2.5.2 was compared with the official CTL (ctlrender) on the same ACES2065-1 chart: a neutral ramp from 2^-26 to 2^10, 35 upstream test patches (SMPTE ST 2065-1 ColorChecker, ACEScg primaries ×4, 18 % grey, perfect diffuser), and 8192 random AP0 colours. The largest difference is 4.5e-4 in code value (at most about 29 16-bit codes, on saturated random colours). The ramp and patches differ by 0.4 16-bit codes in SDR and 4.4 in PQ. **Every sample agrees within 1 10-bit code.** OCIO's fixed-function ACES 2.0 op also reproduces its upstream unit-test vectors to within 1e-6.

The upstream "golden" reference images are distributed only as a 7 GB Dropbox archive, which is over the download limit, so they were not used. See `aces2_native_repro.json`.

## 8. D0.1: ACES's result is an exposure family, not one image

The ACES Output Transform maps **scene-referred ACES values** to a display rendering. The ACES documentation places
the target peak and gamut in the output transform, and the scene exposure *before* it. The tonescale anchors are
ACES 0.18 → 10 cd/m² and ACES 1.0 → ~45.8 cd/m² on the 100-nit output.

ACES defines no unique mapping from real-world cd/m² to ACES values. The mapping "ACES 1.0 = 100 cd/m²" used above
(§3) is the transform's own implied photometric scale, and it is still *our* exposure choice. The D0 statement
"ACES puts the night sky at display black" is therefore a statement about that choice, **not a property of the
algorithm**.

The honest D0 result for ACES is the family below:
- `python3 d0/donors/aces2/run.py family` (with the venv from `run.py`), runs `EXPOSURE_FAMILY_EV..`, label SENSITIVITY_RUN;
- EV 0/8/12/14/16/18, scenes S0, S1, S3 pair and S4, on SDR100 and HDR1000.

| EV | ACES per cd/m² | display | S1 sky, cd/m² | S1 % at black | S1 silhouette Weber | S1 white plateaus (n / largest) | S1 lamp saturation kept | S3 P_det viewer / off | S4 sky, cd/m² |
|---|---|---|---|---|---|---|---|---|---|
| +0 | 2^0/100 | SDR100 | 0.1 | 99.7 | 0.00 | 0 | 0.6 | 0.00 / 0.00 | 0.133 |
| +0 | 2^0/100 | HDR1000 | 0.005 | 99.6 | 0.00 | 0 | 1.1 | 0.00 / 0.00 | 0.0484 |
| +8 | 2^8/100 | SDR100 | 0.1 | 98.9 | 0.00 | 60 / 1.9′ | 0.37 | 0.00 / 0.00 | 61.3 |
| +8 | 2^8/100 | HDR1000 | 0.00527 | 71.6 | 0.05 | 13 / 1.3′ | 0.6 | 0.00 / 0.02 | 189 |
| +12 | 2^12/100 | SDR100 | 0.2 | 50.3 | 0.47 | 104 / 22.7′ | 0.022 | 1.00 / 1.00 | 97.2 |
| +12 | 2^12/100 | HDR1000 | 0.137 | 0 | 0.91 | 80 / 2.5′ | 0.12 | 0.99 / 1.00 | 821 |
| +14 | 2^14/100 | SDR100 | 1.55 | 0 | 0.86 | 83 / 44.0′ | 0.0022 | 1.00 / 1.00 | 99.9 |
| +14 | 2^14/100 | HDR1000 | 1.93 | 0 | 0.91 | 132 / 9.6′ | 0.025 | 1.00 / 1.00 | 958 |
| +16 | 2^16/100 | SDR100 | 10.7 | 0 | 0.83 | 89 / 47.2′ | 0.00066 | 1.00 / 1.00 | 100 |
| +16 | 2^16/100 | HDR1000 | 15.4 | 0 | 0.85 | 86 / 42.7′ | 0.0022 | 1.00 / 1.00 | 999 |
| +18 | 2^18/100 | SDR100 | 38.2 | 0 | 0.68 | 337 / 60.6′ | 0.00066 | 1.00 / 1.00 | 100 |
| +18 | 2^18/100 | HDR1000 | 79.3 | 0 | 0.78 | 87 / 46.7′ | 0.00044 | 1.00 / 1.00 | 1e+03 |

**Reading the family.**
- Every exposure at which the night is not crushed to black (EV ≥ +12) also turns the lamps white. Lamp
  saturation kept is ≤ 0.12, and on SDR it is ≤ 0.02.
- On SDR100 no exposure keeps the sky dark (≤ 0.2 cd/m²) *and* the ribbon as separate lamps. At EV +12 half the
  image is at black and the largest plateau is 23′.
- HDR1000 at EV +12 comes closest: sky 0.14 cd/m², silhouette Weber 0.91, plateaus ≤ 2.5′, lamp saturation 0.12.
- The real night photograph S4 (sky 0.69 cd/m²) needs about 8–12 stops *less* than S1 for a comparable result. So
  a single fixed EV cannot serve both scenes, and a per-scene exposure is exactly the external anchor ACES leaves
  to its user.
