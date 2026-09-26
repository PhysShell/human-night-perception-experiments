# D1-A3-K0: Radiance pcond as a luminance-only axis-A donor, recombined with frozen B

Pre-registered in `PREREG.md` (commit `cf198b1`, before running).

    nix develop -c d1/axis_a3_pcond/run_pcond.sh            # pcond path A (as m1/pcond_colorimetric.sh), -s and -s -c
    tracks/temporal-glare-2009/py.sh d1/axis_a3_pcond/recombine.py   # -> results.json, sheet_S1.png

**Consistency control: passed.** A3-sc's sky reproduces D0 donor A (pcond V0) to 0.9999×: 0.3165 cd/m². Y comes
from pcond; chromaticity comes from frozen B (A0 architecture).

## Result: both candidates pass every pre-registered gate

| gate | A3-s (`-s`) | A3-sc (`-s -c`, pcond-derived scotopic luminance model) |
|---|---|---|
| sky median ≤ 2 cd/m² | 0.322 ✓ | 0.316 ✓ |
| lamps / sky ≥ 10 | 256 (lamps 82) ✓ | 262 (lamps 83) ✓ |
| silhouette Weber ≥ 0.1 (luminance-defined poplars) | 0.556 ✓ | 0.591 ✓ |
| (D0 tree mask, secondary) | 0.499 | 0.556 |
| poplar darker than the 5–20 px ring | ✓ | ✓ |
| edge reversals ≤ 5 % | 0 % ✓ | 0 % ✓ |
| halo, ring / far sky within 1.5× | 0.93 ✓ | 0.91 ✓ |
| B preserved, Δu′v′ ≤ 10⁻⁶ | 3·10⁻¹⁶ ✓ | 3·10⁻¹⁶ ✓ |
| channels above the display peak ≤ 1 % | 0.34 % ✓ | 0.32 % ✓ |

`sheet_S1.png`: a dark night (sky ~3× display black), visible poplar silhouettes, a warm lamp ribbon, and ground
near black. No local operator runs, so there are no reversals and no halos.

## Reading
- **pcond is an admissible deterministic axis-A donor for S1.** A0 made this possible. Its luminance was never
  the problem; its colour was. B now supplies the colour.
- -s and -s -c differ little in luminance: sky −2 %, poplars −10 % with `-c`. `-c` only adds pcond's scotopic
  luminous response. Since B handles chromaticity, `-s -c` is the natural choice: it keeps the scotopic luminance
  weighting (a Purkinje *luminance* effect) in axis A.
  - It is also byte-for-byte the luminance of the frozen V0 baseline.
  - This is a recommendation, not a pre-registered decision.
- **What passing means.** The gates are necessary conditions: dark, ordered, silhouettes, no artefacts, colour
  intact, no clipping. They do not validate pcond's visibility model (Ward Larson et al. 1997: histogram
  adjustment with human contrast sensitivity; TVI after Ferwerda 1996) as *the* right night appearance.
- **Near-threshold regime (unchanged caveat).** S1's sky and poplars lie below ~10⁻³ cd/m². Kellnhofer 2015 would
  be an optional stochastic layer **on top of** this deterministic mapping, to be decided separately.
- **Consequence for the decision tree.** pcond-A is not killed, so A3a (Ashraf & Mantiuk 2024) is **not
  needed** for S1 now. It stays a reference.
