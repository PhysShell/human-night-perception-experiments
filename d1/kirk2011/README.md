# D1-B donor audit: Kirk & O'Brien 2011 (low-light tone mapping)

**Classification: `implementation claiming Kirk 2011`, third-party, author-hosted; colour path DEFECTIVE (fails a photopic white round-trip, see below). Kirk 2011 remains PAPER_REFERENCE for low-light colour.** The runtime is the plug-in's
own C++ core, compiled unmodified and called by a headless driver (§3). The plug-in's Purkinje core (Eqs. 10–13)
matches the paper in form. It differs in these places:
- κ1 = 0.24 instead of 0.25;
- a ×0.24 factor on ΔoLuminance;
- clamping instead of the QP in Eq. 15;
- different range-reduction constants.

Its RGB→LMSR matrix is not published in the paper, so it cannot be verified. It is also nearly rank-1, driven
almost only by G. So the label "equations verified" is **not** earned.

**Coordinator check (D1.0 review): the plug-in's colour path is defective before any low-light modelling.**
The cyan output was first suspected to be an R↔B channel swap, because OpenCV stores BGR and GIMP hands over RGB.
It is not one:
- `render.cc` and our driver store BGR, and `hdrToLMSR.cc` swaps back to R, G, B.

It is the plug-in's own matrices:
- `hdrToLMSR.cc` RGB→LMSR (fitted "with cvx") has singular values 3.5·10⁻², 5.1·10⁻⁴ and 8.8·10⁻⁵. The R and B
  columns are ~10⁻⁴ and partly negative; G carries everything.
- Taken through the plug-in's own `lms2display.cc` monitor matrix **with no Purkinje step at all**:
  - white (1, 1, 1) → display (0.27, 0.28, 1): blue;
  - a warm lamp (1, 0.6, 0.25) → the same blue;
  - pure red → an out-of-gamut negative blue;
  - pure blue → negative LMS, which is the source of the NaN.

So the implementation does not reproduce even *photopic* colours. The input chromaticity is discarded, and every
pixel lands on one fixed chromaticity. The single-chromaticity result measured below is therefore a property of
this implementation's matrix, **not of the Kirk & O'Brien model**.

**Consequence for D1-B.**
- This plug-in can document the Purkinje *luminance* / blend behaviour (the mesopic blend vs level is still
  informative).
- It is **not usable as evidence about low-light colour**.
- Kirk & O'Brien 2011 stays a **PAPER_REFERENCE** for colour until an implementation whose RGB→LMS(R) conversion
  passes a photopic round-trip (white → white, a warm lamp → a warm lamp at high luminance) is available.

Check: `python3` with the two matrices copied from `hdrToLMSR.cc` and `lms2display.cc`. The numbers are in this
section.

## 1. Provenance

Opened on 2026-09-24:

| URL | result |
|---|---|
| https://jamesobrien.com/papers/Kirk-PBT-2011-08/index.html | 200. The authors' paper page (JSON-LD authors: Adam Kirk, James F. O'Brien). Byte-identical to the next row; sha256 of the page `ebe0b032…cc76a` |
| https://objf.ai/papers/Kirk-PBT-2011-08/ | 200, same page |
| https://escholarship.org/uc/item/1jn327c5 | 202 (empty), then 403 bot check. **Not opened** |
| …/Kirk-PBT-2011-08/GimpPlugin/index.html → Welcome.html | "Low-Light Tone Mapper, Plug-in for GIMP, **written by Yeon Jin Lee**". "Our tone mapping algorithm is based on the SIGGRAPH 2011 paper … by Adam Kirk and James F. O'Brien". sha256 `72894172…f8300` |
| …/GimpPlugin/Install.html | build guide: GIMP 2.6.12, OpenCV 2.3.1a, OpenEXR 1.7.0, fftw, CImg. sha256 `9a3e6e72…aca13` |
| …/GimpPlugin/Welcome_files/LOWLIGHT_LINUX.zip | 5 079 577 B, Last-Modified 2023-05-25, **sha256 `203e613b5b8f9312632959c91ae60aca168701829be0c9a0e43b7e336624a89e`** (used) |
| …/GimpPlugin/Welcome_files/LOWLIGHT_MAC.zip | 3 677 938 B, sha256 `5a0e20577c1f6713dcd93c3fef9d36ccf1c7c8abb8886ab4de2bd428a1d339d9`. Same core; `hdrToLMSR.cc` also carries two disabled alternative matrices ("without white balance", "applied white balance on HDR training images") |
| …/Kirk-PBT-2011-08.pdf (paper) | 102 596 760 B > 50 MB cap, so it was **not downloaded whole**. Only the PDF's text objects (≈370 KB, HTTP range requests guided by its xref stream) were fetched into a sparse file, and the text was extracted with `pdftotext`. ETag `"61d8098-4ab10140c00c0"`, Last-Modified 2011-08-22, PDF /ID `80BC6E7D…BD39D7`. Figures were not fetched. The ACM DL copy is behind a Cloudflare challenge. OpenAlex lists it as closed access |
| supplemental.pdf (159 MB), raw_data.zip (2.66 GB) | HEAD only, not downloaded |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC2630540/ (Cao, Pokorny, Smith, Zele 2008, the source of Eqs. 10–12) | 200. Used for the units of the gain constant (§5) |

**Verdict on authorship.**
- The plug-in is **by Yeon Jin (Grace) Lee, not by Kirk or O'Brien**. This is stated in `AUTHORS` and in every
  file header ("Copyright (C) 2011-2012 / 2012 Yeon Jin Lee"). `AUTHORS` thanks O'Brien, Kirk, Durand (bilateral
  tone mapping) and F. Hecht (EXR I/O).
- It is **linked and hosted on the authors' own paper page**, which calls it "a version of this algorithm" with
  "additional controls for artistic changes".
- File dates in the zip run from 2011-11 to 2012-05-01. Ledger L17 ("third-party by Y. J. Lee, 2012, GPL") is
  correct; add "hosted and linked by the authors".

**Licence.**
- `COPYING` is GPL-3. `README` says "Copyright (C) 2011-2012 Yeon Jin (Grace) Lee".
- The `src/*.cc` headers contradict each other: an MIT/X11 permission notice followed by "You should have
  received a copy of the GNU General Public License".
- The bundled `FredoToneMap/` is MIT, © 2006 Sylvain Paris and Frédo Durand. `CImg.h` is bundled but unused.

We treat the plug-in as GPL-3. **No donor source is committed.** `setup.sh` fetches it and checks its sha256 into
`.cache/` (gitignored). `driver.cpp` and `shim/` are ours.

## 2. Equation check

Sources:
- Paper: extracted text of §3.2, §4 and Eqs. 10–16.
- Code: `.cache/src/LOWLIGHT_LINUX/src/…`.

Code parameters are the defaults in `main.cc` `default_tvals`: exposure 64, "kappa1" .33, "kappa2" .5, rho1 .8,
rho2 .139, rho3 .4, rho4 .6, alpha .6189, y 15, z .24, and user offsets 0.

| paper | code | verdict |
|---|---|---|
| §3 "single point of control, uniform scaling of scene luminance" (exposure). No units | `render.cc`: `inputImg->convertTo(hdr, CV_32FC3, tvals->exposure)`. The **8-bit GIMP codes** (sRGB-encoded, not linearised) ×64 | form matches. Input domain differs: the paper takes HDR RGB, the plug-in 8-bit display codes |
| §4 RGB→LMSR: Q = HP, H fitted to the authors' spectra, **H not published** | `hdrToLMSR.cc` "matrix from cvx" (4×3) | **cannot be verified.** H has singular values 0.0347 / 0.00051 / 0.00009, so it is effectively rank 1: L, M, S and R are all ≈ c·G, and B has a negative weight on all four. The Mac zip keeps two disabled alternatives. `rgbToLMSR.cc` (a different, full-rank matrix) is never called |
| Eq. 10 g = 1/(1+0.33(q+κ q_rod))^0.5, κ1 = 0.25 (L, M), κ2 = 0.4 (S) | `purkinje.cc` `G()` with k1 = "kappa1" = .33 (the constant), k2 = "kappa2" = .5 (the exponent). Rod mixing uses k5 = "z" = .24 (L, M) and k6 = "rho3" = .4 (S) | form matches. **κ1 = 0.24 vs 0.25.** The UI names are shifted: "kappa1/2" are the 0.33/0.5 constants, and "z" is κ1 |
| l/m/s_max = .637/.392/1.606 | same | match |
| Eq. 11 opponent A; Eq. 13 q̂ = q + A⁻¹Δo | `value=(LtM−M_L)/2`; ΔL = value, ΔM = LtM − value, ΔS = S_L_M + LtM, added to L, M, S | match |
| Eq. 12 ΔoRG = x κ1 (ρ1 gM/mmax − ρ2 gL/lmax) q_rod; x = 15, ρ1 = 1.111, ρ2 = .939 | `a=15*k5; b=1+rw*k3PC (=1.1112); d=k3PC+rw (=.939)` × R | match (with κ1 = .24). ρ1 and ρ2 are rebuilt from Cao's k3 = .8 and r_w = .139 (r_w is Cao's value at 2 Td) |
| Eq. 12 ΔoBY = y (ρ3 gS/smax − ρ4(α gL/lmax + (1−α) gM/mmax)) q_rod; y = 15, ρ3 = .4, ρ4 = .15, α = .619 | `y*(k6*GS/smax − k3KC*(p*k5*GL/lmax + (1−p)*k5*GM/mmax))` × R | form matches. Effective ρ4 = .6 × .24 = .144 vs .15 (= .6 × .25). ρ3 reuses k6 = .4 |
| Eq. 12 ΔoLum = z (α gL/lmax + (1−α) gM/mmax) q_rod; **z = 5** | `LtM = 5*k5*(…)` × R, so the effective z is 5 × .24 = **1.2** | **differs: ×0.24.** The printed equation has no κ in this row (text extraction, typeset layout) |
| (not in paper) | `redGreenVal`, `blueYellowVal`, `luminanceVal` offsets | artistic extras; 0 by default, so neutral |
| Eq. 14/15 min‖Mp − q̂‖ s.t. p ≥ 0 (QP when needed); M = Apple Cinema HD | `lms2display.cc`: p = M⁻¹q̂ with "Adam's monitor" M, then **negatives clamped to 0** | differs: clamping, not a QP. The M values are not published in the paper |
| §3.2 Durand & Dorsey via Paris & Durand bilateral | `tonemapping.cc` → `tone_mapping in.exr out.ppm 50.0` (bundled FredoToneMap; I = (20R+40G+B)/61, γ 2.2, 8-bit) | match (the paper gives no contrast value) |
| Eq. 16 w; x = max(1 − w^β(1−γ), γ)·ν, β = 1, γ ∈ [0.25, 0.5] | `reduceRange.cc`: max = 255·(γ + (1−γ)·alpha), with γ = **0.1** and alpha = `blend` = max(0, 1 − 1.2 w) (from `purkinje.cc`) | form similar, **parameters differ** (γ 0.1; w scaled by 1.2) |
| §4 "blend between the source image and the mesopic image based on w" | `reduceRange.cc`: final = f·LDR + (1−f)·reduced, f = (1−bf)·alpha + bf. bf ramps where the source intensity passes 210→255, with weights .3/.6/.1 applied to **B, G, R** (OpenCV channel order) | matches in form. Adds a highlight-protection ramp, with a channel-order slip in its weights |
| — | Saturated colours give S + 0.4·R < −3 → `pow(<0, .5)` = **NaN**: 2.7 % of the 8-bit RGB cube; 1 px in S5 | donor behaviour. NaN pixels are excluded in `measure.py` |

## 3. Runtime

The runtime **runs**.

    d1/kirk2011/setup.sh                                          # fetch + sha256 + build (nix: gcc, opencv 4.13, openexr 3.4, fftw)
    tracks/temporal-glare-2009/py.sh d1/kirk2011/run.py           # -> .cache/out/<config>/<scene>.exr, runs.json
    tracks/temporal-glare-2009/py.sh d1/kirk2011/measure.py       # -> results.json
    tracks/temporal-glare-2009/py.sh d1/kirk2011/sheets.py        # -> sheet_S1.png, native_example.png

- **Compiled unmodified** (`-g -O2`, as in the plug-in's `src/Makefile`): `hdrToLMSR.cc`, `purkinje.cc`,
  `lms2display.cc`, `tonemapping.cc`, `reduceRange.cc`, and FredoToneMap with its own Makefiles (only the library
  path variables are overridden).
- **`exrIO.cc`**: the build copy drops only the unused `ReadTxt()`. That function is C++98 code that does not
  compile under C++11+, which OpenEXR 3 needs. `WriteExrRGB` is untouched.
- **Shims** (`shim/`): OpenCV 2 `cv.h`/`highgui.h` → OpenCV 4 headers; glib typedefs; libgimp pixel-region
  prototypes. `driver.cpp` implements those prototypes as no-ops. They are used only by
  `convertOutputToDrawable`, which copies the result into a GIMP layer; `reduceRange` also `imwrite`s the same
  bytes.
- **`driver.cpp`** replays `render.cc` without GIMP. The donor's hard-coded `/tmp` files are redirected to
  `.cache/tmp` through a private mount namespace (`unshare -m`).
- **Resources:** ~30 s for all 20 runs; peak RSS 258 MB (S1-size native run incl. Durand).

## 4. Native example (`native_example.png`)

The zip ships a 2012 plug-in run's intermediates in `src/images`. The original input photo is not shipped.

- **Durand stage.** `tone_mapping BeforeDurandTonemapping.exr out.ppm 50.0` rebuilt here is **byte-identical** to
  the shipped `AfterDurandTonemapping.ppm`.
- **Core stage.** Every shipped core pixel (`BeforeDurandTonemapping.exr`) lies within 0.09 % (median) and 0.46 %
  (p99) of the set of outputs our build produces from 8-bit RGB at exposure 64. At exposure 16 the p90 miss is
  35 %.
- **What this shows.** The shipped result was made by this code at default settings. The cyan, near-monochrome
  core output is the plug-in's genuine behaviour, not a build artefact. Colour comes back only through the final
  blend with the source image.

## 5. Configs, input contract, results

The input contract is in `input-contract.md`. Measured effects are in `results.json`, summarised below.

- **Core colour is replaced, not desaturated.**
  - Because H ≈ rank 1, every pixel's core output has nearly the same chromaticity, whatever the input colour.
  - DOCUMENTED_TARGET_CONFIG (S0/S1): u′v′ (0.142, 0.429), chroma 0.069, cyan.
  - Ladder ×10⁶: u′v′ (0.171, 0.359), chroma 0.113, blue-violet.
  - The warm lamps of S1, S3 and S4 (u′v′ ≈ 0.25, 0.53) also come out blue, at u′v′ ≈ (0.15–0.19, 0.36–0.38).
- **Level dependence (S1 ladder ×10⁰ / 10² / 10⁴ / 10⁶).**
  - Mean blend (1 − 1.2w) is 0.001 / 0.004 / 0.25 / 0.91, i.e. scotopic → photopic.
  - The sky output/input ratio is 18.7 / 17.5 / 6.0 / 2.8: the rod luminance term raises dim regions by up to
    ~6.7× relative to photopic.
  - The core is linear in level below ~1 Td (S1 at ×1 and ×100 are almost the same). **It does not darken the
    scene.** Darkening is only in the display stages (Durand + reduceRange).
- **NATIVE_DEFAULT final (8-bit, vs its 8-bit input).**
  - Sky and ground shift toward blue: S1 sky u′ 0.202 → 0.176, with a hue shift of +134°.
  - Tree chroma falls from 0.056 to 0.016.
  - Ground luminance ×0.59; sky luminance ×0.91.
  - Clipped lamps stay white (highlight ramp).
  - Band-pass detail: ground ×1.27, from Durand local contrast.
- **Detail at the core.** Energy ratio 0.4–1.0 (S1: sky 0.60, ground 0.83). This comes from the G-only projection
  and the gain nonlinearity. No acuity model exists in either the paper or the code.
