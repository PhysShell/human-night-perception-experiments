# Human night vision for a rural night scene: survey of existing software (round 1)

Status: round 1 (research + M0), round 2 (M1) and round 3 (M1.1 colorimetry gate); see the sections **M1 results** and **M1.1** at the end. Checked 2026-09-22/23. Every factual claim is traced in
[`source-ledger.md`](source-ledger.md) (IDs like **[L12]**). Claims marked *tested* were run
in this repository. M0 results are in [`m0-results/`](m0-results/). You can reproduce them with
`nix develop -c m0/run_m0.sh` (see [`../../m0/README.md`](../../m0/README.md)).

**Bottom line**

- **What exists.** Existing, maintained, CPU-only software already covers the hard core of the
  target: darkness-appropriate tone reproduction, loss of colour at low light, the Purkinje
  shift, and dark silhouettes with the lights still standing out.
- **The operator.** That software is **Radiance `pcond -s -c`**, the author's own implementation
  of Ward Larson, Rushmeier & Piatko 1997.
- **What it does not handle well.** Glare, loss of acuity, and keeping the warm colour of the
  lights. On our kind of content (chains of sub-pixel lights) these either produce artifacts or
  get lost.
- **What we had to write.** No vision model. Only packaging (two Nix derivations) and format glue.

---

## A. Problem definition

We want to show, on an ordinary display, **what an observer perceives** when looking across a
dark rural valley at night. We do **not** want what a camera records.

The appearance comes from three physically separate layers. Keep them apart. Do not collapse them
into "bloom".

| # | Layer | Where | Phenomena | Who should model it |
|---|---|---|---|---|
| 1 | **Atmosphere** between the light and the eye | outside the eye, kilometres of air | extinction and aerosol haze (the lights dim and redden with distance); forward-scattered halos in haze; turbulence: scintillation (brightness twinkle) and image dancing (position jitter) of distant point sources | the renderer (Blender volumes) for haze; an image-level turbulence step for shimmer |
| 2 | **Eye optics** | cornea, lens, ocular media | veiling glare / disability glare (stray light around bright sources, CIE 146:2002 glare spread function); point-spread function of the eye | post-process on scene-linear HDR, before any tone mapping |
| 3 | **Retina and neural processing** | photoreceptors onward | photopic → mesopic → scotopic transition (about 5 → 0.005 cd/m²); rod–cone mixing; **Purkinje shift** (blues relatively brighter, reds darker); **desaturation**; **loss of spatial acuity**; threshold contrast sensitivity; local and global adaptation; **temporal dark and light adaptation** | an HVS operator mapping scene cd/m² to display cd/m² |

On top of that there is a 4th, non-physiological layer: **display and viewing conditions.** The
simulation assumes a peak luminance, a black level and the room's ambient light. Every operator
below has such parameters, and a result is only meaningful relative to them.

### Target properties in measurable terms

- **Very dark scene.** Most of the field sits at about 1e-4 to 1e-3 cd/m² (moonless rural night).
  That is deep scotopic: *no colour, low acuity* in fields, trees and hills.
- **Mixed adaptation state.** The distant lights are about 1e2 to 1e4 cd/m² when pixel-averaged,
  which is photopic, so they keep their colour. The lights set the adaptation locally, the
  landscape sets it globally.
- **Salient lights, silhouetted trees.** The lights are small, high-contrast and perceptually
  salient. Their visibility is dominated by contrast against a black field, not by their size.
  Trees are darker than the sky, so they read as silhouettes.
- **Things to avoid.** Camera artefacts: sensor noise, JPEG, sharpening, depth of field, chromatic
  aberration, anamorphic streaks. The real eye does have *rod noise* at scotopic levels (Jacobs et
  al. 2015 **[L31]**; Thompson et al. 2002 **[L33]** add it). Whether to include it is an explicit
  later decision (gate G5), not a default.

---

## B. Existing software landscape

Legend: ✅ *tested here*, 📄 *verified from docs or source only*.

### B1. Radiance `pcond` ✅ (primary candidate)

- **Purpose.** "Condition a Radiance picture for output", optionally mimicking human vision **[L1]**.
- **Implements.** Ward Larson, Rushmeier & Piatko 1997, IEEE TVCG, DOI 10.1109/2945.646233
  **[L2]**. Greg Ward is an author of both the paper and the program, so this is **the author's
  reference implementation**, still maintained.
- **Status.** Radiance master is a daily import from the official CVS tree. Last import
  2026-08-19. Rolling "6.1a" builds. There is CI with unit tests **[L3]**.
- **License.** Radiance Software License v2.0, BSD-style **[L4]**.
- **OS.** Linux, macOS, Windows. CPU-only, single-threaded, fast (a 1920×820 image runs in a few
  seconds).
- **nixpkgs.** **Removed** on 2026-01-02 ("broken for a long time") **[L5]**. ✅ We rebuild it in
  `nix/radiance.nix` with three fixes:
  - `-std=gnu17`, because it uses K&R prototypes and GCC 15 defaults to C23;
  - OpenGL headers, which CMake requires even when headless;
  - a static libtiff for `uv_encode`.
- **I/O.** Radiance RGBE/XYZE pictures in **radiometric units** (W/sr/m²). Luminance =
  179 lm/W × Y **[L6]**. It reads the `VIEW=` header for the angular field; without one it
  assumes 40° **[L6]**. It reads `PRIMARIES=`. There is **no EXR reader**; we convert with
  `oiiotool` ✅.

**What `-h` does.** It is exactly `-a -v -s -c`, verified in source **[L6]**:

| flag | effect | implementation detail (source) | physiology or tone mapping? |
|---|---|---|---|
| `-s` | histogram adjustment capped by human threshold contrast | `htcontrs()` = Ferwerda '96 TVI, rod and cone branches **[L6][L7]** | physiological (threshold visibility matching) |
| `-c` | mesopic/scotopic colour loss plus scotopic spectral response | linear blend between 5.62e-3 and 5.62 cd/m²; below that, grey = scotopic luminance (approx. V′ from RGB weights .062/.608/.330) **[L6]** | physiological (desaturation + Purkinje) |
| `-a` | variable-resolution blur of dark regions | acuity fit 17.25·atan(1.4·log10 La + 0.35) + 25.72 cyc/deg (Shaler) **[L6]** | physiological in intent |
| `-v` | veiling glare | on a ~1° foveal grid; weight ≈ 1/θ²; 8 % of adaptation (`VADAPT`) **[L6]** | physiological in intent, low resolution |
| `-i f` | fixation-weighted adaptation | fixation points read from stdin **[L1]** | gaze model (static) |
| `-I` | shared precomputed histogram (`phisto`) | used for consistent exposure across animation frames **[L1]** | temporal *consistency*, not time-course |
| `-u`, `-d` | display max luminance and dynamic range | defaults 100 cd/m² and 100:1 **[L1]** | display assumption |

**M0 findings** ✅ (sheets in `m0-results/`):

- **`-s -c` is the best result in this survey.**
  - The landscape goes achromatic.
  - The Purkinje shift is right: two probes of equal photopic luminance at 0.03 cd/m² render as
    red → 0.33 and blue → 0.74 grey.
  - Trees read as silhouettes, the field stays dark (mean display value 0.06), and the lights
    stay the brightest things in the frame.
  - On the Fairchild dusk image, the foliage desaturates while the lit windows stay warm and
    salient.
- **`-a` breaks on point-source content.** Its scanline-bar resampling smears chains of sub-pixel
  lamps into long horizontal orange bars (`synthetic_pcond_veil_vs_acuity.jpg`, bottom). This is
  an artefact, not acuity.
- **`-v` is too coarse.** The veil is computed on a ~1° grid (about 32 px here), so a chain of
  lamps becomes a broad, blotchy fog band tens of degrees tall (same file, top).
  - Its physical direction is right. CIE 146 predicts veiling luminance around 0.1–1 cd/m² near
    such a chain, which is ≫ the 3e-4 cd/m² field.
  - But its angular profile cannot be checked, and it cannot resolve the halo around individual
    lamps.
- **Warm hue of bright lamps is lost.** pcond clips highlights to (1,1,1) *inside* the mapping,
  so the orange lamps come out pure white. This is confirmed on its float output. It matters,
  because warm lights are the emotional centre of the scene.

### B2. pfstools / pfstmo ✅

- **Status.** Last release 2.2.0 (2021-08-12). Low-level maintenance in git (2024-10, 2025-09).
  LGPL-2.1 **[L8]**.
- **nixpkgs.** **Removed** on 2026-02-26 because of its ImageMagick-6 dependency **[L9]**.
  ✅ Rebuilt in `nix/pfstools.nix` with ImageMagick, Qt, GL, MATLAB, Octave and OpenEXR off. EXR
  goes through `oiiotool` → PFM.
- **Operators actually in the 2.2.0 tree** ✅: drago03, durand02, fattal02, ferradans11 (did not
  build here: FFTW detection), mai11, mantiuk06, mantiuk08, pattanaik00, reinhard02, reinhard05.
  - **There is no ferwerda96 in pfstmo**; that operator lives only in Luminance HDR **[L10]**.
  - There is no Krawczyk 2005 and no Kirk & O'Brien 2011 **[L10]**.
- **`pfstmo_pattanaik00`** (Pattanaik, Tumblin, Yee, Greenberg, SIGGRAPH 2000 **[L11]**;
  third-party implementation by G. Krawczyk):
  - Needs cd/m² input **[L12]**.
  - Has rod and cone responses with bleaching. Rods add an *achromatic* term, so it desaturates
    in the dark.
  - Source shows **rods are driven by photopic Y, not scotopic luminance**, so there is **no
    Purkinje shift** **[L12]**.
  - `-t --fps` gives a time course of adaptation over a pfs frame stream. It is **the only
    packaged temporal-adaptation operator** found.
  - ✅ Runs on a 20-frame bright→dusk sequence, and its state evolves over time (slow drift
    consistent with τ_rod = 400 s).
  - ⚠ The *direction* of the transient is not yet validated. After a bright frame, the dusk
    frames came out *brighter* than the static render (0.41 vs 0.28).
  - ⚠ A single negative pixel makes its log-average NaN and whites out the frame, so glue must
    clamp.
  - ⚠ It produces red speckle at near-zero pixels on real data.
- **`pfstmo_mantiuk08`** (display-adaptive TMO, Mantiuk, Daly, Kerofsky 2008):
  - Excellent display modelling (gamma, peak, black, ambient, ppd).
  - **No scotopic model.** ✅ It turns night into dusk.
- **`reinhard05`** (Reinhard & Devlin photoreceptor) and **`ferradans11`**: cone-only adaptation
  models. ✅ reinhard05 keeps full colour at 0.03 cd/m², which is wrong for night.

### B3. Luminance HDR 📄

- **What it offers.** A GUI and CLI over the pfstmo operators, plus ferwerda96, kimkautz08,
  ashikhmin, vanhateren and lischinski **[L13]**.
- **Status.** Last tag 2.6.1.1 (2021). Maintenance-only commits until 2025-06. GPL-2 **[L13]**.
- **nixpkgs.** **Removed** on 2026-04-17 (EOL Qt5 WebEngine) **[L14]**.
- **Ferwerda96 bug.** Its ferwerda96 has a **scotopic TVI typo**: it computes `2.18^(…)` where
  the paper has `(…)^2.18` **[L13]**. Use HDR Toolbox's FerwerdaTMO or pcond's TVI instead.
- **Verdict.** Useful only as an interactive toy (Ubuntu still ships 2.6.1.1 **[L15]**). Not worth
  packaging. Ferwerda96 is superseded by pcond for our purpose.

### B4. HDR Toolbox (Banterle, MATLAB) 📄

- **Status.** Active (commit 2026-09-11), GPL-3 **[L16]**.
- **Relevant contents.** Correct `FerwerdaTMO`, static `PattanaikTMO`, `WardHistAdjTMO`
  (histogram only, *no* glare, acuity or colour), and `lumScotopic` **[L16]**.
- **Verdict.** Useful as a *second, independent implementation* when a result looks suspicious.
  Octave works "partially". Not the main path.

### B5. Kirk & O'Brien 2011 low-light operator 📄

- **What it models.** It models rod intrusion into the opponent channels (Cao et al. 2008 **[L35]**),
  i.e. a physiological Purkinje/mesopic *hue* shift. That is more faithful than pcond's grey blend.
- **Code.** A third-party GIMP 2 plugin (Y. J. Lee, last updated 2012, GPL; C++, libgimp2/GTK2,
  OpenCV, OpenEXR) **[L17]**. There is also a 2.66 GB spectral dataset **[L17]**.
- **Verdict.** Abandoned. Escalate to it only if pcond's grey scotopic blend proves
  insufficient (gate G4).

### B6. Papers with **no public code** 📄

- Ferwerda 1996 (no author code; third-party implementations in Luminance HDR and HDR Toolbox)
  **[L7]**
- Pattanaik 1998 multiscale **[L30]**
- Durand & Dorsey 2000 **[L32]**
- Thompson, Shirley, Ferwerda 2002 **[L33]**
- Krawczyk, Myszkowski, Seidel 2005 **[L34]**
- Wanat & Mantiuk 2014: results gallery only **[L36]**
- Jacobs et al. 2015: gaze-contingent; PDF, slides and video only **[L31]**
- Ritschel et al. 2009, temporal glare **[L37]**
- Spencer et al. 1995 glare PSF **[L38]**. Its PSF *is* implemented in Blender's Fog Glow (B7).

Reimplementing any of these is escalation only (section G).

### B7. Blender / Cycles ✅ (scene authoring, HDR source)

- **Version.** nixpkgs ships **Blender 5.2.2 LTS** ✅. That is the current stable release,
  2026-09-15 **[L18]**. CUDA/OptiX via `blender.override { cudaSupport = true; }` **[L19]**.
- **Headless render.**
  `blender -b f.blend -o out/#### -F OPEN_EXR -f 1 -- --cycles-device CPU` **[L20]**.
- **Output.** Linear EXR (half or float) of **radiance in W/(sr·m²)**. Cycles is RGB, not
  spectral **[L21]**.
- **⚠ Calibration.** Light "Watts" are radiant power **[L22]**, and the manual's own table
  implies about 345–380 lm/W for LEDs. Converting EXR to cd/m² therefore needs an explicit,
  documented factor, e.g. 683 × Y for a monochromatic interpretation or a scene-referenced
  calibration. This is the single most important glue parameter for M1 (gate G1).
- **Colour management (5.x).**
  - Selectable working space: Rec.709, Rec.2020, ACEScg.
  - Views include AgX, Filmic, Khronos PBR Neutral, ACES 1.3/2.0 **[L23]**.
  - These are *display renderings for artists*, not HVS models. Keep them out of the
    perceptual path (use "Standard" or "Raw" and export EXR).
- **Compositor Glare → Fog Glow.**
  - Source uses the **Spencer et al. 1995 photopic glare PSF** **[L24]**, a physically motivated
    eye-scatter kernel.
  - Its angular extent comes from a heuristic `size` parameter that is **not tied to the camera
    FOV** **[L24]**.
  - It is photopic only.
  - Usable as the layer-2 glare step if its size is calibrated to degrees (gate G3).
- **Tone Map node.** R/D Photoreceptor (Reinhard–Devlin 2005) is still present **[L25]**. It is
  cone-only, like reinhard05.
- **Atmosphere.** Volumes (5.0 null-scattering default) and the Sky Texture multiple-scattering
  model **[L26]**. The sky is a *daylight* model, not a night sky. Haze and extinction of the
  distant lights (layer 1) belong here, in the render, not in post.

### B8. Stanford ISET ecosystem 📄 (scientific reference, not production)

- **Components.**
  - ISETCam and ISETBio: MATLAB, MIT, both very active (commits in September 2026) **[L27]**.
  - ISET3d: MATLAB driving **PBRT-v4 inside Docker**; CPU image `digitalprodev/pbrt-v4-cpu`
    **[L27]**.
  - isetvalidate: gateway `ieValidate`, needs MATLAB **[L27]**.
- **Eye optics.** Available:
  - wavefront optics (Thibos, Zernike), Ijspeert age/pupil MTF/PSF in ISETCam;
  - Navarro, Arizona and LeGrand schematic eyes via the PBRT `humaneye` camera, which is CPU-only
    in practice **[L27]**.
- **Retina.** The cone mosaic (`cMosaic`) and outer segments exist, but **there is no rod mosaic
  and no scotopic pathway** **[L27]**. Only rod absorptions and scotopic luminance helpers exist.
  So the "3D scene → spectral radiance → eye optics → retinal irradiance → photoreceptors" chain
  **exists for cones only**. It does not give a night-appearance image.
- **Octave.** ISETCam has Octave hooks, and isethdrsensor's full pipeline was tested in Octave
  6.4 (2025). ISETBio realistically needs MATLAB **[L27]**.
- **Blender.** No official exporter. Options are the assimp → .pbrt path or the third-party
  bpbrt4 addon (Blender 4.4, no license file) **[L28]**.
- **Most useful piece for us.** The **ISETHDR** dataset (Liu, Shah, Wandell, IEEE Sensors J.
  2025, DOI 10.1109/JSEN.2025.3550455). It has 2000 physically based spectral HDR driving scenes
  with separate headlight, streetlight, other-light and sky EXR light groups, so they can be
  recombined into night scenes **[L29]**. It is a candidate calibrated test input for M0/M1.

### B9. Perceptual metrics 📄 (comparison tools, **not** renderers)

| Tool | Version, license | What it measures | What it does *not* do |
|---|---|---|---|
| **ColorVideoVDP** (`cvvdp`) | 0.5.7 (2026-08), MIT, PyTorch, CPU works **[L39]** | visible difference (JOD) between test and reference video on a specified display (peak, black, ambient, ppd); spatio-temporal castleCSF | **floors luminance at 0.005 cd/m²** and clamps the CSF LUT there; no rods; no appearance **[L39]**. Only usable for comparing *display-referred outputs* of our pipelines, not scene radiance. |
| **FovVideoVDP** | 1.2.2, **CC BY-NC 4.0**, achromatic **[L40]** | as above, plus foveation (`--foveated`, fixation point) | non-commercial license; no colour |
| **HDR-VDP-3** | 3.0.7 (2023), BSD-style, MATLAB/Octave **[L41]** | still-image visibility and quality; **models rods** (scotopic sensitivity, CSF measured to 0.002 cd/m²), age, MTF, surround | no temporal dimension; not an appearance model **[L41]** |

**Correct use:**
- HDR-VDP-3 on *scene-referred* pairs. Example: "is the change from pipeline A to B visible at
  night luminance?"
- cvvdp on *display-referred* output videos. Example: "is the shimmer visible as flicker on the
  target display?"

Neither tells us what the scene looks like.

### B10. Colour science / CIE tooling 📄

- **colour-science** 0.4.7 (BSD-3) **[L42]**.
  - Has CIE 1951 scotopic V′(λ), the photopic LEFs, and `luminous_efficiency`.
  - Its mesopic function uses MOVE/LRC lookup tables. **It does not implement CIE 191:2010**
    **[L42]**.
- **LuxPy** 1.12.5 (GPL-3) **[L43]**.
  - `vlbar_cie_mesopic` and `get_cie_mesopic_adaptation(Lp, Ls|SP) → (Lmes, m)` implement
    **CIE 191:2010** **[L43]**.
- **CIE documents.**
  - CIE 191:2010: mesopic photometry **[L44]**.
  - **CIE 257:2026**: practical application in outdoor lighting, new this year **[L45]**.
  - CIE 146:2002: disability glare equations, superseding CIE 135/1 **[L46]**.
- **Use.** Use LuxPy as an *oracle* to check pcond's mesopic thresholds and weights. Do not
  transcribe tables.
- **nixpkgs.** Neither library is packaged. Use a `uv` venv inside the devShell.

### B11. Visual-system simulators 📄

- **VSS (Stuttgart).**
  - Rust, Apache-2.0. `main` is dormant since 2023; the `wgpu` branch was active in 2026-08
    **[L47]**.
  - Simulates *impairments*: cataract, refractive error, glaucoma, AMD, colour blindness, and
    nyctalopia as a heuristic rod-loss shader. It has a rod-density retina map **[L47]**.
  - GPU required. **Not a normal-night-vision model.**
- **OpenVisSim.** Unity, GPL-3, deprecated by its author, impairments only **[L48]**.
- **Verdict.** Neither helps with normal scotopic appearance.

### B12. Spectral renderers 📄 (only if the RGB path fails)

- **PBRT-v4.** Apache-2.0, active (2026-09), always spectral, CPU by default, OptiX optional. No
  official Blender exporter **[L49]**.
- **Mitsuba 3.** 3.9.1 (PyPI 2026-08), BSD-3, `scalar_spectral` and `llvm_ad_spectral` CPU
  variants **[L50]**. The **mitsuba-blender** addon is active again: Blender ≥4.2 extension,
  wheels for 5.1+ **[L51]**.
- **Verdict.** If the spectral path is ever needed, Mitsuba + mitsuba-blender is the least
  friction.

### B13. Atmospheric turbulence and scintillation 📄

| Kind | Tools | Temporal correlation | Notes |
|---|---|---|---|
| physics (phase screens + Fresnel propagation) | **HCIPy** 0.7.1, MIT: `InfiniteAtmosphericLayer`, `MultiLayerAtmosphere(scintillation=True)` **[L52]**; **AOtools** 1.0.8, LGPL-3: infinite Kolmogorov/von Kármán screens, `rytov_variance` (vertical-path form) **[L53]** | yes (frozen flow) | produce per-source intensity and tilt time series |
| image-level warp + blur | Chimitt & Chan 2020 (Zernike) **[L54]**, P2S (ICCV 2021) with a public fork under **CC BY-NC-SA** **[L55]**, ATSyn/DATUM (CVPR 2024, temporally correlated) **[L56]** | P2S: per frame; ATSyn: yes | phase-only: tilt and blur, **no amplitude scintillation** (inferred from method) |
| haze and extinction | Blender volumes **[L26]**; libRadtran (physics, not images) | — | layer 1, static |

For kilometre-scale near-ground paths, the physically dominant visible effects on tiny lamps are
**scintillation (intensity)** and **angle-of-arrival jitter (position)**. Weak-turbulence
reference: Rytov variance σ_R² = 1.23 Cn² k^(7/6) L^(11/6) (Andrews & Phillips) **[L57]**.

HCIPy/AOtools can generate *per-lamp* correlated time series. Applying them to point sources is a
small glue step: modulate each lamp's intensity or position in the render or in the EXR. This is
M2 work; no custom turbulence *physics* is needed.

---

## C. Recommended minimal stack

    Blender 5.2 (Cycles CPU)  ── scene-linear EXR, radiance ─┐
                                                             │  glue: ×k → cd/m² (G1),
                                                             │  clamp ≥0, VIEW/PRIMARIES header
                                                             ▼
                     [layer 2, optional]  Blender Fog Glow (Spencer'95 PSF), size calibrated to deg (G3)
                                                             ▼
                     Radiance  pcond -s -c  [-u Ldmax -d Ldyn]  [-I shared histogram for sequences]
                                                             ▼
                     hue-preserving highlight handling (G2, ~3 lines) → PNG / video (ffmpeg)

- **Everything comes from one flake:** `nix develop` → radiance, pfstools, oiiotool, imagemagick,
  ffmpeg, blender, python+numpy+OIIO, uv. This was tested in this environment.
- **Custom code** is limited to:
  - two Nix derivations for tools that nixpkgs dropped;
  - one Bash runner that does format conversion and headers;
  - one synthetic test-image generator (test data only).
- **Why pcond over pattanaik00 for stills.**
  - pcond is the author's implementation, has a scotopic spectral response (Purkinje) and ran
    cleanly on both inputs.
  - pattanaik00 lacks Purkinje, NaNs on negative input and speckles on real data.
- **Temporal adaptation (M2).** `pcond -I` keeps exposure *stable* across frames. That is what a
  steady observer of a static scene needs, and probably all M2 needs. pattanaik00 `-t` is the
  only packaged *time-course* option, kept in reserve until validated.

## D. Scientific reference stack

The goal here is independent confirmation, not production.

1. **Mesopic oracle.** LuxPy CIE 191:2010, used to check pcond's 5.62e-3–5.62 cd/m² band and its
   RGB→V′ approximation on our lamp and field spectra.
2. **Glare oracle.** The CIE 146:2002 general disability-glare equation. It predicts veiling
   luminance from eye illuminance per source. Use it to set or verify the Fog Glow size and
   strength (G3). It is a published formula to *evaluate*, not a model to invent.
3. **Visibility oracle.** HDR-VDP-3 on Octave (it has a rod pathway) for "is this change visible
   at scene luminance?".
4. **Second implementation.** HDR Toolbox `FerwerdaTMO` and `WardHistAdjTMO` as independent
   cross-checks of pcond's TVI and histogram stages.
5. **Calibrated inputs.**
   - Fairchild HDRPS (absolute calibration per scene) ✅ McKeesPub used.
   - ISETHDR night light-groups.
   - Radiance's own renders, which are in physical units by construction.
6. **Full physiological chain (only if gate G6 fires).**
   - ISET3d + PBRT-v4 (Docker CPU) + ISETCam/ISETBio.
   - This is cone-only. A rod pathway does not exist there either, which limits its value for
     *night* appearance.

## E. Gap analysis

| Desired effect | Status with existing tools | Gap |
|---|---|---|
| Darkness-appropriate global mapping, threshold visibility | ✅ pcond `-s` | display assumptions must be set per viewing condition |
| Desaturation, mesopic/scotopic transition | ✅ pcond `-c` (linear grey blend) | hue shifts within mesopic (Cao/Kirk) not modelled; acceptable for now |
| Purkinje shift | ✅ pcond `-c` (scotopic V′ weights) | approximate RGB→V′; verify against LuxPy |
| Loss of acuity | ⚠ pcond `-a` exists but **artefacts on sub-pixel light chains** | need a clean luminance-dependent blur: pcond's `hacuity()` curve applied as a blur in a few luminance bands. This would be the first real custom code; defer (G5). |
| Veiling glare around lamps | ⚠ pcond `-v` too coarse (1° grid); Blender Fog Glow has the right PSF shape (Spencer '95) but FOV-uncalibrated | calibrate the Fog Glow size to degrees and check against CIE 146 (G3) |
| Warm colour of bright distant lamps | ❌ pcond and pattanaik00 clip to white | hue-preserving compression of out-of-gamut highlights (G2): glue, not a vision model |
| Temporal adaptation | ✅ stable exposure via pcond `-I`; ⚠ pattanaik00 `-t` runs but not validated | validate before use |
| Atmospheric haze and extinction | ✅ Blender volumes | scene work in M1/M3 |
| Scintillation / image dancing | 📄 HCIPy or AOtools time series | glue that applies per-lamp modulation (M2) |
| Gaze / fixation | ⚠ pcond `-i` (static fixations) | no gaze-contingent display; not needed for a still or film |
| Rod noise | none packaged | an artistic decision; gate G5 |

## F. M0 experiment plan (executed in round 1)

**Data**

1. `m0/make_synthetic_night.py`: a synthetic image in absolute cd/m² with a documented scene:
   - sky 3e-4–1.5e-3;
   - field 1.5e-4–5.5e-4 with fine furrows (acuity probe);
   - near-black poplar silhouettes;
   - a dense chain of sodium-coloured sub-pixel lamps on a near-horizontal road, with haze
     extinction baked in;
   - village clusters;
   - an equal-luminance red/blue probe at 0.03 cd/m² (Purkinje test).
2. `m0/fetch_fairchild.sh`: the Fairchild HDRPS *McKeesPub*, a real dusk scene with absolute
   calibration ×6.25. Research-only license, so it is **not committed**.

**Command**

    nix develop -c m0/run_m0.sh                                   # synthetic
    nix develop -c m0/fetch_fairchild.sh
    CROPS=0 nix develop -c m0/run_m0.sh m0/data/fairchild_McKeesPub_cdm2.exr 60 m0/out_mckeespub

**Pipelines compared.** All run on the *same* clamped input, with no parameters tuned.

- a) camera auto-exposure
- b) photometric (1 cd/m² scene = 1 cd/m² on a 100-nit display)
- c) pcond histogram only
- d) **pcond -s -c**
- e) pcond -h
- f) pcond -h for a 30-nit display
- g) pattanaik00 global
- h) pattanaik00 local
- i) mantiuk08 display-adaptive
- j) reinhard05
- k) pcond -v only
- l) pcond -a only

Temporal smoke test: pattanaik00 `-t` over a bright→dusk frame stream (see B2).

**Results**

- `m0-results/synthetic_sheet.jpg`, `synthetic_lights_crop.jpg` (4× zoom on the lamp ribbon),
  `synthetic_purkinje_probe.jpg`
- `synthetic_pcond_veil_vs_acuity.jpg`
- `fairchild_mckeespub_sheet.jpg`

**Verdict on the M0 acceptance condition**

| criterion | met by | evidence |
|---|---|---|
| darker, silhouette-like low-light detail | pcond -s -c (d) | trees, hills and field become dark grey masses; field display value ≈ 0.06 |
| perceptually salient distant lights | pcond -s -c (d) | lamps are the maximum display value, with no bloom sprite |
| realistic low-light colour loss and adaptation | pcond -s -c (d) | fully achromatic below 5.6e-3 cd/m²; Purkinje probe red 0.33 < blue 0.74; McKeesPub foliage desaturates while the windows stay warm |
| without generic bloom | yes | `-v` excluded because of its coarse veil |

**The M0 acceptance condition is met by an existing pipeline, with one caveat:** the lamps are
salient but their *warm hue is lost* (gap G2). The generic camera and tone-mapping baselines
(a, i, j) turn the night into dusk and keep full colour. That confirms the difference is
physiological modelling, not exposure.

**What M0 did not test:**
- display calibration of the viewer's actual screen;
- a Blender-rendered input (M1);
- LuxPy and CIE 146 cross-checks (first thing in M1).

## G. Decision gates

- **G0: stay with existing tools (current state).**
  - Continue as long as `pcond -s -c` (+ `-I` for sequences) is judged adequate on our own
    renders in M1, and the gaps are cosmetic.
- **G1: calibration glue (required for M1, expected).**
  - A one-line factor from Blender radiance to cd/m², documented in the scene.
  - Validate it by rendering a Lambertian patch under a known illuminant and checking cd/m² with
    `pvalue` or oiiotool stats.
  - No model code.
- **G2: tiny glue script (expected).**
  - Hue-preserving highlight compression. Scale RGB by 1/max(R,G,B) where the maximum exceeds 1,
    either before pcond's clip or by re-injecting chromaticity from the input.
  - Allowed only as ≤30 lines of numpy/oiiotool with a before/after test on the lamp crop.
- **G3: glare calibration.**
  - Use Blender Fog Glow (Spencer '95) on the EXR *before* pcond.
  - Set its size from the camera FOV so the kernel's angular extent matches, then check the
    predicted veil against the CIE 146 equation at 1°, 3° and 10° from a lamp.
  - If Fog Glow cannot be matched within about 2×, escalate to applying the CIE 146 PSF by FFT
    convolution (numpy, about 20 lines; still an existing *formula*, not a new model).
- **G4: escalate the mesopic colour model.**
  - Only if observers judge pcond's grey blend visibly wrong on lamp-lit mid-mesopic surfaces (the
    near road, lit verges).
  - Then try the Kirk & O'Brien plugin core first, before anything custom.
- **G5: acuity and rod noise.**
  - Only if the M1 renders show fine detail that is clearly too sharp *after* pcond -s -c.
  - Then apply pcond's own `hacuity()` curve as luminance-banded Gaussian blur (the first custom
    image code; must be justified with before/after).
  - Rod noise is an artistic decision; default off.
- **G6: escalate to ISET.**
  - Only for a *scientific* question the RGB pipeline cannot answer. Example: "is the eye's PSF
    at 3 mm pupil + age 40 materially different from Spencer '95 on the lamp ribbon?"
  - Not for production.
- **G7: spectral rendering.**
  - Only if LuxPy shows that RGB→V′ errors on the actual lamp spectra (HPS vs LED) change the
    scotopic/photopic balance by more than about 20 %, *and* that is visible in HDR-VDP-3.
  - Then use Mitsuba 3 via mitsuba-blender.
- **G8: write anything custom (renderer, HVS model, addon, DSL, Lean).**
  - Not justified by any finding so far.

## Summary table

| Need | Existing solution | Ready now? | Missing piece |
|---|---|---|---|
| Scene authoring, HDR radiance | Blender 5.2.2 LTS, Cycles CPU, EXR (nixpkgs) | ✅ yes (M1) | done: K = 179 lm/W, radiometry verified |
| Scotopic/mesopic tone reproduction | Radiance `pcond -s -c` (author's code, Ward Larson '97) | ✅ yes (flake-built) | — |
| Purkinje shift, desaturation | `pcond -c` | ✅ yes | cross-check with LuxPy CIE 191 |
| Veiling glare (eye) | Blender Fog Glow (Spencer '95 PSF); pcond `-v` too coarse | ⚠ partial (M1) | FOV calibration solved; together with pcond it turns halos into disc sprites; magnitude check vs CIE 146 still open |
| Acuity loss | pcond `-a` | ❌ artefacts on point sources | defer; banded blur only if needed (G5) |
| Warm lamp colour preserved | pcond without PRIMARIES + `-x`/`tabfunc`/`pcomb` + PBR Neutral (Blender OCIO) on out-of-gamut pixels only | ✅ (M1) | no new formula needed |
| Stable exposure in video | `pcond -I` + `phisto` | ✅ (docs; not yet run on a sequence) | M2 test |
| Time-course adaptation | `pfstmo_pattanaik00 -t` | ⚠ runs, unvalidated | compare against Pattanaik 2000 figures |
| Haze / extinction | Blender volumes | ✅ | scene work |
| Scintillation / shimmer | HCIPy / AOtools phase-screen time series | 📄 not run | per-lamp modulation glue (M2) |
| Pipeline comparison metric | HDR-VDP-3 (rods, stills), ColorVideoVDP (display video; floor 0.005 cd/m²) | 📄 not run | uv venv / Octave |
| Physiological reference chain | ISET3d + PBRT-v4 + ISETBio | 📄 cones only, MATLAB | rods do not exist there |
| Reproducible environment | `flake.nix` (nixpkgs pin + radiance + pfstools derivations) | ✅ yes | — |

## Recommendation for M1

**Pipeline.** Use **Radiance `pcond -s -c`** as the perceptual stage. It is fed scene-linear EXR
from Blender, converted to cd/m² with one documented factor.

**First steps:**
1. Validate that factor (G1).
2. Add the hue-preserving highlight step (G2).
3. Try Blender Fog Glow, calibrated to CIE 146, as the only glare (G3).

**Keep off for now:** `pcond -a` and `-v`, pattanaik00 and every custom model.


---

## M1 results (round 2)

Details and reproduction steps are in [`../../m1/README.md`](../../m1/README.md). Images are in
[`m1-results/`](m1-results/). **No vision algorithm, tone mapper, glare kernel or addon was
written.**

### Calibration (was gate G1): closed

Cycles 5.2.2 CPU matches closed-form radiometry to within 0.2 % in every calibration case:
- sun on a Lambertian plane;
- point light, whose intensity is **P/(4π) W/sr**;
- world background;
- emission shader;
- sub-pixel emissive sphere at 500 m (energy conserved).

Pitfalls found along the way:
- Point lights are not camera-visible.
- The World Background node's default colour is 0.05, which silently divides the sky by 20.

The photometric scale is one declared convention. We adopt Radiance's 179 lm/W
equal-energy-white convention as the RGB radiometric → photometric calibration: lights are
authored in cd, cd/m² or lux and divided by 179, so cd/m² = 179 · Y.
- 179 lm/W is not the efficacy of any real lamp.
- *Corrected in M1.1:* the EXR is **not** "a Radiance picture as-is" for colour. Its values are
  on Radiance's scale, but its space is Rec.709/D65 and must be converted with `ra_xyze`.

### Fog Glow (gate G3): mechanism solved, perceptual use still open

Findings from the source (`node_composite_glare.cc`, `fog_glow_kernel.cc`):
- **The camera FOV does not reach the kernel.** The FOV in the cache key is derived from the
  Size input as `lerp(180°, 10°, Size^(1/3))`.
- The kernel then samples the PSF at `FOV/max(w,h)` degrees per pixel.
- So **Size = ((180 − FOV)/170)³** calibrates it to the camera.
- Required settings:
  - Threshold 0, which makes the smooth clamp exactly max(0, x);
  - Quality High;
  - the **Glare** socket, because the Image socket is input + glare and double-counts the core.

**Single-pixel test:** the profile matches Spencer Eq. 5 within ±1 % over 0.09°–3° and within
−3 % at 10°. Energy is conserved to 98.4 %.

**In the scene, though, Fog Glow followed by pcond gives visible disc halos**
(`m1_ribbon_crop_pcond_keephue_fogglow.jpg`):
- Each lamp becomes a white disc about 0.3–0.5° across with an orange core. This is close to
  the bloom-sprite look we want to avoid.
- **Halo colour.** The halo luminance is mesopic, so `-c` makes it grey. That part is legitimate.
- **Halo size.** This is not a glare error. *Corrected in M1.1:* pcond is **not** allocating
  display range by histogram here. On these night scenes it falls back to a CSF-chosen linear
  exposure, and the display clips at about 0.13 cd/m², so halo and core land on the same
  display max.
- **Display range barely helps.** Raising the display dynamic range from 100:1 to 1000:1
  (`-d 1000`) shrinks the discs only a little (`fogglow_display_range_d100_vs_d1000.jpg`, from
  the 16-spp test render).
- **Open questions** before Fog Glow can go into the default path:
  - Does the Spencer PSF predict the same veiling luminance as CIE 146:2002 for the same source
    geometry and a chosen observer? This comparison has not been done yet.
  - CIE 146 is an independent disability-glare reference. It is not a model of the dark-adapted
    eye, so agreement would validate the veil, not "human night vision".
  - How should a halo be allocated display range next to its own source?
- **Default:** Fog Glow is **off** in the recommended M1 path.

### Warm lamp colour (was gate G2): solved by reuse

**Root cause** (Radiance source): the white comes from `matscan()` → `clipgamut()`'s
over-brightness branch. That step runs whenever a `PRIMARIES=` header is present (the primaries
check compares pointers) and always for XYZE input.
- *Superseded in M1.1:* the route below relabelled Rec.709 data as Radiance RGB. See M1.1 for
  the honest route.

**Route** (`m1/pcond_keep_hue.sh`, `m1/run_m1.sh`):
1. pcond without a PRIMARIES header.
2. `tabfunc` + `pcomb` rescale only the over-max pixels to pcond's own `-x` display luminance.
3. **Khronos PBR Neutral** (from Blender's OCIO config) is applied only to pixels outside the
   display gamut. Everything else stays exactly pcond's output.

**Alternatives measured:**
- Radiance's own `clipgamut` keeps hue but gives pale lamps (saturation 0.16).
- PBR Neutral or ACES 2.0 applied to the *whole* pcond output crushes the darkness by up to 50×
  (PBR's toe, or ACES re-tone-mapping). So they must not follow pcond globally.

### M1 acceptance

| criterion | result |
|---|---|
| dark landscape is perceptually dark and silhouette-like | ✅ ground → display ≈ 0.004 (sRGB-encoded mean), sky 0.043, poplars read as dark masses against the sky |
| distant lights remain salient | ✅ brightest elements; the chain reads as a ribbon receding to about 14 km |
| lights stay warm instead of clipping to white | ✅ path 4 (PBR Neutral on out-of-gamut pixels); ❌ plain pcond (path 3) |
| no custom HVS algorithm | ✅ only configuration, calibration tests and glue |

**Recommended perceptual stack after M1:**

    Cycles EXR (K = 179) → [Fog Glow: off for now] → pcond -s -c (no PRIMARIES, -x map)
        → tabfunc/pcomb luminance cap on over-max pixels → OCIO: Standard view in gamut,
          Khronos PBR Neutral out of gamut

**Next gates:**
- **G3′.** Check the Spencer PSF magnitude against the CIE 146 disability-glare equation (young
  observer, dark-adapted pupil) before enabling Fog Glow.
  - If the magnitude is right, the disc problem belongs to the display-range allocation. Then
    test pcond `-i` fixations or `-d`, before any custom code.
- **G2 closed.** No hue glue needs to be written.
- **The scene is still too clean.**
  - No atmospheric scattering around the lamps (layer 1; only baked extinction so far).
  - No near road, no terrain relief.
  - This is M3/M4 content, not perceptual-stack work.


---

## M1.1: colorimetry gate (round 3)

Details are in [`../../m1/README.md`](../../m1/README.md), sections 2–5. Tests run with
`nix flake check`.

### 1. Colour provenance: fixed

**The M1 bug.** Giving pcond Rec.709 data without PRIMARIES meant pcond read it as
Radiance-standard RGB (equal-energy white): wrong luminance weights and wrong scotopic weights.
The red probe came out 14 % too bright, i.e. a weaker Purkinje shift.

**Now all conversion is done by `ra_xyze`**, starting from a truthful Rec.709/D65 header.

- Two honest paths were compared:
  - **A:** XYZE → pcond (pcond's `cielum` scotopic formula);
  - **B:** Radiance-standard RGB → pcond (pcond's `rgblum` weights).
- **Whole images agree:** mean |A−B| 0.0002–0.0026.
- **Saturated dark colours differ.** An independent bracket from existing code decides it:
  colour-science's five published spectral-recovery methods with CIE 1951 V′(λ).
  - **A** falls inside the spectral range for red, blue, sodium and warm-LED colours.
  - **B** overestimates the scotopic efficiency of reds and warm colours.

**Used: AB.**
- pcond's XYZE output everywhere it did not clip. This equals pcond as shipped, median and p99
  error 0.0000 on 4.1 M pixels.
- On the pixels pcond clipped: pcond's own **unclipped** result from the honest standard-RGB
  run, scaled to display luminance 1.
  - That run needs no relabelling. Standard RGB is pcond's default space, so the redundant
    PRIMARIES line is moved into the header history after being verified.
- No pcond formula is re-implemented.

### 2. Lamp colour, pcond `-c` and M0 probes after the fix

- **Purkinje probe (red / blue at equal 0.03 cd/m²):** A and AB 0.057 / 0.51; B 0.080 / 0.52;
  old M1 route 0.091 / 0.51.
- **Lamps** keep their hue (31°) and saturation (0.58) before gamut handling.
- **Sodium lamps render orange and 4000 K LEDs whitish** (`m1-results/m1_ribbon_crop_pcond_AB_fogglow.jpg`).

### 3. Gamut compression: existing transforms compared

On the lamp pixels (Y ≤ 1, a channel > 1, all components ≥ 0.14):

- **Do nothing (identical to a clip, 23° hue error):**
  - ACES 1.3 Reference Gamut Compression (OCIO builtin). It compresses chroma outside the
    working gamut, which these pixels are not.
  - ACES 2.0 SDR used as inverse → forward. The inverse clamps to the display cube by design.
- **Shift pcond's darkness when applied to the whole frame:** ACES 2.0 or PBR Neutral as a view.
- **Radiance `clipgamut`:** hue kept, saturation 0.20.
- **Khronos PBR Neutral on the lamp pixels only:** hue error 0.2°, saturation 0.67 of 0.71.
  - Khronos's precondition (input inside Rec.709) holds.
  - What it applies is its designed hue-preserving highlight compression.
  - **Kept, with the pixel restriction documented as the non-standard part.**

### 4. Fog Glow: adapter pinned, still off

- `fog_glow.py` refuses any Blender other than 5.2.2 unless explicitly overridden.
- The PSF regression test is part of `nix flake check`. Its negative control (wrong FOV) fails
  as it should.

### New findings

- **pcond is in linear mode on these night scenes.** `mkbrmap()` returns "no compression
  needed" because 1°-foveal averages fit the display. So `pcond -s -c` acts as a CSF-chosen
  linear exposure + mesopic colour + clip; in the M1 scene the display saturates at
  ~0.13 cd/m².
  - This, not histogram allocation, is why calibrated glare halos become discs.
- **pcond bug:** in linear mode the `-x` table overstates display luminance by 179/Ldmax.
  Confirmed on a ramp (0.556 vs 0.559) and guarded by `m1/test_pcond_mapping.py`.
- **OpenImageIO's RGBE reader fails on long Radiance header lines** (e.g. Nix sandbox paths in
  recorded command lines). Radiance steps run with short relative names; `pcomb -h` is used for
  the final merge.

### M1 status

**Closed**, with these gates left open:
- **G3′ (glare):** compare Spencer-predicted veiling luminance with CIE 146 for the same
  geometry and observer before enabling Fog Glow.
  - If the magnitudes agree, the disc problem is the display's range at a dark-adapted linear
    exposure.
  - Then investigate existing options (pcond `-u`/`-d`, fixation `-i`) before anything custom.
- **G7 (spectral):** only if the A-vs-spectral bracket turns out to matter visibly. It currently
  sits inside the range.
