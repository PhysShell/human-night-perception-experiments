**Possible issue in `hdrvdp_otf_cie99`: inverse 2-D response has large negative lobes and does not reproduce the CIE99 GSF**

HDR-VDP 3.0.7, `utils/hdrvdp_otf_cie99.m`, as used through `{'mtf','cie'}`.

Hello,

When HDR-VDP-3 is switched to the CIE99 glare spread function, I expected the OTF's inverse 2-D
transform (the point image) to be a positive, radially symmetric kernel following the CIE 135/1
(Vos & van den Berg 1999) GSF. A minimal test gives something else. Files attached; the test needs
only `hdrvdp-3.0.7/utils`.

**Setup**

| parameter | value |
|---|---|
| observer | age 24, pigmentation p = 0.5 (the HDR-VDP defaults) |
| sampling | 60 px/deg; visible field 1024², padded to a 2048² canvas (34.1°) as in `hdrvdp_visual_pathway` |
| input | a single-pixel point of unit energy at the centre of the canvas |
| actual | `real(ifft2(fft2(I) .* hdrvdp_otf_cie99(create_cycdeg_image(...), 24, 0.5)))` |
| expected | the CIE 135/1 GSF (sr⁻¹) integrated over each pixel; small-angle mapping, pixel = (1/60°)² sr; not renormalised on the canvas (its sum there is 0.985) |
| control | the zero-order Hankel transform of the same GSF, tabulated and applied with the **same** FFT pipeline |

**What the test shows** (`repro_output.txt`, `repro_profile.png`)

1. **Negative lobes.** The GSF is strictly positive.
   - The minimum of the point image is **−3.4·10⁻³** (unit total energy) for `hdrvdp_otf_cie99`,
     against −1.7·10⁻⁶ for the control through the same pipeline.
   - 2.9·10⁻² of the energy sits in negative pixels, against 3.2·10⁻⁴ for the control.
   - Bin minima reach about −1000 sr⁻¹ at 18′ and −25 sr⁻¹ at 2°.
   - In the metric itself, the `clamp(…, 1e-5, …)` in `hdrvdp_visual_pathway.m` would hide this.
2. **Radial shape.** The control reproduces the GSF; the actual response does not. At 10′ and 18′,
   well inside the GSF's working range and far from the central pixel:

| radius | actual (log-bin mean, sr⁻¹) | control | expected |
|---|---|---|---|
| 10′ | 73 | 2 770 | 2 900 |
| 18′ | 14 | 557 | 570 |
| 30′ | 8.8 | 134 | 133 |
| 60′ | 0.19 | 18.8 | 18.8 |

The actual profile is 40–100× below the GSF and oscillates between pixels. No normalisation
convention changes the sign or a 40× ratio between 10′ and 18′.

**OTF values**

| ρ (cpd) | 0.1 | 1 | 3 | 10 | 30 |
|---|---|---|---|---|---|
| Hankel transform of the GSF | 0.947 | 0.793 | 0.579 | 0.306 | 0.153 |
| `hdrvdp_otf_cie99` | 1.000 | 0.987 | 0.942 | 0.812 | 0.567 |

**Possible cause.** The implementation appears to apply 1-D Fourier-transform expressions as a
radially symmetric 2-D OTF.
- For example, `2 c² |ω| K1(c|ω|)` is the 1-D transform of `(1 + (x/c)²)^−1.5`.
- For a radial 2-D PSF, the corresponding transform is a zero-order Hankel transform: for that term,
  `2π c² exp(−2π c ρ)`.
- This may be an intentional approximation. If so, a note on its intended use would help.

**Not a factor**
- **`dirac`.** The function calls `dirac()`, which GNU Octave lacks.
  - The test runs it with two different stand-ins (0 everywhere; Inf at 0). The OTFs are identical
    (max difference 0), because `dirac` only acts at ω = 0, which the function sets to 1 itself.
  - I have not run MATLAB with the Symbolic Math Toolbox.
- **Encircled energy** depends on the support and normalisation chosen for the GSF, so it is listed
  only as secondary output. It is not the evidence.

Files: `repro_otf_cie99.m` (run with `HDRVDP=/path/to/hdrvdp-3.0.7`), `shim_zero/dirac.m` and
`shim_inf/dirac.m` (Octave only), `repro_output.txt`, `repro_profile.csv`, `repro_profile.png`
(`plot_profile.py`).

Thank you for HDR-VDP.
