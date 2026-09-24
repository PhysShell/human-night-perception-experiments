# Donor E: iCAM06, input contract

**Classification: GENUINE_ORIGINAL_CODE, RUN** (the original MATLAB code, run in GNU Octave 11.3 with trivial shims; no algorithm file edited)

Reference: J. Kuang, G. M. Johnson, M. D. Fairchild, "iCAM06: A refined image appearance model for HDR image rendering", J. Vis. Commun. Image R. 18(5), 406-414, 2007.

## Sources opened

| What | URL | Finding |
|---|---|---|
| RIT MCSL iCAM06 page (live) | https://www.rit.edu/cos/colorscience/re_iCAM06.php | now redirects to a generic MCSL page with no code link |
| Same page, Wayback copy | https://web.archive.org/web/20190320142121/https://www.rit.edu/cos/colorscience/re_iCAM06.php | "Source Code: The iCAM06 model is currently implemented in Matlab ... All of the files and example data can be downloaded here", linking `http://www.rit-mcsl.org/StudentResearch/iCAM06_V1.3.zip` |
| Code zip (live, still served by RIT MCSL, Last-Modified 2014-03-19) | http://www.rit-mcsl.org/StudentResearch/iCAM06_V1.3.zip | 1 059 691 bytes |
| Same zip, Wayback 2022-08-14 | https://web.archive.org/web/20220814154715id_/http://www.rit-mcsl.org/StudentResearch/iCAM06_V1.3.zip | byte-identical: sha256 `b26a0231bda9e74f0578ccbb43cbe22c0e588f3a442c1f3f7f622d71e6e5d4c3` |
| Paper (author copy) | http://markfairchild.org/PDFs/PAP26.pdf | read §2.1 (input) and §2.6 (surround, Eq. 27) |
| Descendants that were seen but not used | github.com/Jackchou00/icam-python, github.com/mdouchement/hdr (tmo/icam06.go), github.com/jackyhkust/iCAM_HDR | ports or re-implementations. The original is available, so none of these is needed. |

**Provenance.** The code is iCAM06 V1.3. Its `Readme.txt` was last updated 2007-08-06 and credits Jiangtao Kuang and Mark Fairchild, with the `www.cis.rit.edu/mcsl/icam06` URL. The helper files are by L. Taplin and G. M. Johnson (MCSL), and the bilateral filter is by Kuang and H. Yamaguchi. It is the authors' own distribution, linked from the lab page.
**Licence.** No licence file is included. The authors distribute it publicly for research, but the terms are unstated. It is kept only under the git-ignored `d0/work/donors/icam06/`, so do not commit it or redistribute it.

## What the method expects (input semantics)

- **Input.** CIE XYZ in **absolute cd/m^2** (paper §2.1: "absolute luminance Y ... is necessary to predict ... Hunt effect and Stevens effect"). The code takes linear RGB and converts it with the sRGB/Rec.709 D65 matrix (`iCAM06_HDR.m`, lines 44-47).
  - Our inputs (linear Rec.709/D65 float, Y in cd/m^2) are exactly this, so **no pixel conversion is needed**. The EXR is passed to Octave as raw float32, bit-exact.
- **`max_L`.** The default `20000` rescales the image so that its maximum Y is 20 000 cd/m^2. `max_L = 0` keeps the input as absolute luminance (Readme: "the original images were stored as physical luminance data, leave max_L = 0").
- **`p`.** Overall contrast. The default is 0.7 (0.6-0.85).
- **`gamma_value`.** Bartleson surround exponent on IPT I. The sources disagree:
  - The code Readme lists average 1.0, dim 1.1, dark 1.2, but its header line also says "gamma_value = 1 (for dark surround)".
  - The paper's Eq. 27 gives c_dark = 1.5, c_dim = 1.25, c_average = 1.0.
  - Both documented dark values were run.
- **Display side.** None of these enter the model: display peak, display black, ambient light or viewing geometry (px/deg). The spatial filters scale with **image size** (bilateral sigma_s = 2 % of the width; Gaussian white = image dim / 2 or / 3), not with visual angle.
  - The output stage (`iCAM06_disp.m`, sRGB branch) normalises XYZ to the image maximum. It then **clips the 1st/99th percentiles of RGB to 0/1**, applies the sRGB OETF and returns `uint8`.
  - The output is therefore a relative, full-range sRGB image. The absolute scene level (for example the 0.47 cd/m^2 maximum of S0) only reaches the display through the model's luminance-dependent appearance terms: FL, rod response, Hunt and Stevens.
- **Low-luminance floor (important for night scenes).**
  - `fastbilateralfilter.m` clamps each XYZ channel to **>= 1e-4 cd/m^2** before the log-domain base/detail split.
  - With `max_L = 0`, **51.7 % of S0/S1 pixels have Y < 1e-4 cd/m^2**. Their base and detail become flat, and the dark ground renders as a uniform tone. The S3 sky is 4e-4 and S4/S5 have 0 % below the floor, so they are unaffected.
  - The NATIVE_DEFAULT (`max_L = 20000`) avoids the floor by discarding the absolute scale.
  - The rod term (`iCAM06_TC.m`) exists but is a simplified Hunt-model rod response, not a scotopic spectral input.

## Shims (all trivial, all in `d0/work/donors/icam06/shim/`, placed ahead of the pristine source on the Octave path)

| Shim | Why |
|---|---|
| `computer.m` returns `'PCWIN'` | The code picks its output branch with `strcmp(computer,'PCWIN')`, and any other OS gets the author's Apple HD Cinema LCD profile. `'PCWIN'` selects the author's documented **sRGB** branch unchanged. |
| `interp1q.m` returns `interp1(x,y,xi)` | Octave 11 lacks MATLAB `interp1q`. The shim is the same linear operation, with NaN outside the range. It is used only in `percentile()`. |
| `figure.m`, `imshow.m` (no-op) | Headless Octave has no graphics toolkit. `iCAM06_HDR` ends with a preview `figure; imshow(outImage)`. |
| `cmatrix.m`, `changeColorSpace.m` | The originals use classic-Mac CR line endings (Octave would read each as one comment line). Only CR was changed to LF. |
| `idl_dist.m` | The original is `IDL_DIST.M` (upper-case name, invisible on a case-sensitive file system). The content is identical. |

## Native example (run first)

Readme example `iCAM06_HDR(read_radiance('PeckLake.hdr'), 20000, 0.7, 1)` gives 697x443, uint8, 2.7 s. It matches the published iCAM06 PeckLake look.
Evidence: the 8-bit native output (sha256 `3c8d0b77...`) is kept in `d0/work/nocommit/` only: PeckLake.hdr is from the Fairchild HDR Photographic Survey (non-commercial research licence), whose derived files this project does not commit.

## Runs (outputs: `d0/work/out/icam06/<config>/<scene>__PHONE_SDR100_DARK.png`, log: `d0/work/out/icam06/runs.json`)

Driver: `nix develop -c python3 d0/work/donors/icam06/run_all.py`, which calls `tracks/hdrvdp3/octave.sh d0/work/donors/icam06/run_scene.m`.
Scenes: S0, S1, S3_bar, S3_nobar, S4, S5. **S2 was skipped** because iCAM06 is a still-image model with per-frame percentile normalisation and no temporal adaptation.

| config | label | call |
|---|---|---|
| `native_default` | NATIVE_DEFAULT | `iCAM06_HDR(img)`, i.e. max_L=20000, p=0.7, gamma_value=1 |
| `target_abs_dark_readme` | DOCUMENTED_TARGET_CONFIG | `iCAM06_HDR(img, 0, 0.7, 1.2)`: absolute input, Readme "dark" |
| `target_abs_dark_paper` | DOCUMENTED_TARGET_CONFIG | `iCAM06_HDR(img, 0, 0.7, 1.5)`: absolute input, paper Eq. 27 c_dark |

**ADAPTED conversions (exact list):**
1. EXR to raw float32 H x W x 3, loaded into Octave as double. The values are unchanged. The alpha channel, if any, is dropped.
2. The native `uint8` sRGB code values from the author's sRGB branch are written as a **16-bit PNG with code16 = code8 x 257**. This changes the container only, and every native 8-bit level is preserved exactly.
   - Code 0 is the author's 1st-percentile clip, which maps to display black under SDR100.
   - The output is identical for any display geometry or peak that uses sRGB encoding. It is labelled PHONE_SDR100_DARK because the display model decodes it that way (`d0/display_model.py`), not because iCAM06 used those values.

No iCAM06 parameter or equation was changed. Runtime was 3-15 s per scene on CPU, and peak memory stayed well under 2 GB.
