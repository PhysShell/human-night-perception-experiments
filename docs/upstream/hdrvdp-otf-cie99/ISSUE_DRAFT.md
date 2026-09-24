# DRAFT (not posted): `hdrvdp_otf_cie99` uses 1-D Fourier transforms as a 2-D OTF

**Target:** HDR-VDP 3.0.7, `utils/hdrvdp_otf_cie99.m` (reached through `{'mtf','cie'}`).

**Summary.** The closed form of the CIE 135/1 (Vos & van den Berg 1999) OTF has terms of the form
`2 c^2 |w| K1(c |w|)`. That is the **1-D** Fourier transform of `(1+(x/c)^2)^-1.5`. The OTF is
applied as a **2-D radial** filter (`create_cycdeg_image` + `fft2`). There, the radially symmetric
PSF needs the 2-D (Hankel) transform: for this term `2 pi c^2 exp(-2 pi c rho)`. The result is not
the 2-D transform of the CIE glare spread function:
- it keeps far too much energy in the core;
- the point image goes negative in the wings, which a PSF cannot do.

**Minimal repro:** `repro_otf_cie99.m`. It is self-contained and needs only `hdrvdp-3.0.7/utils`;
GNU Octave needs the included `octave_shim/dirac.m`.
- Input: a delta at 60 px/deg on a 2x-padded canvas.
- Expected: the published GSF (sr^-1, age 24, p 0.5) integrated per pixel.
- Control: the numerical Hankel transform of the same GSF, applied with the same FFT pipeline.

OTF (age 24, p 0.5):

| rho (cpd) | 2-D Hankel of the GSF | `hdrvdp_otf_cie99` |
|---|---|---|
| 0.1 | 0.950 | 1.000 |
| 1 | 0.795 | 0.987 |
| 3 | 0.581 | 0.942 |
| 10 | 0.307 | 0.812 |
| 30 | 0.153 | 0.567 |

Point image, radial PSF in sr^-1:

| radius | `hdrvdp_otf_cie99` | CIE GSF (expected) | control (2-D OTF, same pipeline) |
|---|---|---|---|
| 3' | 2.85e4 | 5.12e4 | 5.51e4 |
| 10' | 73 | 2.90e3 | 2.77e3 |
| 18' | −4.1 | 564 | 545 |
| 60' | −0.78 | 18.8 | 18.5 |

Encircled energy within 1' / 10' / 60':

| | 1' | 10' | 60' |
|---|---|---|---|
| actual | 0.855 | 0.989 | 0.9995 |
| expected | 0.331 | 0.786 | 0.934 |
| control | 0.341 | 0.784 | 0.932 |

Other results from the repro:
- Energy on the canvas: actual 1.000 (normalised at ω → 0), expected 0.985 (the GSF beyond the
  34° canvas).
- Minimum of the point image: actual −3.4e-3, control −1.7e-6.
- In the metric, `clamp(..., 1e-5, ...)` in `hdrvdp_visual_pathway.m` hides the negative lobe.

**Suggested fix (for the maintainers to judge).** Use the 2-D transform of each term:
- `(1+(t/c)^2)^-1.5` → `2 pi c^2 exp(-2 pi c rho)`;
- `(1+(t/c)^2)^-1` → `2 pi c^2 K0(2 pi c rho)`;
- `(1+(t/c)^2)^-0.5` → `c exp(-2 pi c rho) / rho`;
- the constant and t² terms → DC.

The slow terms do not have a finite integral over the infinite plane; the GSF is defined up to
~90°. A numerically tabulated Hankel transform of the GSF over its defined range may therefore be
simpler than closed forms. That is what the control does.

Full output: `repro_output.txt`.
