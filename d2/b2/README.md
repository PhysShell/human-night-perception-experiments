# D2-B2: the warm-mesopic hue rotation in B. **KILL: it is the Cao/Kirk rod term, not a defect**

Pre-registered in `PREREG.md` (commit `94eb8dc`, before the code). `tracks/temporal-glare-2009/py.sh d2/b2/run.py`
→ `results.json`, `paths.png`. `d1/verify_manifest.sh` OK (recorded in `results.json`). D1 is unchanged.

| necessary condition | result |
|---|---|
| **N1 systematic** (every warm input rotates ≤ −15.5° at visible chroma) | **FAIL, on yellow only**. The Planckian 2200/2700/3000/3500 K, F1 warm_lamp and orange rotate towards red by −77°, −109°, −126°, −139°, −137° and −103° (min over L). Yellow (1, 1, 0) does not rotate: its path runs almost straight to neutral and flips there (`through_neutral`, the known B4-G2 case) |
| **N2 inside B** | PASS. The hero pool flank in scene-linear B: −31.9° (input hue 48.9° → 17.8°), reproducing the −31° seen on the display. Display mapping is not involved |
| **N3 not the rod term** | **FAIL**. With the frozen kernel's rod term off (`nightAdaptation` = 0), the rotation **vanishes exactly**: \|Δhue\| ≤ 3·10⁻⁵° for every warm input, the hero (+8·10⁻⁶°) and the F1 warm_lamp patches (0.0°) |

**F1 warm_lamp, Δhue with the rod term on / off:**

| L (cd/m²) | rod on | rod off |
|---|---|---|
| 100 | −0.5° | 0° |
| 10 | −1.6° | 0° |
| 1 | −5.8° | 0° |
| 0.32 | −11.9° | 0° |
| 0.1 | −28.0° | 0° |
| 0.032 | −74.9° | 0° |
| 0.01 | −122.5° | 0° |
| 10⁻⁴ | −150.8° | 0° |

**Reading** (`paths.png`).
- With the rod term off, the chroma stage takes every warm input to white along a straight line; its hue is kept, as
  B4-G4 requires.
- With it on, the Filament/Cao rod-intrusion signal (KC pathway, k = {0.2, 0.2, 0.3}) adds a tint of fixed
  direction, below and to the left of white. The warm paths bend through the red/pink sector and arrive at white from
  there. The hero's pinkish pool flank (0.02–0.15 cd/m²) sits on this bend.
- This is the Purkinje term that D1 deliberately keeps (B4-G4, B4-G7), exactly as predicted before the run.
- Changing its direction for warm hues would need an independent psychophysical reference. None is in the
  repository, and a search is outside this item's budget.

## Outcome
- **D2-B2 is closed: not a defect under the frozen model.** No correction was tuned.
- **Official limitation (added to the D1 record by this item):** B's Cao/Kirk rod tint, added to warm light, reads
  pinkish at pool-flank luminances (≈ 0.02–0.3 cd/m²). On the N1 hero the observer preferred V0's neutralised pool.
- Whether that tint direction is right for warm stimuli is a question for data (e.g. mesopic hue-shift psychophysics),
  not for this code.
- **Noted, not opened:** B adapts **per pixel**. A pool flank is treated as near-scotopic even though an observer
  looking at the lit pool is adapted higher. That is a separate hypothesis: with a higher adaptation state, the rod
  term at these pixels would be smaller.

**Next:** N1.5 with the current D1 and this residual documented.
