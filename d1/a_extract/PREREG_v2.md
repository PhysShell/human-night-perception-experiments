# D1-AX v2 pre-registration: one correction (DO_LINEAR units), everything else as `PREREG.md`

Committed **before** the corrected code runs. Run 1 (`README.md`, commit `e898ff0`) failed C2/C3 on every still
because the DO_LINEAR branch was read as Y = (dlum/wlum)·L_eff/Ldmax.

**The only change**, derived from the pinned source and not fitted:
- In `pcond.c`, the DO_LINEAR block sets scalef, writes EXPOSURE, then divides scalef by WHTEFFICACY for cielum input.
  `sfscan()` then scales the colour by scalef.
- `putmapping()` prints dlum = scalef·inpexp·WHTEFFICACY·wlum.
- Hence Y_map = (dlum/wlum)·L_eff/**179**. No ldmin offset, no clipping before `clipgamut`.

The mapped branch, M, the clipgamut harness, the tolerances, the controls C0–C3, the gates G1–G2 and the outcome
rule are unchanged.
- The 1.795–1.797 ratio seen in run 1 is 179/100 × 1.003–1.004. The pre-registered prediction for v2 is a ratio of
  1.003–1.004 on the stills, inside the RGBE tolerance (max/128).
- If any control fails again: **KILL A-extraction**. No further harness correction.
- F1 is unaffected (mapped branch), so its run-1 values must reproduce exactly.
