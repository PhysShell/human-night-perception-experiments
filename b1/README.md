# B1.0: oracle validation (three independent reference PSFs, nothing combined)

## ERRATUM (framing; no rerun)

**O2 is `CIE_COMPLETE_VISUAL_SPREAD`, not a pure straylight oracle.** From the CIE 135/1-1999 text
(the public preview, §3–5):
- **Small-angle part.** The part in the minutes-of-arc domain is not an optical spread function.
  CIE adopted **IJspeert et al.'s description of the *visual* PSF** (after Campbell & Green) for it:
  eq. (3), terms 9.2·10⁶ and 1.5·10⁵, "valid roughly for a four mm pupil size", foveal.
- **Large-angle part.** It is attributed to cornea and lens scattering, plus fundus scattering and
  light through the ocular wall.
- **Age.** The simplified age form (7) carries **[1 + 1.6·(A/70)⁴]**. The + sign is in the standard
  itself.
- **Energy.** The report states that the increase of glare with age "can only be obtained at the
  cost of the amount of light in the central PSF lobe".

**Consequences:**
- In the minutes-of-arc range, B1.0 compared *ISET wavefront-only* against *CIE's composite empirical
  visual PSF*: an IJspeert-like small-angle component plus large-angle straylight terms. It did not
  compare against scatter alone.
- O2 and O3 are tied by construction, not just by school: CIE's small-angle terms *are* IJspeert's
  description. Their central agreement is partly built in.
- **Withdrawn:** "wavefront-dominated ≤ ~2–5′, transition ~2–10′, straylight-dominated ≥ ~10′" as a
  *physical* aberration→scatter boundary.
- **What B1.0 shows instead:** **~2–10′ is the region where ISET wavefront-only and the CIE/IJspeert
  empirical complete models diverge strongly.** Beyond ~10′ the complete models are 25–60× above
  wavefront-only.
- The literature supports only the weaker split: the core is mainly aberrations, the wide-angle
  (degree) field mainly scatter. Scatter is measured well inside a degree too: Ginis et al. 2013
  report wavelength-dependent straylight at 0.5° with a fundus contribution.
- **"A unified model is only needed around 2–10′" is withdrawn.** A pupil-plane scatter model moves
  energy from the core into the wings over the whole range. Its point is the global energy
  budget, not one band.
- **CIE 146 vs CIE 135/1.** The simplified CIE 146:2002 disability-glare equations have documented
  domains from about 0.1° upward. B1 uses the complete CIE 135/1 formulation (eq. 8), which has a
  separate small-angle part.
- Everything below is kept as computed. Read O2 as `CIE_COMPLETE_VISUAL_SPREAD`, and the "crossover"
  as a divergence map.

**Scope.**
- Three existing reference models, each reduced to one canonical package, compared zone by zone.
- **No fitting, no unified eye, no Arias screen, no `hdrvdp_otf_cie99`.**
- The question is not "which model is closer" but **where the three agree and where they
  diverge**, and where the wavefront core hands over to straylight.

    export REPO=$PWD
    B1_EYE=zero B1_N=4001 B1_PLANE=32.424 tracks/iset/scripts/run_octave.sh b1/o1_iset_wvf.m LOG   # O1, each grid/eye (below)
    tracks/iset/scripts/run_octave.sh b1/o3_ijspeert.m LOG                                           # O3
    tracks/temporal-glare-2009/py.sh b1/oracles.py   # -> results/oracles.json, results/*.csv, results/oracles.png

O1 grids run: `zero` 201/2001/4001 at 16.212 mm, 4001 at 32.424 mm, 5201/7801 at 8.106 mm;
`native` and `best` 2001 at 16.212 mm, 5201/7801 at 8.106 mm. `b1/out` (1.2 GB) is not committed.

## The oracles and their conventions

| | O1 ISET / Thibos (wavefront core) | O2 CIE 135/1 (straylight) | O3 IJspeert et al. 1993 (analytic full range) |
|---|---|---|---|
| implementation | ISETCam wavefront toolbox (`wvfCreate`/`wvfCompute`), PSF read **on its own grid** (`b1/o1_iset_wvf.m`); NATIVE | Standard Glare Observer spatial GSF, **+** age factor, evaluated analytically; never via `hdrvdp_otf_cie99` | ISETCam `human/ijspeert.m` (MIT), NATIVE; its header cites the Drasdo 1994 corrections, not checked here |
| variants | THIBOS_NATIVE (c4 +0.335 µm), ZERO_DEFOCUS_550 (c4 0), BEST_FOCUS_550 (c4 +0.05 µm, the B0 grid optimum); nothing re-optimised | `CIE_FORMULA_RAW`; `CIE_KERNEL_FINITE_NORMALIZED` (10° disc) | m 0.106 / 6 mm (primary); m 0.142 / 6 mm and m 0.106 / 3 mm (sensitivity) |
| age | not modelled (Thibos virtual eyes) | 24 | 24 |
| pupil | 6 mm | none in the model | 6 mm (3 mm sensitivity) |
| pigmentation | not modelled | p 0.5 ("brown eye") | m 0.106 ("mean brown Caucasian eye", the nearest label); 0.142 Caucasian mean |
| wavelength | 550 nm (= ISET's measured wavelength: no LCA shift) | none (broadband) | none |
| normalisation | **unit sum over its own square support** (ISET) | RAW: as published, **∫ = 1.032 to 90°**, 0.9996 within 10°. FINITE: renormalised on the 10° disc (factor 1.0004), zero beyond | as returned: **∫ = 1.000 to 90°**, but only **0.900 within 10°** (the long-angle β₄ term) |
| angular support | fine grid ±117′ (used ≤ 30′); ±15° grid (used 30′–10°) | 0–90°, sphere | 0–90°, sphere |
| sampling | 0.058′ (zero) / 0.117′ (native, best) per sample; 0.233′ for the wide grid | analytic; quadrature 4·10⁵ log points (1e5 vs 4e5: 2·10⁻⁹) | analytic; same quadrature (3·10⁻¹⁰) |
| geometry | small-angle plane, sample = (arcmin/sample)² sr | sphere, dΩ = 2π sinθ dθ | sphere |

Units: PSF in sr⁻¹. s = θ²·PSF with θ in degrees (deg²·sr⁻¹). EE is the fraction of *each oracle's own*
normalisation. Canonical packages: `results/<oracle>.csv` (θ, PSF, s, EE) and `results/oracles.json`.

## Zones

Format: band energy / cumulative energy to the outer edge / s at the band's geometric middle
(CORE: at 0.5′).

| oracle | CORE 0–1′ | NEAR WINGS 1–10′ | MID 10–30′ | STRAYLIGHT 30′–3° | FAR 3–10° |
|---|---|---|---|---|---|
| O1 THIBOS_NATIVE | 0.327 / 0.327 / 95 | 0.663 / 0.990 / 249 | 0.008 / 0.998 / 2.7 | 0.002 / 1.000 / 0.45 | 0.000 / 1.000 / 0.11 ⁽ᵃ⁾ |
| O1 ZERO_DEFOCUS_550 | 0.612 / 0.612 / 187 | 0.381 / 0.993 / 71 | 0.005 / 0.998 / 2.0 | 0.002 / 1.000 / 0.44 | 0.000 / 1.000 / 0.11 ⁽ᵃ⁾ |
| O1 BEST_FOCUS_550 | 0.599 / 0.599 / 225 | 0.393 / 0.993 / 88 | 0.005 / 0.998 / 2.1 | 0.002 / 1.000 / 0.44 | 0.000 / 1.000 / 0.11 ⁽ᵃ⁾ |
| O2 CIE_FORMULA_RAW | 0.310 / 0.310 / 82 | 0.493 / 0.803 / 133 | 0.118 / 0.920 / 54 | 0.062 / 0.983 / 16.5 | 0.017 / 1.000 / 7.1 |
| O3 IJspeert m .106, 6 mm | 0.203 / 0.203 / 58 | 0.538 / 0.741 / 150 | 0.100 / 0.841 / 46 | 0.045 / 0.886 / 11.4 | 0.013 / 0.900 / 5.8 |
| O3 m .142, 6 mm | 0.195 / 0.195 / 56 | 0.516 / 0.711 / 144 | 0.096 / 0.807 / 44 | 0.044 / 0.851 / 11.2 | 0.014 / 0.866 / 6.2 |
| O3 m .106, 3 mm | 0.369 / 0.369 / 96 | 0.376 / 0.746 / 95 | 0.096 / 0.842 / 44 | 0.045 / 0.886 / 11.4 | 0.013 / 0.900 / 5.8 |

⁽ᵃ⁾ O1 is converged within ~3 % up to 200′, ~10 % at 300′, and not converged towards 600′ (see
Numerics). Its FAR band carries < 10⁻³ of the energy in any case.

PSF at the band middles (sr⁻¹):

| oracle | 0.5′ | 3.2′ | 17′ | 73′ | 5.5° |
|---|---|---|---|---|---|
| O1 ZERO_DEFOCUS_550 | 2.7·10⁶ | 2.5·10⁴ | 24.5 | 0.30 | 0.0036 ⁽ᵃ⁾ |
| O1 THIBOS_NATIVE | 1.4·10⁶ | 9.0·10⁴ | 32 | 0.30 | 0.0036 ⁽ᵃ⁾ |
| O2 CIE RAW | 1.2·10⁶ | 4.8·10⁴ | 652 | 11.0 | 0.24 |
| O3 IJspeert m .106, 6 mm | 8.3·10⁵ | 5.4·10⁴ | 548 | 7.6 | 0.19 |

## Where they agree, where they diverge, and the crossover (read as a divergence map; see the erratum)

Ratio of O1 to the straylight oracles (`results/oracles.png`, right panel):

| ratio | 0.3′ | 1′ | 3′ | 10′ | 30′ | 100′ | 300′ | = 1 at | < 0.1 from |
|---|---|---|---|---|---|---|---|---|---|
| ZERO_DEFOCUS_550 / CIE | 0.99 | 3.5 | 0.52 | 0.053 | 0.034 | 0.025 | 0.016 | 0.30′, 1.9′ | 6.9′ |
| THIBOS_NATIVE / CIE | 1.11 | 1.36 | 1.96 | 0.13 | 0.037 | 0.025 | 0.016 | 0.24′, 5.4′ | 11.3′ |
| BEST_FOCUS_550 / CIE | 1.27 | 3.2 | 0.68 | 0.060 | 0.034 | 0.025 | 0.016 | 0.26′, 2.2′ | 7.5′ |
| IJspeert / CIE | 0.56 | 1.06 | 1.14 | 0.90 | 0.79 | 0.67 | 0.79 | — | — |

**Reading.**

1. **Three zones, in numbers.**
   - **Wavefront-dominated** up to ~2′ (ZERO/BEST) or ~5′ (NATIVE): the aberration PSF is at or
     above both straylight oracles.
   - **Transition** ~2–10′: the wavefront PSF falls to 5–15 % of CIE.
   - **Straylight-dominated** from ~10′: the wavefront PSF is 1.6–3.4 % of CIE from 30′ to 5°.
   - Where the eye's focus convention matters (NATIVE vs ZERO) is exactly the transition: 1–10′.
   - In band energy, O1 puts 0.2 % of the light beyond 30′, CIE 8 % and IJspeert 11 %.
   - **A unified model is only needed around ~2–10′.** Below that the wavefront core is the whole
     story. Above it straylight is, and the core adds < 5 %.
2. **CIE and IJspeert agree within a factor 0.56–1.14 over 0.3′–10°.** Beyond 30′ IJspeert is 8–33 %
   lower. They are *not* fully independent: IJspeert's f_β terms are the same functional family as
   the CIE terms, and van den Berg co-authored both. So their agreement is a consistency check
   between two parameterisations from one school, not a second opinion.
3. **Energy conventions differ, and are recorded, not forced.**
   - CIE RAW integrates to 1.032 over the hemisphere (0.9996 inside 10°).
   - IJspeert integrates to 1.000, but 10 % of it lies beyond 10°.
   - ISET is unit sum on its own support.
   - Cumulative energies (e.g. EE to 1′: 0.61 ZERO, 0.31 CIE, 0.20 IJspeert) are therefore
     comparisons of conventions as much as of optics. They are regression quantities.
4. **IJspeert's core is not a wavefront core.**
   - Its central lobe is pupil-dependent: EE to 1′ is 0.37 at 3 mm and 0.20 at 6 mm.
   - Its wings do not depend on pupil (identical at 3 and 6 mm beyond ~10′), consistent with the
     straylight literature.
   - At 6 mm its core is broader than ISET's Thibos core. At 1′ it is 3× below ZERO_DEFOCUS.
   - It gives a plausible *full* profile, but a fitted one, not an aberration PSF.
5. **Pigmentation (m 0.106 → 0.142)** moves IJspeert's wings by ≤ 7 % and its energy beyond 10°
   from 10 % to 13 %.

## Numerics

- **ISET's default grid is too small for wings.**
  - `wvfCreate` defaults to 201 samples on a 16.212 mm pupil plane: 0.117′ per PSF sample, **PSF
    support ±11.7′**. This is what `oiCreate('wvf human')` used in B0.
  - The B0 kernel (via `oiCompute`) against O1 on its own grid:

| radius | 1′ | 3′ | 10′ | 18′ | 30′ | 60′ |
|---|---|---|---|---|---|---|
| B0 ISET kernel / O1 | 1.07 | 1.10 | 1.14 | 1.18 | 1.58 | 5.7 |

  - B0's ISET wing beyond ~20′ was not the wavefront PSF. B0's qualitative conclusion stands and
    is sharper here: the wavefront core is ~20× (B0) → 25–60× (O1) below straylight at 18′–5°.
- **Periodic FFT fold-in.** The wvf PSF is periodic over its grid.
  - The ±117′ grids read 44 % high at 100′.
  - The ±10° and ±15° grids (same sampling) differ by 0.03 % at 30′, 0.2 % at 100′, 2.7 % at 200′,
    10 % at 300′ and 71 % at 590′.
  - O1 is therefore used ≤ 30′ from the fine grid and 30′–10° from the ±15° grid. It is trusted to
    ~10 % up to 300′ and not converged towards 10°. That region is shaded in `oracles.png`.
- **Core sampling** (vs the 0.058′ grid):
  - 0.117′ grids: within 1 % at 0.3′ and 3.5 % at 1′;
  - 0.233′ grid: 5 %.
  - Fine vs wide grid in the 10–30′ overlap: 13–24 % at single radii, from fine ring structure
    sampled at 0.058–0.117′ vs 0.233′. That is local, not a trend.
- **Analytic oracles:** quadrature converged to 10⁻⁹. The IJspeert table (4·10⁴ log points in φ) is
  interpolated.

## B1.0 stop checklist

- [x] three oracles run independently (O1 ISETCam wvf; O2 analytic CIE; O3 ISETCam `ijspeert.m`);
- [x] units in sr⁻¹; s = θ²·PSF; EE and band energy per oracle;
- [x] normalisation conventions and supports written (RAW vs FINITE_NORMALIZED kept separate);
- [x] radial and band-energy comparison, 0.1′–10°;
- [x] crossover found: wavefront ≤ ~2–5′, transition ~2–10′, straylight ≥ ~10′;
- [x] numerical convergence checked, including the limit it exposed (ISET wing ≤ 300′);
- [x] no fitted or unified model created. **B1.0 stops here.**

---

# B1.1: one energy-conserving pupil (mechanism experiment)

**Question.** Can a single complex pupil do both of the following?
- keep ISET's Thibos wavefront core;
- create experimentally plausible wide-angle wings.

This is not "fixing 2–10′" (B1.0 erratum).

**Roles.**
- `ARIAS_REIMPLEMENTATION` is a **mechanism candidate**. There is no author code, so it is
  rebuilt from the paper.
- CIE 135/1 (O2, `CIE_COMPLETE_VISUAL_SPREAD`) is the **calibration target**, and only on
  **0.5°–8°**. That range was declared before fitting.
- Matching CIE there proves nothing by itself. Checks that were not used in the fit are listed
  separately. No display, pcond, Spencer, Temporal Glare or Blender anywhere.

    B1_EYE=zero   B1_N=9216 B1_PLANE=12.26 tracks/iset/scripts/run_octave.sh b1/o1_export_pupil.m LOG
    B1_EYE=native B1_N=9216 B1_PLANE=12.26 tracks/iset/scripts/run_octave.sh b1/o1_export_pupil.m LOG
    tracks/temporal-glare-2009/py.sh b1/unified_pupil.py     # ~19 min, 4 cores -> results/b1_1.json, b1_1_profiles*.csv
    tracks/temporal-glare-2009/py.sh b1/plot_b1_1.py         # -> results/b1_1.png, b1_1_unfitted.json

## Model

    P = A · exp{ −i 2π/λ · [ W_Thibos + W_s ] },   PSF = |F{P}|², unit sum on the grid

| part | source | settings |
|---|---|---|
| A, W_Thibos | ISETCam wvf, exported (NATIVE) | Thibos 6 mm mean eye, 550 nm, ZERO_DEFOCUS_550 (NATIVE focus as a check); grid 9216², 1.3303 µm pupil sampling (Arias's), PSF sample 0.154′, scatter Nyquist 11.8° |
| W_s | Arias et al. 2018, eq. 2–3, reimplemented | W_s = Σ B f^β R cos(π(i+½)i′/n) cos(π(j+½)j′/n) over the 6.006 mm pupil square, R ~ N(0,1); f = the paper's label, true frequency f/2, θ = λf/2 |
| high-pass | declared before fitting | screen modes scattering to < 3′ removed, so the screen does not duplicate the Zernike terms (sensitivity 1.5′ and 6′) |
| sign | ISET's convention (−i), found by matching ISET's PSF exactly | — |

**Staged fit.** Each stage is done before the next.
1. **β from the wing shape.** Offset-free log residual over 0.5°–8°. B is only re-levelled per β,
   starting in the weak-scatter regime.
2. **B from the level.** Mean log ratio 0, 4 seeds.
3. **Energy and EE as checks only.**

A first attempt started B at 1 µm, which is tens of radians of phase. That is outside the B² regime,
did not converge, and was discarded.

## Result

| β (offset-free wing-shape log RMS) | −0.9 | −1.0 | −1.1 | −1.214 | −1.3 | −1.4 | −1.5 |
|---|---|---|---|---|---|---|---|
| | 0.287 | 0.220 | 0.153 | 0.078 | **0.035** | 0.069 | 0.137 |

- **β\* = −1.31, B\* = 0.0165 µm.**
  - Arias's −1.214 was fitted to a different target: A 30, p 1, the paper's − sign, a 1.33 mm pupil,
    over 0.023–11.6° including the core.
  - B is not comparable with their 9.207 µm: mode density and normalisation differ.

## Acceptance

| criterion | result | |
|---|---|---|
| **scatter_off**: unified PSF = ISET's own PSF | max difference 1.6·10⁻⁷ of the peak (central 1025²; peak 0.0172106 both) | PASS |
| **scatter_on**: 0.5°–8° vs the calibration target (tolerance log RMS ≤ 0.10, max ≤ 0.20) | log RMS **0.032**, max 0.068 | PASS |
| **energy** | unit sum on the ±11.8° support by construction (Parseval). Beyond 8° on the support: 0.45 %. Beyond the band limit: not represented (CIE RAW puts ~3 % beyond 10°) | PASS, with the limit stated |
| **ensemble**, 16 seeds | the 4- and 8-seed means are within 0.004 / 0.003 log of the 16-seed mean. A single seed scatters by ≤ 0.03 log (speckle); targets use the mean | PASS |
| **core** | see the energy budget below | PASS: measurable change, accounted for |
| **external**: at least one check not used in the fit | three below; one agrees, one only structurally, one fails for a known missing mechanism | PASS (≥ 1), see below |
| **no display** | none used | PASS |

## Energy budget: where the scattered light comes from

| | THIBOS_ONLY | THIBOS_PLUS_ARIAS | NAIVE_CONVOLUTION_CONTROL |
|---|---|---|---|
| CORE 0–1′ | 0.651 | **0.446** | 0.201 |
| NEAR 1–10′ | 0.342 | 0.387 | 0.591 |
| MID 10–30′ | 0.005 | 0.086 | 0.123 |
| STRAYLIGHT 30′–3° | 0.002 | 0.062 | 0.064 |
| FAR 3–8° | 0.0002 | 0.014 | 0.014 |
| Strehl (peak / THIBOS_ONLY peak) | 1 | **0.68** | 0.13 |
| FWHM (equivalent area) | 0.87′ | **0.89′** | 1.71′ |

- **Energy moved.**
  - The screen takes 0.205 of the energy out of the central 1′.
  - 0.078 of it lands beyond 0.5°, and the rest in 1–30′.
  - The core keeps its width (FWHM 0.87 → 0.89′) and loses height (Strehl 0.68).
  - This is CIE's own statement: glare comes at the cost of the central lobe. Here it is produced
    by a mechanism, not imposed.
- **Unified vs naive.**
  - In the wings the two are the same, since both carry the CIE level.
  - In the core they are not. The naive convolution counts CIE's small-angle visual PSF (IJspeert,
    ~4 mm) on top of the Thibos core. That doubles the FWHM (1.7′) and leaves Strehl 0.13.
  - The phase architecture therefore matters exactly where B1.0 found the models diverging: core to
    ~30′. Beyond 0.5° it adds nothing over the cheap composition.
- **Not constrained by the calibration.** How much the core loses depends on the declared high-pass:

| high-pass | EE(1′) | Strehl | wing log RMS vs CIE |
|---|---|---|---|
| 1.5′ | 0.37 | 0.57 | 0.034 |
| 3′ (declared) | 0.45 | 0.68 | 0.032 |
| 6′ | 0.51 | 0.79 | 0.034 |

  The wings are identical in all three, so the 0.5°–8° calibration cannot fix the core's energy
  loss. That needs its own data: in-vivo core/near-PSF measurements, or a Strehl/MTF constraint.

## Not fitted: 1′–20′ (prediction against the two empirical visual models)

| log₁₀ ratio | 1′ | 3′ | 10′ | 20′ |
|---|---|---|---|---|
| THIBOS_PLUS_ARIAS / CIE | +0.38 | −0.22 | −0.17 | −0.11 |
| THIBOS_PLUS_ARIAS / IJspeert | +0.35 | −0.28 | −0.12 | −0.03 |
| NAIVE / CIE | +0.19 | +0.08 | +0.03 | +0.02 |
| THIBOS_ONLY / CIE | +0.54 | −0.26 | −1.23 | −1.40 |

- The unified eye is sharper than both empirical *visual* spread functions at 1′.
- It is 0.1–0.3 log below them at 3–20′.
- Not a failure by itself. CIE's and IJspeert's small-angle parts are psychophysical visual PSFs
  (CIE: ~4 mm pupil), not an optical PSF at 6 mm.

## Checks not used in the fit

1. **Same screen, THIBOS_NATIVE focus.**
   - The wings are unchanged (≤ 0.004 log at 0.5°, 2°, 8°).
   - The core carries the native defocus: EE(1′) 0.24, Strehl vs its own scatter-off 0.70.
   - Scatter and defocus separate cleanly in one pupil.
2. **Pupil 3 mm vs 6 mm, same screen.**
   - The wings move ≤ 0.01 log from 0.5° to 8°.
   - That agrees with the literature that straylight hardly depends on pupil size (Franssen 2007:
     ≤ ~0.2 log).
   - It is largely structural for an OPD screen with this statistics, so it is a consistency check,
     not strong evidence.
3. **Wavelength, 500 vs 650 nm, same OPD screen.**
   - The model gives log s(650) − log s(500) = −0.14 at 0.5° and −0.16 at 6°: the same power law at
     every angle, as λ^(−4−2β) predicts.
   - Ginis et al. 2013 (IOVS 54:3702, abstract): at 0.5° straylight follows the haemoglobin
     transmittance (fundus, rising beyond 600 nm); at 6° it depends less on wavelength.
   - **FAIL at 0.5°**, for a known missing mechanism: a pupil phase screen has no fundus term. CIE
     135/1 attributes its second part to the fundus and the ocular wall.
   - **Unresolved at 6°**: the abstract gives no number.
4. **Not done:** `DIGITIZED_EXTERNAL_VALIDATION` against the in-vivo wide-angle PSF of Ginis et al.
   2012 (J Vis 12(3):20, open access, up to 8°). This is the next external check.
5. **Not run from the B1 plan:** `ARIAS_AS_PRINTED` (A 30, p 1, − sign, their 1.33 mm grid). This
   round fitted the standard-form target at our observer.

## Reading

- **THIBOS_PLUS_ARIAS is a working unified mechanism.**
  - It reproduces the CIE wings 0.5°–8° within 0.03 log, conserves energy, and leaves the Thibos core
    exactly intact when the screen is off.
  - With the screen on, it takes the glare energy out of the central lobe instead of painting a
    halo on top.
- **What it adds over `ISET ⊛ CIE` lies in the core and near field, not in the wings.** The naive
  control double-counts CIE's small-angle visual PSF, and its core is 2× too wide.
- **Open, and not settled by this calibration:**
  - how much energy the core loses (the high-pass choice: Strehl 0.57–0.79);
  - the fundus/ocular-wall component, which no pupil screen can produce (FAIL at 0.5° vs Ginis 2013);
  - an independent in-vivo wing check (Ginis 2012, not yet digitised).
- **Stop.** No fitted model is promoted to `target_retina` yet. No display or blind set.
