# Sources — openvissim

Repo paths relative to `research-cache/openvissim/OpenVisSim/OpenVisSim_ExampleUnityProject` (commit 4394bc436d96542db413cb650a965d6abaf76e0b) unless stated.

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| O1 | Official repo, deprecated 2021-08-17, GPLv3, Unity 2017.4.1f1, demo scene, mouse gaze | https://github.com/petejonze/OpenVisSim ; `README.md`, `LICENSE.txt` | code/doc | high |
| O2 | npj Digital Medicine 2020 paper, doi:10.1038/s41746-020-0242-6, CC BY 4.0; VR search + AR mobility experiments; gaze-contingent VFL blur from perimetry | https://www.nature.com/articles/s41746-020-0242-6 ; `research-cache/openvissim/papers/npj2020.txt` l.95-115, l.318-400 | paper | high |
| O3 | Paper states code "free for non-commercial use" (conflicts with GPLv3 file) | `npj2020.txt` l.345-346, l.419 | paper | high |
| O4 | Fig. 1 (field loss, glare, warping, in-filling, colour loss) | https://media.springernature.com/lw1200/springer-static/image/art%3A10.1038%2Fs41746-020-0242-6/MediaObjects/41746_2020_242_Fig1_HTML.png → `results/native/openvissim/NATIVE_npj2020_Fig1_published.png` | image | high |
| O5 | VAR4Good 2018 paper, doi:10.1109/VAR4GOOD.2018.8576885 (author PDF 403 Cloudflare) | https://www.ucl.ac.uk/~smgxprj/pdfs/jones_IEEE_2018 | paper | citation only |
| O6 | Gaze sources and normalized gaze point | `Assets/Scripts/GazeTracker.cs` l.8-20, l.78-150, l.161-175 | code | high |
| O7 | Per-eye effects, LinkEyes reflection copy | `Assets/VisualEffects/Scripts/LinkableBaseEffect.cs` l.13-77, l.91-130 | code | high |
| O8 | Effects are OnRenderImage post-processes (BaseEffect after Thomas Hourdel) | `Assets/VisualEffects/Scripts/BaseEffect.cs` l.1, l.64-78 | code | high |
| O9 | Field loss: gaze-shifted overlay → mip LOD bias | `Assets/VisualEffects/Shaders/myFieldLoss.shader` l.17, l.98-114; `Scripts/myFieldLoss.cs` l.96-121 | code | high |
| O10 | Perimetry grid RBF interpolation, ±55° rough FOV | `Assets/VisualEffects/Scripts/GridInterpolator.cs` l.20-33, l.250-306 | code | high |
| O11 | Glare = LDR bright-pass bloom (threshold 0.25, intensity 0.75), additive | `Assets/VisualEffects/Shaders/myBloom.shader` l.24-25, l.80-96; `Scripts/myBloom.cs` l.22-25 | code | high |
| O12 | Blur by max CPD, 2560 px / 80° default | `Assets/VisualEffects/Scripts/myBlur.cs` l.15-32, l.65-70 | code | high |
| O13 | Temporal animated effects | `Scripts/myFloaters.cs` l.74; `myNystagmus.cs` l.78; `myNoise.cs` l.98; `myWiggle.cs` l.41 | code | high |
| O14 | Content sources webcam / spherical image / ovrvision | `Assets/Scripts/VisSimController.cs` l.19-28 | code | high |
| O15 | Demo scenes are binary-serialized (order of effects not auditable without Unity) | `Assets/Demo1_Fove/MainScene.unity` (`file`: data) | data | high |
| O16 | Author video | http://www.youtube.com/watch?v=LEGkGHwb_Fw | video | not viewed |
