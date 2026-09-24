# Display rendering: open questions after D0 and D0.1

Only questions that D0's measurements actually raised. No answer is proposed here, and D1 is not started.
Numbers: `d0/README.md`, `d0/results/tables/summary.md`.

1. **Where should night brightness come from?** After the D0.1 audit (`d0/input-semantics.md`) this is two
   questions, one per input class.
   - **1a. Absolute-appearance models** (pcond, iCAM06) take the physical level and derive brightness from their
     adaptation machinery.
     - pcond puts the S1 sky at 0.3 cd/m² (3× display black).
     - iCAM06's machinery *does* respond to 4·10⁻⁴ cd/m². But its rod term lifts dark regions, and its relative
       display stage re-stretches the result, so the physical night renders at 27 cd/m²: lighter than the same
       image at daylight level (18 cd/m²).

     Is there an absolute-appearance model whose *display stage* keeps the absolute level, so that a scotopic
     scene is not re-normalised to full range?
   - **1b. Relative / scene-referred renderers** (Mantiuk08, ACES, Reinhard02, CTRL-KEY) need an external
     appearance/exposure anchor *by design*. The sky moves from display black to 38 cd/m² over ACES EV 0…+18, and
     from 5 to 64 cd/m² over Mantiuk08's WHITE_Y. This is not a defect.

     Which documented rule should set the anchor for a night scene: a stated adaptation luminance, a viewer
     judgement, or a convention such as ACES 1.0 = 100 cd/m²? Should it be the same rule for every scene? (For
     ACES, S4 needs ~8–12 stops less than S1.)
2. **WHITE_Y / exposure as the real design axis.**
   - Mantiuk08 WHITE_Y: two defensible anchors 5.4 decades apart.
   - ACES exposure: a family, no member of which gives a dark sky, separate lamps and warm lamps together (HDR1000
     at EV +12 comes closest).

   Should the project fix these anchors from a documented convention, from viewer judgements, or leave them as
   exposed axes?
3. **Giant white lines vs individual lamps.** Where a donor's curve clips many distant lamps (CTRL-KEY, iCAM06,
   Mantiuk08 auto, ACES at any EV that shows the sky), the ribbon becomes one white plateau up to ~110′ long. Donors that keep lamps at ~1′ (pcond,
   Reinhard02, Mantiuk08 anchor, ACES EV 0) do so by very different means (compression, key, WHITE_Y, a black sky).
   Which of these is compatible with P3 (salient) and P5 (no giant disks) at the same time, on our scene?
4. **P4 without crushing.**
   - No donor simulates ocular glare.
   - The only case where the bar next to the lamp lost detectability with the sky *not* crushed was Mantiuk08's
     mapping for 500–1000 cd/m² displays: sky 0.018 cd/m², lamp at peak.
     - HDR-VDP-3 detects the bar with P = 0.43–0.67 with its ocular MTF on, and 0.98 with it off.
     - So the loss comes from the observer model's optics acting on the *displayed* luminance ratio, not from the
       operator.
   - Where the bar "disappears" in CTRL-PHOT or ACES EV ≤ +8, the whole sky is black.
   - Is a displayed luminance ratio that lets the viewer's own eye produce the veil a legitimate route to P4? Or
     does the project need a rendered glare cue (explicitly out of scope for D0)?
5. **Warm colour vs range.** Saturation retention ranges from ≈ 0 (clipped to white: CTRL-KEY, iCAM06, Mantiuk08 even with
   `--tone-value max`) to 0.6–1.1 (ACES at EV 0, where only the lamps are not black; ≤ 0.12 at any EV that shows the sky). Is warm-hue retention of distant sodium/LED lamps worth a
   dedicated test at P6?
6. **Temporal: which breathing is display grid, which is operator?**
   - D0's region-sum temporal measures are flat for every donor (≤ 3 %, no pumping).
   - The per-lamp display-grid breathing found in M2.6 (~11 %) was not measured per lamp here.
   - A per-lamp tracker (as `m25/analyse_clip.py`) on the donor clips would separate the two.
7. **Missing inputs.**
   - No daytime/mixed calibrated scene: the Fairchild site is behind a bot check.
   - The MPI HDR scenes are blocked (403).
   - A manually downloaded calibrated daytime HDR would complete S5.
8. **Donor gaps.**
   - Mantiuk08: the CLI accepts `--display-size` but the operator never uses it, in 2.2.0 and in master c860691
     (source-verified). Testing the geometry axis the paper describes would need a code change: out of scope for a
     native run. 24 fps is unsupported in both builds.
   - BT.2446 needs a display-referred HDR master first (e.g. ACES HDR1000 → BT.2446 → SDR would be a
     *combination*, excluded in D0).
   - Tariq 2023 has no public code.
9. **Observer diagnostics.** P_det (HDR-VDP-3) saturates at 0 or 1 for most outputs on S3. It says little except
   in the Mantiuk08-HDR case. A graded diagnostic, or a psychophysical check with the viewer, would be needed to
   compare P4 behaviour.
