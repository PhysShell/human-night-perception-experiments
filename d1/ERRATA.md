# D1 errata

Corrections to claims in D1 records. The frozen files listed in `MANIFEST.sha256` are **not** edited;
`d1/verify_manifest.sh` stays green. Each erratum names where the error was found.

## E1: the DR v2 encoder knee is NOT an exact inverse of the decoder
- Found in N1.5 Camera C (`n1/view_C.json`, `0f76c6a`).
- **Claim corrected.** `d1/display_r/PREREG_v2.md` and `d1/display_r/README.md` (v2) state that encoding with the
  knee at lin ≤ 0.04045/12.92 makes the encoder the exact inverse of the decoder. It does not.
- **Why.** Just above that knee, the power branch 1.055·v^(1/2.4) − 0.055 still yields codes slightly **below**
  0.04045, so the decoder takes its linear branch.
- **Instance.**
  - One in-gamut pixel on N1 Camera C, R channel: v = 0.00313081 (3·10⁻¹² above the knee), code 0.04044997.
  - G3 and S-2 fail literally: hue 3·10⁻⁵ rad at chroma 8.7·10⁻⁴; chroma +8·10⁻⁹.
- **Classification.** The same measurement-artefact class first diagnosed in DR v1. The display mapping is unaffected:
  the pixel is in gamut and untouched. The failure stays recorded as FAIL wherever it occurs; D1 code is unchanged.
