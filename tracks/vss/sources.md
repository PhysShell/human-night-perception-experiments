# Sources — vss

Repo paths relative to `research-cache/vss/visual-system-simulator` (branch wgpu, commit 22055373eccf4b50220df8f6f57751851ed34e8c).

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| S1 | Repository, Apache-2.0, features, wgpu branch `render` subcommand | https://github.com/UniStuttgart-VISUS/visual-system-simulator ; `README.md` (wgpu), `LICENSE` | code/doc | high |
| S2 | IEEE VR 2019 paper; no full user validation; PSO parameters not always plausible; HDR hoped for glare | doi:10.1109/VR44988.2019.9044164 ; https://www.vis.uni-stuttgart.de/documentcenter/staff/sedlmaml/papers/schulz2019deficiencySim.pdf ; `research-cache/vss/papers/schulz2019.txt` l.305-313, 327-329, 338-340 | paper | high |
| S3 | Node order Cataract → Lens → Retina → Peacock → Display | `vss-desktop/src/flow.rs` l.395-407 | code | high |
| S4 | Lens eye model constants from PSO | `vss/src/node/lens/lens_model.wgsl` l.1-33 | code | high |
| S5 | Lens ray tracing, defocus hack, 8-ray averaging (WGSL switch) | `vss/src/node/lens/mod.wgsl` l.249-314, 342-406 | code | high |
| S6 | Lens inactive unless presbyopia/refraction enabled | `vss/src/node/lens/mod.rs` l.293-341 | code | high |
| S7 | Nyctalopia = darkening of pixels with 5Y<1 weighted by rod map | `vss/src/node/retina/mod.wgsl` l.191-220; `retina_map/nyctalopia.rs` l.9-19 | code | high |
| S8 | Retina identity when no map feature is on | `vss/src/node/retina/mod.rs` l.439-446; `retina_map/mod.rs` l.161-168 | code | high |
| S9 | Østerberg cone/rod densities | `vss/src/node/retina/retina_map/osterberg.rs`; `doc/receptor-density/osterberg-digitized.csv` | data | high (provenance as stated by authors) |
| S10 | Cataract = blur + bloom + contrast | `vss/src/node/cataract/mod.wgsl` l.15-40, 97-150; `vss/src/node/common.wgsl` l.1-60, 145-182 | code | high |
| S11 | Peacock CVD derived from jkulesza/peacock | `vss/src/node/peacock/mod.wgsl` l.1 | code | high |
| S12 | Input decoded to 8-bit RGBA; uploaded as Rgba8Unorm | `vss/src/node/rgb_buffer/upload.rs` l.133-141, l.223 | code | high |
| S13 | Headless render target Rgba8UnormSrgb (double encode) | `vss-desktop/src/cmd/render.rs` l.222; contrast `vss/src/surface.rs` l.42 | code + measurement (`results/native/vss/native_run.log`) | high |
| S14 | Hemeralopia preset is an illustrative approximation, no adaptation | `vss-catalog/articles/hemeralopia/hemeralopia.md` l.18-20 | doc | high |
| S15 | Published nyctalopia teaser (old OpenGL version, 2019) | `doc/teaser-nyctalopia.jpg` (commit eda52b5, 2019-03-23) | image | high (provenance), parameters unknown |
| S16 | Mesa lavapipe device used | `vulkaninfo --summary`: llvmpipe (LLVM 21.1.8), Mesa 26.2.3 | measurement | high |
