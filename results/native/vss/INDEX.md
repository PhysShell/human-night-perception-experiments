# results/native/vss — index

Produced by `tracks/vss/run_native.sh` (VSS wgpu 22055373, headless `vss-desktop render`, Mesa lavapipe), converted
PNG → JPEG q92 afterwards for size (identity metrics were computed on the PNGs before conversion).
Inputs: bundled `assets/*.png`; configs: bundled `vss-catalog/presets/**.json`; "vss" = no config (normal eye).

| label | files | note |
|---|---|---|
| NATIVE | NATIVE_<asset>.<preset>.jpg | raw VSS output (carries the extra sRGB encode of the batch render path) |
| ADAPTED | ADAPTED_<asset>.<preset>.srgbfix.jpg | same, one sRGB encode undone by `tracks/vss/undo_extra_srgb.py` (format conversion only) |
| NATIVE (published) | NATIVE_published_teaser-nyctalopia.jpg | `doc/teaser-nyctalopia.jpg` from the repo (Apache-2.0), old OpenGL version, settings unknown |
| log | native_run.log, identity_check.txt | timings, oiiotool diffs, identity check of the normal eye |

Impairment outputs (cataract, myopia, nyctalopia) are impairment simulations, NOT normal vision.
