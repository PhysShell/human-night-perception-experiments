# D2-A2c pre-registration: is H2v2 a valid proxy for "broad roadway saturation"?

Following `d2/TEMPLATE.md`. Committed **before** the blind sheet is built.

**A2b stage 1 stays a literal KILL on H2v2, for good.** This experiment changes no policy.

## 1. Question
Is H2v2 (road luminance ceiling ≤ 0.1 %) too strict a surrogate for the visual failure it was built to proxy? That
failure is "broad roadway saturation", defined as V6 in N1.6 RoadLine-A2 and as the pre-registered A2b V6.

## 2. What is held fixed
**No change:** no algorithm, no percentile, no constant, no render, no new image. The three existing RoadLine-A2
canonical D1 outputs are used as they are:

| role | file | scale |
|---|---|---|
| frozen D1 (known V6 FAIL; the sensitivity control) | `n1/roadline/renders/A2_canonical_final.png` | pcond `-s -c` |
| oracle A1a2 | `d2/a1/renders/roadline_a1a.png` | s = 0.2641 |
| Q99.9 guard A2b | `d2/a2/renders/roadline_A2b.png` | s_hist = 0.2692 |

## 3. Blind sheet
- **Labels.** X, Y and Z are assigned by a seed-0 numpy permutation.
  - The key is written to `A2c_blind_key.json`.
  - **Its sha256 is committed before the sheet is shown.** The key file is committed at the reveal.
- **Layout.** Per label: the full frame, plus **one identical road crop**: rows 410–820, columns 560–1360 (the lit near
  and middle road), shown 1:1 in nearest-neighbour.
- **Format.** The sheet format that opens for the observer: matplotlib, ~960 px wide, black background.
- **No numbers on the sheet.**
- **My reading** is written, hashed and committed before the verdict, and does not count.
- **Stated limitation.** The observer has seen the frozen D1 and A1a images before (A2 and A1a sheets), so recognition
  is possible. The blind layer mainly separates the oracle from A2b.

## 4. Questions to the observer (per label, answered before the reveal)
1. **V6:** is there broad roadway saturation?
2. **V6:** is there a new A-side defect (beyond the declared white lamp cores and the B rod-term tint)?
3. **Comparative, the only addition, not a numeric gate:** among the labels without broad saturation, does one show
   noticeably worse loss of road gradient/structure than another? If so, which?
4. Optional: an order of preference.

## 5. Validity control (fixed now)
The frozen-D1 label **must** be judged to have broad roadway saturation. If it is not, the sheet cannot detect the
defect: **A2c is INVALID, not PASS**, and nothing about H2v2 is concluded.

## 6. KILL (the Q99.9 global-histogram branch is closed)
After the reveal, the A2b label:
- has broad roadway saturation; **or**
- is noticeably worse than the oracle label in road gradient/structure; **or**
- has a new A-side defect.

**Then:**
- the Q99.9 global-histogram policy is substantively dead;
- there is no 99.92, 99.95, road mask, or "only 0.028 stop";
- richer metering or adaptation (D2-B3) becomes earned.

## 7. PASS
The validity control holds, **and** the A2b label has V6 PASS (no broad saturation, no new A-side defect) **and** it is
not noticeably worse than the oracle. The recorded wording is then:

> A2b stage 1 remains a literal KILL on H2v2. A2c shows that H2v2 was over-strict relative to the pre-existing visual
> defect it was meant to proxy. The Q99.9 policy itself is not yet accepted.

**Only then:** a new prospective stage-2 PREREG, with the **unchanged** Q99.9 policy, on Camera C, the hero, B (if its
input is present) and the whole corpus. It is the stage 2 already written in `PREREG_A2b.md` section 4, including the
"active everywhere = ND filter" KILL.

## 8. Budget
0 renders; one sheet; minutes of CPU. D1 is untouched; `d1/verify_manifest.sh` runs before the sheet is built.

## Prediction (recorded before building the sheet)
- **The validity control holds:** frozen D1 has 82 % of the road at the luminance ceiling.
- **The oracle and A2b are visually indistinguishable,** being 0.028 stop apart. Their road ceiling fractions are
  0.07 % and 0.15 %, a few hundred pixels in the near-road hot spot.
- **Expected: PASS.**

## Sheet built (before the verdict)
- Sheet: `renders/A2c_blind_sheet.png`, made by `sheet_A2c.py` with a seed-0 permutation and a salted key.
- **Key** `A2c_blind_key.json` (not committed until the reveal): sha256 `fad1a45df74419ba75eafb70bf7082feaaba6d1f482fb8e62b80d43cc1c1d7cd`.
- **My reading** `A2c_my_reading.txt`: sha256 `832d45de53e6576dbf9cb50ddb2d00627b2808ce435c19e33bd30da749515f2c`.
