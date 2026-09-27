# N1.6 RoadLine pre-registration: a line of real road luminaires receding into a moonless night, through the frozen D1

Committed **before** any RoadLine scene code. D1 is unchanged (`d1-baseline`); `d1/verify_manifest.sh` runs before and
after every run. This is **not D2**: no model changes. The hypothesis of adapting per pixel vs over an adaptation field
(D2-B3) stays closed; CIE 257:2026 is noted as its future reference, not used here.

## Question
Does the frozen D1 render the project's original stimulus — a line of distant road lights at night — without
distorting what the luminaires physically send to the eye?

## Two stimuli, one frozen geometry (`B0_RESULTS.md`, `LUMINAIRE.md`)
| | A (mandatory, first) | B (B0 PASS; only after A's verdict) |
|---|---|---|
| luminaire | Cooper Streetworks **Archeon ARCH-AF16-50-D-U-T2R-7030**, LED Type II roadway optic | Cooper Streetworks **RMA15SXX22**, 150 W HPS, open-bottom Type II acrylic refractor |
| photometry | LM-63 absolute, 5813 lm; **measured intensity at V = 90° is 0 cd** | LM-63 relative, 12772 lm luminaire; 1372 cd at V = 90° along the road |
| file | sha256 `01f3de18…`, fetched by URL, not committed | sha256 `5041092f…`, fetched by URL, not committed |
| spectrum → colour | 3000 K Planckian (Kim et al. cubic, as N1) | HPS: CIE xy (0.52, 0.42), a typical high-pressure-sodium chromaticity (approximate; labelled so) |
| emitter size | luminous opening from the file: 0.5 × 0.75 ft → a 0.15 × 0.23 m rectangle | from the file's luminous dimensions |

The word "full-cutoff" is not used: its lamp-lumen-based definition is superseded (IES RP-8, LCS). The data are stated
literally.

**Frozen geometry (both):**
- flat ground: field (Lambertian 0.08, as N1) plus a 7 m road (asphalt 0.07, the N1 material);
- no buildings, trees, hills, fog, volumes, bloom, glare or fill;
- **sky**: uniform 4·10⁻⁴ cd/m² (the M1/S0/S1 value, M1 tint). This is the sky's absolute luminance, not a claim about
  the eye's adaptation luminance. **No moon.**
- **eye**: 1.7 m, on the near road edge at (0.5, 0); looking along the road (+y), pitch 0°, HFOV 60°, 1920 × 820
  (32 px/deg), as the D1 corpus.
- **luminaires**: poles on the far edge (x = 7.5); luminaire centre (5.5, d, 8.0) over the road; street side (H = 0°)
  facing −x. The LM-63 table is applied through the Cycles IES texture on a point light.
- **distance ladder**: d = 25, 50, 100, 200, 400, 800, 1600 m, seven identical luminaires.

**Predicted from the LM-63 tables** (`n1/roadline/lm63.py`) for the exact eye direction, including the 5 m lateral
offset (V from nadir; H from the street side):

| d (m) | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| V / H (°) | 76.1 / 78.7 | 82.9 / 84.3 | 86.4 / 87.1 | 88.2 / 88.6 | 89.1 / 89.3 | 89.55 / 89.6 | 89.77 / 89.8 |
| A: I towards the eye (cd) | 2372 | 252 | 57.8 | 19.9 | 9.6 | 4.7 | 2.3 |
| A: E at the eye (lx) | 3.4 | 9.8·10⁻² | 5.7·10⁻³ | 5.0·10⁻⁴ | 6.0·10⁻⁵ | 7.3·10⁻⁶ | 9.1·10⁻⁷ |
| B: I towards the eye (cd) | 6939 | 4009 | 2478 | 1882 | 1624 | 1497 | 1434 |
| B: E at the eye (lx) | 10.1 | 1.6 | 0.25 | 4.7·10⁻² | 1.0·10⁻² | 2.3·10⁻³ | 5.6·10⁻⁴ |
| emitter size at 32 px/deg | 22 px | 11 | 5.5 | 2.8 | 1.4 | 0.7 | 0.3 |

## Pipeline (all frozen, as in N1)
- Cycles CPU, 4096 spp, the same seed; OIDN with the addendum-5 settings; the noisy pass stored.
- The render is multiplied by 179 → cd/m², then D1 as on the N1 hero (extraction + C0 self-check, B, Y-priority
  display).
- The V0 pcond path.
- The plain-Blender comparator: factory AgX; exposure in whole stops **chosen from a ladder and committed before any D1
  output of that stimulus exists**.

## Gates, per stimulus
| id | criterion |
|---|---|
| **R1 photometry** | For every lamp, its rendered intensity towards the eye = LM-63 I(direction) within **10 %** (the N1 L4 tolerance). Measured from the raw scene-linear render: the lamp window's integrated luminance above the local background × pixel solid angle × distance². Also: the illuminance under the 25-m lamp = I(0°)/h² within 10 %, from an albedo-1 probe as in N1 |
| **R2 OIDN bias** | ≤ 2 % on crops fixed in the code before the render: near road, far road, field, sky. **Also on each lamp window's integrated signal**, since the denoiser must not erase or smear point sources |
| **R3 D1 self-check** | C0 bit-identical, C2/C3; display gates G1–G3, S-1…S-3. The sRGB knee artefact is a known class (`d1/ERRATA.md` E1): FAIL stays FAIL, classified if it is that class |
| **R4 ordering** | Where the scene-linear lamp signal decreases with d, the D1 output lamp signal (display luminance integrated over the lamp window above background) decreases too. Adjacent lamps both at the display floor are N/A, not an inversion |
| **R5 presence** | A lamp is *present* in an image if its window contains at least one pixel ≥ 1 16-bit code above the local-background median. **D1 must show present exactly the lamps that the raw linear anchor shows present** (the N1 "raw" variant: scene Y × k with the N1 anchor rule, scene colour, Y-priority). D1 making a lamp vanish earlier, or persist longer, than the linear anchor is a FAIL of R5 |
| **R6 colour by distance** | Reported: the u′v′ hue and chroma of each lamp core in D1 vs scene. Visual only, part of V6; the known rod-term residual (`d2/b2`) is declared |
| **V1–V6** | By the same external observer, on the D1 image alone, in the sheet format that opens. Declared residuals: white cores at the SDR peak; the rod-term pinkish tint on warm light |
| **V7 blind** | A blind sheet: D1 / V0 / plain Blender, seed-0 permutation, key hash committed before showing, judged by the external observer. The question: which renders a line of distant road lights most convincingly |

## KILL (stops N1 before motion)
- R4 or R5 fails: D1 reorders, erases or artificially keeps identical lamps.
- R1 or R2 fails and cannot be classified as a scene or measurement error: then the stimulus itself is not trusted.
- A new display pathology (clipping/gamut) not in the declared classes.
- On the blind sheets D1 is judged **worse than V0 on both A and B**, and no D1 advantage appears anywhere in this
  stimulus.

A physical disappearance is not a KILL. A's far lamps are expected to fall towards invisibility because the measured
intensity near the horizon is small. What is tested is whether D1 **follows** the physics (R4/R5 against the linear
anchor), not whether all seven lamps are visible.

## Budget and order
1. A: one static still (+ probes).
2. A verdict.
3. Then B: one static still.

There is no animation before both verdicts. The motion step (N1.7) needs its own addendum.

## Predictions (recorded before running)
- **R1 passes** for both, within 10 %, if Cycles' IES texture follows the table. That is the main technical risk: the
  Cycles IES normalisation and the camera visibility of an IES point light are untested here. If R1 fails, the failure
  is located in the renderer before anything else.
- **A:** the lamps at 25–200 m are clearly present; 400 m faintly; **800 and 1600 m absent or at the edge** of
  presence in the raw anchor and in D1 alike. The image reads as a few lamps plus their road pools, not a long string.
- **B:** all seven lamps present as a receding string: the M1-like stimulus, now from a measured luminaire.
- **R4 and R5 pass** for both (D1's A is a single global pcond scale, and B changes no luminance).
- The far HPS cores in B are small bright points, rendered close to photopic by B's per-pixel law; the rod-term tint
  is expected mainly on the dim road pools, not on the cores.
