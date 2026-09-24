# B1: full ocular PSF donor study (research only)

**Question.** How does the literature build **one** physically coherent wide-angle ocular PSF,
with an aberration core (RETINAL_WAVEFRONT, ISET `wvf human`) and scatter wings
(RETINAL_STRAYLIGHT, CIE 135/1), instead of convolving an ISET kernel with a CIE kernel?

**Short answer.**
- Only one published family unifies core and wings physically: **Arias, Ginis & Artal 2018**.
  They put a random power-law phase screen in the pupil plane and use Fraunhofer diffraction.
  **Ntatsis et al. 2025** adds that screen to a Zernike aberration wavefront inside one pupil
  function.
- Neither paper releases code.
- Every other source is one of three things:
  - an analytic full-range fit (IJspeert 1993, CIE 135/1);
  - a parametric splice, `(1−a)·PSF_dl + a·wing` (Ginis 2012; Westheimer & Liang 1995);
  - a convolution.
- The B1 target should therefore be a **HYBRID**:
  - ISET's Thibos pupil function (NATIVE);
  - plus an Arias-type phase screen, which is a **reimplementation from the paper** because no
    donor code exists;
  - the screen's amplitude is fitted to CIE 135/1 wings, and IJspeert (ISETCam, MIT) serves as a
    second oracle.

Date of study: 2026-09-24. Nothing is implemented here. The numbers marked *(our calc)* are quick
transcription checks (numpy, scratch only). They are not B1 results.

---

## 1. Verdict table

| # | work | models | how core + wings are coupled | parameters | angular range | normalisation | code / data (license) | verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **Arias, Ginis, Artal 2018**, BOE 9(6):2664 | straylight as a random pupil-plane phase (IDCT of power-law-weighted Gaussian noise) | **physically unified**: one pupil function, PSF = \|FFT\|². The screen also carries HOA-like low frequencies | B (µm, RMS/amount), β (spectral slope); fitted A = 30, p = 1; 540 nm; ϕ = 1.33 mm | 0.023°–11.6° (set by pupil sampling 1.3 µm and N = 1000) | **∫α·PSF dΩ = 1, sr⁻¹**; α = [(λ/ϕ)² ΣPSF]⁻¹ (Eq. 8) | **none**: no code, no data statement, no supplement. Article under the OSA Open Access agreement | **PAPER ONLY** (method donor, reimplement) |
| 1b | **Ntatsis, Christaras, Artal, Ginis 2025**, BOE 16(7):2709 | aberrations (GMM Zernike sampler, orders 2–4) + Arias screen, double pass | **unified**: W = W_a + W_s in one pupil function, h = \|F[A·exp(−2πiW/λ)]\|² | β = −1.214 (from Arias), B sampled by OSI; 555 nm; 2 mm / 5 mm pupils | ≈ ±1° only (1024² grid over 15 mm ⇒ dx ≈ 14.6 µm) *(our calc)* | not stated | "not publicly available … upon reasonable request" | **PAPER ONLY** (confirms the coupling recipe) |
| 2 | **Ginis, Pérez, Bueno, Artal 2012**, JoV 12(3):20 | in-vivo optical wide-angle PSF from double-pass images of uniform disks: I_c(θ) = ∫2πφ PSF dφ, then PSF = (1/2πθ)·dI_c/dθ, single-pass via PSF = F⁻¹[√\|F(PSF_dp)\|] | **splice** (Eq. 6): PSF = (1−a)·PSF_dl + a·b/(θ+θ₀)ⁿ, n ≈ 2, b normalises the wing, **PSF_dl** = diffraction-limited Airy (2 mm sub-pupils, "aberrations minimal") | a, n, θ₀; 530 ± 30 nm; 2 mm sub-apertures, ≥ 6 mm dilated pupil; 3 subjects | 0.18°–8.1° (disks); PSF reported to 8° | radial normalisation to the largest disk (energy ≈ 1 within ~8–10°) | no data or code released; figures only (Fig. 6, 7: log PSF vs θ, with CIE curves) | **DATA ORACLE** (digitise Fig. 7, 1–8°) |
| 3 | **IJspeert, van den Berg, Spekreijse 1993**, Vis Res 33(1):15 (the "van den Berg 1993" item: pii 0042-6989(93)90053-Y) | analytic foveal PSF + closed-form MTF + LSF over the **full** angular range | **analytic sum of 4 terms** f_β = β/[2π(sin²φ + β²cos²φ)^{3/2}], weights c₁…c₄. Pupil acts on the two short-angle terms, age/pigmentation on the long-angle terms. **Not wavefront**: the "core" is a fitted 0.3′ lobe | age, pupil p (mm), pigmentation m (0.056–0.16), no λ | 0–π/2 (hemisphere) | **∫PSF dΩ = 1 (sr⁻¹), MTF(0) = Σc = 1**; our check: 1.0000 at 2/4/6/8 mm *(our calc)* | paper paywalled (abstract only opened). **NATIVE code in ISETCam `isetcam/human/ijspeert.m` (MIT)**, notes Drasdo 1994 corrections | **CODE DONOR + DATA ORACLE** |
| 3b | **CIE 135/1 (Vos & van den Berg 1999)** "complete" GSF; in HDR-VDP as `hdrvdp_otf_cie99.m` | empirical GSF L_eq/E_gl (sr⁻¹); 5 Lorentz-like terms + p-terms + constant | analytic fit; small-angle terms (θ₀ = 0.0046°, 0.045°) mimic a core but are **pupil-independent** and not wavefront | age A, pigmentation p; achromatic; no pupil | stated to cover 1/100°–100° (McCann & Vonikakis 2018) | nominally sr⁻¹; **hemisphere integral = 1.03 (A24, p .5), 1.06 (A30, p 1), 1.07 (A70)** *(our calc)*, so not exactly unit | CIE document sold, **not opened**. Formula taken from Arias Eq. 1 and the HDR-VDP code (HDR-VDP license per `research-cache/hdrvdp3`). McCann MATLAB (Frontiers supplement, article CC BY) | **DATA ORACLE** (wing target); HDR-VDP code = existing NATIVE donor |
| 4 | **Westheimer & Liang 1995**, JOSA A 12(7):1417 (**not Artal et al.**; JOSA A 12(7):1417 is Westheimer & Liang, checked on the Optica abstract page) | psychophysical scatter + companion objective double-pass (JOSA A 12:1411) in the same subjects → "complete PSF" | **splice**: objective data to 7′, extrapolation beyond, Strehl S = S₁·E (per abstract page) | 3 subjects (2 young, 1 older) | core ≤ 7′ + wide-angle psychophysics | not verifiable | **paywalled**, abstract only. No code | **PAPER ONLY** (historical splice precedent) |
| 5a | **Watson 2015**, JoV 15(2):26 "Computing human optical PSFs" | Zernike → PSF, Thibos 200-eye data, polychromatic, SCE (per abstract/search) | aberrations only, **no scatter** | pupil, λ, defocus | central PSF | – | supplement `Zernike.nb` (Mathematica) + CDF demo (per search snippet). **PDF not retrievable here** (NASA reset, ARVO 403). License unknown | **NOT RELEVANT** for wings (ISET already covers the core) |
| 5b | Franssen, Tabernero, Coppens, van den Berg 2007 IOVS 48:2375 | straylight vs pupil 1.3–8 mm | – | pupil, λ, pigmentation | 3.5°–28° | s = θ²·PSF | abstract | **DATA ORACLE**: for 2–7 mm pupils, straylight changes by ≤ 0.2 log units. Eye-wall translucency matters at small pupils and large angles |
| 5c | Coppens, Franssen, van den Berg 2006 Exp Eye Res 82:688 | straylight 457–625 nm | – | λ, pigmentation | – | – | abstract | **DATA ORACLE** for λ: ≈ λ⁻⁴ only in young, well-pigmented eyes; light eyes add a red-dominated component (translucency) |
| 5d | C-Quant (Franssen/Coppens/van den Berg; commercial, Oculus) | compensation-comparison straylight log(s) | – | – | ≈ 7° | log(s) | commercial instrument, no code | **NOT RELEVANT** as a donor; log(s) values usable as a scalar check |
| 5e | Navarro 1985 (JOSA A 2:1891), Chen et al. 2012 JBO (Mie scatter in CodeV/ASAP), Kelly-Pérez 2013 JOSA A | schematic eyes with diffuser / Mie particles | ray/scatter volume, commercial optics codes | particle size, density | varies | – | no open code (commercial CodeV/ASAP/Zemax) | **PAPER ONLY**. Per Arias, single-size particles do not reproduce the CIE angular shape |
| 5f | ISETCam flare: `wvfAperture.m`, `piFlareApply` (camera dust and scratches) | **amplitude-only** aperture ("We ignore any phase shift", `wvfAperture.m`) | pupil amplitude mask → diffraction streaks | dot/line counts | – | – | MIT | **NOT RELEVANT** for the eye's straylight. The **aperture hook in `wvfComputePupilFunction.m`** is the insertion point for B1 |
| 5g | ISET3d human eye (Navarro/Arizona/LeGrand in PBRT-v4) | geometric ray tracing | no intraocular scatter medium (grep: "scatter" hits are unrelated) | accommodation, λ | wide field | – | MIT (iset3d-v4) | **NOT RELEVANT** for B1 |
| 5h | **HCIPy** (existing donor), `make_power_law_error`, `SpectralNoiseFactoryFFT`, `MatrixFourierTransform` | power-law phase screens, amplitude = √PSD; MFT onto arbitrary focal grids | tool only | exponent, PTV (not B) | any | – | **MIT** (`research-cache/hcipy/src/LICENSE`) | **CODE DONOR** (screen generator + MFT; ADAPTED) |
| 5i | Psychtoolbox `WestPSFMinutes`/`WestLSFMinutes` (Westheimer 1986), in isetbio/external | central LSF/PSF fit | two-term fit, no wide angle | – | a few arcmin | normalised to max 1 | in isetbio tree | **NOT RELEVANT** |
| 5j | Ritschel et al. 2009 Temporal Glare (existing project donor) | Fraunhofer of pupil + lens particles + lashes | unified via pupil (toy statistics, not fitted to CIE) | pupil (hippus) | display-limited | – | already in `tracks/temporal-glare-2009` | **NOT RELEVANT** as a physical target (it is a DISPLAY_ENCODING in B0) |
| 5k | `eyewave` (github.com/joaoslaurino/eyewave) | Zernike → PSF simulator | aberrations only | – | – | – | seen in search results only, **not inspected** | not assessed |

---

## 2. Arias 2018 in detail (the only coherent recipe)

From the full text (Europe PMC XML of PMC6154192):

- **Screen (Eq. 2):** W(i′,j′) = circ(i′,j′)·Σᵢⱼ U_ij R_ji cos(π ϕ f_i i′/N) cos(π ϕ f_j j′/N).
  - R ~ N(0,1).
  - Modes f_i = (i+½)/ϕ, i.e. an IDCT over the pupil.
  - N = 1000, ϕ = 1.33 mm, pixel ≈ 1.3 µm.
- **Weighting (Eq. 3):** U = F(f) = B·f^β, with f = √(f_i²+f_j²) in cycles/mm.
  - Fit: **B = 9.207 µm, β = −1.214** ("pink noise").
  - Fitting: `fminunc` on the log-RMS difference to CIE Eq. 1, **A = 30, p = 1**.
- **Amplitude and straylight:** log RMS is linear in log S, with S = θ²·PSF(6°) (Fig. 4).
  - The paper plots this relation but gives no formula. It shows 10–80 deg²/sr.
  - **Age and pigmentation are not mapped to screen parameters.** Only B is rescaled to a target
    S. β is held fixed.
- **Units of W:** µm of optical path (B is in µm). The conversion to phase (2π/λ) is not written
  out. Nor is the IDCT normalisation (for example, MATLAB `idct` orthonormal), so **B is not
  portable**: B has to be refitted in our pipeline, and β is the transferable number.
- **Normalisation (Appendix):** ∫Ω α·PSF dΩ = 1. The PSF pixel subtends (λ/ϕ)², so
  α = [(λ/ϕ)² Σ PSF]⁻¹, in sr⁻¹ (paraxial).
- **Speckle:** re-randomising R keeps the mean profile. Fig. 3b shows the **angular average**.
- **Wavelength:** a single wavelength (540 nm). There is no λ model, and pupil dependence is not
  studied.
- **Discrepancy to note:** the Europe PMC text of Eq. 1 reads `[1 − 1.6·(A/70)⁴]` for the
  long-angle factor. HDR-VDP's `hdrvdp_otf_cie99.m` uses `(1 + 1.6·(A/70)⁴)` (scatter increases
  with age), and the 0.08 factor has a minus sign in both. B1 must pick the CIE original sign; the
  HDR-VDP sign is physically plausible. At A = 30 the factor is 0.946 (Arias) vs 1.054 (HDR-VDP).
- **Coupling insight** *(our inference, not in the paper)*: a phase screen with amplitude spectrum
  ∝ f^β gives, far from the core, a halo ∝ PSD(θ/λ) ∝ θ^{2β} = θ^−2.43. That is close to the
  Stiles–Holladay θ⁻²… θ⁻³ wings. The core keeps a fraction ≈ exp(−σ²_φ) of the energy, where
  σ²_φ is the screen's phase variance. Energy is conserved by construction, which is what
  "physically coherent" means here.

**Ntatsis 2025 (same group):** W = W_a (Zernike, orders 2–4, defocus ×0.8) + W_s (Arias, β = −1.214).
Pupil grid 1024² over 15 mm, 555 nm. This is exactly the B1 coupling, but only to ≈ 1°, and it is
tuned to OSI (double-pass), not to CIE.

---

## 3. Relation of IJspeert 1993, CIE 135/1 and the HDR-VDP GSF

- **Shared parametric form.** The CIE 135/1 terms (1+(θ/θ₀)²)^−1.5 are IJspeert's f_β in the
  small-angle limit, with θ₀ = β in degrees. The CIE small-angle constants (0.0046°, 0.045°) play
  the role of IJspeert's pupil-dependent β₁ and β₂ (0.3′ and 2.1′ at 6 mm). **In CIE they are
  frozen**: there is no pupil. The CIE p-terms and constant correspond to IJspeert's long-angle
  term β₄ = 1 rad (eye-wall and fundus light).
- **HDR-VDP.** `hdrvdp_otf_cie99.m` is labelled the analytic Fourier transform of the same CIE 135/1
  formula.
  - **Erratum (B0, `b0/cie_otf_check.py`):** its closed form is the **1-D** transform of the GSF
    profile, used as a 2-D radial OTF: 0.987 at 1 cpd against the 2-D (Hankel) value 0.795. Its retinal
    veil is 14× too low at 18′.
  - B1 must not use it as the CIE oracle. Use the GSF in space (`b0/cie135_target.py`), or its Hankel
    transform.
  - It renormalises by M(ω→0), so the ≈ 1.03 non-unit integral is divided out.
  - The θ² term and the constant become Dirac terms, zero for ω ≠ 0.
  - The comment "CIE99" means CIE 135/1-1999.
- **Numbers** *(our calc, A = 24, p = 0.5; IJspeert age 24, 6 mm, m = 0.142)*:

| θ | CIE (sr⁻¹) | IJspeert 6 mm (sr⁻¹) | ratio IJ/CIE |
|---|---|---|---|
| 0.01° | 8.1e5 | 6.1e5 | 0.75 |
| 0.1° | 1.17e4 | 1.09e4 | 0.93 |
| 1° | 19.3 | 13.3 | 0.69 |
| 3° | 1.03 | 0.75 | 0.73 |
| 10° | 0.061 | 0.061 | 1.00 |
| 30° | 0.0078 | 0.022 | 2.9 |

- **Encircled energy.**
  - CIE: EE(1′) = 0.31, EE(0.3°) = 0.88, EE(1°) = 0.95, EE(11.6°) = 1.00, of a total of 1.03.
  - IJspeert 6 mm: EE(11.6°) = 0.87; 13 % sits in the wide β₄ term.
  - **Reconciled:** B0's "energy within 1′ = 0.539" had two causes.
    - It is a grid quantity: the five 73 px/deg pixels whose centres lie within 1′, and it includes
      the 3-px source footprint (no optics: 0.75).
    - It came from the defective `otf_cie99`.
    - The 2-D CIE 135/1 target on the same grid gives 0.221 ≈ 0.75 × 0.31, consistent with the
      continuous 0.31 here.
- **Young-eye straylight check:** CIE (A24, p .5) gives log s = 0.93 at 3.5°, 0.82 at 7° and 0.79
  at 10° (s = θ²·PSF, deg²/sr). These are consistent with the usual young-eye log(s) ≈ 0.9.

---

## 4. What cannot come from a pupil phase screen (be honest in B1)

- **Eye-wall / iris / sclera translucency and fundus reflection.** These are the CIE p-terms,
  IJspeert c₄, the red component in Coppens 2006, and the small-pupil effect in Franssen 2007.
  They are not pupil-plane phenomena.
  - Ginis 2012 states explicitly that its optical PSF excludes the light transmitted through the
    iris and sclera, which psychophysical GSFs include.
  - B1 should either leave them out and record the gap, or add them as a labelled incoherent
    additive term (HYBRID).
- **Wavelength law.** A µm-OPD screen implies a specific λ scaling. Measured straylight is ≈ λ⁻⁴
  only for pigmented young eyes. B1 stays monochromatic (550 nm, as in B0-optics) and only
  reports the implied scaling.
- **Large-angle geometry.** Beyond ~10–20°, the paraxial sr pixel (λ/L)² and the flat retina
  break down. CIE runs to 100°, the screen to θ_max = λ/(2·dx).

---

## 5. Proposed B1 experiment plan

**Target (HYBRID, labelled):**

    P(u,v) = A_6mm(u,v) · exp{ i·2π/λ · [ W_Thibos(u,v) + W_s,hp(u,v) ] }

- W_Thibos: ISET `wvf human`, Thibos mean eye, 6 mm, 550 nm, ZERO_DEFOCUS_550 as in B0. NATIVE.
- W_s,hp: an Arias power-law screen, β = −1.214. It is **high-passed** above the lowest Arias mode
  (≈ 1/(2·1.33 mm) ≈ 0.38 cyc/mm, or above the Zernike order ISET carries), so it does not
  double-count the low-order aberrations. This is a reimplementation from the paper, because no
  author code exists.
- B is refitted so that the **wings only** (θ ≥ 0.5–1°, declared before fitting) match CIE 135/1 at
  A = 24, p = 0.5 (the B0 donor defaults).

**Stages**

| stage | what | label | pass criterion (declare before running) |
|---|---|---|---|
| B1.0 | Oracles: (a) CIE 135/1 from `hdrvdp_otf_cie99` constants; (b) **run ISETCam `ijspeert.m` in Octave** (NATIVE) at 24 y, 2/4/6/8 mm; (c) the B0 ISET kernel | NATIVE | hemisphere ∫ = 1.00 (IJspeert), 1.03 (CIE, recorded, not forced). Reproduce the §3 table ±1 %. B0 "EE(1′) 0.539" reconciled (§3) |
| B1.1 | **Reproduce Arias Fig. 3b / Fig. 4**: IDCT screen, N = 1000, ϕ = 1.33 mm, 540 nm, A = 30, p = 1; `fminunc`-equivalent log-RMS fit; average ≥ 16 realisations, radial profile | REIMPLEMENTATION (paper only; ask augusto.arias@um.es for the MATLAB before starting) | β within ±0.05 of −1.214. log PSF within ±0.1 of CIE over 0.1–11°. log RMS vs log S linear. B reported, not required to be 9.207 µm (normalisation undefined) |
| B1.2 | Same screen via **HCIPy** `SpectralNoiseFactoryFFT` with PSD exponent 2β = −2.43 (FFT screen instead of IDCT) | ADAPTED (MIT) | same mean profile as B1.1 within ±0.05 log. If it passes, use HCIPy for B1.3 |
| B1.3 | **Coherent 6 mm PSF**: ISET pupil function (via the `aperture`/phase insertion point in `wvfComputePupilFunction.m`, a local patch, or export the ISET wavefront map) × exp(i2πW_s,hp/λ). Pupil sampling dx ≤ λ/(2θ_max): 1.33 µm for 11.6° ⇒ ~4500² pupil samples. Use the **HCIPy MFT** onto two focal grids (fine core, ≤ 0.25′, ±1°; coarse wing, ±12°) instead of one 16k² FFT | HYBRID (ISET NATIVE + screen ADAPTED) | see checks below |
| B1.4 | Controls on the same grid: (i) naive ISET ⊛ CIE; (ii) Ginis-type splice (1−a)·PSF_ISET + a·CIE-wing; (iii) IJspeert 6 mm | control | report the differences at the B0 radii 1′, 3′, 18′, 60′ and at 3.5°/7°/10° |

**Checks for B1.3**

1. **Normalisation.** ∫PSF dΩ = 1 with dΩ = (λ/L)² per pixel (Arias Eq. 8), in sr⁻¹, on both
   MFT grids. The energy outside ±12° is reported as a number (CIE puts ≈ 3 % beyond 11.6°), never
   silently renormalised.
2. **Core preservation.** With B = 0, the result equals the B0 ISET kernel (EE50 0.92′, EE(1′)
   0.52) to ≤ 1e-6. With the screen on:
   - core peak ratio ≈ exp(−σ²_φ,hp) (predicted);
   - ΔEE(1′) and ΔEE50 reported.
3. **Wings.**
   - θ²·PSF at 3.5°, 7°, 10° within ±0.1 log of CIE (A24, p .5);
   - the IJspeert 6 mm curve shown as a second oracle;
   - digitised Ginis 2012 Fig. 7 (1–8°) shown as an in-vivo optical band.
4. **Pupil.** Repeat at 4 and 7 mm with the same screen statistics. The wings must move by
   ≤ 0.2 log (Franssen 2007). The core must change as ISET predicts.
5. **Speckle.** Report the variance of the radial profile over realisations. Targets use the
   realisation mean. A single realisation is a separate, labelled "instantaneous eye" variant.
6. **Not modelled** (written in the result): eye-wall translucency, the λ law, and angles beyond
   ~12°.

**Reimplementation vs adaptation, summarised**
- **NATIVE:** ISET `wvf human`; ISETCam `ijspeert.m`; HDR-VDP CIE constants.
- **ADAPTED:** the HCIPy screen generator and MFT; the ISET pupil-function hook (a local patch, not
  upstream).
- **Reimplemented from the paper** (allowed only because no donor code exists): the Arias IDCT
  screen and its fit.

  Nothing else is written from scratch.
- **Licenses:**
  - ISETCam/ISETBio MIT; HCIPy MIT; HDR-VDP as recorded in `research-cache/hdrvdp3`.
  - Arias 2018 and Ntatsis 2025 articles: Optica Open Access agreement (text, not code).
  - McCann 2018 code: Frontiers supplement, article CC BY (code license not separately stated).

---

## 6. Availability ledger (what was and was not opened)

| source | status |
|---|---|
| Arias 2018 full text | opened (PMC page + Europe PMC full-text XML) |
| Ntatsis 2025 full text | opened (Europe PMC XML) |
| Ginis 2012 full PDF | opened (Univ. Murcia LOUM copy). The JoV site returned 403 |
| IJspeert 1993 | abstract only (Europe PMC). Formula verified through the ISETCam code, not the paper |
| CIE 135/1 | **not opened** (sold by CIE). Formula from Arias Eq. 1 and the HDR-VDP code |
| Westheimer & Liang 1995 | abstract page only (Optica). Paywalled |
| Watson 2015 | abstract only. PDF blocked (NASA connection reset, ARVO 403). Code description from a search snippet |
| Franssen 2007, Coppens 2006, Chen 2012, Kelly-Pérez 2013 | abstracts only (Europe PMC) |
| McCann & Vonikakis 2018 | full text (Europe PMC XML). MATLAB supplement not downloaded |

## Sources (URLs opened)

- https://pmc.ncbi.nlm.nih.gov/articles/PMC6154192/ and https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6154192/fullTextXML (Arias 2018, doi:10.1364/BOE.9.002664)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12265425/fullTextXML (Ntatsis 2025, doi:10.1364/BOE.559749); https://pmc.ncbi.nlm.nih.gov/articles/PMC12265425/
- https://lo.um.es/lo.um/wp-content/uploads/2012/05/2012_JOV_TheWide_Ginis.pdf (Ginis 2012, doi:10.1167/12.3.20); PubMed 22451158
- Europe PMC record for doi:10.1016/0042-6989(93)90053-Y (IJspeert 1993, PMID 8451840)
- https://opg.optica.org/josaa/abstract.cfm?uri=josaa-12-7-1417 (Westheimer & Liang 1995)
- Europe PMC records: PMID 25724191 (Watson 2015), 17460305 (Franssen 2007), doi:10.1016/j.exer.2005.09.007 (Coppens 2006), doi:10.1117/1.JBO.17.7.075009 (Chen 2012), doi:10.1364/JOSAA.30.002585 (Kelly-Pérez 2013)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5776149/fullTextXML (McCann & Vonikakis 2018, doi:10.3389/fpsyg.2017.02079)
- Attempted, failed: https://jov.arvojournals.org/Article.aspx?doi=10.1167/12.3.20 (403); https://humansystems.arc.nasa.gov/publications/Watson_2015_comp_human_optical_point_spread.pdf (reset); https://arvojournals.org/arvo/content_public/journal/jov/933690/i1534-7362-15-2-26.pdf (403)
- Local code read: `research-cache/hdrvdp3/src/hdrvdp-3.0.7/utils/hdrvdp_otf_cie99.m`; `research-cache/iset/isetcam/human/ijspeert.m`; `research-cache/iset/isetcam/opticalimage/wavefront/{wvfAperture,wvfComputePupilFunction}.m`; `research-cache/iset/isetbio/external/psychtoolbox/PsychOptics/West*.m`; `research-cache/hcipy/src/hcipy/optics/aberration.py`, `hcipy/util/spectral_noise.py`; `research-cache/iset/iset3d/human/`
