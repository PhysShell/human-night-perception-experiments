# Track gazehdr-2015: Jacobs et al. 2015, gaze-aware display of very bright and very dark scenes

## IDENTITY

- David E. Jacobs, Orazio Gallo, Emily A. Cooper, Kari Pulli, Marc Levoy, "Simulating the Visual
  Experience of Very Bright and Very Dark Scenes", ACM TOG 34(3), Article 25, 2015,
  doi:10.1145/2714573 [G1].
- Project page (reachable): https://graphics.stanford.edu/papers/gazehdr/ [G2]. It hosts the preprint
  PDF (54 MB), the demo video (290 MB), the SIGGRAPH 2015 talk as Keynote (248 MB) and an
  auto-exported PPTX (237 MB). All four were downloaded to `research-cache/gazehdr-2015/`
  (sha256 in sources.md).
- Kind: **paper, video and slides only; no code.** Related patent: US 9,773,473 B2, "Physiologically
  based adaptive image generation", NVIDIA, inventors Gallo, Pulli and Jacobs [G9].

## PURPOSE

The question is whether a normal SDR monitor with a gaze tracker can make HDR content *feel*
brighter or darker by showing the side effects of adaptation ("epiphenomena") [G1 abstract]:

- gaze-driven global adaptation;
- bleaching afterimages and local-adaptation afterimages (bright side);
- Purkinje shift, mesopic hue shift and desaturation, and a stochastic loss of acuity (dark side).

The psychophysics found that mesopic cues make images look darker: the median PSE shift was
+0.13 log units, p = 2.84e-6 [G1 §4.2.2, Fig. 14]. Afterimages did **not** make images look brighter:
median −0.02 log units, p = 0.449 [G1 §4.1.2]. The talk summarises this as "≈ 25 % reduction in
brightness" for low-light rendering and "≈ 5 % increase, not significant" for afterimages
[G4 slide 21 and notes 21, 43].

## HVS COMPONENTS (implementation map, D2)

"eq" means the paper gives an equation, "phen" a phenomenological approximation, "param" a value
from Appendix A.

| Component | Treatment in the paper | Kind | Needs gaze? | Needs temporal state? |
|---|---|---|---|---|
| Optics / glare | **not modelled.** "some glare is inherently included by the camera capturing the scene—synthetic scenes can add glare using a technique such as [Ritschel et al. 2009]" [G1 p.2]. Slide 11 lists glare as a bright-light epiphenomenon but it is not implemented [G4]. | — | — | — |
| Global adaptation / tone curve | Naka–Rushton R(I)=Iⁿ/(Iⁿ+σⁿ) (Eq. 1), σ from the plateau M(Ī) (Eq. 2). Applied globally to photopic luminance; colour by constant channel ratios [G1 §2.1]. n=0.7 [App. A]. | eq, with params tuned for looks | yes: target A_T = log mean luminance "in a small patch around the user's gaze position" [§2.1] | yes: A moves toward A_T at a constant rate, a1=0.75 (to brighter) or a2=0.2 (to darker) log-units/s, no overshoot (Eq. 3) |
| Floor on adaptation | "we artificially restrict the viewer's ability to globally adapt to any luminance lower than 100 cd/m²" [§2.4] | phen / display fix | — | — |
| Bleaching afterimage | Per-cone (LMS) bleaching B from Baylor 1974, dB/dt=b1(1−B)I−b2 B, solved analytically (Eqs. 4–6). Added as J=R(I)+j1·max(B−B∞,0) (Eq. 7), converted back with matrix H [App. A]. | eq (physiology-inspired, parameters hand-tuned: "using their experimental values directly ... does not result in a plausible appearance" [§2.4]) | yes: afterimages are retinotopic and follow gaze [§2.2]; Gaussian foveal fall-off of their visibility [§2.4] | yes: per-pixel, per-cone B state |
| Local-adaptation afterimage | Calcium C, dC/dt=c1 S−c2 C with S≈1−R (Eqs. 8–10), gain α=(Cmax−C∞)/(Cmax−C) (Eq. 11). J=α j2 R(I)+j1 (C/Cmax) max(B−B∞,0) (Eq. 12). Can be negative, i.e. darker. | eq (form "chosen because we find it gives plausible results" [§2.2.3]) | yes | yes: per-pixel, per-cone C state; Gaussian blur of the B and C maps between frames [§2.4] |
| Rods/cones, Purkinje | Scotopic weights w_S=(0, 0.8451, 0.1459) on RGB, blended with photopic by ρ=(L−m2)/(m1−m2), m1=0, m2=−2 log cd/m² [§2.3.1, Eq. 13, App. A] | phen | no (ρ from pixel luminance) | no |
| Mesopic hue shift / desaturation | "simplified version of Shin et al.'s model": colour ratio blended toward the scotopic ratio of a neutral chip (dull purple), weighted by ρ [§2.3.2] | phen | no | no |
| Acuity | Stochastic band-pass loss: G=Σ w_i(ρ,X)G_i, w_i=(ρ+gX>ρ_i), X~N(0,1) sampled at low spatial and temporal resolution; σ_i=0.75·2^(i/4), ρ_i=0.286·i, g=0.25 [§2.3.3, Eqs. 14–15, App. A]. Tied to an assumed 0.6 m-diagonal 1920×1080 monitor at 1 m. | phen (the paper calls it a novel observation, "not mentioned in the literature") | no | yes: X is resampled over time |
| Scotopic foveal blind spot | tried, then **removed**: needs a better gaze tracker [§5] | — | would need gaze | — |
| Temporal state | A (global), B and C (per pixel, per cone), X (acuity noise) | — | — | — |
| Gaze | Tobii Rex, 30 Hz, about 1° accuracy; adequate "due to the relatively slow speed of adaptation processes" [§3] | — | — | — |
| Display model | J=R(I)^γ with γ=0.455; temporal dithering against banding [§2.1, §2.4]. Experiments ran on a Sony PVM-2541 OLED in a dark room (1.8e-4 cd/m² with black screen) [§4.1.1]. | simple gamma | — | — |
| Spectrum | RGB/LMS only; input is calibrated radiance-map EXR [§3] | — | — | — |

## NATIVE ENVIRONMENT

The authors' system was a set of OpenGL shaders plus OpenCV preprocessing on a GTX670 with a Tobii
Rex gaze tracker. It ran at more than 60 fps at 1920×1080 [G1 §3]. None of this was released.

## NATIVE REPRODUCTION

- **No code exists** (D3 search below), so per RULES we did **not** implement the model.
- NATIVE here means **measurements of the authors' own demo video** (`gazehdr.mp4`, 10:20,
  1366×720, 60 fps, H.264, sha256 88275cd7…). Scripts in `tracks/gazehdr-2015/scripts/`:

```
PY=<nix python3.withPackages(numpy,matplotlib,pillow)> ; V=research-cache/gazehdr-2015/gazehdr.mp4
$PY tracks/gazehdr-2015/scripts/frame_stats.py $V results/native/gazehdr-2015/NATIVE_video_framestats_30fps.csv 30 341
$PY tracks/gazehdr-2015/scripts/segment_patches.py $V lamp 27 93 results/native/gazehdr-2015/NATIVE_lamp_27-93s_patches.csv
$PY tracks/gazehdr-2015/scripts/segment_patches.py $V sunset 577 620.4 results/native/gazehdr-2015/NATIVE_sunset_577-620s_patches.csv
$PY tracks/gazehdr-2015/scripts/compare_passes.py $V results/native/gazehdr-2015
$PY tracks/gazehdr-2015/scripts/plot_native.py      # plots + NATIVE_measurements_summary.json
```

- The red gaze marker is detected automatically (R>200, G<70, B<70) and masked out of every patch.
  Values are 8-bit display code values decoded with an **assumed sRGB transfer**. They are relative
  display luminance, not cd/m².
- **Result: PASS (behaviour measured).** The video reproduces the documented behaviours.
  1. **Gaze-driven global adaptation; the time course is a ramp with an asymmetric rate.** Sunset
     demo, 600–620 s (`NATIVE_sunset_adaptation_timecourse.png`):
     - Fixating the sun at 602.0 s darkens the whole frame. The grass drops from log −0.54 to
       log −1.98 in 4.4 s (1.44 decades), mean slope −0.33 log10/s. The second sun fixation
       (614.0 s) gives −0.37 log10/s.
     - Looking away from the sun re-brightens the frame at only +0.197 log10/s, at both 606.6 s and
       618.0 s. This asymmetry matches a1 > a2 in Eq. 3.
     - The approach is a steady ramp that bends as it goes, not an exponential settle. That fits
       Eq. 3 (constant step in log A) seen through the Naka–Rushton curve.
     - Lamp demo, pass 1: moving the gaze from lamp to dark background raises the dark patch at
       +0.074 log10/s. Moving it back to lamp or bright checker lowers it at −0.12 to −0.15 log10/s.
  2. **Bright source stays clipped.** The sun disk reaches code 255 while the viewer is adapted to
     the dark house (600.4–601.9 s). Just after the long sun fixation (606.7–607.9 s) it is still
     222–238. There is **no halo or bloom** added by the system; any glow is baked into the
     photograph.
  3. **Dark-area desaturation and acuity loss.** Lamp demo, the same scripted gaze path shown three
     times (`NATIVE_lamp_passes_*`). Over t_rel 6.0–8.3 s, with gaze on the dark half and the
     afterimage faded:
     - left-checker saturation is 0.389 in pass 1 (global only), 0.407 in pass 2 (+afterimages)
       and **0.249 in pass 3 (+low-light)**, a −36 % change;
     - edge energy |∇²Y|/Ȳ is 0.151, 0.157 and **0.129** (−15 %);
     - once the gaze moves to the bright checker (9.0–11.4 s), pass 3 edge energy is 0.066 against
       0.102 (−35 %).
     - Pass 3's edge metric also flickers from frame to frame, which is the stochastic acuity.
  4. **Gaze-dependent state transitions and afterimages.**
     - After a 14 s dwell on the lamp (47–61 s), the gaze jumps to the dark checker. Pass 2 shows a
       magenta, gaze-locked lamp afterimage (difference map, row 4 of `NATIVE_lamp_passes_stills.png`).
     - When the gaze returns to the bright checker (t_rel ≈ 8.4 s), passes 2 and 3 show a
       transient **brightness boost** of the whole right side. The left-checker luminance spikes
       from 0.0097 to 0.0135 relative. This is the local-adaptation gain α>1 of Eq. 11–12
       ("local adaptation to a dark region can briefly boost the perceived brightness of other
       regions", Fig. 1 caption).
- Limits:
  - H.264 compression.
  - sRGB decode assumed.
  - Patches were hand-placed from stills.
  - The video is a screen capture at unknown display calibration, so slopes are in display-code
    log-luminance, not in the model's A.

## COMMON STIMULUS

**Not run.** There is no code, and the RULES forbid reimplementing the model. The S0–S7 stimuli
could only be passed through a reimplementation.

## ASSUMPTIONS

- Input: "calibrated radiance maps stored in OpenEXR" [§3], i.e. an absolute-scale RGB scene.
  Mesopic thresholds are in log cd/m² (m1=0, m2=−2).
- RGB→LMS for afterimages; RGB weights for photopic and scotopic luminance. No spectra.
- Viewing geometry: the acuity sampling assumes a 0.6 m-diagonal 1920×1080 monitor at 1 m
  [§2.3.3]. Gaze accuracy about 1°.
- Display: γ=0.455; the global adaptation floor is 100 cd/m² ("dimly-lit office") [§2.4].
- All parameters are "suggested", tuned for plausibility, and not claimed optimal [§2.1, App. A].

## VALIDATION

- Psychophysics with 13 participants, 11 analysed, recruited from students [§4.1.1]. Mesopic cues
  gave a significant darkening; afterimages gave no significant brightening.
- Real-flash afterimage colour: 10 participants; afterimage colour depends on flash intensity
  [§4.3].
- No validation of the adaptation time course against physiology. Rates are sped up on purpose:
  "we tune its parameters to speed up this process" [§2.1].

## REUSE

- No code. The paper and video are © ACM and the authors; the video is research-cache only.
- Small stills and derived CSVs in `results/native/gazehdr-2015/` are research notes.
- Patent US 9,773,473 (NVIDIA) covers the per-photoreceptor afterimage idea [G9]. Treat any future
  reimplementation as patent-encumbered.

## FAILURES / SURPRISES

- The talk lists **glare** among the bright-light epiphenomena, but the system deliberately leaves it
  to the camera or to Ritschel 2009 [G1 p.2; G4 notes 11].
- The authors rejected measured photoreceptor constants (Rushton & Henry 1968) as implausible-looking
  and hand-tuned instead [§2.4].
- The global-adaptation floor of 100 cd/m² means true night scenes are **never** adapted to their
  real level on this display. Darkness is conveyed by the mesopic cues instead.
- The authors themselves observed a **temporally varying acuity loss** in the dark ("irregularly
  shaped patches of locally higher resolution appearing and disappearing at random", §2.3.3). It is
  the only "breathing"-like dark-vision phenomenon in these sources. It is phenomenological, and it
  concerns detail, not point sources.

## BRIGHT POINT SOURCE

1. Where the optical PSF is applied: **nowhere.** No PSF is modelled; glare is whatever the input
   photo contains [G1 p.2].
2. Before/after adaptation: n/a. Bright sources act on adaptation only through the gaze patch mean
   A_T and through the per-pixel bleaching and calcium states.
3. Before/after tone reproduction: n/a. The afterimage term is added after the Naka–Rushton
   response (Eq. 7/12).
4. Energy preserved: not applicable (no PSF).
5. Absolute-luminance aware: **yes.** Adaptation, bleaching (B∞ depends on I in cd/m²) and mesopic
   ρ all use absolute luminance. Afterimage colour depends on source cd/m² (Fig. 5).
6. PSF depends on adaptation, pupil, age, wavelength or angle: n/a.
7. HDR source on an LDR display: global Naka–Rushton compression. The source clips or saturates,
   measured at code 255 for the sun, and stays 222–238 even when adapted to it. The paper then adds
   a gaze-locked coloured **afterimage** after the viewer looks away.
8. Halo and perceived brightness: no halo exists. Afterimages did **not** significantly raise
   perceived brightness (p=0.449) [§4.1.2].
9. Temporal PSF variation: no. Temporal effects are adaptation ramps, afterimage decay and
   stochastic acuity. None of these makes a point source flicker.
10. Clip before or after convolution: n/a (no convolution).

## D3: code search (all negative)

- Project page and Orazio Gallo publication page: PDF and video links only, "No source code is
  linked" [G2, G6].
- NVIDIA Research page: only GazeAwareDisplays.pdf and tmp.txt (162 B) [G7].
- ACM DL page: HTTP 403 to curl and WebFetch. Its supplementary list could not be checked; a search
  engine summary claimed "supplemental files including software", which is unverified. Status
  **BLOCKED**, https://dl.acm.org/doi/10.1145/2714573.
- GitHub: repository search `gazehdr` gave 0 results. Code search
  `"Simulating the Visual Experience of Very Bright and Very Dark Scenes"` gave 21 hits, all
  bibliography or paper lists. Code search `Jacobs 2015 afterimage bleaching calcium
  "Naka-Rushton" gaze` gave 0. Repository search `afterimage bleaching gaze tone mapping mesopic`
  gave 0.
- Web searches (queries in sources.md) found no student reimplementation.
- The patent was found (G9), which is not code.
- The 2014 ledger (docs/research/source-ledger.md L31) already said "no code released"; this
  search confirms it.

## D5: conceptual comparison (no composition)

| | pcond (Ward Larson 1997) | Krawczyk/Myszkowski/Seidel 2005 ("MPI 2005") | Vangorp et al. 2015 local adaptation | Jacobs 2015 |
|---|---|---|---|---|
| Goal | static visibility-matching tone reproduction | real-time TMO with perceptual effects | model of spatial adaptation, detection | make an SDR display *feel* HDR via epiphenomena |
| Adaptation | histogram adjustment over a 1° foveal grid; human-contrast/acuity/colour/veil flags (`-h`) | local contrast compression (abstract, via search listing [G12]); temporal behaviour not re-read here | per-pixel local adaptation after glare (retinal image → adaptation map) [LA Fig. 1] | **one global state A driven by gaze**, ramping in time, plus per-pixel calcium gain |
| Glare | veiling from a coarse 1° grid (`-v`) | glare listed among modelled effects (abstract [G12]); paper PDF on resources.mpi-inf.mpg.de = 403 here; no code (ledger L34) | optical GSF (CIE 135/1-6) **first**, as retinal image input to adaptation [LA §3 Eq. 2] | none |
| Night | mesopic colour loss, acuity blur | scotopic desaturation and acuity loss | tvi of retinal luminance, no colour | Purkinje, purple desaturation, **stochastic temporal** acuity |
| Temporal | none | not verified here | "can easily be combined with temporal filters" [LA §7.4] | yes, core of the method |
| Gaze | none (fixed full-frame) | none | none | required |

Jacobs is **complementary** to the baseline: it covers exactly the parts pcond lacks (temporal
adaptation, gaze, afterimages) and deliberately omits the one we need for a point source (glare).

## VERDICT

**BEHAVIORAL ORACLE.** There is no code. The paper gives exact equations and parameters, and the
authors' video yields measurable time courses. This track provides no evidence on how an unresolved
lamp should look, beyond "it clips; no halo".
