# D2-A1b V7 acceptance: blind RoadLine comparison A1b vs V0 vs Blender AgX +7

Committed **before** the blind sheet is built. It is the last acceptance gate before freezing A1b as a D2 candidate.
0 renders; all three images already exist.

## Why
The original RoadLine KILL (`n1/roadline/PREREG_A2.md`) was not only V6 (broad saturation). It was also **V7**:
- frozen D1 was judged worse than plain Blender;
- and worse than V0.

A1b removed the saturation. Its stage 1 and stage 2 passed, but V7 was never re-tested.

## Stimuli (all from the RoadLine-A2 canonical input)
| role | file |
|---|---|
| A1b (the shoulder f = Y/(1+Y)) | `d2/a1/renders/roadline_A1b.png` |
| V0 (pcond) | `n1/roadline/renders/A2_v0.png` |
| Blender AgX +7 (the pre-committed comparator, `n1/roadline/comparator_A2.json`) | `n1/roadline/renders/A2_comparator.png` |

**Frozen D1 is not included.** It is known to be bad, and a fourth card would only make guessing easier.

## Blind sheet
- **The same layout as the A2 blind sheet:**
  - per label, the full frame plus the far-lamp crop (rows 330–440, cols 900–1180, nearest);
  - 8-bit conversion as in A2;
  - labels X/Y/Z from a numpy permutation with **seed 1**, since seed 0 was used by A2 and A2c;
  - a salted key, **its sha256 committed before the sheet is shown**, and the key committed at the reveal.
- **My reading** is hashed from the command output and committed before the verdict. It does not count.
- **Stated limitation:** the observer has seen V0 and Blender +7 on the A2 sheet, so recognition is possible.

## Questions (the original RoadLine set)
- **Per label:** V1–V6 as on the original RoadLine sheet (V5 N/A).
- **Which** looks like the most convincing night road?
- **Which** looks worst?
- **The full order.**

## Gate (one)
**A1b must not be visually worse than Blender.** That is, the observer ranks A1b above Blender, or ties them.

**Also required** (consistency with stage 1): A1b gets no V6 FAIL.

## Outcomes (fixed now)
- **PASS:** V7 is restored and the causal loop closes.
  - The loop: RoadLine frozen D1 had V6 and V7 FAIL → D2-A1 research → the fixed A1b shoulder → full corpus and
    temporal PASS → RoadLine blind comparator, V7 restored.
  - **Next:** freeze a separate D2 candidate baseline **without rewriting D1**. It records the exact A1b operator,
    manifests/hashes, the accepted evidence and the G1 limitations. The proposed tag is `d2-a1b-candidate`, created at
    the user's instruction.
  - The curve is not touched further.
- **FAIL** (A1b ranked below Blender):
  - "The original failure is fixed" **may not** be written. The shoulder solved the saturation, but not the whole
    perceptual acceptance problem.
  - The observer's stated reason is recorded. If it is the cold/lavender cast, it points at the frozen B rod-term tint
    (`d2/b2`) as the remaining loss.
  - No change to A1b.

## Prediction (recorded before building the sheet)
- **V0 is worst:** its broad road saturation is the same as frozen D1's minus the B tint.
- **A1b vs Blender: uncertain, a slight lean to FAIL.**
  - Blender +7 renders a neutral grey road with a smooth gradient.
  - A1b has a comparable gradient but a cold/lavender cast from B, which the observer has marked as a D1 disadvantage
    before.
  - I expect Blender ≥ A1b, possibly tied.

## Sheet built (before the verdict)
- Sheet: `renders/V7_blind_sheet.png`, made by `sheet_A1b_V7.py` (seed 1).
- **Key** `work/V7_blind_key.json` (git-ignored until the reveal): sha256 `7800f99fea0720dfdcc8c6bab5867ecd105d87f6457d9f02499bff0adb4f60b8`.
- **My reading** `V7_my_reading.txt`: sha256 `0a22f6dea4c34eb75574cd288383568ecfdcccbad87b8c9de7854915d2e1b042`.
