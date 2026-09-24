# D0 controls: input contracts

## D2 reinhard02

**Operator.** Reinhard, Stark, Shirley, Ferwerda 2002, "Photographic Tone Reproduction for Digital Images" (ACM TOG 21(3), SIGGRAPH 2002). We use its pfstools implementation `pfstmo_reinhard02` from **pfstools 2.2.0**, the same build and tarball as donor B (sha256 `9bf6844985663226c21998eeb43c261acb8e4b3891b9a91b729554406289d7ca`; `src/tmo/reinhard02/`, GPL-2.0-or-later; see `d0/input-contracts/mantiuk08.md` §1). It runs with **defaults only** and no artistic tuning. Command: `pfsinpfm x.pfm | pfstmo_reinhard02 -v`. It is a control, not a donor under study.

**Defaults (from source).** The tool runs the global operator (`--scales` off, so no dodging-and-burning). Key a = 0.18 and φ = 1. It computes L = a·Y / L̄w, where L̄w = exp(mean log(1e-5 + Y)) over the frame. Then Ld = L·(1 + L/Lwhite²)/(1 + L), with Lwhite = the frame's maximum scaled L (Eq. 4 with Lwhite = max). RGB is scaled by Ld/Y. `--temporal-coherent` is off, so every S2 frame is processed independently.

**What it expects.** It expects linear scene-referred luminance in **any** unit. The key normalisation divides out the absolute scale, so the absolute cd/m² of our inputs is removed. Night-specific exception: the `1e-5` guard inside the log-average is in *input units*. For our S0/S1/S2 (geometric mean about 1.0e-4 cd/m²), that guard raises L̄w by **15 %**, which lowers the scaled luminance L by about 13 % compared with a scale-free key normalisation. The effect is 2 % for S3 and none for S4/S5. It is a property of the native code on absolute night input, and we do not correct it. Our input goes in unscaled (`oiiotool EXR → PFM → pfsinpfm`, format conversion only). The pfs Y matrix matches our Rec.709 Y.

**Display-unaware.** The output (`LUMINANCE=RELATIVE`) is display-relative linear RGB, nominally in [0, 1) with 1 = display white. Channels of saturated colours can exceed 1. The operator has no notion of peak luminance, black level, ambient light or viewing geometry. **The only thing that differs between luminance scenarios is the encoding**, which we apply after the tool: the value is clamped to [0, 1], then the sRGB OETF is applied for SDR100, or ^(1/2.2) for SDR200 and BRIGHT500. Code 0 = display black and 1 = peak. So the *same* relative image is shown at 100, 200 or 500 cd/m² peak, over that display's black. HDR1000 is not produced for this control, since it has no defined HDR mapping. PHONE geometry and DARK ambient are nominal labels only.

**Edge case.** In S3_bar the bar pixels have Y = 0 exactly, so the tool's Ld/Y rescale gives 0/0 there: 2398 non-finite pixels. We write them as 0 (black), which is what they are. The count is logged in `runs.json`.

**Outputs.** `d0/work/out/reinhard02/defaults/<scene>__PHONE_{SDR100,SDR200,BRIGHT500}_DARK.png` for S0, S1, S3_bar, S3_nobar, S4 and S5. S2 is always tone-mapped (48 frames, one stream). Its frames are written to `…/S2__PHONE_<LUM>_DARK/frame_####.png` only when `D0_WRITE_S2` allows it: in the D0 round they were **not kept**, to stay inside the disk budget (about 7 MB per 16-bit frame). Regenerate them with `D0_WRITE_S2=all d0/donors/mantiuk08/run.sh`, or with the `reinhard02` step alone. Command lines and parameters are in `d0/work/out/reinhard02/runs.json`.

## D1 exposure + clamp (`d0/donors/controls_d1.py`)

No curve, no adaptation, no tuning. Two fixed variants, labelled DOCUMENTED_TARGET_CONFIG.

- **Input.** `d0/work/inputs`, linear Rec.709/D65 RGB, Y in absolute cd/m². Used as is.
- **d1a_photometric.** Exposure 1: the display is asked to emit the scene's own luminance.
  - Each channel is clamped to [black, peak] of the scenario.
  - This is the literal "show the physical scene" control.
  - For the night scenes nearly everything lands on the display's black.
- **d1b_key018.** Exposure k = 0.18 · peak / L̄, then the same clamp.
  - L̄ = exp(mean ln(Y + 1e-9)) of the frame. That is Reinhard et al. 2002 eq. 1–2 *without* their curve.
  - The guard (1e-9 cd/m²) is far below every scene's level.
  - For the clip it is computed per frame with no temporal smoothing: a naive auto-exposure.
- **Encoding** (`d0/display-scenarios.json`):
  - SDR: code = OETF((L − black)/(peak − black)), sRGB for SDR100 and ^(1/2.2) for SDR200/BRIGHT500.
  - HDR1000: code = PQ(L) after Rec.709 → Rec.2020 primaries (absolute).
  - 16-bit PNG. Per-channel clamping shifts the hue of clipped warm sources towards the display's primaries/white.
- **Display awareness.** Peak and black enter only through the exposure (d1b) and the clamp. No ambient, no
  geometry.
- **Exposures used** (S1): d1b k = 1.7·10⁵ (SDR100) … 1.7·10⁶ (HDR1000). Every value is in
  `d0/work/out/controls/runs.json`.
