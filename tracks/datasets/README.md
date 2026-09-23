# Track: datasets (calibrated night HDR data for cross-testing)

## IDENTITY

Not a donor. A survey and fetcher for measured HDR photographs that carry an **absolute luminance
scale**, so donors can also be tested on real night scenes, not only on the synthetic
`stimuli/pack` (S0–S7v). Output: `manifest.json` (machine-readable), `fetch.sh` (idempotent,
SHA-256 verified), `make_s8.py` (one real night scene converted to the pack convention), and
`stats.py` (luminance statistics).
**No dataset pixels are committed.** Everything lives in `research-cache/datasets/` (gitignored).

## PURPOSE

1. Priority list: MPI HDR gallery (AtriumNight), MPI HDR video (Tunnel/Highway), Fairchild HDR
   Photographic Survey, any other calibrated night HDR.
2. For each one, record: source, licence, absolute-luminance status and multiplier, colour
   space, bit depth, dynamic range, reachability.
3. Download the few night scenes that are reachable and allowed.
4. Build a stimulus **S8 candidate**.

## RESULT TABLE

| dataset | reachable here | licence / redistribution | absolute cd/m² | night content | fetched |
|---|---|---|---|---|---|
| **Fairchild HDRPS** | ✅ 200 | © Fairchild, research & non-commercial publication only; **no redistribution** | ✅ per-scene multiplier; CS-100 spot data for 28 scenes | GoldenGate(2), Zentrum, McKeesPub, WaffleHouse, Frontier, Peppermill, Flamingo, LasVegasStore, OCanadaLights, MtRushmoreFlags | 5 EXRs + 2 data sheets + 3 docs (~160 MB) |
| **MPI HDR gallery** | ❌ **403** (server side, also WebFetch) | "freely downloaded and used", © original authors | ✅ claimed (AtriumNight 0.708–6846 cd/m², 1:9,673) | AtriumNight = lit **indoor** atrium, upper mesopic at worst | ❌ BLOCKED |
| AtriumNight via G. Ward's HDR-encoding page | ✅ 200 | no licence text; "Image courtesy Karol Myszkowski" | ⚠ **probable only** (see below) | same image | ✅ 2.6 MB RGBE |
| **MPI HDR video** Tunnel/Highway | ❌ **403** | unknown (page unreachable) | claimed (calibrated Lars III / HDRC cameras) | driving transitions, **not** night | ❌ BLOCKED |
| Laval Photometric Indoor (ICCV 2023) | page 404, root 200 | licence agreement (non-profit); 100-sample subset open | ✅ per pixel vs chroma meter | indoor only | no |
| UPIQ (Cambridge) | not tried (metadata only) | repository licence (not checked) | display-referred, not scene | none | no |
| HdM-HDR-2014 | ✅ 200 | educational only; redistribution restricted | ❌ relative | some dusk | no |
| ISETHDR (Stanford) | paper only | — | synthetic radiance | night driving | no (iset track) |

Exact blocked URLs and errors:
- `https://resources.mpi-inf.mpg.de/hdr/gallery.html`
- `https://resources.mpi-inf.mpg.de/hdr/img_hdr/AtriumNight.exr`
- `https://resources.mpi-inf.mpg.de/hdr/video/`

All three return `HTTP/1.1 403 Forbidden`, "You don't have permission to access this resource",
Apache/2.4.68 (Debian). WebFetch also gets 403, and `web.archive.org` resets the connection.
`fetch.sh --probe` re-checks them. The gallery's metadata was recovered from a 2005 copy of the
page in `hxa7241/p3tonemapper` (see sources.md D5).

## HVS COMPONENTS

Not applicable: these are data. Relevant data properties:

- **Optics are already baked in.** Every photograph already contains the camera lens PSF, flare
  and sensor MTF. An eye-PSF donor applied on top double-counts some veiling glare near lamps.
- **Spectrum.** HDRPS is white-balanced camera RGB with a published camera→XYZ matrix. There is
  no spectral data except the 9-channel Luxo scene.
- **Temporal.** Only MPI video has a time axis, and it is blocked.

## NATIVE ENVIRONMENT / NATIVE REPRODUCTION

The "native" check for a dataset is: does its own calibration claim hold on its own data?

- **HDRPS GoldenGate(2) — PASS.**
  - Scale: factor 0.28, applied to Y = 0.1904 R + 0.7646 G + 0.0450 B. That is the Y row of the
    D65-normalised D2x matrix (D2xCharacterization.pdf, p. 1).
  - Check: the median over the sky above the left tower (native rows 50–550, columns 1400–1750)
    is **0.633 cd/m²**. The data sheet's Minolta CS-100 reading is **0.63 cd/m²**, a ratio of
    **1.005**.
  - Chromaticity does **not** match (image xy 0.195/0.214 against the measured 0.26/0.23). The
    EXRs were white-balanced to the camera white point (CIC15 paper, "Imaging Procedures"), so
    luminance is absolute but colour is not.
  - Command: `nix develop -c python3 tracks/datasets/make_s8.py` (it prints `calibration_check`).
- **Ward's AtriumNight — PARTIAL, scale unverified.**
  - Multiplied by 179 (the Radiance convention), its max is 7518 cd/m² and its 0.1 % percentile
    0.32 cd/m², against MPI's stated max 6846 and min 0.708.
  - The max agrees within 10 %, but the minimum statistic is undefined, and without ×179 the max
    is 42.
  - Conclusion: probably the MPI calibrated image in W/(sr·m²), but not proven. Do not use it as
    a photometric reference.
- **MPI gallery and video — BLOCKED** (403).

## COMMON STIMULUS — S8 candidate (label: ADAPTED, format conversion only)

`research-cache/datasets/S8/` (not in `stimuli/`; the coordinator decides):

| file | content |
|---|---|
| `S8.exr` | 1024×512, float32 linear Rec.709/D65, Y in cd/m², **32 px/deg**, 32°×16° crop centred on the bridge deck lamps |
| `S8_Y.pfm` | luminance only; same PFM row order as the pack (verified against S7) |
| `S8_clipmask.exr` | 654 pixels that contain any clipped native pixel |
| `S8_native_rec709_cdm2.exr` | full 4288×2847 frame, half float, native ≈56.8 px/deg |
| `S8_preview_log10Y_clipred.png` | informational only; clipped pixels drawn red |
| `meta.json` | provenance, SHA-256, geometry, clipping, gamut, calibration check |

Conversion steps (`make_s8.py`):
1. Camera RGB → XYZ with the D65 matrix.
2. × 0.28 → cd/m².
3. XYZ → linear Rec.709. Negatives are clipped to 0: 8.9 % of pixels are affected, and the total
   Y changes by +0.11 %.
4. Exact area-average resampling to 32 px/deg. Mean luminance is preserved to 0.07 %.

Statistics:
- Y 0.032–36.0 cd/m², median 0.29 cd/m².
- The surround is upper mesopic, not scotopic: the sky is 0.4–0.6 cd/m².

**Geometry is ESTIMATED.**
- Basis: the data sheet's nominal 18 mm on the 17–55 zoom, and the D2x sensor
  (23.7 mm / 4288 px = 5.53 µm).
- The EXR carries no EXIF.
- 56.85 px/deg is the on-axis value.
- The crop reaches 18.3° off axis, where the rectilinear radial px/deg is 1.11×. Lens distortion
  is unknown.

**Caveat for the bright-point question:** the lamp cores are **clipped** by the HDR merge (a
plateau at raw 128.875 ≈ 36 cd/m²; 1,936 native pixels). The lamps' luminance and energy are
lower bounds, and they already carry the Nikkor's own PSF. S8 is valid for the **surround and
the layout** (a row of distant lamps receding over about 2 km). It is not valid as a photometric
point-source reference.

## ASSUMPTIONS

- cd/m² comes from the published multipliers.
- The camera matrix is D65-normalised.
- Rec.709 is reached via IEC 61966-2-1.
- px/deg is an estimate.
- No display is involved.
- Absolute chromaticity is **not** preserved (white-balanced source).

## VALIDATION

- Luminance calibration of S8's source is checked against its own spot measurement (above).
- No other dataset could be checked: MPI is blocked, and AtriumNight's scale is ambiguous.

## REUSE

`fetch.sh` (idempotent; verifies checksums; `--probe` re-tests the blocked hosts), then
`nix develop -c python3 tracks/datasets/make_s8.py`, then optionally `stats.py` (usage in its
header). Other night scenes can go through the same conversion by changing `SRC` and `FACTOR`:
- Zentrum ×7: range 2e6:1, the widest found.
- WaffleHouse ×94
- McKeesPub ×6.25
- Frontier ×42 (not fetched; its oncoming headlights are relevant to the point-source question)

## FAILURES / SURPRISES

- **Every HDRPS night scene checked has a hard clipping ceiling.**
  - Raw max per scene: GoldenGate(2) 128.875, Zentrum 171.875, McKeesPub 45.78,
    OCanadaLights 93.94.
  - So "calibrated HDR" does not mean the lamps are measured.
- **`OCanadaLightsData.xls` is the *No Lights* sheet.** Its multiplier of 40.8 belongs to the
  sunset shot. The Lights scene has **no** known multiplier.
- **WaffleHouse has 19 % zero-valued pixels** (crushed shadows).
- **"AtriumNight" is an indoor atrium with a 0.7 cd/m² minimum.** It is not a dark night scene,
  so it matters less than its name suggests.
- **The MPI video sequences are driving/tunnel transitions** (temporal adaptation), not night.

## BRIGHT POINT SOURCE (as data)

1. The optical PSF is applied in the camera lens, before capture (baked in).
2. Not applicable (no adaptation).
3. Not applicable (no tone reproduction).
4. Energy is **not** preserved: the cores are clipped at the merge ceiling.
5. Absolute scale: yes for the surround (checked to 0.5 %); lower bound for the lamps.
6. The camera PSF is fixed (f/8, 18 mm). It does not vary with adaptation.
7. Not applicable.
8. Not applicable.
9. No temporal variation (still image).
10. Clipping happens after the lens PSF (in the sensor/merge), so halos are real camera flare and
    cores are truncated.

## VERDICT

Not a donor. As a data source: **Fairchild HDRPS = usable, research-only, fetch-don't-commit**.
Its GoldenGate(2) is calibration-verified and is the S8 candidate. MPI gallery and video are
**BLOCKED** (manual download needed).
