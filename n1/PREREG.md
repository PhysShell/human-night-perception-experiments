# N1 pre-registration: one complete night scene (hero shot) through the frozen D1 baseline

Committed **before** any scene code. N1 tests a **scene**, not the model.
- D1 is used as is: tag `d1-baseline`, `d1/verify_manifest.sh` must pass before and after every N1 run.
- **Nothing in D1 changes.** A problem found here is first classified (scene / lighting / materials / art direction /
  D1 residual). Only a D1 residual may open a D2 item, via `d2/TEMPLATE.md`.

## Question
Is the frozen D1 enough to turn a physically reasonable night scene into a convincing, usable night image, without
artistic crutches?

## Necessary condition
With physically plausible night lighting (no hidden fill, no levels raised by orders of magnitude) and plausible
materials, the scene's key structure is physically present in the absolute render. D1 then makes it read as night
at least as convincingly as a plain exposure does.

## The hero view (N1.0, fixed here)
One camera; the same geometry convention as the D1 corpus: eye height 1.7 m, HFOV 60°, 1920 × 820, shown on the
PHONE geometry (73 px/deg).

The rural edge of a village, continuous with the M1 world (the poplar row, a field). The frame contains:

| required element | in the scene |
|---|---|
| open sky | uniform clear night sky, upper ~40 % of the frame |
| dark ground | a mown field (left half) |
| a large silhouette | the poplar row plus a barn against the sky |
| an artificial source, visible | one street luminaire on a 6 m pole, mid-right, emitter visible |
| a surface it lights | the asphalt lane and barn wall under it |
| a specular material | a rain puddle on the lane, reflecting the luminaire |
| a region that should almost vanish | the ground under the poplars, in their moon shadow |

- A second practical source, **one lit barn window**, is added only after the lamp passes N1.1.
- **Moon:** a quarter moon, low (elevation 25°), 60° to the side of the view direction. It is **out of frame** (a
  moon in frame belongs to later camera C), raking across the field and leaving the poplars in silhouette.

## Photometric authoring
The unit convention stays the D1/M1 one: K = 179 lm/W (`m1/README.md` §1), luminance = 179·Y.

These are **authoring values plus sanity bands**, not targets to fit to the third digit.

| source | authored as | sanity reference |
|---|---|---|
| moon | Cycles Sun, horizontal illuminance on open ground **0.02 lx** (→ 0.02/179 W/m² normal to the beam, corrected for elevation) | CIE quarter moon under clear sky ≈ 0.01–0.03 lx (full moon ≈ 0.1–0.3 lx); Blender's own moonlight hint is ~0.001 W/m², i.e. full-moon order |
| sky | uniform world radiance **1·10⁻³ cd/m²** (M1's moonless 4·10⁻⁴ plus moonlit brightening; an authoring assumption) | the sky must stay brighter than the moonlit field and darker than any lit surface |
| street luminaire | Cycles Spot, full-cutoff optic: cone half-angle 70°, blend 0.3, radius 0.15 m, **2000 lm**, 3000 K blackbody; plus the visible emitter disc (same radius), camera-visible only | a residential lane lamp |
| window (N1.1 step 3 only) | an emissive pane, warm 2700 K, **10 cd/m²**, lighting nothing beyond what its emission physically does | lit curtain seen from outside |

**Materials** (diffuse albedo; Principled BSDF, no emission unless listed above):
- asphalt 0.07;
- field 0.08;
- poplar foliage 0.06;
- barn wall (weathered plaster) 0.45;
- roof 0.10;
- pole 0.3;
- puddle: water, IOR 1.33, roughness 0.02, over the asphalt.
- Roughness and specular are physical settings, **never used to brighten**.

## N1.1: physical sanity (cheap falsifiers before any production render)
Probes are measured on low-sample renders of the hero camera plus dedicated illuminance probes (small horizontal
white diffuse patches, albedo 1, invisible to the camera). The results go to `n1/probes.json`.

Order:
1. **Environment only** (moon plus sky).
2. **+ luminaire.**
3. **+ window.** Each source switched on one at a time.

| id | gate |
|---|---|
| **L1 no hidden light** | the scene's light list is exactly: sky, moon, luminaire spot plus emitter disc, window pane. It is checked programmatically: every light object, every material with a non-zero Emission Strength, the world. Any extra light, or emission not in the table, is a FAIL |
| **L2 environment levels** | environment only: open-field illuminance 0.01–0.03 lx; sky luminance within 5 % of authored; open-field luminance within 3× of ρE/π; sky > field; the shadow under the poplars darker than the open field |
| **L3 luminaire containment** | the lamp's own ground illuminance (step 2 minus step 1): under the lamp 5–30 lx; at 30 m horizontal from the pole **< 10 % of the moon's illuminance**. So "one lamp lights half the village" fails |
| **L4 visible source** | the emitter disc luminance equals Φ/(π·A) within 10 %, i.e. the visible core and the light it casts come from the same luminaire |
| **M1 materials** | every diffuse albedo as tabled (≤ 0.5 everywhere); no roughness/specular override tied to lighting |
| **M2 attribution** | for any probe outside its band, the Cycles direct/indirect/colour passes are read before anything is changed, and the cause is recorded |

**Budget for N1.1:** at most **3 correction rounds** of lights or materials.
- Each is logged with its cause.
- No new renderer features (no volumes, no fog, no bloom, no denoiser changes); D1 untouched.
- If the bands still fail after 3 rounds: **stop and report**.

## N1.2: hero render and diagnostic versions
- Production render: Cycles CPU, no denoiser (as M1), with the sample count fixed once N1.1 passes and recorded.
- Absolute EXR in cd/m² (×179), then through the frozen D1 code: `d1/a_extract` extraction for the new image; B and
  Y-priority display as in `d1/final/run.py`.

Four versions of the same frame, **for diagnosis, not for choosing the prettiest**:

| version | luminance | chromaticity | display |
|---|---|---|---|
| raw | scene Y × one global exposure | scene u′v′ | Y-priority projection |
| A-only | D1 A (Y_A) | scene u′v′ | Y-priority |
| B-only | scene Y × the same global exposure as raw | D1 B | Y-priority |
| final | D1 A | D1 B | Y-priority (= D1) |

- The raw/B-only exposure is fixed as the one mapping the open-field median to the same display luminance as in
  final. It is a diagnostic anchor, not a tone map.
- D1's numeric gates P-1…P-3 (finite, in-gamut B preserved / projection exact, no clipping) are **reported** for the
  hero frame (information: they hold by construction).

## N1.3: the blind-ish sanity check (anti-self-deception, not psychophysics)
Three versions of the hero frame on the same SDR100 display, shown unlabelled in a random order:
1. **D1 final**;
2. **plain Blender**: the same EXR through Blender's default view transform, with an exposure chosen by hand
   **before** the D1 final is rendered or seen, and recorded;
3. **the D0 pcond default baseline** (`pcond -s -c` full RGB, the old reference).

- Order: seed 0 permutation.
- The key's sha256 is committed **before** the sheet is shown; the key is revealed after the judgement.

## Acceptance (product acceptance, visual; judged by the user, not by me)
I report my own reading separately; it does not count. **No single-number "nightness".**

| id | criterion |
|---|---|
| **V1 night identity** | without a caption it is obvious the scene is at night |
| **V2 composition** | the main structure (lane, lamp, barn, poplar row, field) reads |
| **V3 darkness** | a substantial region exists where detail is genuinely lost |
| **V4 sources** | the sources look brighter than their surroundings and plausibly light them (pool on the lane, reflection in the puddle) |
| **V5 silhouettes** | the large forms read without artificial fill |
| **V6 no new artefact** | no clipping blobs, halos, banding, blue plates or similar |
| **V7 blind check** | D1 final is not judged worse than the plain exposure (information if equal, KILL if worse; see below) |

The known D1 limitations (lamp cores whiten at the SDR peak; B's chroma) are not V6 failures, but they are reported
where visible.

## KILL (N1 in its current form ends)
- readability needs a hidden fill light;
- real night levels must be raised by orders of magnitude, beyond the sanity bands above;
- D1 final is judged worse than the plain exposure in the blind check;
- the key composition cannot be read even with reasonable lighting.

After a KILL: classify the cause (scene design, lighting, materials, art direction, or a D1 residual). **Only a D1
residual may open a D2 item.**

## Not in N1
Kellnhofer; any sky-chroma fix; special warm lamp cores; a new TMO; volumetric fog; bloom or glare; a cinematic LUT;
manual colour grading; more cameras or motion. Cameras B, C and a short move come only after the hero passes.

## Layout
- `n1/PREREG.md`, `n1/scene/` (the Blender script), `n1/probes.json`, `n1/README.md`.
- `n1/renders/{raw,axis_a,axis_b,final}/`: 8-bit/16-bit PNG only.
- EXR and other large intermediates live in `n1/work/` (gitignored, like `d0/work`); their sha256 is recorded in the
  README.
