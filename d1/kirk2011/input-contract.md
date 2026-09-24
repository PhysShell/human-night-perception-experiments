# Input contract: Kirk & O'Brien 2011 via Y. J. Lee's GIMP plug-in

## What the donor's input numbers mean

- **Paper.** The input is "normalised" LMSR receptor responses q. For spectral data these come from Eq. 8; for
  RGB they come from q = H·RGB. The paper leaves the absolute scale to a free **exposure** knob:
  - "uniform scaling of scene luminance", §3;
  - "the range of intensities in an image can be scaled however one desires", §5.
  - No cd/m² or troland calibration is stated.
- **Plug-in.** The input is the **8-bit GIMP image**: sRGB-encoded codes 0–255, used as if they were linear.
  They are multiplied by `exposure` (default 64, UI range 0–192) and then by the H matrix in `hdrToLMSR.cc`.
- **Physical meaning.** The gain constant 0.33 (Eq. 10) comes from Cao et al. 2008 / Miyahara et al. 1993. There,
  q is in **cone trolands**, "k1 is about 0.33 Td" (Cao 2008, PMC2630540, Eqs. 4–6). That is the only physical
  unit the model's nonlinearity carries.

## How our inputs are converted

Our inputs are `d0/work/inputs/*.exr`: linear Rec.709/D65, Y in absolute cd/m².

| config | conversion | label |
|---|---|---|
| **NATIVE_DEFAULT** | The plug-in only accepts 8-bit images, so the scene is first encoded with the fixed viewing aid: k = 0.18 / exp(mean ln(Y + 1e-9)) of the input, clip to [0, 1], sRGB OETF, round to 8 bit. The codes go in as GIMP would pass them, with exposure 64 and all defaults. It runs the full pipeline: core → Durand/Paris 50.0 → reduceRange + blend with the same 8-bit image | ADAPTED (the 8-bit encoding is ours; the absolute level is discarded by the key) |
| **DOCUMENTED_TARGET_CONFIG** | Float linear RGB × s, with s = A_pupil / (q_L + q_M of a D65 white per unit RGB) = 38.485 / 0.037711 = **1020.5**. So the plug-in's L + M response equals photopic retinal illuminance in Td through a fixed **7 mm** pupil (Y cd/m² × 38.5 mm²). This follows the units of Cao 2008. Same `convertTo(…, scale)` call as the plug-in. It runs the **core only** (HDRToLMSR → purkinje → lms2display), because Durand/reduceRange need the plug-in's 8-bit source image | ADAPTED (the troland units and the 7 mm pupil are ours. A lit interior like S5 would have a smaller pupil, so its Td is overstated by up to ~×3) |
| **SENSITIVITY_RUN** | S1 as DOCUMENTED_TARGET_CONFIG × 10^k, k = 0, 2, 4, 6 | — |

## What the output is

- **Core** (`lms2display` output). Linear RGB of the plug-in's monitor ("Adam's monitor", i.e. the paper's Apple
  Cinema HD), with negatives clamped. The plug-in sends it to the screen as RGB, so we write it as Rec.709
  **without** conversion.
  - The units are arbitrary: input × s → H → M⁻¹, about 0.002–0.009 per unit input, before the rod term.
  - It is **not** in cd/m². Only colour, region-to-region ratios and ratios across levels can be read.
- **Final** (NATIVE_DEFAULT). A display-referred 8-bit sRGB image, after:
  - Durand tone mapping (γ 2.2, max → 1);
  - range reduction;
  - the blend with the source image.

  We decode it to linear for the measurements.
- **Blend map** (`*_blend.exr`). This is max(0, 1 − 1.2 w), the plug-in's mesopic factor: 0 means scotopic, 1
  photopic.

## What is not done

- **Dynamic-range control.** The core keeps the input's range linearly at low levels. Only the display stages
  reduce range: Durand's contrast 50 with γ 2.2, then the range-reduction factor 0.1 + 0.9 × blend on 8 bit.
- **Absolute darkening.** The core output is linear in input level below ~1 Td. There is no "it is dark"
  rendering in the scene domain.
- **Acuity or noise loss.** The paper states this is not modelled (§5).
- **Mesopic adaptation of κ.** The paper and the code fix κ at full scotopic adaptation. The absolute level acts
  only through the gain g and the rod term.
- **Temporal adaptation, glare, colour constancy.** None of these is modelled.
