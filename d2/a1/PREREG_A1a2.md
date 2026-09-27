# D2-A1a2 pre-registration: a corrected falsifier of global-scale sufficiency, with an independent hold-out

Committed **before** any A1a2 code or output. It is a new experiment: **A1a stays a literal KILL** (H2,
`README.md`, `e382455`), and nothing is rewritten.

## Why A1a2 exists, and why not A1b now
- **H2 did not measure A1a's hypothesis.** It counted "any channel at the ceiling", so it caught axis B's known
  rod-term blue tint (the blue channel at 65535 while the display luminance is 87–100 cd/m²). It did not catch
  axis-A luminance saturation.
- A shoulder (A1b) would also reduce that blue ceiling. It would therefore "pass" a test that never failed on the tone
  curve's shape: a bad diagnostic.

## Question (unchanged from A1a)
Is a single global linear scale sufficient to remove the RoadLine luminance saturation?

## Frozen
- s = **0.2641**. No new exposure fitting; the **same s** is applied to the hold-out.
- The RoadLine-A2 canonical input; all of D1's B and display logic; the Y-priority display.
- Only the change A1a already made: Yreq = 0.1 + 99.9 · s · Y_A.

## Measurement correction (the only change)
- **H2v2 road luminance ceiling:** the fraction of road-surface pixels (the same geometric mask) with **display
  luminance Y_disp ≥ 99.9 cd/m²** is ≤ **0.1 %**.
  - On RoadLine this is **not prospective**: 0.07 % is already known. It only confirms the metric fix and is not
    counted as new evidence.
- **C1 chromatic ceiling:** the fraction of road pixels with any channel at 65535 while Y_disp < 99.9. **Report
  only**, classified as a B-side effect.
- H1 (any-channel frame ceiling) stays as a report. H3, R4 and R5 are unchanged (A1a: PASS).

## Independent hold-out: N1 Camera C
- Why C: source in frame, bright pool; not used to derive s.
- Input: `n1/work/view_C/view_cdm2.exr`, the frozen extraction `N1_C`, the same s.
- Baseline, frozen D1 on C: display-luminance ceiling 0.444 % of the frame, any-channel ceiling 1.170 %, floor 0.

| id | criterion |
|---|---|
| **HO1 no new luminance saturation** | frame fraction with Y_disp ≥ 99.9 cd/m² ≤ the frozen-D1 value on C, **0.444 %** |
| **HO2 no darkness collapse** | frame fraction with all channels at the display floor ≤ **0.62 %** (the accepted-output anchor, as H3) |
| **HO3 source readable** | the lamp head (C pixel 961, 153): max-channel code in a 3-px-radius aperture ≥ the median of the 4.5–7 px annulus + 1 code (the presence rule) |
| **R3** | display gates. The known knee class (`d1/ERRATA.md` E1): FAIL stays FAIL, classified |
| **V6 hold-out** | the external observer, the A1a2 C image alone: is there a **new A-side defect class** (broad saturation, collapsed darkness, unreadable source)? Declared residuals: white lamp core; the B rod-term tint |

## KILL
- H2v2 fails;
- **or** HO1, HO2 or HO3 fails;
- **or** V6 finds a new A-side defect on the hold-out.
- **Then A1b** (a shoulder) is the honest next experiment.

## PASS reading (fixed now)
- "A1a was a literal FAIL from invalid H2 instrumentation. The substantive hypothesis — a global linear scale can
  remove the RoadLine luminance saturation — survives on an independent hold-out."
- **Linear shape not falsified; pcond's exposure selection is the remaining suspect.**
- D2-A1 closes. A separate D2 item on selection/adaptation (where CIE 257 / D2-B3 may enter) is opened only by the
  user.

## Budget
No new Blender render; minutes of CPU. `d1/verify_manifest.sh` before and after.

## Prediction
- H2v2 passes (known: 0.07 %).
- HO1 passes: C's pool and core become darker, so less reaches the peak.
- **HO2 is the risk:** C's dark foreground (barn moon shadow) drops 1.92 stops towards the floor.
- HO3 passes: the lamp core is ≫ its surroundings.

## A1a2 results before the verdict (`results_a1a2.json`, code c1b76d9)
- `d1/verify_manifest.sh` before and after: all OK.
- **RoadLine (confirmatory only):** H2v2 road luminance ceiling **0.070 %** ≤ 0.1 % PASS. C1 chromatic ceiling (report)
  1.08 %. H1 any-channel frame ceiling (report) 0.29 %.
- **Hold-out Camera C, same s:**
  - HO1 luminance ceiling **0.046 %** ≤ 0.444 % PASS (any-channel ceiling, report: 0.061 %);
  - HO2 floor **0.000 %** ≤ 0.62 % PASS;
  - HO3 lamp head 60 643 codes above the annulus ≥ 1 PASS;
  - R3 display gates G1–G3, S-1…S-3 all PASS.
- **Automatic: PASS.** V6 pending: external observer, sheet `renders/holdout_C_a1a2_sheet.png`.
- My reading, written before the verdict: `A1a2_my_reading.txt`, sha256 `00ab5916aa7ce86a4c66e9a5b40da0aee47e249bfdf2a417d7aa34a31f87c0d1`.
