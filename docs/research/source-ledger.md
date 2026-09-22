# Source ledger

All entries were checked on **2026-09-22**.

**Source types:**
- **paper**: peer-reviewed publication or standard
- **src**: source code read directly
- **doc**: official documentation, man page or README
- **pkg**: package-index metadata
- **run**: executed in this repository

**Confidence:**
- **H**: primary source read
- **M**: primary page read but a detail is inferred
- **L**: secondary or unverified

**Tested:** ✅ means we exercised the claim by running the software in this repository.

| ID | Claim | Source URL / DOI | Type | Conf. | Tested |
|---|---|---|---|---|---|
| L1 | pcond flags: `-h` bundles `-a -v -s -c`; `-i` fixations from stdin; `-I` precomputed histogram (from `phisto`) for animation; `-u` Ldmax, default 100; `-d` dynamic range, default 100; `-x` map file | https://github.com/LBNL-ETA/Radiance/blob/master/doc/man/man1/pcond.1 | doc | H | ✅ `-h -s -c -a -v -u -x` run |
| L2 | pcond implements Ward Larson, Rushmeier & Piatko 1997, "A visibility matching tone reproduction operator for HDR scenes", IEEE TVCG 3(4) | doi:10.1109/2945.646233 | paper | H | — |
| L3 | Radiance GitHub is a daily one-way mirror of the official CVS tree, with CI unit tests and rolling installers; master last import 2026-08-19 (bcffc2b) | https://github.com/LBNL-ETA/Radiance (README, `git ls-remote`) | doc | H | ✅ built that commit |
| L4 | Radiance Software License v2.0 (BSD-style, LBNL) | https://github.com/LBNL-ETA/Radiance/blob/master/License.txt | doc | H | — |
| L5 | nixpkgs removed `radiance` ("broken for a long time", 2026-01-02) | https://github.com/NixOS/nixpkgs/blob/master/pkgs/top-level/aliases.nix ; eval of nixos-unstable 26.11pre1077996.6774f7bc2537 | src | H | ✅ eval error reproduced |
| L6 | pcond internals: `DO_HUMAN = ACUITY\|VEIL\|HSENS\|COLOR`; mesopic band 5.62e-3–5.62 cd/m² with a linear blend; scotopic luminance from RGB weights .062/.608/.330 × 2.26; veil on a 1° foveal grid with weight ½cosθ/(1−cosθ) and VADAPT 0.08; acuity `17.25·atan(1.4·log10 La+0.35)+25.72`; default view 40° when no VIEW header; 179 lm/W | src/px/pcond.h, pcond.c, pcond2.c, pcond3.c, pcond4.c at bcffc2b | src | H | ✅ behaviour matches (M0) |
| L7 | Ferwerda, Pattanaik, Shirley, Greenberg 1996, "A model of visual adaptation for realistic image synthesis", SIGGRAPH 96 (TVI used by pcond `htcontrs`) | doi:10.1145/237170.237262 | paper | H | — |
| L8 | pfstools latest release 2.2.0 (2021-08-12); git activity 2024-10 and 2025-09; LGPL-2.1 | https://sourceforge.net/projects/pfstools/files/pfstools/ ; https://git.code.sf.net/p/pfstools/git | doc/src | H | ✅ built 2.2.0 |
| L9 | nixpkgs removed `pfstools` (ImageMagick 6 dependency, 2026-02-26) | nixpkgs aliases.nix; eval as for L5 | src | H | ✅ eval error reproduced |
| L10 | pfstools 2.2.0 `src/tmo` contains drago03, durand02, fattal02, ferradans11, mai11, mantiuk06, mantiuk08, pattanaik00, reinhard02, reinhard05; no ferwerda96, Krawczyk05 or Kirk11 | pfstools-2.2.0.tgz source tree | src | H | ✅ listed; ferradans11 not built here |
| L11 | Pattanaik, Tumblin, Yee, Greenberg 2000, "Time-dependent visual adaptation for fast realistic image display", SIGGRAPH 2000 | doi:10.1145/344779.344810 | paper | H | — |
| L12 | pfstmo_pattanaik00: needs cd/m² input; `-t --fps` time dependence over frames; `--local` cancels time dependence; rod response uses photopic Y (`l=(*Y)(x,y)`) and adds achromatically; t0cone .08, t0rod .15, τcone 110, τrod 400 | pfstools-2.2.0 src/tmo/pattanaik00/{pfstmo_pattanaik00.1,tmo_pattanaik00.cpp} | doc/src | H | ✅ still + 20-frame `-t` run; NaN on negative input observed |
| L13 | Luminance HDR: last tag 2.6.1.1 (2021); maintenance commits until 2025-06-13; GPL-2; TMO list includes ferwerda96, kimkautz08, vanhateren06; CLI `--tmo`; ferwerda96 TVI uses `powf(2.18, 0.405t+1.6)` (inverted vs. paper) | https://github.com/LuminanceHDR/LuminanceHDR (src/TonemappingOperators, src/MainCli/commandline.cpp) | src | H | — |
| L14 | nixpkgs removed `luminanceHDR` (EOL Qt5 WebEngine, 2026-04-17) | nixpkgs aliases.nix; eval as for L5 | src | H | ✅ eval error reproduced |
| L15 | Ubuntu 24.04 ships luminance-hdr 2.6.1.1 and pfstools 2.2.0 | `apt-cache policy` in this container | run | H | ✅ |
| L16 | HDR Toolbox: active (2026-09-11), GPL-3; contains FerwerdaTMO (correct TVI), static PattanaikTMO, WardHistAdjTMO (histogram only), lumScotopic | https://github.com/banterle/HDR_Toolbox | src | H | — |
| L17 | Kirk & O'Brien 2011, "Perceptually based tone mapping for low-light conditions", ToG 30(4); third-party GIMP plugin by Y. J. Lee (2012, GPL, C++/libgimp2); 2.66 GB spectral raw data | doi:10.1145/2010324.1964937 ; https://objf.ai/papers/Kirk-PBT-2011-08/ (formerly graphics.berkeley.edu) | paper/src | H | — |
| L18 | Blender current stable is 5.2.2 LTS (2026-09-15); 4.5 LTS supported to 2027-07 | https://www.blender.org/download/ ; https://developer.blender.org/docs/release_notes/ | doc | H | ✅ nixpkgs `blender` = 5.2.2 LTS (`blender --version`) |
| L19 | nixpkgs blender has `cudaSupport` (CUDA + OptiX); `blender-hip` replaced by `rocmSupport` | nixpkgs pkgs/by-name/bl/blender/package.nix ; aliases.nix | src | H | — |
| L20 | Headless CLI: `blender -b f.blend -o path -F OPEN_EXR -f N -- --cycles-device CPU`; `-o` must precede `-f` | https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html | doc | H | — |
| L21 | Cycles render buffer is radiance W/(sr·m²) and RGB (not spectral) | https://developer.blender.org/docs/features/cycles/units/ | doc | H | — |
| L22 | Blender light Watts are radiant power; the manual's table (800 lm LED ≈ 2.1 W) implies ~345–380 lm/W | https://docs.blender.org/manual/en/latest/render/lights/light_object.html | doc | M (ratio computed by us) | — |
| L23 | Blender 5.0: selectable working space (Rec.709/Rec.2020/ACEScg); views AgX, Filmic, Khronos PBR Neutral, ACES 1.3/2.0 | https://developer.blender.org/docs/release_notes/5.0/color_management/ | doc | H | — |
| L24 | Fog Glow kernel = Spencer et al. 1995 Eq. 5 photopic mix (0.384 f0 + 0.478 f1 + 0.138 f2); FOV from `lerp(180°,10°,size^(1/3))` heuristic | blender source: compositor/cached_resources/intern/fog_glow_kernel.cc ; node_composite_glare.cc | src | H | — |
| L25 | Compositor Tone Map node still offers R/D Photoreceptor and Rh Simple | blender source: node_composite_tone_map.cc | src | H | — |
| L26 | Blender 5.0: null-scattering volumes default; Sky Texture "Multiple Scattering" mode (daylight) | https://developer.blender.org/docs/release_notes/5.0/cycles/ ; …/5.0/rendering/ | doc | H (sky being day-only is M) | — |
| L27 | ISET: ISETCam/ISETBio MATLAB, MIT, active 2026-09; ISET3d drives PBRT-v4 in Docker (`digitalprodev/pbrt-v4-cpu`); humaneye camera CPU-only; cMosaic cones, no rod mosaic or scotopic pathway; Octave hooks in ISETCam; isetvalidate `ieValidate` | https://github.com/ISET/isetcam ; https://github.com/isetbio/isetbio ; https://github.com/ISET/iset3d (docs/setting-up-iset3d.md, docs/sceneEye-gpu.md) ; https://github.com/ISET/isetvalidate | src/doc | H | — |
| L28 | No official Blender→PBRT-v4 exporter; third-party NicNel/bpbrt4 (Blender 4.4, 2025-04, no license file); upstream recommends assimp | https://github.com/NicNel/bpbrt4 ; https://github.com/mmp/pbrt-v4 README | doc | H | — |
| L29 | ISETHDR: 2000 spectral HDR driving scenes as separable light groups (headlights, streetlights, other lights, sky) | Liu, Shah, Wandell, IEEE Sensors J. 2025, doi:10.1109/JSEN.2025.3550455 ; arXiv:2408.12048 ; https://purl.stanford.edu/bt316kj3589 | paper/doc | H | — |
| L30 | Pattanaik, Ferwerda, Fairchild, Greenberg 1998, multiscale adaptation and spatial vision; no author code found | doi:10.1145/280814.280922 | paper | H (code absence: M) | — |
| L31 | Jacobs, Gallo, Cooper, Pulli, Levoy 2015, "Simulating the visual experience of very bright and very dark scenes", ToG 34(3); gaze-contingent; no code released | doi:10.1145/2714573 ; http://graphics.stanford.edu/papers/gazehdr/ | paper/doc | H (code absence: M) | — |
| L32 | Durand & Dorsey 2000, "Interactive tone mapping", EGWR; no code | doi:10.1007/978-3-7091-6303-0_20 | paper | M | — |
| L33 | Thompson, Shirley, Ferwerda 2002, "A spatial post-processing algorithm for images of night scenes", JGT 7(1): blue shift, blur, noise; no public code | doi:10.1080/10867651.2002.10487550 | paper | M (scanned PDF not text-read) | — |
| L34 | Krawczyk, Myszkowski, Seidel 2005, "Perceptual effects in real-time tone mapping", SCCG; no code (MPI directory 403) | doi:10.1145/1090122.1090154 | paper | H (code absence: M) | — |
| L35 | Cao, Pokorny, Smith, Zele 2008, "Rod contributions to color perception: linear with rod contrast", Vision Res. 48(26) | doi:10.1016/j.visres.2008.05.001 | paper | H | — |
| L36 | Wanat & Mantiuk 2014, "Simulating and compensating changes in appearance between day and night vision", ToG 33(4) 147; project page has PDF and result galleries, no code | doi:10.1145/2601097.2601150 ; http://luminance-retargeting.bangor.ac.uk/ | paper/doc | H | — |
| L37 | Ritschel et al. 2009, "Temporal glare", CGF 28(2); no code confirmed | doi:10.1111/j.1467-8659.2009.01357.x | paper | M | — |
| L38 | Spencer, Shirley, Zimmerman, Greenberg 1995, "Physically-based glare effects for digital images", SIGGRAPH 95 | doi:10.1145/218380.218466 | paper | H | — |
| L39 | ColorVideoVDP 0.5.7 (2026-08-02), MIT, PyTorch, CPU supported; absolute linear EXR input; display models JSON; clips input at max(0.005, Y_black); CSF LUT 0.005–10000 cd/m²; no foveation, no rods | https://github.com/gfxdisp/ColorVideoVDP (pycvvdp/display_model.py, cvvdp_metric.py, vvdp_data/) ; https://pypi.org/project/cvvdp/ | src/pkg | H | — |
| L40 | FovVideoVDP 1.2.2, CC BY-NC 4.0, achromatic, `--foveated` / `fixation_point` | https://github.com/gfxdisp/FovVideoVDP ; doi:10.1145/3450626.3459831 | src | H | — |
| L41 | HDR-VDP-3 3.0.7 (2023), BSD-style, MATLAB/Octave; models rods (`rod_sensitivity`, CIE scotopic data); CSF includes 0.002 cd/m²; no temporal | https://sourceforge.net/projects/hdrvdp/files/hdrvdp/ ; https://hdrvdp.sourceforge.net/wiki/ | src/doc | H | — |
| L42 | colour-science 0.4.7 (BSD-3): `SDS_LEFS_SCOTOPIC`, `luminous_efficiency`, `sd_mesopic_luminous_efficiency_function` (MOVE/LRC table lookup); no CIE 191:2010 m solver | https://pypi.org/project/colour-science/ ; wheel source colour/colorimetry/ | src | H | — |
| L43 | LuxPy 1.12.5 (GPL-3): `vlbar_cie_mesopic`, `get_cie_mesopic_adaptation` "according to CIE191:2010" | https://pypi.org/project/luxpy/ ; wheel source luxpy/spectrum/basics/spectral.py | src | H | — |
| L44 | CIE 191:2010, Recommended system for mesopic photometry based on visual performance | https://cie.co.at/publications/recommended-system-mesopic-photometry-based-visual-performance | paper | H | — |
| L45 | CIE 257:2026, practical application of mesopic photometry in outdoor lighting | https://www.cie.co.at/publications/recommendations-practical-application-cie-system-mesopic-photometry-outdoor-lighting | doc | H | — |
| L46 | CIE 146:2002 disability-glare equations (valid 0.1°–100°, with age and pigmentation), superseding CIE 135/1:1999 | https://cie.co.at/publications/cie-collection-glare-2002 | doc | H (contents: M, not purchased) | — |
| L47 | VSS (Stuttgart): Rust, Apache-2.0; `main` last commit 2023-03, `wgpu` branch active 2026-08; impairment simulator; nyctalopia heuristic; Østerberg rod density map | https://github.com/UniStuttgart-VISUS/visual-system-simulator ; doi:10.1109/VR44988.2019.9044164 | src | H | — |
| L48 | OpenVisSim: Unity, GPL-3, "now depreciated" per README; impairments only | https://github.com/petejonze/OpenVisSim | doc | H | — |
| L49 | PBRT-v4: Apache-2.0, point-sampled spectral, CPU default, OptiX optional, active 2026-09 | https://github.com/mmp/pbrt-v4 | doc/src | H | — |
| L50 | Mitsuba 3: 3.9.1 on PyPI (2026-08-07), BSD-3, spectral CPU variants (`scalar_spectral`, `llvm_ad_spectral`) | https://github.com/mitsuba-renderer/mitsuba3 ; https://pypi.org/project/mitsuba/ | doc/pkg | H | — |
| L51 | mitsuba-blender: Blender ≥4.2 extension, active 2026-09, wheels for Blender 5.1+ | https://github.com/mitsuba-renderer/mitsuba-blender | doc | H | — |
| L52 | HCIPy 0.7.1 (MIT): `InfiniteAtmosphericLayer`, `MultiLayerAtmosphere(scintillation=True)` | https://pypi.org/project/hcipy/ ; https://github.com/ehpor/hcipy | src | H | — |
| L53 | AOtools 1.0.8 (LGPL-3): infinite phase screens, `rytov_variance` (vertical-profile form) | https://pypi.org/project/aotools/ ; https://github.com/AOtools/aotools | src | H | — |
| L54 | Chimitt & Chan 2020, Zernike-based anisoplanatic turbulence simulation, Opt. Eng. 59(8) | doi:10.1117/1.OE.59.8.083101 | paper | H | — |
| L55 | P2S (Mao, Chimitt, Chan, ICCV 2021); public fork Riponcs/TurbulenceSimulatorPython under CC BY-NC-SA 4.0 | arXiv:2107.11627 ; https://github.com/Riponcs/TurbulenceSimulatorPython | paper/doc | H | — |
| L56 | ATSyn / DATUM (CVPR 2024): temporally correlated turbulence synthesis | arXiv:2401.04244 ; https://github.com/xg416/DATUM | paper/doc | H (no-amplitude-scintillation is inferred: M) | — |
| L57 | Plane-wave Rytov variance σ_R² = 1.23 Cn² k^(7/6) L^(11/6) | Andrews & Phillips, *Laser Beam Propagation through Random Media*, 2nd ed., SPIE 2005, doi:10.1117/3.626196 | paper | M (textbook formula, not re-read) | — |
| L58 | Fairchild HDR Photographic Survey: 106 EXRs with absolute luminance calibration; McKeesPub multiplier ×6.25; research and non-commercial license | http://markfairchild.org/HDR.html ; http://markfairchild.org/HDRPS/HDRcharacterization.html | doc | H (multiplier from scene page: M) | ✅ downloaded and processed |
| L59 | Poly Haven night HDRIs are CC0 and unclipped but carry no absolute-luminance calibration | https://polyhaven.com/license ; https://docs.polyhaven.com/en/technical-standards/hdris | doc | M | — |

## Observations from runs in this repository

These are *our* measurements, not claims from any source.

| ID | Observation | How to reproduce | Conf. |
|---|---|---|---|
| R1 | Radiance master bcffc2b and pfstools 2.2.0 build under nixpkgs 26.11pre (GCC 15) with the flags in `nix/*.nix` | `nix build .#radiance .#pfstools` | H |
| R2 | `pcond -s -c`: Purkinje probe (red and blue at equal Y = 0.03 cd/m²) → display grey 0.33 and 0.74; landscape fully achromatic | `m0/run_m0.sh`, `sheet_purkinje_probe.png` | H |
| R3 | `pcond -a` produces horizontal bar artefacts on chains of sub-pixel lamps | `l_pcond_acuity_only.png` | H |
| R4 | `pcond -v` makes a broad, blotchy veil (1° grid) around the lamp chain | `k_pcond_veil_only.png` | H |
| R5 | pcond and pattanaik00 output (1,1,1) at lamp pixels: warm hue lost inside the operator (checked on float output) | inspect `m0/out/tmp/*.hdr` | H |
| R6 | pattanaik00 outputs NaN (white frame) if any input pixel is negative; resizing with Lanczos creates negatives | see `m0/fetch_fairchild.sh` comment | H |
| R7 | pattanaik00 `-t --fps 1`, bright frame then 19 dusk frames: mean display value 0.405 → 0.421 (slow drift), static render 0.276; transient direction not validated | README M0 temporal smoke test | M |
| R8 | Order-of-magnitude CIE 146 check: about 200 lamps of ~1e-4–6e-4 lux each at the eye → E ≈ 0.02–0.1 lux → L_veil ≈ 10·E/θ² ≈ 0.1–1 cd/m² at θ = 1°, i.e. ≫ the 3e-4 cd/m² field. Veiling glare should dominate near the ribbon | hand calculation | L–M |
