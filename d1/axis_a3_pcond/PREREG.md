# D1-A3-K0 pre-registration: Radiance pcond as an axis-A (luminance-only) donor

Committed **before** running.

**Why now.** Before A0, pcond V0 was judged as a whole renderer and lost on colour. After A0, axis A needs only
Y_display: pcond's chromaticity is **discarded** and replaced by frozen B (B4: Cao/Kirk κ = 3 plus the
Wanat-derived local chroma collapse).

## Candidates (fixed now)
| id | pcond flags | name |
|---|---|---|
| A3-s | `-s` | pcond human-contrast-sensitivity histogram mapping, luminance only |
| A3-sc | `-s -c` | **pcond-derived scotopic luminance model**: `-c` also switches to a scotopic luminous response, so this is not a pure tone mapper |

- No `-a`, no `-v`, no `-h`.
- No exposure correction.
- pcond defaults otherwise: Ldmax 100 cd/m², 100:1.

## Pipeline
- S1 physical × 1/179 → Radiance picture with `VIEW= -vtv -vh 60 -vv <from aspect>` and a Rec.709 `PRIMARIES=`
  header, exactly as `m1/pcond_colorimetric.sh`.
- `ra_xyze` → `pcond <flags> -p <Rec.709>`. This is the wrapper's path A, the one V0 took its luminance from.
- Y_rel = the Rec.709 luminance of pcond's display-relative output (1 = Ldmax).
- **Y_display = 0.1 + 99.9 · Y_rel**: the SDR100 DARK display model applied to luminance, as `d0/display_model.py`
  decodes a code value.
- Recombination: `x = b · (Y_display / Y(b))`, with b the frozen B output (A0 architecture). Then SDR100 encoding
  and emitted-light decoding, as in A1/A2.

**Consistency control.** A3-sc's Y_display must reproduce the luminance of D0 donor A (pcond V0). Test: the S1
sky-mask median within 5 % of V0's 0.3165 cd/m². If not, the pipeline is wrong and **no gate is evaluated**.

## KILL (per candidate)
1. **The A1 gates, unchanged.** Sky median ≤ 2 cd/m²; lamps/sky ≥ 10; silhouette Weber ≥ 0.1, using the
   luminance-defined poplars from A2-K0 as primary and the D0 tree mask as secondary.
2. **The A2 artefact gates.** Poplar darker than the 5–20 px sky ring; edge-pair reversals ≤ 5 %; ring/far-sky
   within 1.5×.
3. **B preserved.** |Δu′v′| between the displayed colour and B's chromaticity ≤ 10⁻⁶ on unclipped pixels.
4. **Gamut/clipping.** The fraction of pixels with any channel above the display peak is ≤ 1 %. The fraction with
   a channel below black is reported; it is not gated, because it is the same effect as in A1/A2.
5. **Decision.**
   - A candidate passing 1–4 is an admissible deterministic axis-A donor.
   - If both fail on silhouettes or clipping, **pcond is closed as an axis-A donor**. The next step is then A3a-K0:
     a scalar supra-threshold feasibility check for Ashraf & Mantiuk 2024 (is C_source > C_t(source) at
     0.5–1.14 cpd for the S1 poplars?), before any image implementation.

**Expectations.** A3-sc ≈ V0: sky 0.32 cd/m²; silhouette 0.56 on the D0 mask. It should pass unless clipping
bites. A3-s: not predicted.

**Scope reminder.** Kellnhofer 2015 is **not** an axis-A replacement. It is an optional near-threshold stochastic
layer on top of a deterministic mapping, and is decided separately.
