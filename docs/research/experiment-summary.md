# Round 8 summary: parallel donor bake-off

**Question:** how do existing human-vision systems represent an unresolved, very bright point
source on a limited display? And what makes distant lights "breathe"? The baseline stayed
frozen, and nothing was added to the Blender pipeline.

**Setup:**
- a common immutable stimulus pack S0–S7v (`stimuli/`, cd/m², 32 px/deg, energy-exact points);
- explicit display targets: PHONE 73 px/deg and DESKTOP 48.4 px/deg (`stimuli/display_targets.json`);
- baseline outputs (`results/baseline/`);
- seven parallel workers under one rule set (`tracks/RULES.md`: native first, no reimplementation).

## Outcome by track (details: [donor-atlas.md](donor-atlas.md), [donor-matrix.md](donor-matrix.md))

- **Ran natively here:**
  - temporal glare (the co-author's GPU demo under Mesa);
  - HDR-VDP-3 (Octave);
  - ISET human optics (Octave, partial);
  - HCIPy;
  - ColorVideoVDP / FovVideoVDP;
  - Mitsuba 3;
  - VSS (lavapipe).
- **Measured from authors' material:** GazeHDR (author video).
- **Blocked:**
  - MPI-hosted artifacts (Temporal Glare PNG sequences, Local Adaptation code, MPI HDR
    gallery/video; HTTP 403 from the server);
  - MATLAB-only parts of ISET;
  - Windows/Unity builds (VisSimFramework, OpenVisSim);
  - commercial systems (Speos, Ocean: documentation only).
- **Stopped:** the local-adaptation worker ran HDR-VDP-3 but never documented Vangorp 2015. The
  coordinator wrote that track from the paper; the code is not obtained.

## What we learned (cross-cutting)

1. **Where the PSF goes is settled across all optical models.** On radiance, before tone
   reproduction, energy-preserving. Every system that clips first is an LDR effect. Vangorp 2015
   goes further: glare's main job is to set the **adaptation** state near the source, not to be
   a visible bloom.
2. **No donor solves showing the above-white part** of a point source on a limited display.
   The options are:
   - industrial threshold gating (Ocean, 10× the mean);
   - adaptation plus white point (Speos, Ocean);
   - plain saturation with no halo (GazeHDR, Tariq 2023);
   - Spencer's argument that the halo exists to make the source look brighter.

   This is a design decision to test, not something to adopt.
3. **The eye's optical core is small.** Warm lamps give 1–2′ (ISET, Thibos). The M2.6 core of
   2×2 px at 74 px/deg (~1.6′) is already at that scale. The large halo in Spencer/Vos is the
   wide-angle straylight, and M1's disc came from clipping it.
4. **Three candidate "breathing" sources, now with numbers:**
   - display-grid modulation ~11 % (M2.6);
   - eye hippus 3–5 % below 0.6 Hz (Ritschel demo);
   - atmospheric scintillation σ_I² 0.1–1.7 at 6–90 Hz.

   Image motion and seeing are sub-pixel. Only scintillation is physically large, and most of
   its spectrum is above what 24 fps can show.
5. **Shared ancestry** ([model-genealogy.md](model-genealogy.md)):
   - Spencer's PSF sits inside Fog Glow, Mitsuba 0.6, Pattanaik 1998 and (per vendor) Ocean;
   - `pcond -v` is a different, 1° veil (Holladay / Moon–Spencer);
   - Vos is the common root of Spencer and CIE 135/146.
6. **Tool findings worth keeping:**
   - LuxPy's CIE 191 mesopic function omits a factor;
   - VSS's batch path double-encodes sRGB;
   - the Temporal Glare demo reads an uninitialised FFT size;
   - HDR-VDP-3 is luminance-only for chromatic questions.

## Stop condition check

| condition | status |
|---|---|
| high-priority open donors run natively or explicitly blocked | ✅ Temporal Glare ran (demo); Local Adaptation BLOCKED (403); HDR-VDP-3, HCIPy, VDPs, Mitsuba ran |
| papers/demos/slides archived/indexed | ✅ per-track `sources.md`; binaries in `research-cache/` (not committed) |
| several independent outputs for the same bright-point stimuli | ◐ S0/S1: baseline, temporal glare (ADAPTED), ISET optics, HDR-VDP-3. The ribbon only via baseline and metrics |
| where glare/PSF/adaptation occur in each architecture | ✅ [bright-point-source.md](bright-point-source.md) |
| eye vs atmosphere vs display-sampling effects distinguished | ✅ with magnitudes (item 4) |
| production pipeline untouched | ✅ (m0–m26, t2, flake unchanged this round) |

**Next:** [next-experiment-options.md](next-experiment-options.md). The cheapest discriminating
step is option A's side-by-side plus the C/D ColorVideoVDP tests at the render-noise bar.
The user can unblock C and B by downloading the MPI files in a browser.
