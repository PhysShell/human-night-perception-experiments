# D2 decision record: close the D2 research line

A record only: no new experiment, no candidate tag. D1 stays the immutable baseline (tags `d1-pipeline-accepted`
→ 0ee0765, `d1-baseline` → 8596641; `d1/verify_manifest.sh` green throughout).

## Causal chain
```
Frozen D1 on N1.6 RoadLine-A2
  -> V6 FAIL (broad roadway saturation, axis A)       n1/roadline/PREREG_A2.md
  -> V7 FAIL (worse than V0 and plain Blender AgX +7)

D2-A1 (global linear scale)
  A1a  literal KILL (H2 any-channel gate: my instrument error)          d2/a1/PREREG.md
  A1a2 PASS: linear shape not falsified; oracle scale survives hold-out C d2/a1/PREREG_A1a2.md

D2-A2 (exposure selection)
  -w   KILL (-0.009 stop)                                                d2/a2/PREREG.md
  A2b  Q99.9 guard: stage 1 literal KILL (H2v2 0.150 %)                  d2/a2/PREREG_A2b.md
  A2c  PASS: H2v2 over-strict vs the visual defect                       d2/a2/PREREG_A2c.md
  A2b stage 2 FAIL: S1/S2 crushed (-3.36 stops) -> global-scalar highlight/shadow trade-off
                                                                         d2/a2/PREREG_A2b_stage2.md
D2-A1b (fixed shoulder f(Y) = Y/(1+Y), A-only, no parameters)            d2/a1/PREREG_A1b.md
  stage 1 PASS (RoadLine V6 fixed, S1 unchanged)
  stage 2 PASS (hero/B/C, corpus, S2, P-7; E1 literal FAILs classified)
  T0: atmosphere robust; glare coupling unresolved (C2 holds either way) d2/a1/PREREG_T0.md
  V7 blind: FAIL (Blender > A1b > V0)                                    d2/a1/PREREG_A1b_V7.md

D2-A3a (oracle exposure before the shoulder, -1.41 stops)                d2/a3/PREREG_A3a.md
  gap shrinks (clear loss -> small but visible), V7 still FAIL -> exposure branch KILL

D2-B2: the warm/pink shift is the intentional Cao/Kirk rod term;
       no justified fix without external psychophysics                   d2/b2/

D2-G1: simple glare architecture KILL on 3 independent necessary conditions
       (frame-only CIE 146; one alpha by convention; ignoring display glare)   d2/g1/PREREG_D2_G1.md
```

## Decision
- **No further D2 optimisation.**
- **D1 remains the immutable baseline.**
- **A1b = a validated partial repair, rejected as a replacement for D1.**
  - What it does: it fixes the V6 broad saturation and passes the corpus, temporal and no-regression checks.
  - What it does not do: restore V7 against the pre-registered Blender AgX +7 comparator.
  - It gets **no** candidate tag, and it is not used in application work.
- **Next:** return to N1. **N1.7** is a bounded viewpoint-motion stress test on **frozen D1** (its own PREREG).
  - It asks a narrow question: is frozen D1 stable under viewpoint changes inside the accepted N1 scene?
  - It does not continue any claim of perceptual superiority.
- **Backlog, untouched without a new independent reason:**
  - observer glare;
  - D2-B3 (adaptation field);
  - an AgX-like curve;
  - A1b tuning;
  - RoadLine-B (RMA).

## Limitations carried forward
- **Observer glare** remains unresolved and depends on the display and viewing conditions (D2-G1).
- **The residual gap to hand-graded AgX** is tonality/colour and the surround/local-contrast distribution (A3a). It is
  not localised further.
