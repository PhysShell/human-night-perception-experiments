# Donor A: pcond, the frozen V0 display path (historical perceptual baseline)

**Implementation.** Radiance `pcond -s -c` (Ward Larson, Rushmeier & Piatko 1997: human sensitivity and colour
loss; histogram adjustment, veiling glare off, acuity off in this path), wrapped by `m1/pcond_colorimetric.sh LC`.
Radiance comes from the project's own build, `nix/radiance.nix`.

**Display step.** Khronos PBR Neutral on out-of-gamut pixels, sRGB Standard elsewhere (Blender 5.2.2's OCIO config
via oiiotool). This is the M2.6 `frame()` stack. **It is run unchanged** by `d0/donors/pcond/run.sh`.

**Input contract**
- Units: linear Rec.709/D65 RGB, Y in cd/m². pcond needs Radiance radiometric units (W sr⁻¹ m⁻², luminance =
  179 Y).
  - `SCALE = 1/179` for `d0/work/inputs`.
  - The frozen M2.6 stack used SCALE 1 on raw Cycles output (Cycles authored with the 179 lm/W convention).
  - So pcond receives the same numbers. ADAPTED only in this bookkeeping sense.
- Viewing geometry: pcond's HFOV = image width / *scene* px/deg (60° for S0–S2, 12° for S3, 32° for S4, ~75° for
  S5). pcond models the eye looking at the *scene*. It knows nothing about the phone.
- Colour: LC composition, i.e. luminance from pcond on XYZE input and chromaticity from pcond's unclipped RGB
  result (`m1/README.md` §4).

**Display assumptions and configurations**

| config | label | pcond display | encoding | scenario |
|---|---|---|---|---|
| native_default | NATIVE_DEFAULT | defaults: Ldmax 100 cd/m², 100:1 range | sRGB (the frozen display step) | SDR100 |
| target_SDR200 | DOCUMENTED_TARGET_CONFIG | `-u 200 -d 1000` | frozen sRGB step, then re-encoded ^(1/2.2) | SDR200 |
| target_BRIGHT500 | DOCUMENTED_TARGET_CONFIG | `-u 500 -d 100000` | as above | BRIGHT500 |

- Not supported: HDR1000 (pcond has no PQ/HDR output) and ambient (pcond has no reflected-light term).
- pcond's own internal display model (100:1, black 1 cd/m² in the default) differs from SDR100's 0.1 cd/m² black.
  The common decoder (`d0/display_model.py`) uses the scenario's black for every donor.
- The clip S2 is run frame by frame. pcond adapts per frame; the exposure it chose is logged per frame
  (`*.expo`).
