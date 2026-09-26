# D1-DR: display realisation of (Y_A, u′v′_B) on SDR100, C-priority vs Y-priority

Pre-registered in `PREREG.md` (commit `f743089`, before the code).

    nix develop -c d1/a_extract/run_ax.sh; nix develop -c d1/display_r/run_s2_ax.sh     # frozen axis-A extraction (stills, F1, S2)
    tracks/temporal-glare-2009/py.sh d1/display_r/run.py                               # -> results_v1.json
    tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline                         # P-7 (dr_cprio, dr_yprio)

**Disclosed before running, not in the PREREG.**
- S5 has no sky mask. The S5 sky report (no gate) uses a proxy fixed in code before the run: the top 8 % of rows.
- A first launch crashed on an import bug, and a second ran out of disk; no gate was evaluated in either.
- A disk-hygiene fix to `run.py` (`cd570a6`) makes no computational change.

## Run v1 (`results_v1.json`): under the literal rule **both candidates KILLED**

| gate | C-priority | Y-priority |
|---|---|---|
| DR-G1 physical, finite | ✓ all | ✓ all |
| DR-G2 in-gamut identity | ✓ all | ✓ all |
| DR-G3 no hue reversal | ✓ stills and F1; **✗ S2 frame 3 (1 px)** | ✓ stills and F1; **✗ S2 frame 3 (the same 1 px)** |
| **DR-G4 F1 monotone** | **✗ red, blue** | ✓ all 7 colours |
| DR-G5 S1 | ✓ sky 0.318, lamps/sky 175, Weber 0.593, 0 reversals, halo 0.91 | ✓ sky 0.318, lamps/sky 315, Weber 0.593, 0 reversals, halo 0.91 |
| DR-G6 S3 | ✓ 0.753 | ✓ 0.753 |
| DR-G7 S2 | ✓ mean step 0.087 %, sky 0, flashes 0 | ✓ mean step 0.071 %, sky 0, flashes 0 |
| S-1 kept coordinate | ✓ Δu′v′ ≤ 1.8·10⁻¹⁶ | ✓ ΔY/Y ≤ 1.0·10⁻⁷ |
| S-2 direction | **✗ S3_bar** (Y_out/Y_req = 1 + 10⁻⁷); **✗ S2 frame 3** | ✓ |
| S-3 minimality | **✗ F1** (3072 px, max channel 99.94); **✗ S2 frame 3** | ✓ |

## Diagnosis of each failure (after the run; nothing changed)

**G3 on S2 frame 3, both candidates: a measurement artefact of our own sRGB encode/decode pair.**
- The single failing pixel is **in-gamut**, so both candidates leave it untouched (x = x₀, G2 ✓).
- Its blue channel is linear 0.0031308, exactly the encoder's knee.
- The encoder (`d1/pipeline/pipeline.py`, `d1/display_r/run.py`) takes the power branch for lin > 0.0031308 and
  writes 0.0404499. That is below the decoder's knee (`d0/display_model.py`: v ≤ 0.04045 → linear), so the decoder
  uses the other branch.
- The two sRGB constants are standard, but they are not exact inverses in a ~10⁻⁸ band: Δhue 4.9·10⁻⁶ rad at
  chroma 6·10⁻⁴.
- The same artefact is behind the 3.6·10⁻⁸ Δu′v′ reported on S2 in the original acceptance.

**C-priority S-2/S-3 on S2 frame 3:** the same pixel. The round trip makes emitted Y fall below Y_req outside the
above-peak class.

**C-priority S-2 on S3_bar: a request below display black.**
- Y_A is ≈ −10⁻⁹ on some pixels (pre-gamut pcond output with X ≤ 0 inputs; 2398 px in S3_bar), so
  Y_req < 0.1 cd/m².
- No display can emit less than its black, so Y_out = 0.1 > Y_req by 10⁻⁷ relative.
- Y-priority is gated against clamp(Y_req), C-priority against raw Y_req. This asymmetry is a spec defect.

**C-priority G4 on F1: real, and predicted.**
- As L rises, B restores saturation, so Y_max(u′v′_B) falls towards the primary ceilings while Y_A rises.
- Blue: requested 17.9 → 24.5 → 49.9 → 91.2, emitted 8.4 → 7.7 → 7.5 → 7.3. Red plateaus at 21.3–21.5.

**C-priority S-3 on F1: real.**
- Mixed-class pixels: saturated red at 31.6 cd/m² is first scaled so its max channel = 100. Then its green goes below
  display black, and the shared fallback projects it towards white, lowering the max to 99.94.
- So on that class C-priority, as specified, reduces Y more than the minimum.

## Reported numbers

**S1 lamps** (lamp mask dilated by 3 px; core Y_req ≥ 90, 4856 px; shoulder 50–90, 372 px):

| | C-priority | Y-priority |
|---|---|---|
| core: Y_out/Y_req (median) | **0.083** | 0.146 (clamped to 100 of a larger request) |
| core: chroma retention | **1.0** | **≈ 0** (white) |
| shoulder: Y_out/Y_req | 1.0 | 1.0 |
| shoulder: chroma retention | 1.0 | 1.0 |

- The shoulder is fully in-gamut in both.
- The whole trade-off sits in the core, where pcond requests far above peak.

**S5 sky proxy.** B chroma median 0.1043 → C-priority 0.1043, Y-priority 0.0999. 34 % of the proxy region lies
outside SDR100, but only 4 % of chroma is lost under Y-priority. **As predicted, the blue sky stays: a B residual,
not a DR failure.**

**F1 chroma retention, Y-priority**, source 3.16 → 100 cd/m²: red 1.0 / 0.87 / 0.27 / 0.02; blue 0.66 / 0.50 / 0.20
/ 0.02; warm lamp 1.0 / 1.0 / 1.0 / 0.15.

**Old P-4** (information only): identical for both candidates (S4 0.937, S5 0.968). The candidates do not change
luminance order; `-c` does.

## Outcome
- Under the pre-registered decision rule, **both candidates are KILLED**:
  - C-priority fails on real grounds: G4 (F1 red and blue) and S-3 (the mixed class);
  - Y-priority fails only DR-G3 on one in-gamut pixel that it does not touch, i.e. an artefact of our emission
    measurement.
- This is not recoloured green. The encoder-knee correction is pre-registered separately (`PREREG_v2.md`) before any
  re-run.
