# B1.0: oracle validation (three independent reference PSFs, nothing combined)

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

## Where they agree, where they diverge, and the crossover

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
