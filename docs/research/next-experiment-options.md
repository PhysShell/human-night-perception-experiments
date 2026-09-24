# Next experiment options (after round 8)

> **Naming after review.** The former M3a/M3b are renamed:
> - E1 = ocular dynamics (hippus, temporal glare);
> - E2 = atmospheric dynamics (image motion, seeing, scintillation).
>
> Together with the display-grid artefact, the three stay separate experimental branches, never
> mixed before a separate A/B/C comparison. The next step is the **B0 bright-point bake-off**
> (`b0/`), run before any of these.

Not a recommendation of a winner. These are experimentally distinct directions, each with:
- the donor that supports it;
- what is missing;
- the experiment that would falsify it;
- how much new code it needs.

The baseline stays frozen until one of them is chosen.

## A. Eye optics first (small core + wide straylight veil)

- **Support:**
  - ISET (Thibos optics; ran under Octave), VisSimFramework (wavefront PSF code, BSD-2);
  - Spencer / Vos / CIE 146 for the wide straylight term;
  - HDR-VDP-3's `cie` option;
  - our frozen Fog Glow adapter (Spencer).
- **Claim:** a distant lamp = an optics-sized core (1–2′, i.e. ~2×2 px at 74 px/deg; M2.6 already
  gets there) plus a faint θ⁻² veil. The 0.3–0.5° "disc" of M1 comes from clipping that veil
  against a 100:1 display, not from the optics.
- **Missing:** a rule for showing the above-white part of the core and veil on a limited
  display that is not "clip".
- **Falsify:** side-by-side on PHONE of (a) the M2.6 core only, (b) core + CIE 146 veil at its
  true level, (c) Spencer halo clipped as in M1. If viewers pick (c) as closer to the memory of
  the scene, A is wrong about what matters.
- **New code:** none for the PSF (existing kernels, applied to radiance before pcond, as the
  sources agree). A display rule is design work.

## B. Local adaptation first (glare feeds adaptation, not the picture)

- **Support:** Vangorp 2015 (paper; code BLOCKED by the 403), HDR-VDP-3 (runs under Octave), Speos Dynamic
  Adaptation 2019.
- **Claim:** the veil mostly changes what the eye adapts to near each lamp: dark objects next to
  the ribbon become harder to see. It is not a visible bloom.
- **Missing:** the Vangorp code (manual download by the user); its fitted range is photopic (5–2500 cd/m² pedestals).
- **Falsify:** on S5 (source next to a dark bar) the model predicts reduced bar visibility at
  0.25°. HDR-VDP-3 with its glare option on vs off quantifies it. If predicted visibility loss
  is negligible at our levels, B adds nothing.
- **New code:** a wrapper around existing Matlab/Octave code.

## C. Temporal glare (the eye breathes) = E1, ocular dynamics

- **Support:** Ritschel 2009 (co-author demo ran natively), with its perceptual claim that
  dynamic glare looks brighter.
- **Measured:** 3–5 % halo pulsation below 0.6 Hz.
- **Missing:** the published 600/120-frame PNG sequences (BLOCKED here; the user can fetch them
  in a browser); the particle/lash components exist only in the paper.
- **Falsify:** ColorVideoVDP of S1 with the demo's hippus billboard vs static, on PHONE, at the
  true halo level. At < 0.3 JOD (the render-noise level) it is invisible and C is out.
- **New code:** none if the PNG sequences are obtained; otherwise it would need a
  reimplementation (not allowed).

## D. Atmosphere first (the air twinkles) = E2, atmospheric dynamics

- **Support:** HCIPy (native tests pass) + textbook horizontal-path formulas. At our geometry
  scintillation is the only large effect: σ_I² 0.1–1.7, pupil averaging negligible, 6–90 Hz.
  Image motion and seeing are sub-pixel.
- **Missing:**
  - verified all-regime spherical-wave formulas (two are NOT VERIFIED);
  - a validated near-ground Cn² for East Kazakhstan nights;
  - a display frame rate high enough to carry most of the spectrum (24 fps shows < 12 Hz).
- **Falsify:** scintillation time series from HCIPy for a 6 mm pupil on S3 lamps at 60 fps vs
  none, ColorVideoVDP on PHONE. If it stays below the noise level after the eye's temporal
  integration, D is out. If far lamps twinkle visibly and near ones don't, that is D's
  signature.
- **New code:** a wrapper feeding HCIPy intensity series as per-lamp gains (M3b). Allowed only
  after this decision.

## E. Industrial practice (Speos / Ocean-like)

- **Support:** documentation only.
- **Claim:** adaptation gains, then glare only above a threshold (Ocean 10× the mean), then a
  global tone map.
- **Missing:** runnable code; the order of glare vs tone mapping is undocumented.
- **Falsify:** the S3 ribbon under a 10×-mean threshold. If all 492 lamps pass the threshold,
  the gate does nothing for our scene.
- **New code:** would require implementing a closed product's documented behaviour. Not
  allowed this round.

## F. Spectral (ISET/Mitsuba-like)

- **Support:** Mitsuba (units verified), ISET optics.
- **Findings:**
  - S/P ratios LPS 0.23, HPS 0.56, LED 1.21;
  - the scotopic-weighted PSF of a warm source is ~2× wider (LCA);
  - no validated CIE 191 mesopic tool (LuxPy bug).
- **Falsify:** pcond's RGB-based scotopic estimate vs a spectral one for HPS and LED lamps (G7
  in the backlog). If the difference is below one JND of the displayed colour, F changes nothing
  visible.
- **New code:** none (existing tools), plus measured lamp SPDs.

## B0 status

**Run: `b0/` (v3, technically frozen).**

**The central task is an inverse perceptual rendering problem.** Literal retinal equality is
unreachable: a real lamp can deliver retinal irradiance no display can. The problem is to find D
within the display's capabilities whose **perceptual features**, seen by the viewer's eye in its
adaptation state and viewing condition, match those of the target retina in the real adaptation
state. The features:
- visibility of nearby objects;
- apparent source brightness and extent;
- local contrast loss;
- colour appearance;
- adaptation;
- temporal character.

This will define the objective function of a future inverse renderer. Roles:
- **Targets:** RETINAL_WAVEFRONT (ISET, Thibos) and RETINAL_STRAYLIGHT (CIE 135/1 in 2-D, the HDR-VDP fitted MTF).
- **Candidate encodings D:** pcond, Spencer, Temporal Glare.
- **Judge:** HDR-VDP's perceptual stages.

v3 findings, B0-optics layer. The only feature measured is the visibility of a trunk 0.3° from the
lamp, and P_det is a diagnostic under the HDR-VDP-3 observer model:
- **Frozen V0.** Under the selected B0 observer diagnostic, V0 substantially over-preserves the
  visibility of the nearby silhouette relative to every scene-observer reference (0.997 vs 0–0.29).
- **Spencer as D** is too revealing at low source levels against the straylight targets (gap 0.72 at
  8.9·10⁻⁶ lx, 0.17 at 8.9·10⁻⁵ lx) and matches from ~10⁻³ lx.
- **Temporal Glare** is window-limited from ×1. In its native clip, the inner glare pulsates by ~3–4 %,
  with a dominant component around 0.2–0.3 Hz, and does not wander.
- **Erratum: HDR-VDP 3.0.7 `hdrvdp_otf_cie99` is not CIE 135/1 in 2-D.** It uses a 1-D Fourier
  transform as a 2-D OTF, so its veil is 14× too low at 0.3°.
  - With the published GSF applied in 2-D, CIE 135/1 and the HDR-VDP fitted MTF agree on the trunk
    P_det.
  - The "10–20× straylight model disagreement" of the first v3 draft was this defect.
- **Wavefront vs straylight** are two parts of one PSF. Within 1.5× at 3′; from 10′ outwards scatter
  is ~20× the aberration PSF. The joint target is B1 (`docs/research/b1-full-ocular-psf-donors.md`).
- **ISET focus conventions:** THIBOS_NATIVE (+0.26 D, as published), ZERO_DEFOCUS_550 and
  BEST_FOCUS_550 (grid optimum around +0.04 D; near-optimal +0.015 … +0.054 D). The focus convention
  moves the core as much as the spectrum does.
- **Blind set.** The viewer's choice is pending; it reads as preference/resemblance, not physiology.

## Cheapest discriminating experiment

**A (falsification side-by-side) and C/D (ColorVideoVDP at the render-noise bar)** can be run
with existing code and the frozen stimuli, and together they separate the three candidate
sources of "breathing":
- display grid ~11 %, measured;
- eye hippus 3–5 %, measured;
- atmospheric scintillation, large on paper.
