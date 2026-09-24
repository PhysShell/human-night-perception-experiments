# Input contract: `pfstmo_pattanaik00` (pfstools 2.2.0; master c860691 identical)

**Donor.** Pattanaik, Tumblin, Yee, Greenberg 2000, "Time-dependent visual adaptation for fast realistic image
display", SIGGRAPH 2000, doi:10.1145/344779.344810 (ledger L11). Third-party implementation by G. Krawczyk
(2003/04), `src/tmo/pattanaik00/` (ledger L12). **Class: absolute appearance (D1-A).** A native donor, not a
production candidate. Equation audit: `audit.md`.

## What the tool's input numbers mean

- **Channels.** The tool reads the pfs `X, Y, Z` channels. It converts them to pfs "RGB" with pfs' sRGB/Rec.709
  matrix (`transformColorSpace`). It uses `Y` as the luminance of **both** the cone and the rod pathway.
- **Units: absolute cd/m².** The man page says: "requires properly calibrated image data (in cd/m2)". The paper
  (§4.1.2) says: "Be sure to use cd/m² units in Equations 4–7". All the σ and B constants assume cd/m².
- **Tags.** The tool ignores the `LUMINANCE` tag on input. On output it sets `LUMINANCE=RELATIVE`.
- **`--mul`.** `--mul` (default 1) multiplies X, Y, Z before anything else. We use it only for the level ladder.

## Our inputs → tool input: the exact conversion

- **Inputs.** `d0/work/inputs/{S0,S1,S3_bar,S3_nobar,S4,S5}.exr` and `S2/frame_0001…0048.exr` (24 fps). They are
  linear Rec.709/D65 float, Y = 0.2126 R + 0.7152 G + 0.0722 B in absolute cd/m².
- **Conversion.** `oiiotool <exr> --ch R,G,B -d float -o x.pfm` → `pfsinpfm x.pfm` → stdin of `pfstmo_pattanaik00`.
  - This is a format conversion only: **no scaling**, no tag change. pfsinpfm writes `LUMINANCE=RELATIVE`, which
    the tool ignores.
  - pfs XYZ = `PFS_RGB2XYZ · RGB` (pfs matrix, Y row 0.212656 / 0.715158 / 0.072186). Y equals our luminance to
    within 3·10⁻⁵ relative.
  - All frames of a clip go through **one** process as one pfs stream. This is the same approach as
    `d0/donors/mantiuk08/run_pfstmo.py`.
- **Synthetic uniform fields** (the native time-course check and the 100 cd/m² history frames) are written as pfs
  frames directly, with the same matrix. They match pfsinpfm's channel data exactly (max abs diff 0, checked in
  `native_timecourse.json`).

## Minimum of each input, and what needed changing

| input | channel min (R, G, B) | pixels < 0 | pixels with Y ≤ 0 | pixels with one channel = 0 | treatment |
|---|---|---|---|---|---|
| S0, S1 | 2.3e-5, 1.9e-5, 7.3e-6 | 0 | 0 | 0 | none (NATIVE) |
| S2 (frames 1, 13, 25, 37 checked) | ≥ 7.3e-6 | 0 | 0 | 0 | none |
| S3_bar | 0, 0, 0 | 0 | **2398** (the black bar, exactly 0) | — | NATIVE run, plus **ADAPTED** `target_floor` |
| S3_nobar | 3.8e-4 … | 0 | 0 | 0 | none |
| S4 | 8.3e-3 … | 0 | 0 | 0 | none |
| S5 | **0**, 1.0e-3, **0** | 0 | 0 | **80 846 (R = 0), 93 (B = 0)** | NATIVE run, plus **ADAPTED** `target_floor` |

- **No input is negative, so no clamp ≥ 0 is needed.** The m0 NaN came from negative pixels in a real HDR merge.
  Here, zeros are the hazard.
- **A channel at 0 turns into a white channel.**
  - The tool computes `r = R/Y`, then `pow(r, Scolor)`, then clamps with `(r<1) ? ((r>0) ? r : 0) : 1`.
  - The clamp maps NaN to **1.0**, because every comparison with NaN is false.
  - pfs' RGB→XYZ→RGB round trip makes an exact 0 slightly negative. `pow(negative, s)` is then NaN, and the
    clamp turns it into 1.0.
  - Result: all 80 846 S5 pixels with R = 0 come out with **R = 1.0**. This is the "speckles on real data" of the
    landscape notes.
- **Y = 0 pixels.**
  - *Global model:* they give `pow(NaN, 0) = 1` times zero responses. The S3 bar therefore comes out 0 (correct
    by luck).
  - *`--local`:* `log(0)` enters the local-adaptation weights, so A = NaN and the **bar renders white**.
- **ADAPTED `target_floor`.**
  - Pixels with all channels 0 are set to 1·10⁻⁶ cd/m², neutral.
  - Every channel is floored at 10⁻⁴·Y.
  - It is applied to S3_bar, S3_nobar (input unchanged) and S5 only. Every row carries the label.

## Output → display (d0 output contract)

- **What the tool emits.**
  - Linear RGB, clamped to [0, 1] per channel, converted back to XYZ, tag `LUMINANCE=RELATIVE`.
  - 1.0 is the paper's display REFwht. The display observer is hard-coded (paper §4.3, `tmo_pattanaik00.cpp`
    l. 73–94): adaptation 25 cd/m², white 125 cd/m², black 3.9 cd/m², S_d = 0.1383. There is no option to change it.
  - The man page says "results should be gamma corrected" and gives `pfsgamma -g 2.2` as its example.
- **The tool is display-unaware**, so every scenario differs only by encoding:
  - `native_default`: the man-page pipeline `| pfsgamma -g 2.2`. Its code values are decoded as SDR100, the
    nearest scenario.
  - `target` (DOCUMENTED_TARGET_CONFIG):
    - SDR100: code = sRGB OETF(clip(I, 0, 1)), where 1 is the 100 cd/m² peak;
    - BRIGHT500: code = clip(I)^(1/2.2), display-relative.
  - `sens_abs125` (SENSITIVITY_RUN): reads the output as absolute, emitted = 125·I cd/m². It is encoded as
    (125·I − black)/(peak − black) and clipped at the peak.
- **Where the files go.** `d1/pattanaik00/.cache/out/<config>/<scene>__PHONE_<LUM>_DARK.png`. S2 is written as
  frames only for `clip_t24` SDR100.

## Temporal (`-t --fps`)

- **fps.** `--fps` accepts any value > 0, so **24 is used exactly** (not ADAPTED). The default is 16.
- **The fps stability limit.**
  - The explicit update of the rod-bleaching equation (paper eq. 7a, implemented verbatim) is unstable when
    G·T/16 > 2. At 24 fps that means G > 768 cd/m².
  - A log-average goal G above 768 cd/m² makes B_rod diverge to NaN, and the output then stays white for good
    (`native_timecourse.json`, run A).
  - Our night inputs are far below this. The 100 cd/m² history field gives G·T/16 = 0.26, which is stable.
- **Frame 0** is set to the tool's *static* state, A = 5 × log-average. From frame 1 on, the goal is the
  log-average itself (×1). Details in `audit.md`.
