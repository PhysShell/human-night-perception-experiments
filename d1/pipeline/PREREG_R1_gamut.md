# D1-R1 pre-registration: display-aware minimum chroma projection at the A0 recombination

Committed **before** any R1 code exists. Fixes only R1 from the D1 acceptance (`README.md`, commit `4b1750c`):
the A0 recombination x = b·(Y_display/Y(b)) has no gamut step, so a (Y_A, u′v′_B) pair that SDR100 cannot emit is
clipped per channel. That clipping produces S5 4.1 % above peak, the saturated clipped blue sky, and the F1 red/blue
luminance non-monotonicity. A and B are unchanged. The old acceptance result stays as recorded.

## The operation (no fitted constants)
- Display gamut in emitted linear Rec.709: every channel in [0.1, 100] cd/m². This is SDR100 DARK, as
  `d0/display_model.py` decodes it: emitted = 0.1 + 99.9·EOTF(code) per channel.
- Per pixel:
  - x₀ = b·(Y_A/Y(b)) (the A0 recombination, unchanged);
  - w = Y_A·(1, 1, 1), the display white at the same luminance;
  - x(t) = w + t·(x₀ − w), with t ∈ [0, 1].
- Additive mixtures lie on straight lines in u′v′, and (1, 1, 1) has exactly the Rec.709 white chromaticity (the
  exact white used by B4). So x(t) keeps Y = Y_A exactly and moves B's u′v′ along the straight line to the white
  point. The u′v′ hue angle is kept; the chroma radius scales monotonically with t.
- **t = the largest value in [0, 1] with x(t) inside the gamut.** The constraints are linear in t, so it is
  computed in closed form, which gives the same t as a bisection but exactly:
  - for channel i with d_i = x₀ᵢ − Y_A > 0: t ≤ (100 − Y_A)/d_i;
  - with d_i < 0: t ≤ (0.1 − Y_A)/d_i;
  - t = min(1, all of these).
- In-gamut pixels get t = 1: the output is x₀ bit for bit (`np.where`, not recomputed).
- Y_A always lies in [0.1, 100] by construction (0.1 + 99.9·Y_rel). If pcond's Y_rel falls outside [0, 1], that
  pixel's grey itself is out of gamut. Its count is **reported**; it is clamped to the nearest bound and flagged. It
  is not hidden.
- Encoding and measurement are unchanged: SDR100 sRGB 16-bit PNG, emitted light via `d0/display_model.py`.

## Specification change recorded here (not a post-hoc relaxation of R1)
Old P-2 ("displayed u′v′ = B's on unclipped pixels") cannot be required where B's chromaticity is physically
unreachable at Y_A. It is split:
- **P-2a** (t = 1, in gamut): |Δu′v′| (displayed vs B) ≤ 10⁻⁶. Same as old P-2.
- **P-2b** (t < 1): |ΔY|/Y_A ≤ 10⁻⁶; |Δhue| ≤ 10⁻⁶ rad (for pixels with B chroma > 10⁻⁶); displayed chroma ≤ B's
  chroma; tightness: at least one channel sits on a gamut bound within 10⁻⁹ relative (t is the maximum, not merely
  admissible).

## R1 gates (all on the float code before 16-bit quantisation, as in the acceptance)
| id | criterion |
|---|---|
| R1-G1 in-gamut identity | pixels with t = 1 identical to the old pipeline's recombination (max \|Δ\| = 0) |
| R1-G2 P-2a | as above, every still, F1 and all S2 frames |
| R1-G3 P-2b | as above, same set |
| R1-G4 gamut | every channel in [0.1, 100] (tolerance 10⁻⁹ relative) on every image; P-3 above-peak = 0 |
| R1-G5 F1 monotone | displayed Y non-decreasing with source L for every colour; no patch above peak at any level |
| R1-G6 numerics | finite; no NaN or Inf |
| R1-G7 S5 visual | the S5 sheet no longer shows a clipped saturated-blue region. Visual, stated as such |

**KILL.**
- Any of G1–G6 fails, or G7 shows a new artefact class (hue reversal, banding at the projection boundary,
  posterisation), or any in-gamut pixel loses chroma: **KILL this projection**. The next step is then a different
  gamut mapper (a separate pre-registration).
- No tuning.

## Reported (not gated)
- Fraction of pixels with t < 1 per image, and the distribution of t (median, p5).
- Chroma lost on the S5 sky and on the S1 lamps: the S1 lamp chroma ratio against the old pipeline.
- P-5, P-6 and P-7 re-run. S1/S3 should be (near) unchanged because few pixels are projected.

## Then: the acceptance re-run with the R1 pipeline
- Same PREREG gates, with P-2 → P-2a/P-2b as above. Everything else is unchanged.
- **P-4 is still evaluated exactly as originally defined.** S4, S5 and S3_nobar are expected to remain FAIL. That
  history is kept; P-4 v2 is a separate, later pre-registration.
- Output: `d0/work/out/d1_pipeline/r1_gamut/`, `acceptance_r1.json`. The old `frozen/` and `acceptance.json` stay
  untouched.

## Prediction
All of G1–G6 pass. The S5 sky desaturates towards a paler blue at the same luminance. F1 red and blue become
monotone and lose saturation above their primaries' ceilings (red > 21.3 cd/m², blue > ~7.3 cd/m²).
