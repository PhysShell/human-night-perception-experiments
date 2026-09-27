# N1.6 RoadLine-B0 results (per `PREREG_B0.md`, commit `3d9b3ce`)

- Checker: `n1/roadline/lm63.py`. Along-road plane = H 90°/270°.
- The convention was verified for every file: H = 0° and H = 180° (street/house side) differ strongly, so the
  mirrored H 0–180 table is symmetric about the road-perpendicular plane.
- Eye 1.7 m high; pole 8 m.
- Files are fetched from Cooper's public IES directory (`https://www.webtools.cooperlighting.com/Public/files/ies/instabase/STREETWORKS/ROADWAY/…`)
  and not committed (all rights reserved; see `LUMINAIRE.md`).

| # | family / file | refractor (header) | luminaire flux (integrated) | I(82.5 / 85 / 87.5 / 90°) along road | I towards the eye at 50 / 200 / 800 / 1600 m | B0 |
|---|---|---|---|---|---|---|
| A (reference) | Archeon ARCH-AF16-50-D-U-T2R-7030, sha256 `01f3de18…` | LED Type II optic | 5813 lm (absolute) | 176 / 79 / 25.5 / **0** | 164 / 18 / 4.6 / 2.3 | – |
| 1 | OVZ Drop Lens Refractor **OVZ10SXX2EG** (100 W HPS, Type II), sha256 `cf971ff1…` | 2-way prismatic glass | 6920 lm | 289 / 222 / **170** / 151 | 281 / 165 / 154 / 153 | **FAIL** (170 < 255) |
| 2 | OVX Drop Prismatic Glass **OVX10SXX2DF** (100 W HPS, Type II), sha256 `60326693…` | **flat glass** (in the drop-glass family) | 7043 lm | 0 / 0 / **0** / 0 | 0 / 0 / 0 / 0 | **FAIL** |
| 3 | RMA/RMC Security Light **RMA15SXX22** (150 W HPS, Type II), sha256 `5041092f…` | **open-bottom Type II acrylic** | 12772 lm | 2898 / 2341 / **1831** / 1372 | 2827 / 1703 / 1455 / 1413 | **PASS** |

**Notes, recorded honestly:**
- **The flux check was ill-posed for relative photometry.** PREREG_B0 asked for the integrated flux to "match the
  stated lumens within 1 %". For relative-photometry files the stated value is the *lamp* lumens (9500, 9500, 16000);
  the integral is the *luminaire* output (efficiency 73 %, 74 %, 80 %). The check applies only to absolute files, where
  Archeon matches to 0.01 %.
- **The selection rule (Type II, flux closest to Archeon) picked a flat-glass file in the OVX "drop" family.** The drop
  (EG) variants in OVX are 150 W and were not picked. The rule is kept as registered.
- **OVZ (drop lens) sends light to the horizon, but below the 10× bar.** It gives ~150–170 cd near the horizon; a
  real but dimmer "string".
- **The winner is a rural security/yard light, not a cobra-head.** It emits even above the horizon (V 100°: 532 cd).
  The high near-horizon intensity (> M1's assumed 800 cd) is a property of this open refractor.

**Outcome:**
- **B0 PASS with RMA15SXX22.** It becomes stimulus B: a legacy HPS open-refractor luminaire, 12772 lm.
- Stimulus A stays Archeon: modern LED, 5813 lm, measured I(90°) = 0 cd.
- A and B differ in optics, flux and spectrum (3000 K LED vs HPS), because they are the real luminaires.
