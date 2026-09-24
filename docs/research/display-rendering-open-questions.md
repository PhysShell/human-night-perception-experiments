# Display rendering: open questions after D0

Only questions that D0's measurements actually raised. No answer is proposed here, and D1 is not started.
Numbers: `d0/README.md`, `d0/results/tables/summary.md`.

1. **Where should night brightness come from?** Every donor places the sky somewhere between display black and a
   dusk grey:
   - D1a / ACES: 0.1 cd/m² (= black);
   - pcond: 0.3;
   - Mantiuk08 anchor: 5;
   - Mantiuk08 auto: 12;
   - iCAM06 / Reinhard02 / D1b: 27–50.

   Not one of them has a principled input for the viewer's night adaptation *state* at the scene (4·10⁻⁴ cd/m²):
   - pcond has one only implicitly;
   - Mantiuk08 assumes an eye adapted to 1000 cd/m², except through WHITE_Y;
   - ACES uses fixed dim-surround constants.

   Is there an existing, documented rule for "how bright should a scotopic scene look on a photopic display",
   rather than a free parameter?
2. **WHITE_Y / exposure as the real design axis.**
   - Mantiuk08 WHITE_Y: two defensible anchors 5.4 decades apart.
   - ACES exposure: a 16-stop range from all-black to day-like.

   Both are appearance-design parameters for a night scene. Should the project fix them from a documented
   convention (e.g. a stated adaptation luminance), from viewer judgements, or leave them as exposed axes?
3. **Giant white lines vs individual lamps.** Where a donor's curve clips many distant lamps (D1b, iCAM06,
   Mantiuk08 auto), the ribbon becomes one white plateau up to ~110′ long. Donors that keep lamps at ~1′ (pcond,
   Reinhard02, Mantiuk08 anchor, ACES) do so by very different means (compression, key, WHITE_Y, a black sky).
   Which of these is compatible with P3 (salient) and P5 (no giant disks) at the same time, on our scene?
4. **P4 without crushing.**
   - The only D0 case where the bar next to the lamp lost detectability *because of glare* was Mantiuk08 on
     500–1000 cd/m² displays: there the real display's glare in the real eye does it.
   - Where it "disappears" in D1a/ACES, the whole sky is black.
   - Is display-side glare (a bright physical display plus a dark surround) a legitimate route to P4, or does the
     project need a rendered glare cue (explicitly out of scope for D0)?
5. **Warm colour vs range.** Saturation retention ranges from ≈ 0 (clipped to white: D1b, iCAM06, Mantiuk08) to
   0.6–1.1 (ACES, per its CAM and gamut mapping). Is warm-hue retention of distant sodium/LED lamps worth a
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
   - Mantiuk08 in pfstools 2.2.0 ignores viewing geometry and 24 fps.
   - A newer pfstools git build would test the geometry axis the paper describes.
   - BT.2446 needs a display-referred HDR master first (e.g. ACES HDR1000 → BT.2446 → SDR would be a
     *combination*, excluded in D0).
   - Tariq 2023 has no public code.
9. **Observer diagnostics.** P_det (HDR-VDP-3) saturates at 0 or 1 for most outputs on S3. It says little except
   in the Mantiuk08-HDR case. A graded diagnostic, or a psychophysical check with the viewer, would be needed to
   compare P4 behaviour.
