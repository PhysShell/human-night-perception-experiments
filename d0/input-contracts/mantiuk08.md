# D0 donor B: Display Adaptive Tone Mapping (pfstmo_mantiuk08): input contract

Mantiuk, Daly, Kerofsky 2008, "Display Adaptive Tone Mapping", ACM TOG 27(3):68, DOI 10.1145/1360612.1360667.
This is the authors' own open implementation, `pfstmo_mantiuk08` from **pfstools/pfstmo 2.2.0**. We run it unmodified.
We are not ranking it and we did not tune it by eye. This file records what the tool expects and what we give it.
§1–§4, §6 and §7 and the mechanism in §5 come from the source, the man page and the paper. The concrete numbers in §5 and §8 were added after the runs. They are descriptive and were not used to choose any parameter: the anchor rule is set from the tool's semantics, and the sweep values are fixed log steps.

## 1. Provenance

| item | value |
|---|---|
| release | pfstools 2.2.0, `https://downloads.sourceforge.net/project/pfstools/pfstools/2.2.0/pfstools-2.2.0.tgz` (fetched as `mirror://sourceforge/pfstools/pfstools/2.2.0/pfstools-2.2.0.tgz`), sha256 `9bf6844985663226c21998eeb43c261acb8e4b3891b9a91b729554406289d7ca` |
| build | `nix/pfstools.nix` in the repo flake (`nix develop` puts `pfstmo_mantiuk08`, `pfstmo_reinhard02`, `pfsinpfm`, `pfsinrgbe` on PATH). nixpkgs dropped pfstools. The build turns off OpenEXR, ImageMagick, Qt, GL, MATLAB and Octave, so the OpenEXR reader `pfsinexr` is **not built**. |
| licence | pfstools is LGPL-2.1+ (`COPYING`). The pfstmo operators, including `mantiuk08/*.cpp` and `reinhard02/*.cpp`, carry GPL-2.0-or-later headers. We copied no donor source into the repo. |
| paper | author copy at `https://www.cl.cam.ac.uk/~rkm38/pdfs/mantiuk08datm.pdf`. The project page `resources.mpi-inf.mpg.de/hdr/datmo/` returns 403. |
| man page | `https://pfstools.sourceforge.net/man1/pfstmo_mantiuk08.1.html`. It documents the **git head**, which is newer than 2.2.0 (see §6). The 2.2.0 page is in the tarball: `src/tmo/mantiuk08/pfstmo_mantiuk08.1`. |
| source read | `src/tmo/mantiuk08/{pfstmo_mantiuk08.cpp, display_adaptive_tmo.cpp, display_function.cpp, display_size.cpp}`, `src/fileformat/pfsinpfm.cpp`, `pfsinexr.cpp`, `src/pfs/colorspace.cpp`, `pfs.cpp` (2.2.0 tarball) |

## 2. Luminance units: what the tool actually uses

* **pfs tag `LUMINANCE` = ABSOLUTE / RELATIVE / DISPLAY.** `pfstmo_mantiuk08` reads this tag only to print a warning when it is `DISPLAY` (gamma-encoded input). The tag has no effect on the result. On output the tool sets `LUMINANCE=DISPLAY`.
* **Readers.** `pfsinpfm` (the path we use) tags `LUMINANCE=RELATIVE`, applies no scaling except the PFM header scale (|scale| = 1 here) and sets no `WHITE_Y`. `pfsinexr` (not built here) multiplies by the EXR `whiteLuminance` attribute if present and then tags `ABSOLUTE`. `pfsinppm` and the ImageMagick reader set `WHITE_Y=1` for LDR images. `pfsabsolute` only rescales and retags. Because mantiuk08 ignores the tag, **pfsabsolute is not needed and we do not use it**.
* **Why the absolute level barely matters.** The optimisation (paper §4) works on a histogram of *log-luminance differences* on a fixed grid, `x_i = -8 … 8` log10 in steps of 0.1 (`conditional_density::l_min/l_max/delta`). Values below 1e-8 are clamped (`MIN_PHVAL`). The **scene-side** visual sensitivity is evaluated at a fixed adaptation of **1000 cd/m²** (`scene_l_adapt = 1000`; paper §4.2: "we often want to see images, as if our eye were adapted to high luminance levels … La = 1000 cd/m²"). The display side is absolute through the display model. As a result, multiplying the input by any constant only shifts the histogram along x, and the resulting display image is unchanged. With the default options, **the absolute scale of our cd/m² inputs is ignored**, apart from the explicit `WHITE_Y` anchor.
  *Verified:* we ran S1 and S1 × 10⁶ through the same SDR200 configuration. The tone curves are identical after a shift of 6.0 log10 units (max |Δy| = 1.1e-4). The images agree to 1e-4 at the 99.9th percentile. The only exceptions are pixels pushed past the tool's 1e8 clamp. The same check confirmed that our pfs-stream parser matches `pfsoutpfm` to 8e-6.
* **Exception: `--scene-y-adapt` (`-a`).** This option is not in the man page. `-a auto` evaluates the scene sensitivity at each tone level's *own* input luminance. That is the only path by which absolute scene luminance enters the scene-side model. We ran it once as a SENSITIVITY_RUN (`sens_sceneadapt_auto`).
* **Colour.** The tool works on the pfs **Y channel**, i.e. luminance with pfs' sRGB/D65 matrix (Y row 0.212656, 0.715158, 0.072186, which matches our 0.2126, 0.7152, 0.0722 to 4 decimals). The tone curve is applied to Y. Each RGB channel is then `inv_display((C/Y)^s · L_out)`, where s is the per-tone-level saturation correction from Mantiuk et al. 2009 (default `-c 1`). **The output is per-channel pixel values of the given display function.** The man page says "The result of this TMO does not require gamma correction".

**Our conversion (FORMAT CONVERSION ONLY, nothing ADAPTED):** `oiiotool S*.exr --ch R,G,B -d float -o x.pfm; pfsinpfm x.pfm | pfstmo_mantiuk08 …`. The linear Rec.709/D65 RGB in absolute cd/m² goes in **unscaled**, with no WHITE_Y tag. The PFM round trip matches the EXR to 5e-7 relative. For clips, all 48 frames go in one pfs stream through one process so the temporal filter can work. We parse the output pfs stream ourselves (X, Y, Z float; pfs' XYZ→RGB matrix, as `pfsoutpfm` uses) and write the per-channel pixel values as 16-bit PNG.

## 3. Display function (`-d`) → our scenarios

Display model (paper Eq. 2 and 3; `DisplayFunctionGGBA`): `L_d(V) = V^γ·(L_max − L_black) + L_black + k/π·E_amb`.
This is the same model as `d0/display_model.py`, including the reflected-ambient term. `inv_display` clamps to `[L_d(0), L_d(1)]` and returns V. The optimisation uses `log10 L_d(1) − log10 L_d(0)` as the available dynamic range. The top of the tone curve lands on `L_d(1)` (Eq. 12, α = 1; see §5).
Syntax gotcha: `-d` and `-s` must be **separate argv words** (`-d g=2.2:l=200:…`). The synopsis form `--display-size=<spec>` is **not** parsed, because the tool's own pre-parser does `strcmp(argv[i], "-s")`.
Presets: `pd=lcd` (default; g 2.2, l 200, b 0.8, k 0.01, a 60 lx), `lcd_office`, `lcd_bright`, `crt`. `lut=<csv>` takes pixel value (0…1, first 0, last 1, fewer than 4096 rows) → cd/m² (> 0). The table is interpolated in log10 L and must include reflected ambient.

| scenario | `-d` we pass | notes |
|---|---|---|
| SDR100 (sRGB, 100 / 0.1) | `lut=d0/donors/mantiuk08/luts/SDR100_{DARK,DIM}.csv`: 4001 rows, `L = 0.1 + 99.9·EOTF_sRGB(V) + E·k/π` | GGBA cannot express the sRGB piecewise curve. The LUT is the tool's own "most accurate" option. Output V = sRGB code. |
| SDR200 (γ 2.2, 200 / 0.2) | `g=2.2:l=200:b=0.2:k=0.01:a=0` | exact |
| BRIGHT500 (γ 2.2, 500 / 0.005) | `g=2.2:l=500:b=0.005:k=0.01:a=0` | exact |
| HDR1000 (PQ Rec.2020, 1000 / 0.005) | `lut=…/HDR1000_DARK.csv`, indexed by `p = V_PQ / V_PQ(1000)` (V_PQ(1000) = 0.751827), `L = 0.005 + PQ(p·0.751827)·0.995` | **Supported, with one labelled encoding step.** The tool's p is per channel in Rec.709 primaries. We convert it as p → PQ-linear (Rec.709) → Rec.709→Rec.2020 matrix → PQ code. This is a container conversion, not tone mapping. p is used instead of V_PQ so that the LUT is strictly increasing over [0, 1]; above 1000 cd/m² the display clips. |
| DARK / DIM ambient | `a=0` / `a=50` with `k=0.01` (inside the LUT for SDR100) | DIM adds 0.159 cd/m² reflected. The tool compensates for it, as the paper's model intends. |

These are parametric scenarios, not measured hardware. The `luts/*.csv` files are written by `run_pfstmo.py`.

## 4. Viewing geometry (`-s`): a finding

`-s ppd=73:d=0.3` (PHONE) and `-s ppd=48.4:d=0.6` (DESKTOP) are parsed and printed (`-v`), **but pfstools 2.2.0 never uses them**:
* `datmo_compute_conditional_density()` builds `new conditional_density()` with its default `pix_per_deg = 30`, so the band frequencies are 15, 7.5, 3.75 … cpd for any `-s`.
* `csf_daly()` is called with its default viewing distance of 0.5 m.

The DESKTOP sensitivity run is **byte-identical** to PHONE (`sens_desktop` = `target_whiteauto/S1__PHONE_SDR100_DARK`). Geometry is therefore not an axis of this donor. Our 32 px/deg scene sampling versus 73 px/deg display is irrelevant for the same reason. The man page says the effect of size is "moderate" and "skipping this parameter should not do much harm".

## 5. WHITE_Y and why dark scenes come out bright

**What WHITE_Y is:** "what luminance level in the input image should be mapped to the maximum luminance of a display … what luminance level … should be perceived as a diffuse white surface" (man page). It is given in **input units**, which for us means cd/m². Source: `--white-y` overrides the pfs tag `WHITE_Y`. Default: no anchor. In `optimize_tonecurve`, an anchor adds one soft equation. It asks that the display-luminance increments of all nodes **above** WHITE_Y sum to 0, with weight 0.1 × (total contrast count). Everything above WHITE_Y is compressed onto the display peak. If WHITE_Y lies above the image content, the empty luminance gap between content max and WHITE_Y also enters the problem as a "framework" whose contrast should be preserved. That pushes the content down from the peak by roughly the (transduced) size of the gap. Because the anchor is soft, it is not an exact absolute mapping.

**Why dark scenes are made "too bright" without it** (the man page warning):
1. The tone curve is a function of log-luminance *differences* only, and the scene-side CSF is fixed at 1000 cd/m² (§2). The optimiser cannot tell a 1e-4 cd/m² night scene from the same scene ×10⁶.
2. Paper Eq. 12, `y_i = Y_min + Σd_k + α(Y_max − Y_min − Σd_k)` with **α = 1** ("We set α = 1 to display possibly bright images"). This is `compute_y()` with `alpha = 1`. It pins the **top of the image's luminance range to the display peak** whatever the absolute scene level. Any spare display range goes below the image content, not above it.
3. The scene-side sensitivity is photopic (1000 cd/m²), so the scotopic contrasts of a night scene are treated as fully visible and reproduced at photopic visibility.

For S1 this puts everything above about 0.6 cd/m² (lamp ribbon, glow) at the display peak. The dark sky and ground (1e-4 cd/m²) land at a few cd/m² (median displayed luminance 2.25 cd/m² on SDR100).

**The anchor we chose, and the finding.** A diffuse white requires a known illuminant. Our rural night scene contains no diffuse white surface and no documented scene illuminance: the only "illumination" is the sky dome and distant lamps. Two anchors follow from the tool's semantics:
* **(a) Sky-lit perfect white:** a horizontal Lambertian ρ = 1 surface under a uniform sky of luminance L_sky has luminance ρ·E/π = L_sky, which is about **4e-4 cd/m²**. This value is scene-specific and does not exist for S4 or S5.
* **(b) Absolute intent, which we used for `target_whiteanchor`: `WHITE_Y = display peak` (100 / 200 / 500 / 1000 cd/m²).** Because our input is absolute cd/m² and WHITE_Y is the input level that should reach the display maximum, this asks the tool to show a scene luminance equal to the display peak at the display peak. It is one rule for all scenes, it follows from our units without any appearance guess, and it is the closest this tool comes to "no brightening".

Result: the two physically defensible anchors, (a) and (b), are about 5.4 log10 units apart and give very different images. S1 on SDR100 has a displayed median of 9.3 cd/m² at 4e-4 against 1.3 cd/m² at WHITE_Y = 100. **For night scenes, WHITE_Y is an appearance-design parameter, not a measured quantity.** The sweep `sens_whitey_{4e-4, 4e-3, 4e-2, 0.4, 4}` (S1, PHONE, SDR100, DARK) spans (a) up to the auto behaviour. For S1, WHITE_Y ≥ 4 gives output byte-identical to automatic, because the automatic curve already puts everything above about 0.6 cd/m² at the peak. With (b), S0 (maximum 0.47 cd/m²) reaches at most 1.4 cd/m², not 100. The soft anchor and the gap framework trade the empty 1–100 cd/m² range against content contrast, so even (b) is not a 1:1 reproduction. S5 SDR100/SDR200 anchored output is byte-identical to automatic.

## 6. Temporal filtering, fps, tone-curve output

* **pfstools 2.2.0:** `--fps` accepts **only 25, 30, 60** (default 25). `-f 0` and `--tone-value` exist only in later git versions, which is what the online man page describes. Our clip is 24 fps. **ADAPTED: we run `--fps 25`**, the nearest supported filter. Its time constants are therefore about 4 % longer in real time than designed.
* **Filter:** the paper (§5) describes a windowed linear-phase FIR with a 0.5 Hz cut-off. The 2.2.0 code instead applies a **3rd-order IIR low-pass** (per-fps coefficients, DC gain 1) to the node values y_i of the tone curve. At frame 0 the filter state is initialised to the first frame's curve, then the output is clamped to the display range. It needs all frames in one pfs stream.
* **`--output-tone-curve file.csv`:** one row per node per frame: `frame, log10 input luminance, log10 display luminance, pixel value`. There are 161 nodes, −8 … 8. These are the *filtered, clamped* curves the tool applied. We save them for every run under `d0/results/curves/mantiuk08/<config>/<scene>__<GEOM>_<LUM>_<AMB>.csv`. The *unfiltered* per-frame curves (each S2 frame in its own process) are in `video_unfiltered_*`. `d0/donors/mantiuk08/curve_smoothness.py` summarises both in `video_smoothness.json`.

## 7. Options left at default (not axes)

`-e 1` (no contrast enhancement), `-c 1` (saturation), visual model `full` (contrast masking + luminance masking + CSF), `scene_l_adapt = 1000` except in the one sensitivity run. Run labels: NATIVE_DEFAULT (no options at all, i.e. `pd=lcd`, ppd 30, S1 only), DOCUMENTED_TARGET_CONFIG (scenario display function, PHONE ppd, WHITE_Y auto or anchored), SENSITIVITY_RUN. Every command line is in `d0/work/out/mantiuk08/runs.json`. Reproduce with `d0/donors/mantiuk08/run.sh`.

## 8. What the round produced (descriptive, not a ranking)

* **Supported scenarios:** PHONE × {SDR100 (LUT), SDR200, BRIGHT500, HDR1000 (PQ LUT + container conversion)} × DARK. DIM is supported through the ambient term. DESKTOP is accepted but has no effect (§4).
* **Automatic WHITE_Y (S1, SDR100):** the displayed median is 2.25 cd/m² and everything above about 0.6 cd/m² scene luminance sits at the 100 cd/m² peak. On BRIGHT500 and HDR1000 the median is about 1.2 cd/m² and the peak is used. The top of every image lands on the display peak (§5).
* **Anchored (WHITE_Y = peak):** S1 median 1.3 cd/m² (SDR100) and 0.39 cd/m² (BRIGHT500). S0 (no lamps) reaches at most 1.4 cd/m² on SDR100. For S5 SDR100/SDR200 the output is identical to automatic.
* **`--scene-y-adapt auto`:** the scene-side CSF is evaluated at the scene's own scotopic levels. Night contrasts are then judged nearly invisible, and the image is flattened to a uniform mid-grey (S1 SDR100: 1st–99th percentile displayed range 20.8–28.4 cd/m²).
* **Temporal (S2, `--fps 25`):** the filtered tone curves change very little and smoothly. Over the nodes the content occupies, the largest frame-to-frame step is 1.1e-3 log10 (SDR100, auto) and ≤ 2e-4 in the other three clips. The unfiltered per-frame optimum steps by up to 2.6e-2 log10 (SDR100 auto) and 1.8e-2 (BRIGHT500 anchored), with second differences up to 5e-2. So the IIR filter removes frame-to-frame jitter of the per-frame optimum. Drift over the 2 s clip is ≤ 0.02 log10 in all cases (`d0/results/curves/mantiuk08/video_smoothness.json`).
* **Disk budget:** a 16-bit 1920 × 820 frame is about 7 MB. Of the S2 clips, only `video_whiteauto/S2__PHONE_SDR100_DARK/` (48 frames) was kept. The three other mantiuk08 clips and the reinhard02 clips were computed (their tone curves are saved) but their frames were not written. Regenerate them with `D0_WRITE_S2=all d0/donors/mantiuk08/run.sh`. Byte-identical stills are hardlinked.
