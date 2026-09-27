# N1.6 RoadLine-A2 pre-registration: the direct true-radius reference as the far-lamp stimulus

Committed **before** any A2 code or output. **A2 is a new, separate experiment, not a repair of A1.**

## History, unchanged
- **RoadLine-A1:** FAIL. Run 1 was invalid (far clip); R1 and R2 failed.
- **Addendum 5:** FAIL (convergence of sub-pixel emitters; R1v2 at 50 m).
- **Addendum 6:** FAIL. The M2.5 enlargement 0.22 → 0.70 px does not preserve the 1600 m output-pixel stimulus
  (L1 0.154 > 0.10). That is the result, and it is not reinterpreted.
- A1 stays KILL for good.

## Why A2 is admissible
The true-radius reference was **not** invented after the failure. Addendum 6 built it beforehand, as the physical
standard for judging the 0.7 px approximation. The approximation failed against it; the reference itself passed:
- radius 0.105 m, no enlargement, no surrogate reconstruction, Cycles' own pixel filter, 16 384 spp;
- seed-to-seed energy 0.37 % (800 m) and 0.32 % (1600 m); raster L1 between seeds 0.008 and 0.020;
- the photometry chain matches LM-63 (R1 0.983–0.998 for all six in-frame lamps; the addendum-6 aperture of emitter
  radius + 1.5 px stays the R1 estimator, and no new R1 estimator is introduced).

## Inputs (all existing; **no new Blender render**)
- **Base:** `work/A6/base.exr`. Raw Cycles, 4096 spp, no OIDN; the 800/1600 m camera emitters absent, their IES road
  lighting present.
- **Far references:** `work/A6/ref_0.exr`, `ref_1.exr` (true radius, 16 384 spp, seeds 0 and 1).
- Nothing changes: no enlargement, 4×, resampling or new filter, and no change to geometry, emitter sizes, sky,
  LM-63, base spp or pixel filter.
- Scene-linear sums in Cycles units, then × 179 → cd/m²:
  - `in_s0 = base + ref_0`;
  - `in_s1 = base + ref_1`;
  - **canonical = base + (ref_0 + ref_1)/2**: the mean of two independent unbiased estimates of the same signal.

## Order (fixes an order conflict in the request)
The A1 rule requires the comparator exposure to be committed before *any* D1 output of the stimulus exists.
1. Build the three inputs.
2. **The plain-Blender comparator** (factory AgX, whole stops) on the **canonical** input. Exposure chosen from a
   ladder and **committed before any D1 run** of A2.
3. D1 on `in_s0` and `in_s1` (robustness gate), then on canonical.
   - Each runs through the frozen extraction (C0 self-check) and the Y-priority display.
   - `d1/verify_manifest.sh` runs before and after.
4. V0 on canonical.

## Gates
| id | criterion |
|---|---|
| **G-A2 robustness** (D1 is nonlinear) | D1(`in_s0`) vs D1(`in_s1`), for the 800 and 1600 m lamps: the display-domain background-subtracted lamp signal (aperture emitter radius + 1.5 px, annulus background as in addendum 6) differs **≤ 2 %**; **and** R4 ordering and R5 presence are identical between the two over all in-frame lamps |
| **R3** | on canonical: extraction C0/C2/C3; display gates G1–G3, S-1…S-3 (known knee artefact class `d1/ERRATA.md` E1: FAIL stays FAIL if it occurs, classified) |
| **R4 ordering** | on canonical, as pre-registered, with the addendum-6 estimator |
| **R5 presence** | on canonical: D1 vs the linear anchor (N1 raw variant; anchor = the field crop), with the addendum-6 estimator; one 16-bit code above the annulus background |
| **V1–V6** | the external observer, D1 image alone, sheet format |
| **V7 blind** | D1 / V0 / plain Blender, all from the **same canonical input**; seed-0 permutation, key hash committed before showing |

## KILL
- **G-A2 fails:** A2 is KILLed for good. There is no 32k or 64k spp, and no new trick.
- **R4 or R5 fails on canonical:** a real D1 finding on the original use case. It is recorded and classified, not
  repaired inside N1.
- **D1 judged worse than V0 on the blind sheet, with no D1 advantage anywhere:** as in the RoadLine PREREG.

## Predictions
- **G-A2 passes.** The ~0.3 % energy seed spread is far inside 2 %, and D1's A is a single global scale for this scene.
- **R4 and R5 pass.**
- Visually: a few lamps at 50–200 m, faint points at 400–800 m, and 1600 m at the edge of presence. This is the
  modern-LED "short road".

## A2 results before the verdict (`a2_A.json`)
**Automatic gates, all PASS:**
- **G-A2:** far display signal seed 0 vs 1: +1.05 % (800 m), −0.11 % (1600 m); R4/R5 identical.
- **R3:** C0 bit-identical, C2/C3 at 100 %, display gates all PASS.
- **R4:** no inversion.
- **R5:** presence identical to the linear anchor.

**Stated plainly:**
- D1's A (pcond's linear branch, anchor 2.55 Y_A per cd/m²) puts the display peak at **0.39 cd/m² of scene**.
- The lit near road (≈ 1.2 cd/m²) and **all six lamps reach the display peak**. Peak pixels per lamp: 50 m 49 of 49,
  1600 m 2 of 49.
- **R5 is therefore trivially true.** R4 holds through the size of the saturated spot only: display signal 2.6·10⁻³ →
  8.4·10⁻⁵.
- Frame fraction at the peak: **D1 17.9 %**, raw anchor 16.2 %, V0 16.2 %, plain Blender 0 %.

**Blind sheet** `renders/blind/sheet.png` (X, Y, Z plus far-lamp crops); seed-0 permutation of D1 / V0 / Blender
AgX +7, all from the canonical input.
- Key sha256 `0465859c9d40ac53b267bcc8a7568d9f7f7d5f8e355008b1e6ade132c2b2842b`.
- My reading, written before the verdict: sha256 `4e6b13dd5229e5a7724e8bb54c657817f846a5d0dacdc05250390875ee070992`.
