# Sources — vissimframework

Repo paths are relative to `research-cache/vissimframework/VisSimFramework` (commit 274ca986d695da1694975213b82e90bdab3d8dde).

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| V1 | Repository, BSD-2-Clause, requirements (VS2019, OpenGL 4.3, MATLAB R2020b, TF 2.5), SharePoint third-party archives | https://github.com/csobaistvan/VisSimFramework ; `README.md`, `LICENSE` | code/doc | high |
| V2 | CGF 2021 tiled PSF splatting paper, doi:10.1111/cgf.14267 (PDF 403 from Wiley) | https://doi.org/10.1111/cgf.14267 | paper | high (citation), not read |
| V3 | CITDS 2022 ENZ GPU PSF paper, doi:10.1109/CITDS54976.2022.9914232 | https://doi.org/10.1109/CITDS54976.2022.9914232 | paper | high (citation), not read |
| V4 | VCIBA 2023 survey, open access | https://doi.org/10.1186/s42492-023-00132-9 ; `research-cache/vissimframework/papers/vciba2023.pdf` | paper | high |
| V5 | TVC 2024 peripheral aberrations + NN personalization; evaluation by PSNR vs ground truth and prior methods | https://doi.org/10.1007/s00371-023-03060-0 ; `research-cache/vissimframework/papers/tvc2024.txt` l.1-36 | paper | high |
| V6 | TiledSplatBlur render callbacks in HDR and LDR effect phases; precondition by `m_inputDynamicRange` | `Source/Scene/Components/Aberration/TiledSplatBlur.cpp` l.11-16, l.1908-1920 | code | high |
| V7 | Demo default input dynamic range = LDR; maxCoC 80; crop 0.99; FrontToBack; 3 wavelengths | `TiledSplatBlur.cpp` l.2662-2844 (l.2687, 2700, 2738) | code | high |
| V8 | Tone map order: tone map runs after "Effects (HDR) [End]"; output `saturate(linearToSrgb(color))` | `Source/Scene/Components/Settings/RenderSettings.cpp` l.34-35; `Assets/Shaders/OpenGL/PostProcessing/ToneMap/tonemap_fs.glsl` l.30-34 | code | high |
| V9 | G-buffer is RGBA16F in demo | `Source/Demo/Demo.cpp` l.116; `RenderSettings.cpp` l.855-869 | code | high |
| V10 | Fragment colour read from G-buffer, packed as half floats | `Assets/Shaders/OpenGL/Aberration/TiledSplatBlur/fragment_buffer_build_cs.glsl` l.19; `TiledSplatBlur/common.glsl` l.233-238 | code | high |
| V11 | Accumulation modes and final normalization | `TiledSplatBlur/convolution_cs.glsl` l.299-331, l.394-399 | code | high |
| V12 | PSF weight clamp and alpha rescale | `TiledSplatBlur/PSF/common.glsl` l.441-476, l.555-561 | code | high |
| V13 | PSF crop to 99 % energy then normalize to unit sum | `Source/Scene/Components/Aberration/WavefrontAberration.cpp` l.1976-1989, l.2010-2013, l.2854-2872 | code | high |
| V14 | Default wavelengths 612/549/464 nm | `WavefrontAberration.h` l.202 | code | high |
| V15 | Healthy preset = piston only, 5 mm, 587.56 nm | `Assets/Aberrations/healthy.abp` | data | high |
| V16 | Default -aberration healthy; -fov 60; -aperture 5.0; -focus 8.0 | `WavefrontAberration.cpp` l.5772-5778; `Source/Scene/Components/Rendering/Camera.cpp` l.537-557 | code | high |
| V17 | Schematic eye after Escudero-Sanz & Navarro in MATLAB eye reconstruction (modified Optometrika) | `Assets/Scripts/Matlab/EyeReconstruction/EyeParametric.m` l.3; README "Code organization" | code | high |
| V18 | Ground-truth component also defaults to LDR, disables tone mapper for HDR input | `Source/Scene/Components/Aberration/GroundTruthAberration.cpp` l.2010-2022, l.2592 | code | high |
| V19 | Published screenshots (healthy off-axis San Miguel/Sponza, myopia) | `Docs/*.png`, copied to `results/native/vissimframework/` | image | high (provenance), low (no parameters stated beyond file names) |
| V20 | Tone mapper auto exposure / exponential adaptation defaults | `Source/Demo/Demo.cpp` l.295-349 | code | high |
