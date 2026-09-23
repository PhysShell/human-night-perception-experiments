# Track `openvissim` — OpenVisSim (Pete R. Jones et al., Unity3D sight-loss simulator, deprecated)

## IDENTITY
- Official repository: https://github.com/petejonze/OpenVisSim, commit `4394bc436d96542db413cb650a965d6abaf76e0b`
  (2021-08-17, 12 commits total), cloned to `research-cache/openvissim/OpenVisSim` (gitignored; `.git` and the 141 MB `Assets/Demo2_TobiiViveZEDm` vendor plugins removed afterwards to save disk).
- Status: **deprecated** by the author (README "UPDATE: 17/08/2021 ... OpenVisSim is now depreciated", successor VARID announced).
- License: GNU GPL v3.0 (`LICENSE.txt`, "Copyright (c) 2015, Pete R Jones"). Note a discrepancy: the npj paper
  Methods say the code "is free for non-commercial use" (`research-cache/openvissim/papers/npj2020.txt` l.345-346 and l.419);
  the repository license file (GPLv3) governs the code. GPLv3 = copyleft: no code copied into this repo's tracks/.
  The Unity project also bundles Unity "Standard Assets" image effects, FOVE/SteamVR/Tobii/ZED plugins (own licenses).
- Papers:
  1. Jones, Somoskeöy, Chow-Wing-Bom & Crabb, *Seeing other perspectives: evaluating the use of virtual and augmented
     reality to simulate visual impairments (OpenVisSim)*, npj Digital Medicine 3:32 (2020), doi:10.1038/s41746-020-0242-6
     (open access CC BY 4.0; fetched: `research-cache/openvissim/papers/npj2020.pdf`, `.txt`).
  2. Jones & Ometto, *Degraded Reality: Using VR/AR to simulate visual impairments*, IEEE VAR4Good 2018,
     doi:10.1109/VAR4GOOD.2018.8576885 (technical details; author PDF BLOCKED, see FAILURES).

## PURPOSE
Gaze-contingent, per-eye post-processing library to **simulate symptoms of eye disease** (glaucomatous field loss
from perimetry, AMD in-filling, metamorphopsia/warping, colour loss, glare, floaters, nystagmus, noise, double
vision) in VR/AR headsets, for empathy/accessibility/health-economics studies (paper Fig. 1, Methods "Simulated VFL").
It is an **impairment simulator, not a normal-eye model** (H3): with all effects off the image is passed through
unchanged; no effect models healthy optics, adaptation, rods/cones or night vision. README: "OpenVisSim is not suitable
for simulating refractive error".

## HVS COMPONENTS
| component | present? | where |
|---|---|---|
| optics | NO physical optics. `myBlur` = Gaussian blur specified by a max-CPD "acuity" value converted with `screenWidth_px / viewingAngle_deg` (defaults 2560 px / 80°) | `Assets/VisualEffects/Scripts/myBlur.cs` l.15-32, l.65-70 |
| glare | `myBloom` (impairment "glare"): LDR bright-pass `max(color/4 - threshold, 0) * intensity` (threshold 0.25, intensity 0.75), blurred, added | `Assets/VisualEffects/Shaders/myBloom.shader` l.24-25, l.80-96; `Scripts/myBloom.cs` l.22-25, l.46-80 |
| adaptation | NO (only a manual brightness/contrast/gamma effect) | `Shaders/myBrightnessContrastGamma.shader` l.38 |
| rods/cones, mesopic/scotopic | NO | |
| acuity / field | field loss: perimetry grid (e.g. 24-2 dB values) → RBF interpolation (alglib) → 128×128 overlay covering ±55° → mip-map LOD bias blur per pixel | `Scripts/GridInterpolator.cs` l.20-33, l.250-306; `Shaders/myFieldLoss.shader` l.98-114; paper Fig. 1b |
| temporal state | only effect animations (`Time.deltaTime` timers in floaters, nystagmus, noise, wiggle) — not visual adaptation | `Scripts/myFloaters.cs` l.74; `myNystagmus.cs` l.78; `myNoise.cs` l.98; `myWiggle.cs` l.41 |
| gaze | YES: `GazeTracker` singleton, sources Fove / Tobii / Mouse / None, normalized screen coords `xy_norm`; field-loss overlay shifted by gaze each frame | `Assets/Scripts/GazeTracker.cs` l.8-20, l.78-150 (Tobii: average of L/R gaze directions), l.161-170 (mouse), l.172-175 (none = centre); `myFieldLoss.cs` l.105-108; `myFieldLoss.shader` l.99-101 |
| binocular / per-eye | YES: every effect is a `LinkableBaseEffect` on both the `LeftEye` and `RightEye` tagged cameras; `LinkEyes` copies `[Linkable]` fields from left to right by reflection each frame; per-eye projection offset hack in shader | `Scripts/LinkableBaseEffect.cs` l.20, l.40-77, l.91-130; `myFieldLoss.shader` l.99 comment "pretty sure this is a really stupid hack" |
| display model | NO (Unity LDR camera render texture / webcam / stereo camera passthrough) | `Scripts/VisSimController.cs` l.19-28 (content = webcam, spherical image, ovrvision) |
| spectrum | NO (RGB; colour loss via recolouring) | `Scripts/myRecolour.cs` |

## NATIVE ENVIRONMENT
Unity 2017.4.1f1 (README "Programming language"), open `Demo1_Fove/MainScene.unity`, press Play; mouse simulates gaze;
optional FOVE0 / HTC Vive + Tobii / ZED mini for AR (Demo2). Windows/macOS Unity Editor with a GPU.

## NATIVE REPRODUCTION
- Exact example: `OpenVisSim_ExampleUnityProject/Assets/Demo1_Fove/MainScene.unity` (binary-serialized scene) in the
  Unity Editor, mouse gaze.
- Command: none (interactive Editor). Per track instructions no Unity install and no porting.
- Result: **BLOCKED** (by instruction: no Unity; also no GPU/display here).
- NATIVE reference captured: `results/native/openvissim/NATIVE_npj2020_Fig1_published.png` = Fig. 1 of the npj
  Digital Medicine paper (CC BY 4.0), downloaded from
  `https://media.springernature.com/lw1200/springer-static/image/art%3A10.1038%2Fs41746-020-0242-6/MediaObjects/41746_2020_242_Fig1_HTML.png`.
  Panel C "glare" shows the LDR bloom washing a bright clinic room toward white — the only glare-like depiction.
  Author video: http://www.youtube.com/watch?v=LEGkGHwb_Fw (README; not downloaded).

## COMMON STIMULUS
Not applicable / not run: NATIVE BLOCKED; and OpenVisSim is an LDR impairment filter set with no normal-eye
configuration (its neutral configuration is identity), so feeding S0-S7 would produce either the input or a disease.

## ASSUMPTIONS
- Input: LDR 8-bit camera/webcam/rendered image; no cd/m^2, no absolute scale.
- Geometry: headset FOV guesses (`GridInterpolator.cs` l.23-30 "rough estimates!", ±55°), `myBlur` 2560 px / 80°;
  `_ViewDist_m = 2.4815` in `myFieldLoss.shader` l.17.
- Display: none modelled.

## VALIDATION
Behavioural only: 19 normally sighted participants in a VR search task and 4 in an AR mobility task with simulated
superior/inferior glaucomatous VFL; search 74 % / 125 % slower (paper Results, `npj2020.txt` l.95-99). Face validity
of the image appearance vs patient reports is argued, not measured. Nothing validates glare or night vision.

## REUSE (H4) — concepts only (GPLv3 code not copied)
- Gaze-contingent rendering: a single normalized gaze point per frame drives per-pixel lookups of a retina-fixed
  map (`myFieldLoss.shader` l.99-101) — the right abstraction if eccentricity-dependent PSF/acuity is needed.
- Post-process ordering: each effect is a Unity `OnRenderImage` component; the order of components on each eye
  camera is the processing order (an editor helper `Assets/Editor/ReorderMyComponents.cs` exists to reorder them).
  The actual order in the demo scene is stored in the binary `MainScene.unity` and could not be read without Unity.
- Binocular handling: two cameras tagged LeftEye/RightEye, parameters linked via reflection (`LinkableBaseEffect`).
- Retina-fixed maps from clinical grid data (RBF interpolation) — reusable idea for any eccentricity map.
- Not reusable for physics: glare is an LDR threshold bloom; no PSF, no radiance.

## FAILURES / SURPRISES
- Author PDF of the 2018 VAR4Good paper: `https://www.ucl.ac.uk/~smgxprj/pdfs/jones_IEEE_2018` → HTTP 403 with a
  Cloudflare "Just a moment..." challenge. BLOCKED (not routed around).
- Scene files are Unity binary serialization (`file` reports "data"), so post-process order and enabled effects in
  the demo could not be audited.
- The "glare" effect thresholds the LDR frame at 0.25 of the downsampled value (`myBloom.shader` l.96), i.e. it acts
  on already clipped display values.
- License statement mismatch GPLv3 (repo) vs "free for non-commercial use" (paper).

## BRIGHT POINT SOURCE
1. Where a PSF is applied: none physical. Closest: `myBloom` bright-pass + blur + add on the LDR camera image (post-render, post-display-encoding); `myBlur` Gaussian.
2. Before/after adaptation: not applicable (no adaptation).
3. Before/after tone reproduction: after (inputs are LDR camera/render textures).
4. Energy preserved: no (bloom is additive, `color + tex2D(_Bloom, uv)`, `myBloom.shader` l.80/85).
5. Absolute-luminance aware: no.
6. PSF dependence on adaptation/pupil/age/wavelength/field angle: none; blur amount depends on gaze-relative field position only in the field-loss effect (disease map).
7. HDR source on LDR display: not handled; everything is LDR.
8. Halo changes perceived brightness: not modelled.
9. Temporal PSF variation: no; only animated impairment effects (floaters, nystagmus, noise).
10. Clip before or after convolution: clip BEFORE (bloom thresholds already-clipped LDR values).

## VERDICT
**HISTORICAL REFERENCE** (deprecated impairment simulator; infrastructure ideas for gaze-contingent, per-eye
post-processing only). Not a normal-vision model; NATIVE BLOCKED by instruction (no Unity).
