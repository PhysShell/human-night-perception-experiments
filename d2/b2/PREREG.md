# D2-B2 pre-registration: does the frozen B push warm mesopic light through red towards pink as a defect?

Committed **before** any D2-B2 code. It follows `d2/TEMPLATE.md`. D1 is not changed. `d1/verify_manifest.sh` is run
first and its output is recorded.

**Origin.** N1 hero (`n1/README.md`, `3ea5c40`), blind: V0 pcond > D1 > plain Blender. D1 lost to V0 only on colour.
On the lamp-pool flank (display Y 5–60 cd/m²) the chroma from D65 and the u′v′ hue were:

| version | chroma | hue |
|---|---|---|
| scene | 0.075 | 53° |
| A-only | 0.073 | 50° |
| B-only | 0.008 | 6° |
| D1 final | 0.012 | 19° |

## 1. Question
Is the rotation of warm practical light's hue towards red/pink inside B a **defect**? Or is it the Cao/Kirk
rod-intrusion (Purkinje) term that D1 deliberately keeps?

## 2. Necessary conditions (all three must hold for D2-B2 to make sense)
- **N1 systematic.** It is reproduced on a synthetic warm set, not only on the hero. Every warm input rotates
  towards red (negative Δhue) by at least half the hero's observed rotation (≥ 15.5°) at some luminance where
  chroma_B ≥ 0.002. The 0.002 is B4-G4's visibility floor.
- **N2 inside B.** It is present in B's scene-linear output (before any display stage), with the same sign.
- **N3 not the model's intended term.** The rotation must **not** be fully explained by the kernel's rod-intrusion
  term. Test: the same inputs through the same frozen kernel with `nightAdaptation = 0`, where the rod term
  `deltaOpponent` is identically zero and f = input.
  - If the rotation vanishes with the rod term off and appears with it on, **it is the Cao/Kirk rod signal**. That is
    what B4-G4 (kernel hue kept) and B4-G7 (the Purkinje tint must survive) protect by design.
  - Removing it would then change the model's rod-intrusion direction for warm hues. That needs an **independent
    psychophysical reference** saying warm stimuli at these levels do not shift that way. None is in the repository,
    and hunting for one is outside this budget.
  - If a rotation of ≥ 15.5° remains **with the rod term off**, it comes from elsewhere in B (κ scaling, the chroma
    stage, numerics): a defect.

## 3. Cheapest falsifier (no new render, no new scene)
Frozen B code only (`d1/chroma_b4/run.py`: filament(), stage(), t(L) = L/(L + 0.108), κ = 3).

**Warm set** (unit luminance, linear Rec.709):
- Planckian 2200, 2700, 3000, 3500 K (the Kim et al. 2002 cubic, the same as `n1/scene/scene.py`);
- F1 warm_lamp (1, 0.55, 0.2);
- orange (1, 0.5, 0);
- yellow (1, 1, 0).

**Luminance** L = 10⁻⁴…10² cd/m² (61 log steps) and 200, as in B4.

**Also:**
- the hero pool-flank pixels from `n1/work/hero_cdm2.exr`, the same region as the N1 diagnosis;
- the F1 warm_lamp patches.

**Per input and L,** u′v′ chroma and hue (from D65) of:
- the input;
- f (kernel, `nightAdaptation` = 1);
- b (full B);
- f₀ and b₀ (kernel with `nightAdaptation` = 0, then the same stage).

Also reported: whether the path passes through neutral, i.e. chroma dips below 0.002 and the hue then flips by more
than 90°.

## 4. KILL
- N1 or N2 fails: the rotation is not systematic or not B's.
- **N3 fails:** the rotation is the rod-intrusion term. D2-B2 is closed as "not a defect under the frozen model", and
  the residual stays an **official limitation**: B's Cao/Kirk rod tint, added to warm light, reads pinkish at
  pool-flank levels, and on the N1 hero V0 is preferred.
- No correction may be tuned in this item.

## 5. Budget
Analysis of existing code and data plus the small synthetic set: one script, one run.
- **If N1–N3 all pass:** exactly **one** correction candidate is pre-registered in an addendum before any code. It must
  remove the non-model rotation, keep B4-G1…G8, and pass the D1 corpus gates P-1…P-9. Then the hero blind comparison
  is repeated as the regression check.
- **Otherwise stop.**

## 6. Baseline check
`d1/verify_manifest.sh` before the run; output in `results.json`.

## 7. No regression
Applies only to a correction (see 5): the full D1 corpus P-1…P-9 plus B4 gates.

## Prediction (recorded before running)
- **N1 and N2 pass. N3 fails**, so D2-B2 is KILLed.
- Reason: the chroma stage preserves f's hue exactly (B4-G4), and nothing else in B changes hue. So I expect the
  whole rotation to be the Filament/Cao rod term (k = {0.2, 0.2, 0.3}, KC pathway), which adds a fixed-direction tint
  to the warm chroma. The path from orange (≈ 50°) towards the rod tint's direction then crosses the red/pink region
  geometrically.
- If this holds, the next step is N1.5 with the residual documented.

## Not in scope (noted, not opened)
B applies adaptation **per pixel**: the kernel sees each pixel's own value, and t(L) uses the pixel's own luminance.
A pool flank at 0.01–0.1 cd/m² is therefore treated as near-scotopic, even though an observer looking at the lit pool
is adapted higher. That is a separate hypothesis (spatial adaptation state). It would need its own item and is not
tested here.
