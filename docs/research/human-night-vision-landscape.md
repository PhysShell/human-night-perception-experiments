# Human night vision for a rural night scene: survey of existing software (round 1)

Status: first execution round, checked 2026-09-22. Every factual claim is traced in
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
| Scene authoring, HDR radiance | Blender 5.2.2 LTS, Cycles CPU, EXR (nixpkgs) | ✅ yes | radiance → cd/m² factor (G1) |
| Scotopic/mesopic tone reproduction | Radiance `pcond -s -c` (author's code, Ward Larson '97) | ✅ yes (flake-built) | — |
| Purkinje shift, desaturation | `pcond -c` | ✅ yes | cross-check with LuxPy CIE 191 |
| Veiling glare (eye) | Blender Fog Glow (Spencer '95 PSF); pcond `-v` too coarse | ⚠ partial | FOV calibration + CIE 146 check (G3) |
| Acuity loss | pcond `-a` | ❌ artefacts on point sources | defer; banded blur only if needed (G5) |
| Warm lamp colour preserved | none (all clip to white) | ❌ | hue-preserving clip, ~30 lines of glue (G2) |
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
