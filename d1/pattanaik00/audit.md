# Equation audit: `pfstmo_pattanaik00` against Pattanaik et al. 2000

## Sources

- **Paper.** The authors' copy, `https://www.cs.ucf.edu/~sumant/publications/sig00.pdf` (8 pages, 316 282 bytes,
  sha256 `fac3f654…88a7e`), read as text. It is not stored in the repo.
  - Figure 4, the block diagram, did not survive text extraction. Its per-pixel recombination of rod and cone
    signals is therefore **unverified** (marked below).
- **Code.**
  - pfstools 2.2.0, `src/tmo/pattanaik00/`: `tmo_pattanaik00.cpp`, `pfstmo_pattanaik00.cpp`, `.h`, man page.
    Source is the Nix store tarball `pfstools-2.2.0.tgz`.
  - `diff -r` against master c860691 (`d0/donors/mantiuk08/pfstools-master.nix` source) is **empty**. The operator
    has not changed since 2009 (CVS ids 2008/09, 2009/04).
- Line numbers below are for `tmo_pattanaik00.cpp` (T) and `pfstmo_pattanaik00.cpp` (P).

## Audit table

| paper element | paper | source | verdict |
|---|---|---|---|
| **Receptor response** (eq. 2) | R = B · Lⁿ/(Lⁿ + σⁿ), n = 0.73, for rods and cones | T l.43, 180–181, 249–252 | **matches** |
| **Rod input luminance** | L_rod = CIE scotopic **Y′**; L_cone = Y (§4.1.1) | T l.164, 180: `l=(*Y)(x,y)` is used for rods and cones | **differs**: rods are driven by photopic Y. No scotopic spectral weighting, **no Purkinje shift** |
| **σ_cone, σ_rod** (eqs. 4, 5; Hunt) | 12.9223·A/(k⁴A + 0.171(1−k⁴)²A^⅓), k = 1/(5A+1); 2.5874·A/(19000 j²A + 0.2615(1−j²)⁴A^⅙), j = 1/(5·10⁴A+1) | T l.219–247 | **matches** (constants identical) |
| **Static bleaching** (eq. 6) | B_cone = 2·10⁶/(2·10⁶ + A), B_rod = 0.04/(0.04 + A) | T l.357–363 (`setAdaptation`) | **matches** |
| **Adaptation goal G** | user's choice: 1/5 of the paper-white patch (title page), or 1° foveal weighting (tunnel) | T l.365–381 | **differs** (details below the table) |
| **Rod vs cone goal** | G_rod from L_rod (scotopic), G_cone from L_cone | T l.351–355: `calculateAdaptation(Acone, Acone, dt)` | **differs**: one goal from photopic Y for both |
| **Neural adaptation A** (Fig. 6) | A += F·(G − A), F = 1 − e^(−T/t0); t0,cone = 80 ms, t0,rod = 150 ms; "fast, symmetric" | T l.306–331 | **matches** (symmetric, as in the paper) |
| **Pigment kinetics B** (eq. 7a/b) | B += T(1−B)/τ − T·G·B/k, with k_rod = 16, k_cone = 2.2·10⁸, τ_rod = 400 s, τ_cone = 110 s; G is the goal, not A | T l.333–348 | **matches verbatim**, including the explicit (forward-Euler) step (details below) |
| **Light/dark asymmetry** | from the B terms: bleaching rate ∝ G (fast in bright light), regeneration τ = 110/400 s (slow in the dark) | as above | **matches in form**. B_cone ≈ 1 for G < 10⁴ cd/m², so cone dark adaptation has **no minutes-long phase** below that. The slow phase is rods only (see `native_timecourse.json`) |
| **Colour compression** (eq. 3) | R_color = (RGB/L_cone)^S_color, S_color = n·B_cone·Lⁿσⁿ/(Lⁿ+σⁿ)², using the cone σ | T l.165–167, 189–191 | **matches** |
| **Display colour** | Cd = Q_color^(1/S_d), S_d = forward difference of eq. 2 between display REFblk and REFwht = 0.1383 | T l.92–94, 191 (`Scolor /= S_d`), 201–203 | **matches** (computed S_d = 0.138311) |
| **Rod + cone combination** | R_lum = R_rod + R_cone (§4.2); per-pixel recombination with colour is in Fig. 4 | T l.182–187, 201–203 | R_lum **matches**. Recombination **unverified**: see below the table |
| **Reference white / black** (eq. 8) | REFwht at 5A, REFblk at 5A/32, rod + cone responses | T l.73–76, 104–113 (`dark_factor = 32/5`) | **matches** |
| **Inverse appearance rules 1–4** | (1) reproduce directly if possible; (2) if the scene span > display span, compress + offset to match REFwht and REFblk; (3) if scene Qmid > display Qmid, shift down until scene REFwht ≤ display REFwht; (4) else shift up until display REFblk ≤ scene REFblk | T l.115–154, 194–195 | **matches**, except that rules 3/4 test REFwht/REFblk instead of Qmid (minor). Ra is clamped to [0, 0.9999999] |
| **Display observer** | "typical CRT in office light": A = L_display = 25, REFwht 125, REFblk 4 cd/m², σ_cone 646, σ_rod 722, B_cone 1, B_rod 0.0016; display gamma 1 | T l.78–94 | **matches** for the cones (σ_cone(25) = 646.1). The display's rod response is **omitted** (B_rod = 0.0016, negligible). The paper's σ_rod = 722 is 5 × eq. 4 at 25 (144.7) |
| **Inverse display model** | inverse of eq. 2 with display constants, gamma 1 | T l.198: `I = σ_d·(Ra/(1−Ra))^(1/n)/125` | **matches**. Output 1.0 = display REFwht = 125 cd/m². Display black is not subtracted |
| **Display / Ldmax parameters** | the paper fixes one display | P: none (`-m`, `-c`, `-r`, `-t`, `-f`, `-l` only) | **no display parameters**. The tool is display-unaware |
| **Acuity loss, noise, glare** | named as future work (§6) | — | **missing** (as in the paper) |
| **Local adaptation** (`--local`) | **not in this paper**. Man page cites Pattanaik & Yee, SCCG 2002 | T l.169–177, 269–295; P l.155 | **extra** (details below the table) |

**Adaptation goal G (T l.365–381).**
- The static state and frame 0 use `setAdaptation(Y)`: **A = 5 × log-average**, with B at its steady state.
- Frames ≥ 1 under `-t` use the goal **G = log-average × 1**.
- The log-average is exp(mean log(Y + 10⁻⁴)) − 10⁻⁴, summed in float32.
  - At night the 10⁻⁴ offset is larger than the scene itself (S1 median 7·10⁻⁵). S1 comes out 1.36·10⁻⁴ in
    double precision vs a geometric mean of 1.03·10⁻⁴.
  - The float32 sum gives 1.27·10⁻⁴, as `--verbose` A/5 shows.
- The factor-5 mismatch means a **static clip drifts under `-t`**. On a static 0.01 cd/m² field the background
  rises from 0.038 to 0.115 within 1 s (run E). That drift was seen in m0 and not explained there.

**Explicit-step stability (eq. 7).**
- The step for rods is unstable when G·T/16 > 2. At 24 fps that means G > 768 cd/m² (at 16 fps, G > 512 cd/m²).
- **1000 cd/m² at 24 fps**: B_rod oscillates, diverges to ±10², then NaN. The output is **white for the rest of
  the stream**.
- **At the paper's own T = 30 ms**, the 0.01 → 1000 step oscillates: B_rod alternates in sign for about 0.3 s,
  and the display flickers 0.55 / 0 / 0.37 / 0.12 … on successive frames.

**Rod + cone combination (T l.182–187, 201–203).** out_c = C_c^(S/S_d) · I · R_cone/R_lum + I · R_rod/R_lum.
- The rod share is added **achromatically**. This desaturates as rods dominate.
- The cone share keeps the compressed chroma ratio.
- This combination is not in the paper's text. It is the implementation's reading of Fig. 4.

**`--local` (not in the 2000 paper).**
- **Per-pixel A.** A = weighted mean over a radius-4 px disc, with weights exp(−|log₅L − log₅L_c|⁶). B is static
  per pixel.
- **The global mapping is not updated.** In `--local` the model object is never set (P l.155 skips it), so the
  reference white/black and the display offset use the **constructor default A = 60 cd/m²** ("office") for every
  image.
- **Options that do nothing.** `-t` is cancelled; `-c`/`-r` are ignored.
- **Y = 0.** It gives log(0), so A = NaN and the pixel renders **white**.
- The disc also skips row/column 0 (`x+kx>0`).

## Other behaviour relevant to the runs

- **Input units.** Absolute cd/m² are required (man page, paper). `LUMINANCE` tags are not read. The output is
  tagged `RELATIVE`.
- **`-t --fps`.**
  - dt = 1/fps. Any fps > 0 is accepted; the default is 16.
  - Frame 0 = the static state (A = 5·log-average) or the `--cone`/`--rod` values.
  - From frame 1 on, A and B follow the goal from each frame's log-average.
  - "No influence on single-frame input" (man page) holds.
- **`--cone`/`--rod`.**
  - Without `-t`: a fixed A for every frame, with B at its steady state.
  - With `-t`: only the initial state.
- **NaN handling.** The clamp `(v<1)?((v>0)?v:0):1` maps NaN to **1**.
  - Input chroma channels ≤ 0 become 1.0 in that channel (S5: 80 846 red pixels).
  - A negative Y makes the global log-average NaN and hence the whole frame NaN (the m0 observation).
- **Colour space.** The pfs sRGB/Rec.709 matrix. Output channels are clamped to [0, 1] before the conversion back
  to XYZ.
