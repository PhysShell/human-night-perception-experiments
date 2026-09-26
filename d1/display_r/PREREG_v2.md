# D1-DR v2 pre-registration: two measurement/spec corrections, the mappers unchanged

Committed **before** re-running. v1 (`README.md`, commit `346bb1d`) killed both candidates.

## Corrections (neither touches C-priority or Y-priority themselves)
1. **Encoder knee = exact inverse of the decoder.**
   - The output encoder used lin ≤ 0.0031308 → 12.92·lin, else the power branch. The decoder
     (`d0/display_model.py`) switches at v ≤ 0.04045.
   - In the band 0.0031308 < lin < 0.04045/12.92 the power branch yields v < 0.04045, and the decoder then decodes
     it with the other branch.
   - v2 encodes with the knee at **lin ≤ 0.04045/12.92**, the exact inverse of the decoder. The decoder is not
     changed.
   - This affects only pixels whose channel lies in a ~10⁻⁸ band. v1's only Y-priority failure (S2 frame 3, 1 px) and
     C-priority's S2 S-2/S-3 failures come from it.
2. **C-priority S-2 reference = clamp(Y_req, 0.1, 100), as for Y-priority's S-1.**
   - v1 compared C-priority against the raw Y_req, which can be ≈ 10⁻⁹ below display black (Y_A ≈ −10⁻⁹ on
     X ≤ 0 inputs).
   - No display can emit below its black, so that was an asymmetric spec defect.

Everything else is unchanged: gates, tolerances, corpus, core/shoulder reporting, decision rule. `run.py` differs only
in these two lines.

## Predictions
- **Y-priority passes every common and specific gate.**
- **C-priority stays KILLED** by DR-G4 (F1 red, blue) and S-3 (F1 mixed class). Those are real and unaffected by
  either correction.
- All other numbers change by ≤ 10⁻⁶ relative.
- If Y-priority fails anything in v2, it is KILLED too. The next step is then a hybrid, pre-registered separately.
