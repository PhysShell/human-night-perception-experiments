# Track: historical-roots (who inherited what, 1926 → 2026)

## IDENTITY

A reading and mapping track. **Nothing here is re-implemented or run as a model.**
- Papers: read from PDFs cached in `research-cache/historical-roots/papers/` (text extracted with
  pdftotext).
- Code: read from sources cached in `research-cache/historical-roots/code/`.
- Evidence ids `[H..]` point to `sources.md`.
- Graph: `genealogy.mmd` (Mermaid; checked with `mermaid.parse`).

## PURPOSE

Map each historical night-vision or glare model to:
- the component(s) it models,
- the data and equations it takes (and from whom),
- its validation,
- its known implementations,
- who reuses it.

The main job is to find where two "different" systems are secretly the same model, especially
for the open question: an unresolved, very bright lamp on a limited display, and why distant
lights "breathe".

## DEPENDENCY MAP (paper → component → data it uses → implementations → validation)

| paper | components | key equations / data (and where from) | validation in the paper | implementations (licence) | reused by |
|---|---|---|---|---|---|
| **Spencer, Shirley, Zimmerman, Greenberg 1995**, SIGGRAPH [H1] | **optics / glare PSF** (bloom + ciliary corona + lenticular halo); adaptation-state choice | f0 = 2.61e6·exp(−(θ/0.02)²), f1 = 20.91/(θ+0.02)³, f2 = 72.37/(θ+0.02)², θ in degrees, from **Vos 1984** [33]. f3 = lenticular halo at 3°·λ/568 nm from **Simpson 1953 / Hemenger 1992**. Weights: photopic **.384/.478/.138** (Eq. 5); mesopic .368/.478/.138/+.016 f3 (Eq. 8); scotopic .282/.478/.207/+.033 f3 (Eq. 9). State ranges <0.01, 0.01–3, >3 cd/m² (Rea, IES). Age (Eq. 10, after Vos): (0.384 − 6.9e-9·A⁴)f0 + 0.478f1 + (0.138 + 6.9e-9·A⁴)f2. Pupil from **Moon & Spencer 1944**, gating the halo. Unit-volume filters; random radial flare lines added. | 7 subjects, brightness matching on a CRT: perceived source intensity rises with flare intensity (Fig. 12); context has no significant effect | **Blender Fog Glow** `fog_glow_kernel.cc` L54–72 (GPL-2+) [H20]; **Mitsuba 0.6** `mtsutil tonemap -B fov` L74–110 (GPL-3) [H21]; **Eclat Ocean** Human Vision glare ("fully based on" Spencer) [H22]; Celestia PSF stars (approx.) [H23]; Bruneton black-hole bloom (f1 only, BSD-3) [H24]; `divnorm-brightness` bloom.py [H25] | Pattanaik 1998 (glare step); our M1 `fog_glow.py` |
| **Ferwerda, Pattanaik, Shirley, Greenberg 1996**, SIGGRAPH [H2] | **adaptation**, **rods/cones**, **mesopic**, **acuity**, **temporal** (light/dark) | cone TVI log tp (Eq. 4) and rod TVI log ts (Eq. 5), fitted to psychophysical threshold data (Fig. 3). Ward-1994 contrast scale factor m = t(Lda)/t(Lwa). Mesopic Ld = Ldp + k(La)·Lds (Eq. 6). Acuity from **Shaler 1937** (Fig. 7), Gaussian cut-off. Time course from Adelson 1982 (rods), Baker 1949 (cones), Hecht 1934 / Riggs (dark adaptation). Uses V and V′ (Wyszecki 1982). Cites Spencer 1995 as separate glare work; **no glare of its own**. | none beyond demonstrations (Macbeth/Snellen scenes) | none by the authors. Third-party: Luminance HDR `ferwerda96` (GPL-2, **scotopic TVI typo**) and HDR Toolbox `FerwerdaTMO` (GPL-3) [H30]. The TVI lives on in pcond `htcontrs()` [H10]. | Ward 1997, pcond, Thompson 2002 |
| **Ward Larson, Rushmeier, Piatko 1997**, IEEE TVCG (= **Radiance pcond**) [H3] | **adaptation** (histogram of 1° foveal samples), **veiling glare**, **mesopic colour**, **acuity** | Human contrast sensitivity = Ferwerda TVI. **Veil (Eq. 8–11):** La = 0.913·Lf + K∫L/θ²·cos·sin, with **K = 0.0096 (Holladay 1926)**, integrated by **Moon & Spencer 1945**. Discrete: Lv_i = 0.087·Σ Lj cosθ/θ² / Σ cosθ/θ², weight ≈ cosθ/(2−2cosθ), then L′ = 0.913·L + Lv. Mesopic: linear ramp 0.0056–5.6 cd/m² with **Yscot = Y·[1.33(1+(Y+Z)/X) − 1.68]** (Eq. 13, fitted on a Macbeth chart). Acuity **R(La) = 17.25·atan(1.4·log10 La + 0.35) + 25.72** (Eq. 15, fit to Shaler 1937) via mip-map. | comparison with prior operators; **no psychophysical validation** | Radiance `pcond` [H10] (Radiance Software Licence): `htcontrs` = "formula taken from Ferwerda et al. [SG96]" (pcond3.c L371); `compveil` (pcond4.c L79–127, VADAPT 0.08); `hacuity` (pcond4.c L311–317); `cielum` Yscot (pcond2.c L57–66); BotMesopic/TopMesopic 5.62e-3/5.62 (pcond.h L23–24). HDR Toolbox `WardHistAdjTMO` (histogram only) [H30]; hxa7241 p3tonemapper (a re-implementation) [H26] | our frozen baseline (`m1/pcond_colorimetric.sh`: `-s -c`); Krawczyk 2005 (acuity fit); Thompson 2002 (Yscot) |
| **Pattanaik, Ferwerda, Fairchild, Greenberg 1998**, SIGGRAPH [H4] | **optics PSF + glare**, **spectral** cones/rods, **multiscale CSF**, adaptation (gain control), colour appearance | Optical PSF after **Westheimer 1986**, glare by convolution with **Spencer 1995** functions, sampled at **130 px/deg** (p. 5). Spectral integration to L, M, S, rod. Laplacian pyramid with band CSFs (van Nes 1967; Georgeson and Sullivan for suprathreshold); Hunt 1995 response; Peli contrast. | demonstrations; no user study | no public code found [H30] | its glare = Spencer |
| **Pattanaik, Tumblin, Yee, Greenberg 2000**, SIGGRAPH [H5] | **temporal adaptation**, rods/cones, appearance | Hunt's static rod/cone model + pigment **bleaching/regeneration** (τcone = 110 s, τrod = 400 s, citing [14]); neural adaptation filters; Ward-97 1° foveal weighting for the goal. **No optics/glare.** | none (demos) | `pfstmo_pattanaik00` (third-party, G. Krawczyk, pfstools LGPL); notes: rods driven by photopic Y, so **no Purkinje shift** [H30] | Krawczyk 2005 lineage (MPI) |
| **Thompson, Shirley, Ferwerda 2002**, JGT 7(1) [H6] | **acuity** (as *perceived* blur), **noise**, blue shift | Blur G_blur followed by a DoG-tuned sharpening, because pure low-pass looks blurry, which night does not (Hess 1990, Nordby). Additive Gaussian noise σ = 0.0125, set **subjectively**. Scotopic V from **Ward 1997 Eq. 13**; blue tint after Durand & Dorsey 2000. Input is an **already tone-mapped LDR image**. | none (subjective) | no code [H30] | cited by Zhou 2009 |
| **Krawczyk, Myszkowski, Seidel 2005**, SCCG [H7] | **temporal adaptation**, rods (mesopic desaturation), **acuity**, **veiling glare** | exp. adaptation after Durand & Dorsey 2000 (τrods 0.4 s, τcones 0.1 s); rod sensitivity σ = 0.04/(0.04+Y) (Hunt 1995); acuity = Ward's Shaler fit; glare = **Deeley et al. 1991 OTF** with pupil from Moon & Spencer, chosen explicitly *instead of* Spencer ("not obvious how to apply it in continuously changing luminance") (thesis §4.2.5) | real-time demo | no public code (MPI page 403) [H30] | — |
| **Zhou, Dong, Wang, Paul 2009**, "Simulating Human Visual Perception in Nighttime Illumination", *Tsinghua Science & Technology* 14(1):133–138; HAL inria-00521845 [H8] | **mesopic colour** (spectral reconstruction → cone/rod responses), luminance change, **acuity** (bilateral filter) | Linear spectral reconstruction from RGB; cone/rod weights a, b from **Shin et al. 2004** (mesopic colour appearance model); curves from Wyszecki & Stiles; day-for-night from a bright image. **No glare, no temporal.** | visual comparison with Shin et al. | none found | — |
| **Kirk & O'Brien 2011**, ACM TOG 30(4) [H9] | **mesopic/scotopic colour** (rod intrusion → Purkinje hue shift), spectral input | **Cao, Pokorny, Smith, Zele 2008** LMS + rod model; spectral images or reconstructed spectra. **No glare, acuity or temporal.** | none formal | third-party GIMP 2 plugin (Y. J. Lee, GPL, abandoned) [H30] | Wanat 2014 (same Cao root) |
| **Wanat & Mantiuk 2014**, ACM TOG 33(4) [H11] | **contrast** across luminance (retargeting), **mesopic colour**, acuity/CSF; both directions (simulate and compensate) | Kulikowski 1976 contrast matching; Barten 1999 / Mantiuk CSF; rod contribution after **Cao et al. 2008** with Smith & Pokorny fundamentals. Own psychophysical experiments (haploscopic matching). **No glare.** | own matching experiments | results gallery only [H30] | — |

Nodes only (other workers study them):
- **Ritschel et al. 2009** (Temporal Glare) [H12]: wave-optics PSF (pupil, lens and vitreous
  particles, lashes); **pupillary hippus** h(t,p) with the Moon & Spencer 1944 mean pupil (Eq. 2)
  after Fry's curves; compared to CIE-99 glare. User studies show higher perceived brightness and
  preference for dynamic glare. Track `temporal-glare-2009`.
- **Vangorp et al. 2015** [H13]: glare from **CIE 135/1-6 (Vos & van den Berg)** and the CSF from
  HDR-VDP-2 (`research-cache/local-adaptation-2015/paper.txt` L143–147, L300–320).
- **Jacobs et al. 2015** (ACM TOG, gaze-contingent bright and dark scenes): not read here.
- **HDR-VDP lineage** (metrics, not renderers):
  - HDR-VDP 1.x uses the **Normann & Baxter 1983 OTF**, with the Moon & Spencer pupil
    (`otf.cpp`, GPL-2) [H27].
  - HDR-VDP-2 (2011) fits a 4-exponential MTF in **Ijspeert 1993** form against
    **CIE 135/1 (Vos & van den Berg 1999)** data, "the only model that could approximately fit
    all experimental data" [H14].
  - HDR-VDP-3 keeps that fit as default and adds `'cie'` = the CIE 135/1 GSF with age and
    pigmentation (`hdrvdp_otf_cie99.m`) [H15].
- **Standards:**
  - Vos 1984 (CIE Journal 3(2):39–53) is Spencer's PSF source.
  - CIE 135/1 (1999) is the age/pigment GSF; CIE 146:2002 is its successor equations
    (see `docs/research/human-night-vision-landscape.md` B10).
  - CIE 191:2010 (MES2 mesopic photometry) is implemented only in LuxPy `vlbar_cie_mesopic` /
    `get_cie_mesopic_adaptation` (GPL-3) [H28]. colour-science's mesopic function uses another
    table (BSD-3) [H29].
  - CIE 1951 V′(λ) is used by Ferwerda 1996 (Fig. 2) and HDR-VDP-2 [H14]. pcond approximates
    it with RGB weights .062/.608/.330 (pcond2.c L47–49).

## SAME MODEL UNDER DIFFERENT NAMES (verified)

1. **Spencer 1995 Eq. 5 (photopic f0/f1/f2, weights .384/.478/.138) is literally the same
   kernel in:**
   - Blender's Fog Glow (`fog_glow_kernel.cc` L62–72: identical constants; FOV heuristic
     10–180° from "size", node_composite_glare.cc L2266–2282). This is our M1 `fog_glow.py`,
     which the baseline regression test checks against Spencer Eq. 5 (`m1/check_fog_glow.py`).
   - Mitsuba 0.6 `mtsutil tonemap -B` (`tonemap.cpp` L80–110: identical constants, normalised
     to sum 1).
   - Eclat **Ocean**'s Human Vision glare filter (vendor page: "fully based on" Spencer).
     Ocean also has Spencer's three states, "0.01–3 cd/m²" mesopic, an age option, and a
     threshold that applies the PSF only to pixels above 10× the mean.
   - Pattanaik 1998's glare stage.
   - `divnorm-brightness` bloom.py (same constants).
   - A reduced version: Bruneton 2020 black-hole bloom (f1 only), with the source comment
     "Curve f1(theta) from ... Spencer et al. 1995".
   - An approximation: Celestia's 2026 PSF star renderer ("Approximation of Greg Spencer et al.
     (1995) photopic PSF": val = ((peak^0.4/r − a)·b)^2.5, clipped at the peak).

   **All of these inherit Vos 1984's PSF via Spencer.** So "Blender vs Ocean vs Mitsuba" glare
   comparisons are *not* independent evidence.
2. **Radiance pcond `-v` is NOT the Spencer PSF.**
   - What it is: Holladay 1926 (K = 0.0096) through the Moon & Spencer **1945** integral, a
     1/θ² weight on a **1° foveal grid**, which moves 8 % of adaptation into the veil
     (paper Eq. 8–11; code `VADAPT 0.08`, `t2 *= .5/(1.-t2)`).
   - Ritschel 2009 writes that the glare in [LRP97] is "mostly based on Spencer et al.'s
     approach". For Ward 1997 that is **inaccurate by the paper's own text**: it cites Spencer
     as prior work but implements Holladay / Moon & Spencer.
   - Shared ancestor: Spencer's f2 ∝ θ⁻² and Holladay's L_v ∝ E/θ² (also the Stiles–Holladay
     base of CIE 135/146) are the **same far-field power law** with different normalisation and
     angular resolution.
   - Consequence: running Fog Glow **and** `pcond -v` double-counts intra-ocular scatter. M1
     keeps Fog Glow off and does not use `-v` in the frozen stack (`m1/README.md` §6), which
     is consistent.
3. **Vos is the common root of Spencer 1995 *and* CIE 135/1 / 146** (Vos 1984 → Vos &
   van den Berg 1999). So HDR-VDP-3 `'cie'`, Vangorp 2015 and the CIE 146 check proposed in
   `m1/README.md` L257 are cousins of Fog Glow, not strangers. They differ in age/pigment
   dependence and in the ~0.1° core.
4. **The Moon & Spencer 1944 pupil formula** D = 4.9 − 3·tanh(0.4(log10 L + 1)) mm is shared by:
   - Spencer 1995 (lenticular halo on/off),
   - Ritschel 2009 (mean pupil for the hippus),
   - Krawczyk 2005 (Deeley OTF),
   - HDR-VDP 1 (`getPupilDiameter`).
5. **Ferwerda 1996 TVI = pcond `-s`** (comment in pcond3.c L371). The Luminance HDR port carries
   a typo, so "Ferwerda" results differ by implementation, not by model.
6. **Shaler 1937 acuity** goes Ferwerda 1996 → Ward 1997 fit → pcond `-a` (`hacuity`) →
   Krawczyk 2005 (same fit).
7. **The Ward 1997 scotopic formula** is used by both pcond (`cielum`) and Thompson 2002 (Eq. 7).
8. **Cao et al. 2008** is the common root of Kirk & O'Brien 2011 and Wanat & Mantiuk 2014.
   **Hunt 1995** is the common root of Pattanaik 1998/2000 and Krawczyk's rod sensitivity.
9. **Mesopic bounds are not shared:**

   | source | mesopic range |
   |---|---|
   | pcond / Ward 1997 | 5.6e-3–5.6 cd/m², linear ramp |
   | Spencer 1995 and Ocean | 0.01–3 cd/m², three discrete PSFs |
   | Krawczyk 2005 | continuous 0.04/(0.04+Y) |
   | CIE 191:2010 | 0.005–5 cd/m², MES2 |

   Only LuxPy implements CIE 191.

## HVS COMPONENTS (coverage across the lineage)

| component | who models it |
|---|---|
| optics/glare PSF | Spencer 95 (static, 3 states), Pattanaik 98 (Westheimer + Spencer), Krawczyk 05 (Deeley, pupil-continuous), Ritschel 09 (wave optics, temporal), HDR-VDP 1/2/3 (metric only) |
| veiling (adaptation-level) glare | Ward 97 / pcond `-v` (Holladay) |
| adaptation | Ferwerda 96 (TVI), Ward 97 (histogram), Pattanaik 98 (multiscale gain), Pattanaik 00 / Krawczyk 05 (temporal) |
| rods/cones, mesopic colour | Ferwerda 96, Ward 97 (grey ramp), Pattanaik 98 (spectral), Kirk 11 / Wanat 14 (Cao hue shift), Zhou 09 (Shin) |
| acuity | Ferwerda 96, Ward 97, Thompson 02 (perceived sharpness), Krawczyk 05, Zhou 09 |
| noise | Thompson 02 only |
| temporal state | Ferwerda 96 (data), Pattanaik 00, Krawczyk 05, Ritschel 09 (PSF itself) |
| gaze | Ward 97 (1° fixation samples), Jacobs 15 (not read) |
| display model | Ferwerda 96 / Ward 97 (display observer TVI, Ld range), Wanat 14 (retargeting) |
| spectrum | Spencer 95 (f3 halo per λ), Pattanaik 98, Kirk 11, Zhou 09 |

## NATIVE ENVIRONMENT / NATIVE REPRODUCTION

Not applicable: papers only, no reimplementation (RULES §3).

What *was* checked natively is the **identity of code with paper**: Blender, Mitsuba 0.6 and
divnorm constants against Spencer Eq. 5, and pcond functions against Ward 1997 Eq. 8–15 and
Ferwerda Eq. 4–5, by reading source (lines cited above). Status: **PASS (textual identity)**.

## COMMON STIMULUS

Not applicable (no runnable donor in this track).

## ASSUMPTIONS

- Implementations were read at their current default branches (fetched 2026-09-23): Blender
  `main`, Mitsuba `master`, Radiance `master`, Celestia `master`.
- Ocean's behaviour comes from the vendor page only (closed source).
- Ansys **Speos**: public material says its Human Vision "emulates ... glare, depth of field,
  acuity and temporal adaptation". **No public document naming its glare model was found.**
  "Speos cites Spencer/Vos" is **UNVERIFIED**.

## VALIDATION (what each root was validated against)

- Only four works in this set have human-subject validation:
  - **Spencer 1995**: brightness matching, 7 subjects.
  - **Ritschel 2009**: brightness and preference studies.
  - **Wanat & Mantiuk 2014**: contrast/colour matching.
  - **HDR-VDP-2**: fitted to detection datasets; its glare MTF was fitted to scatter data and
    compared to CIE 135/1.
- The others are demonstrations. In particular, **Ward 1997 / pcond has no perceptual
  validation in its paper**; its components inherit the validity of Holladay, Shaler and
  Ferwerda's TVI data.

## REUSE

- `genealogy.mmd` renders in any Mermaid viewer.
- The dependency table is meant for the coordinator's docs.
- Cached PDFs and code are in `research-cache/historical-roots/` (SHA-256 in `sources.md`).

## FAILURES / SURPRISES

- **Primary PDFs missing from the expected hosts:**
  - Cornell's `graphics.cornell.edu/pubs/1995/SSZG95.pdf` redirects to bowers.cornell.edu
    (302). The Spencer PDF came from a UIUC course mirror.
  - `mathinfo.univ-reims.fr` has no DNS here.
  - MPI (`krawczyk05sccg.pdf`) returns 403. The thesis came from people.mpi-inf.mpg.de instead.
- **Ritschel 2009's characterisation of LRP97 glare as Spencer-based is wrong** (see point 2
  above).
- **Krawczyk 2005 rejected Spencer on purpose** in favour of the pupil-continuous Deeley OTF.
- **Celestia (2026) is the only implementation found that explicitly targets the *unresolved
  point on a limited display* case.** It draws a point cone plus a Spencer-like glow that
  switches on only when the peak exceeds the displayable 1.0, with a soft clip on huge peaks.
  That is our exact problem, solved heuristically.

## BRIGHT POINT SOURCE (per historical model; 1 PSF where, 2 vs adaptation, 3 vs TMO, 4 energy, 5 absolute, 6 PSF dependence, 7 LDR/HDR display, 8 brightness, 9 temporal, 10 clip order)

- **Spencer 1995:**
  1. The PSF is convolved on the floating-point radiometric image.
  2. It is applied before adaptation/TMO; the adaptation *state* only picks the weights.
  3. Before tone reproduction; "a tone mapping algorithm should be used" was left unaddressed.
  4. Energy is preserved (unit-volume filters).
  5. Absolute luminance only via state thresholds and the pupil.
  6. Depends on adaptation (3 sets), pupil (halo), wavelength (f3), and age (Eq. 10: an A⁴
     term moves weight from f0 to f2); not on field angle.
  7. The glare is shown on the CRT, burning out above 1.
  8. **Yes**: measured, perceived intensity rises with flare.
  9. No temporal variation.
  10. Convolve first, then clip.
- **Ward 1997 / pcond `-v`:**
  1. A 1/θ² veil computed on 1° foveal samples, bilinearly added.
  2. The veil also raises the adaptation (Eq. 12).
  3. Before histogram mapping.
  4. Energy is approximately preserved (0.913 + 0.087).
  5. Absolute-aware (cd/m², Holladay K).
  6. No pupil, age or wavelength dependence (colour of the source kept); field angle only via
     θ.
  7. The histogram maps to Ld 1–100 cd/m²; the pcond display clips.
  8. "lighter around glare sources, slightly darker on" them.
  9. No temporal variation.
  10. Veil first, then map/clip.
  - It cannot make a sub-degree halo: the grid is 1°.
- **Ferwerda 1996:**
  1. No PSF.
  2. Not applicable.
  3. Not applicable.
  4. Not applicable.
  5. Absolute (TVI in cd/m²).
  6. Not applicable.
  7. Scale-factor mapping, clipping at the display maximum.
  8. Not applicable.
  9. Adaptation time course only.
  10. Not applicable.
- **Pattanaik 1998:**
  1. Westheimer PSF + Spencer glare on the spectral radiance image at 130 px/deg.
  2. Before gain control.
  3. Before the display inverse model.
  4. Presumably energy-preserving (Spencer filters); not stated.
  5. Absolute yes.
  6. As Spencer.
  7. Through its inverse display model.
  8. Unknown.
  9. No temporal variation.
  10. Convolve first.
- **Pattanaik 2000:**
  1. No PSF.
  2–4. Not applicable.
  5. Absolute yes.
  6. Not applicable.
  7. Display white/gray reference.
  8. Not applicable.
  9. Temporal adaptation, not PSF.
  10. Not applicable.
- **Thompson 2002:**
  1. No PSF.
  2–3. Not applicable (it works after tone mapping).
  4. Not applicable.
  5. No (LDR input).
  6. Not applicable.
  7. The input is already LDR.
  8. Not applicable.
  9. Noise is static per frame.
  10. Not applicable.
- **Krawczyk 2005:**
  1. Deeley OTF on the HDR luminance.
  2. The pupil follows the *adapted* luminance.
  3. Before the TMO.
  4. Energy preserved (MTF(0) = 1).
  5. Absolute yes.
  6. Depends on the pupil via adaptation.
  7. The TMO output.
  8. Claimed (glare cue).
  9. Only slowly, as adaptation changes (τ 0.1–0.4 s).
  10. Convolve first.
- **Kirk 2011, Wanat 2014, Zhou 2009:** no PSF. Answers 1–4, 6, 8–10 are "not applicable".
  5: absolute yes for Kirk and Wanat; relative/user-set for Zhou.
- **Ritschel 2009 (node):**
  1. Wave-optics PSF on the HDR frame.
  2. The pupil follows the field luminance.
  3. Before tone mapping.
  4. Normalised.
  5. Absolute via Lv.
  6. Depends on pupil, λ, and particles.
  7. Tone-mapped LDR.
  8. **Yes (user study)**.
  9. **Yes: hippus and particle motion make the glare "pulsate"**. This is the only historical
     model with a physiological "breathing" of lights.
  10. Convolve first.

## VERDICT

**HISTORICAL REFERENCE** for all nine papers mapped. Spencer 1995 and Ward 1997 are also
**present as code** in the baseline (Blender Fog Glow; Radiance pcond).
