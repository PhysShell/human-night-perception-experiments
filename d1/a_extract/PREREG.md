# D1-AX pre-registration: extract axis A from pcond *before* its gamut clip

Committed **before** the extraction code exists. The axis-A model is unchanged: Radiance `pcond -s -c`, path A,
defaults, same inputs and HFOV (`d1/pipeline/axis_a.sh`). What changes is *where* we read its luminance.

**Why.** R1 (`d1/pipeline/README.md`, commit `f5dd713`) showed that the frozen Y_A is the Rec.709 luminance of
pcond's output **after** `matscan()` → `clipgamut()`. That clip pulls out-of-gamut colours towards a grey whose
brightness is that of the per-channel-clamped colour (`greypoint()`, `src/px/pcond2.c:144`), so Y is lost for
saturated colours. Hypothesis: that step alone causes the F1 non-monotonicity.

## pcond's chain, from the pinned source (`/nix/store/rp1xsl3b…-source`, the source of the binary we run)
`nextscan()` (`pcond2.c`): `scotscan()` (if `-c`) → `mapscan()` (or `sfscan()` in DO_LINEAR) → `matscan()` =
colour matrix M, then `clipgamut(col, greypoint(col), CGAMUT, 0, 1)` → RGBE write.

1. **L_eff (post-`scotscan`)**, from the XYZE file pcond actually reads (`inX.hdr`, kept, not recomputed from the
   EXR):
   - L_p = Y / inpexp;
   - w = clamp((L_p − 5.62·10⁻³)/(5.62 − 5.62·10⁻³), 0, 1);
   - Y_s = Y·(1.33·(1 + (Y + Z)/X) − 1.68) (`cielum(·,1)`);
   - XYZ′ = w·XYZ + (1 − w)·(Y_s/2.26)·(1, 1, 1);
   - L_eff = Y′/inpexp.
   
   Constants are from `pcond.h` (SWNORM 2.26, BotMesopic, TopMesopic).
   **Global `-c` disabling is reproduced.** pcond clears DO_COLOR when the 5th histogram percentile ≥ 5.62
   (`check2do()`). This is read from pcond, not re-derived: `pcond -s` (no `-c`) is also run on the same file. If its
   output is bit-identical to `-s -c`, then XYZ′ = XYZ and L_eff = L_p.
2. **F, pcond's own tone map, from `-x mapfile`** (`putmapping()`: 100 rows (wlum_i, Lb(BLw(wlum_i))) at the bin
   *centres*). F is reconstructed exactly (up to the 7 printed digits), not interpolated:
   - `Bl = ln`;
   - `cf()` is linear between bin *edges*, with cumf[0] = 0;
   - so c_i = (ln Ld_i − ln ldmin)/(ln ldmax − ln ldmin) = (cumf[i] + cumf[i+1])/2, which gives
     cumf[i+1] = 2c_i − cumf[i];
   - bwmin and the bin width come from the printed wlum.
   
   BLw's branches are kept: L ≤ 10⁻⁷ (LMIN) → black (`mapscan`), b ≤ bwmin → ldmin, b ≥ bwmax → ldmax.
   `mapscan` gives Y_map = (F(L_eff) − ldmin)/(ldmax − ldmin), with ldmax 100 and ldmin 1.
   **DO_LINEAR** (the scene range fits the display, or `mkbrmap` fails) is recognised from the map file (dlum/wlum
   constant). Then Y_map = (dlum/wlum)·L_eff/ldmax, unclipped. This reading of the units is **validated by C3**, not
   assumed.
3. **Pre-gamut output colour:** rgb_pre = Y_map · M·XYZ′ / Y′.
   - M = `compxyz2rgbWBmat(Rec.709)`, computed by compiling Radiance's `spec_rgb.c` verbatim (`matscan_mat.c`).
   - M includes the von Kries E → D65 step, which can change luminance for chromatic colours.
4. **New axis-A luminance (primary):** **Y_A^new = Rec.709 luminance of rgb_pre**. This is what pcond's own chain
   would emit on a display with no gamut limit.
   - Sensitivity: Y_A′ = Y_map, i.e. F(L_eff) alone, without the von Kries luminance factor. Reported, not a
     candidate.

## Controls (all must pass, or the extraction is not validated → KILL)
| id | criterion |
|---|---|
| AX-C0 non-interference | `pcond -s -c -x map` output bit-identical to the frozen `.cache/A` output, every image |
| AX-C1 F reconstruction | recovered cumf non-decreasing (tolerance 10⁻⁵) and \|cumf[100] − 1\| ≤ 10⁻³ (pcond sets it to exactly 1) |
| AX-C2 unclipped identity (neutrals first) | on pixels where `clipgamut` is inactive for rgb_pre (all channels in [0, 1]): \|Y_A^new − Y_A^old\| ≤ max_ch(old)/128 + 10⁻³·Y_A^new. The RGBE mantissa bound is max/128 per channel. All F1 **neutral** patches, all such F1 patches, and ≥ 99.9 % of such pixels in each still |
| AX-C3 full-chain reproduction | `clipgamut(rgb_pre, greypoint(rgb_pre), CGAMUT, 0, 1)`, compiled verbatim (clipgamut linked from `spec_rgb.c`; greypoint copied verbatim from `pcond2.c:144–158`), reproduces pcond's output RGB per channel within max_ch/128 + 10⁻³·max_ch: every F1 patch median, and ≥ 99.9 % of pixels in each still. The failing fraction is reported. This tests the prediction on the clipped pixels too |

## Gates
| id | criterion |
|---|---|
| **AX-G1 F1 monotone (decisive)** | Y_A^new non-decreasing with source L for every colour (relative tolerance 10⁻⁶). If it fails, "clipgamut is the whole cause" was incomplete: **KILL A-extraction, and no gamut work starts** |
| AX-G2 S1 still passes | the A3-K0 gates on the *requested* display luminance 0.1 + 99.9·Y_A^new (recombined with B, before any display realisation): sky ≤ 2 cd/m², lamps/sky ≥ 10, poplar Weber ≥ 0.1, reversals ≤ 5 %, halo within 1.5× |

## Reported (no gate)
- S1 and S5: Y_A^new / Y_A^old (median, p1, p99; fraction differing by > 1 %).
- Fraction of pixels with Y_A^new > 1, i.e. requested above peak.
- Fraction whose requested (Y_A^new, u′v′_B) lies outside SDR100. This is the input to the next (gamut) PREREG.
- Per F1 patch: old, new and sensitivity Y; the monotonicity of the sensitivity Y_A′.
- The range of the von Kries luminance factor.
- Which images ran in DO_LINEAR, and which had `-c` disabled.
- Every still is run for C0/C3; gates only on F1 and S1.

## Outcome
- **C0–C3 and G1–G2 all pass:** freeze **axis-A extraction = Y_A^new** (the model stays pcond `-s -c`).
- **Any fail:** KILL; no tuning, no harness change inside this run.
- Next, in this order and each with its own PREREG:
  1. display realisation (chroma-priority Y_out = min(Y_A, Y_max(u′v′_B)) as primary, R1 Y-priority as control);
  2. P-4 v2 (reference L_eff) and R3 (N/A plus flat-field guard);
  3. the final corpus acceptance.
