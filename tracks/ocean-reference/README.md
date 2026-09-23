# Track ocean-reference: Ocean™ (Eclat Digital), Human Vision filters

## IDENTITY

- Ocean™ Light Simulator is a commercial spectral renderer by Eclat Digital. The current documentation
  is "Ocean™ Light Simulator 2025 reference — Ocean 13.2.6 documentation" at
  https://docs.eclat-digital.com/ocean2025-docs/ [O1].
- The documentation server also exposes versions 2013–2024 and a 194 MB tarball `ocean_doc_13.2.5.tar.gz`.
  The Human Vision node pages exist only in the 2025 tree; the same path returns 500 in 2021–2024.
- The "Human Vision module" is a set of **post-processing filter nodes** in the output chain:
  - `glare` ("Human Vision - Glare filter") [O2];
  - `drago` ("Human Vision - Drago filter") [O3];
  - `spectraltohv` ("Spectral to Human Vision filter") [O4];
  - an API-only `purkinje` node with one float parameter `visionmode`, which has no prose page [O5].
  - Discomfort-glare **metrics** (UGR, DGP, GR) are a separate Glare Map / Glare report output
    [O6, O9].
- Secondary sources are two Eclat blog articles by L. Raimbault, 2023-06-21 [O7] and 2023-11-10 [O8].
  They are marketing and tutorial pages, not validation.

## PURPOSE

To show a rendered scene "depending on the visual abilities of the observers" on a limited display.
The listed uses are automotive ageing studies of screens, dashboard lights and streetlights [O7].

## HVS COMPONENTS (J2: feature / parameter matrix, verbatim from documentation)

| Feature | Node / parameter | Documented values | Source |
|---|---|---|---|
| Glare PSF | `glare`: `luminance` | photopic / mesopic / scotopic, three PSFs "dedicated to three different lighting conditions": photopic 10 to 10⁸ cd/m², mesopic 0.01 to 3.0, scotopic 10⁻⁶ to 10⁻³ | O2 |
| Glare age | `glare`: `age` | "real, age of the viewer"; the API getter returns int32; the XML example uses 20 | O2, O5 |
| Glare dispersion | `glare`: `dispersion` | boolean, "Activate 'rainbow' effect in the lenticular halo" | O2 |
| Light-source thresholding | `glare`: `threshold` | PSF applied to pixel I(X,Y,Z) only if I(X,Y,Z) > mean(I(Y)) · threshold, **default 10** | O2 |
| Glare input | — | "Input channels must contain either X,Y,Z channels"; "Denoising filters must be applied BEFORE this filter" | O2 |
| Spectral → vision | `spectraltohv`: `luminance` | Photopic / Mesopic / Scotopic | O4 |
| Mesopic stimulus level | `spectraltohv`: `illuminance` | "from 0.01 to 1000, 10 factor multiplicator" | O4 |
| Time adaptation | `spectraltohv`: `time_adaptation`, `time` | No time adaptation / Light adaptation / Dark adaptation; `time` = "Time (in seconds) after which the simulated scene is captured" | O4 |
| Age (sensitivity) | `spectraltohv`: `age` | integer 0–120 | O4 |
| Tone mapping | `drago`: `b`, `ld` | b in 0..1, "best value of 0.85"; ld = display scale factor, "ld = 100 cd/m2 is a common reference value for CRT displays" | O3 |
| Purkinje | `purkinje`: `visionmode` | float; no prose documentation | O5 |
| Other tone maps | `reinhardglobal`, `reinhardlocal` | exist as generic filters | O1 filter list |

What the secondary article [O8] adds about the models:

- Photopic: CIE 1931 XYZ with gain 683 lm/W. Scotopic: a "black and white" image from the scotopic
  luminosity function, gain 1700 lm/W.
- Mesopic: "a method based on ... Color Appearance Model Applicable in Mesopic Vision – Satoshi
  Shioiri" (Shin et al. 2004, Optical Review).
- Age: gain factors adjusted from Jackson & Owsley 2000 and Jackson, Owsley & McGwin 1999.
- Time adaptation: "simulated by modifying the gain factors in the luminosity functions (Photopic
  luminosity function for light adaptation, Scotopic luminosity function for dark adaptation)". The
  article shows 1 s / 1 min / 20 min examples. Its dark-adaptation curve figure is from Pirenne 1962.
- Rods, cones and mesopic are handled only as the three luminosity regimes plus Shioiri blending.
- Acuity: not documented.
- Depth of field: mentioned as a principle in [O8], but no node is documented.
- Gaze: none.
- Display model: Drago `ld` only.

## J3: glare implementation, as documented (no inference beyond the text)

- "The generation of the PSF that mimic the human eye response is fully based on this paper:
  Physically-Based Glare Effects for Digital Images - Greg Spencer and al." [O2]
- The PSF "is calculated in the section 3 of the paper ... which is based on J.Vos PSF definition
  that has attempted to unify the large number of PSF models for the eye" [O7]. [O7] reproduces
  Spencer's photopic and scotopic PSF figure.
- Adaptation dependence: "As the eye adapt to the luminosity (e.g: pupil radius decreases with
  luminosity, cone cells are active only under well-lit conditions, …), the PSF might vary. This node
  defines three kinds of PSF" [O2]. The regime is a **user-chosen enum**. The documentation does not
  say it is derived from the image.
- Age: "the ratio of scattered light on unscattered light increase with age which leads to more
  glare" [O2]. No formula or age function is given.
- Appearance: "For photopic conditions, glare is visible as a halo around light source ... For
  scotopic and mesopic conditions, in addition to the halo around light source, a lenticular colored
  halo (due to dispersion) and random straight lines are also visible" [O7].
- Thresholding: I(X,Y,Z) > mean(I(Y))·threshold, default 10. The purpose given is "to applied the PSF
  only on light source (otherwise glare effect would be applied on the entire image)" [O7].
- **Not documented:**
  - the PSF formulas or constants actually used;
  - energy normalisation;
  - how the PSF is scaled to degrees (field of view or pixel pitch);
  - the pupil value per regime;
  - whether non-thresholded pixels are left unconvolved (the wording implies yes);
  - whether the core is replaced or added;
  - whether any clamp is applied.
- **UNKNOWN; not inferred.**

## J4: architectural order compared

| System | Order (as documented) | Source |
|---|---|---|
| Spencer et al. 1995 | Glare PSF (photopic or scotopic mix chosen by adaptation) convolved with **scene** luminance, then display mapping. *Our summary; the paper is not in the cache, ledger L38.* The repo pins the photopic Eq. 5 mix 0.384 f0 + 0.478 f1 + 0.138 f2 | docs/research/source-ledger.md L24, L38 |
| Vangorp et al. 2015 (Local Adaptation) | "First, optical glare is simulated to produce a retinal image. Then, the local luminance adaptation map is computed": L_O = I ∗ O (CIE 135/1-6 GSF), then tvi(L_O) | research-cache/local-adaptation-2015/paper.txt l.12, 305–313 |
| Our baseline (frozen) | Cycles EXR (cd/m²) → [Blender Fog Glow = Spencer '95 Eq. 5 photopic, FOV-calibrated; **OFF**] → pcond (Ward Larson 1997, its own 1° veil option) | docs/research/human-night-vision-landscape.md l.325, 462, 579, 611 |
| Ocean | spectral buffer → `spectraltohv` (regime, age, time-adaptation **gains**) → `glare` (user regime PSF on thresholded XYZ pixels) → tone map (`drago`, ld) are separate chained filters. The documentation says only that glare "could be applied afterwards" spectraltohv and that denoising must come before glare and drago. **The glare-versus-Drago order is not stated.** | O2, O3, O4, O1 filter page ("They are chained in the output node") |

- Ocean's glare works on an XYZ (luminance-valued) buffer, as Spencer, Vangorp and our intended
  baseline do. Its position relative to the tone map is **not fixed by the documentation**: Drago
  also accepts XYZ, and the chain is user-ordered.
- It differs from Vangorp: the Ocean adaptation step (`spectraltohv`) comes **before** glare. Glare is
  therefore not documented as an input to adaptation.
- It differs from Spencer and from our calibrated Fog Glow in the **threshold gating**: only pixels
  above 10× the image mean get a PSF. Spencer (as pinned in our ledger) and our Fog Glow calibration
  convolve all energy.

## J5: role of glare in Ocean

- **Visible post-effect: yes.** It is a "post-processing filter", documented for "direct comparison of
  simulation with and without human vision effects" [O7, O2].
- **Retinal stimulus:** only implicitly. It modifies the XYZ buffer, which is documented as physical
  and luminance-valued.
- **Adaptation input: not documented.** No node documents using the glared image to set adaptation.
- The **Glare Map** output (UGR/DGP/GR) is a separate *discomfort metric* path, not a rendering [O6, O9].

## NATIVE ENVIRONMENT / NATIVE REPRODUCTION

- **BLOCKED.** Ocean is commercial (licence or registration: https://eclat-digital.com/register/,
  licensing pages in O1).
- No reverse engineering was done (per task).
- No binary was obtained.

## COMMON STIMULUS

Not run (NATIVE BLOCKED).

## ASSUMPTIONS

- Spectral input converted to CIE XYZ with 683 lm/W (photopic) or 1700 lm/W (scotopic) [O8].
- Glare thresholding is **relative** (image mean). The regime is a user parameter; its absolute
  luminance ranges are documented but not enforced (as far as documented).
- Display: Drago `ld` (cd/m²). No px/deg or viewing-distance parameter is documented for the glare PSF.

## VALIDATION

- None documented. The blog figures are illustrations.
- The EGSR 2025 talk and paper (Glare Map) concern discomfort indices [O9, O10]. The Zenodo dataset
  15396471 is listed there; it was not downloaded because it is not about the Human Vision filter.

## REUSE

- Proprietary software. The public documentation is readable, and we quoted short excerpts for
  research notes only.
- Nothing was copied into tracks/ beyond short quotations.

## FAILURES / SURPRISES

- The documented "mesopic" PSF range (0.01–3 cd/m²) and scotopic range (10⁻⁶–10⁻³) leave the gap
  10⁻³–10⁻² undefined.
- "Photopic 10 to 10⁸" leaves 3–10 cd/m² undefined.
- The age parameter is documented as real but the API returns int.
- The threshold is relative to the image mean (default 10×). By the documented formula alone, a night
  scene with a very dark mean passes almost every lamp, while in a bright scene the same lamp may get
  **no** glare. This is a direct consequence of the formula, not a tested behaviour.
- Documentation for Human Vision nodes appears only in the 2025 docs tree (older trees return
  HTTP 500 for these paths).

## BRIGHT POINT SOURCE

1. Where the PSF is applied: on the XYZ image buffer, only to pixels with I > mean(Y)·threshold [O2].
2. Before/after adaptation: after `spectraltohv` (regime, age, time-adaptation gains), per "could be
   applied afterwards" [O4]. Glare does not feed adaptation (not documented).
3. Before/after tone reproduction: **unknown**. It is a user-ordered filter chain.
4. Energy preserved: **unknown** (not documented).
5. Absolute-luminance aware: **partly**. The regime ranges are in cd/m², but the regime is chosen by
   the user and the threshold is relative to the image mean.
6. PSF depends on: adaptation regime (user enum, standing in for pupil and rod/cone state), age, and
   wavelength (optional dispersion "rainbow" lenticular halo). Field angle: unknown.
7. HDR source on a display: glare filter, then Drago log mapping with `ld`. Whether the core clips
   is not documented.
8. Halo and perceived brightness: not addressed.
9. Temporal PSF variation: **none documented**. The "random straight lines" (ciliary corona) are
   static in single images. Time adaptation changes gains only.
10. Clip before or after convolution: threshold gating before convolution; clipping unknown.

## VERDICT

**SCIENTIFIC ORACLE** (documentation-level). Its value for us is the documented architecture:
- Spencer-derived, regime- and age-dependent PSF;
- mean-relative source thresholding;
- adaptation as gains before glare.

It is not runnable (commercial), so it is not an oracle of pixel values.
