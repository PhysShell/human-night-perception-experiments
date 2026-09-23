# Track pa-tonemapping-2023: "Perceptually Adaptive Real-Time Tone Mapping" (SIGGRAPH Asia 2023)

## IDENTITY

- Authors: Taimoor Tariq (Meta and University of Lugano), Nathan Matsuda, Eric Penner, Jerry Jia,
  Douglas Lanman, Ajit Ninan and Alexandre Chapiro (Meta). SIGGRAPH Asia 2023 Conference Papers,
  doi:10.1145/3610548.3618222 [P1, P2].
  - The task's guess "Tariq/Mantiuk/Myszkowski" is **wrong**. Mantiuk is cited, not an author.
- Author PDF: https://achapiro.github.io/Tar23/Tar23.pdf. It is byte-identical to
  https://taimoor6864.github.io/VRTMO.pdf (sha256 e447c125…). Video: https://achapiro.github.io/Tar23/Tar23.mp4
  (4:48, 720×404) [P1, P3].
- Kind: **paper and video only. No code, no project page.** The `achapiro.github.io/Tar23/` directory
  has no index (GitHub Pages 404). Chapiro's publication entry links only the PDF, bibtex and video [P4].

## PURPOSE

The paper chooses tone-curve parameters **in real time** so that an HDR frame keeps its perceived
*supra-threshold contrast* on a dimmer display. The target is VR, and it runs in under 1 ms per
frame on a Quest 2 [P1 abstract, §5.2].

It is a **parameter controller** for existing global TMOs; it does not make a new curve.
- Demonstrated on Reinhard's Photographic TMO, where it chooses the key `a`.
- Also shown on Drago 2003, Tumblin 1999 and a sigmoid [§7.2, Fig. 8].
- Local and global-local blending variants are in §7.3.

It addresses "fitting HDR scene contrast into a limited display instead of clipping" by picking the
compression strength that minimises a perceived-contrast difference.

## HVS COMPONENTS

| Component | In the paper |
|---|---|
| Optics / glare | **none** |
| Adaptation | local adaptation luminance = Gaussian pyramid value two levels up, "nearer to the 0.5° adapting area" of Vangorp 2015 (Eq. 1) [§3]; no temporal adaptation model |
| Contrast | Weber contrast per Laplacian level C=L(x,i)/(G(x,i+2)+ε) (Eq. 1) |
| Sensitivity | Barten 2003 CSF at the adapting luminance, band peak frequency and area: T=1/CSF (Eq. 2); band frequencies "following Mantiuk et al. [2021]" |
| Supra-threshold matching | Kulikowski contrast constancy C̃=C−T, matched between reference and test (Eq. 3); a threshold-scaling ablation fails (Fig. 3) |
| Masking | FovVideoVDP masking model, p=2.4, k=0.2854, q_c=3.237 (Eqs. 4–5) |
| Pooling | per-pixel optimal a(x,i), **simple mean** over pixels and M=3 bands (Eq. 12) |
| Rods / mesopic / scotopic | none. Kulikowski is justified for the 20–2000 cd/m² VR range [§2.3] |
| Acuity | only through the CSF weighting |
| Temporal state | leaky integrator on a and L̄_r, k_{f+1}=αk_f+(1−α)k_{f−1}, with α=0.01 (a user test found a PSE of 0.1026, but they default to 0.01) [§5.3] |
| Gaze | none. A foveated, gaze-tracked variant is future work [§8] |
| Display model | "standard display photometry and geometry model"; luminance in nits (YUV); chroma compensated by colour-to-luminance ratios (Schlick) [§3]. Mapped output L_t=L_max·aL_r/(L̄_r+aL_r) (Eq. 9) |
| Spectrum | none (YUV) |

## NATIVE ENVIRONMENT

- Unity scriptable render pipeline with two fragment shaders (parameter and tone-map), on an RTX 3080
  at 5 ms per frame (2560×1620) and on Quest 2 under 1 ms [§5.2].
- Study hardware: the Matsuda 2022 HDR-VR prototype. 20 ppd, 62° FOV, over 20,000 nits peak,
  0.05 nits black; the reference was limited to 5,000 nits [§6.1].

## NATIVE REPRODUCTION

**BLOCKED: no code.** Searches:
- GitHub repositories "perceptually adaptive tone mapping": 2 unrelated.
- `user:taimoor6864`: only Noised-Foveation and the homepage.
- `org:facebookresearch tone mapping`: 0.
- Code search on the exact title: bibliographies only.
- Web searches (sources.md).

Nothing to run.

NATIVE observation of the **authors' video** only: `results/native/pa-tonemapping-2023/NATIVE_authorvideo_nightstreet_50_60_70_80s.jpg`.
- Frames at 50, 60, 70 and 80 s: "Ours" interior; then the night street under "Fixed (Reinhard 2002)",
  "Heuristic (Krawczyk 2005)" and "Ours".
- The VR capture moves, so the views are not pixel-aligned.
- The night street has a visible street lamp. Every frame reaches code 255 (8-bit luma max 255), and
  the lamp is shown as a small saturated disc with no halo in all methods.
- "Fixed" is darkest (median code 0), "Heuristic" brightest (median 53), "Ours" in between (median 11).
- The video's own disclaimer: results are "optimized for a display peak luminance of 100 nits"; an
  uncalibrated monitor gives only a relative comparison.

## COMMON STIMULUS

**Not run** (NATIVE BLOCKED; no reimplementation allowed).

## ASSUMPTIONS

- Absolute luminance in **cd/m² (nits)**. Study stimuli were uncalibrated CC0 PolyHaven panoramas
  "manually graded to a maximum value of 5,000 nits" [§6.2].
- Display is defined by peak L_max (50/100/500/1000 nits in the study) through Eq. 9. The prototype's
  black level scaled with the backlight at constant contrast [§6.1].
- Viewing geometry from the HMD: 20 ppd, and a 2-levels-up pyramid ≈ 0.5° adapting area.
- For our targets (PHONE 73 px/deg, DESKTOP 48.4 px/deg) the band frequencies would need re-deriving.
  The paper gives no general recipe beyond "following Mantiuk 2021".
- Frame-based, frustum-only information; no knowledge of the full 360° scene [§6.2].

## VALIDATION

- 24 participants (23 analysed); 5 scenes × 4 peak luminances × 3 methods.
- "Ours" beats Fixed and Heuristic (ANOVA F=176, p≪0.01). Ours at 100 nits (Q=5.9) is preferred to
  Fixed (5.8) or Heuristic (4.5) at 1000 nits [§6.4, Fig. 6].
- This is a preference and similarity study, not a physiological validation.

## REUSE

- No code. The paper and video are © the authors (ACM author copy).
- Research-cache only: `research-cache/pa-tonemapping-2023/Tar23.pdf`, `Tar23.mp4`, text dump.

## FAILURES / SURPRISES

- No code, even though the method is small (a lookup texture plus two shaders).
- The global mean pooling of a(x,i) (Eq. 12) gives every pixel equal weight. An unresolved lamp
  (a few pixels out of about 4.1 M at 2560×1620) cannot influence the chosen curve.
- Headline figures show HDR references "with luminances above 100 nits clipped and marked with
  dashes" (Fig. 1, Fig. 7b). The paper makes no claim about how highlights should look.

## BRIGHT POINT SOURCE (from the paper's equations; nothing was run)

1. Optical PSF: **none**.
2. Before/after adaptation: n/a. The source enters only the log-mean L̄_r (Eq. 6) and the local
   pyramid adaptation used for **parameter choice**.
3. Before/after tone reproduction: n/a.
4. Energy preserved: **no**. A point with L_r ≫ L̄_r/a maps to L_t → L_max (Eq. 9): soft
   saturation, not a hard clip, and not energy-conserving.
5. Absolute-luminance aware: **yes** (nits, CSF at the adapting luminance, display L_max).
6. PSF dependence: n/a.
7. HDR source on LDR/HDR: through the global Photographic curve toward the display peak. Its
   footprint stays at its pixel size. With our S0 (sky 4e-4 cd/m², lamp peak 74.7 cd/m²) the lamp
   would sit at the top of the curve, since the scene key is set by the sky. The optimiser's
   **simple average** over pixels makes the lamp's contribution to `a` negligible.
8. Halo and perceived brightness: no halo is produced. Brightness perception is modelled only as
   local supra-threshold contrast (Kulikowski).
9. Temporal PSF variation: no. Only parameter smoothing (α=0.01) is temporal, meant to *suppress*
   flicker.
10. Clip before or after convolution: n/a. Values above L_max cannot occur after Eq. 9.

## VERDICT

**HISTORICAL REFERENCE** for this project. The paper is recent, but for us it is a documented method
without code. It is relevant as a model for *display-adaptive curve selection*, not for point-source
appearance. It is not a runnable donor.
