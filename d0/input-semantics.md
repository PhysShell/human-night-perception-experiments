# D0.1 input-semantics audit

**What went wrong in D0.** The donors were compared on one axis, emitted cd/m², as if they all took the same kind
of input. They do not. D0 fed every donor the same absolute-luminance EXR, but the numbers mean different things
to each:

- to pcond, physical luminance;
- to iCAM06, absolute XYZ;
- to Mantiuk08, relative log-luminance plus an optional anchor;
- to ACES, scene-referred exposure;
- to Reinhard02, luminance up to a key.

As a result, the "WHITE_Y and exposure uncertainties" in the D0 report were partly an artefact of this. A
relative or scene-referred renderer *needs* an external appearance/exposure anchor by design; that is not a defect
to be measured.

This file fixes, per donor, **what its input numbers mean**, what anchor D0 supplied, and how its results may be
read.

| donor | class | what its input numbers mean | anchor D0 used | how to read its D0 results |
|---|---|---|---|---|
| pcond V0 | **physical** | Radiance radiance (luminance = 179·Y), absolute. It uses the level for its own adaptation model (Ward Larson et al. 1997) | none needed | physical input → display; the frozen baseline |
| iCAM06 | **absolute appearance** | absolute XYZ in cd/m² (`max_L = 0`). The level drives FL, rod response and Hunt/Stevens terms (paper §2.1) | none needed (absolute configs). NATIVE_DEFAULT rescales max Y to 20 000 cd/m² and discards the level | absolute input → model appearance → **relative display stage** (max-Y normalisation, 1–99 % stretch). D0.1 ladder: the level changes hue and model contrast, not displayed lightness (`input-contracts/icam06.md` §D0.1) |
| Mantiuk08 | **relative + anchor** | log-luminance *differences*. The absolute level enters only through `--white-y` (maps a level to display peak) or the undocumented `--scene-y-adapt` | WHITE_Y auto (tool: image max → peak), WHITE_Y = display peak, sweep 4e-4…4 | a family over WHITE_Y. Geometry (`-s`) is accepted but unused in 2.2.0 and in master (source-verified, §9). Master (2025) = 2.2.0 byte for byte; `--tone-value` is not an anchor |
| ACES 2 | **scene-referred + exposure** | scene-referred ACES2065-1. ACES defines no real-world cd/m² ↔ ACES mapping | ACES 1.0 = 100 cd/m² (the transform's implied scale), EV sweep −4…+20, family EV 0…18 on 5 scenes × 2 displays | **only as an exposure family** (`input-contracts/aces2.md` §8). "Sky at black" is the EV 0 member, not the algorithm |
| Reinhard02 | **relative (key)** | luminance up to the key normalisation (log-average → a = 0.18). The absolute level cancels except for a 1e-5 guard | key a = 0.18 (default) | a display-unaware control; brightness scales with the display peak |
| CTRL-PHOT | **physical display clipping** | absolute cd/m², emitted as is, clamped to [black, peak] | exposure 1 | the literal control: what "showing the physical night" does on each display |
| CTRL-KEY | **relative (key)** | as Reinhard02 without its curve | key 0.18·peak | naive auto-exposure control |

## Consequences for the D0 conclusions

- **"Where should night brightness come from?"** splits into two questions:
  1. **For absolute-appearance models (pcond, iCAM06)**, brightness should follow from the physical level and the
     model's adaptation. The question is whether that machinery produces "night".
     - pcond places the S1 sky at 0.32 cd/m², about 3× display black.
     - iCAM06 does not produce night. Its rod term lifts dark regions, and its display stage re-stretches to the
       full range. At the physical level the sky shows at 27 cd/m², lighter than the same image at daylight level
       (18 cd/m²).
  2. **For relative / scene-referred renderers (Mantiuk08, ACES, Reinhard02, CTRL-KEY)**, an external appearance
     or exposure anchor is required by design. There the question is which documented rule should set it:
     WHITE_Y, ACES EV, key. It is not "why does the algorithm not know the night".
- **P4.** No donor simulates ocular glare. Where the bar's detectability dropped (Mantiuk08 on 500–1000 cd/m²),
  it dropped only with HDR-VDP's ocular MTF on (0.57–0.67 vs 0.98 off). That is the observer model's optics acting
  on the displayed luminance ratio.
- **Controls renamed.** D1a/D1b are now CTRL-PHOT / CTRL-KEY (`d0/donors/controls_exposure.py`). "D1" is reserved
  for the next round, which has not started.
