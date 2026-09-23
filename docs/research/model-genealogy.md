# Model genealogy: who reuses whom (round 8)

The detailed map with page and line citations is in
[`../../tracks/historical-roots/README.md`](../../tracks/historical-roots/README.md). The graph is in
[`genealogy.mmd`](../../tracks/historical-roots/genealogy.mmd), a Mermaid file.

## Shared roots that make "different" systems NOT independent evidence

| root | appears in (verified in source or text unless marked) |
|---|---|
| **Spencer et al. 1995 photopic PSF** (built on Vos 1984) | Blender Fog Glow as calibrated in our `m1/fog_glow.py`, Mitsuba 0.6 `mtsutil tonemap -B`, the glare stage of Pattanaik 1998, Ocean's glare filter ("fully based on", vendor documentation only). Bruneton's bloom and Celestia's star renderer use a partial or approximate form |
| **Vos 1984 / CIE 135, CIE 146** | Spencer 1995, HDR-VDP-3's `'cie'` glare option, Vangorp 2015, the Speos 2023 blog's recommendation (named model; Speos internals unverified) |
| **Holladay 1926 / Moon & Spencer 1945 veil** (θ⁻² on a 1° grid) | Radiance `pcond -v` (our baseline's optional veil; OFF). **Not** the Spencer PSF: it cannot produce a sub-degree halo. Ritschel 2009's statement that Ward 1997 is Spencer-based is wrong by Ward's own text |
| **Moon & Spencer 1944 pupil formula** | Spencer 1995, Ritschel 2009 (with hippus on top), Krawczyk 2005, HDR-VDP 1 |
| **Ferwerda 1996 thresholds** (tvi, rods and cones) | `pcond -s` (baseline) |
| **Shaler acuity data** | `pcond -a`, Krawczyk 2005 |
| **Ward's scotopic luminance formula** | `pcond -c` (baseline), Thompson 2002 |
| **Cao et al. 2008 rod contribution to colour** | Kirk & O'Brien 2011, Wanat & Mantiuk 2014 |
| **Thibos 2009 mean human Zernike aberrations** | ISETBio / ISETCam human optics. VisSimFramework uses its own Zernike and Extended Nijboer–Zernike code with measured aberration sets |
| **Deeley eye-optics model** | Krawczyk 2005, deliberately used instead of Spencer |

## Consequences for comparisons

- Our Fog Glow, Ocean and Pattanaik 1998 would agree on a halo **because they share one
  kernel**. That agreement is not validation.
- Fog Glow and `pcond -v` both carry the far-field θ⁻² eye scatter, so running them together
  counts it twice.
- The only historical model in which lights "breathe" is Ritschel 2009 (pupil hippus). In its
  co-author's demo that is a 3–5 % halo pulsation below ~0.6 Hz (tracks/temporal-glare-2009).
- The 2009 night paper is Zhou, Dong, Wang & Paul, *Tsinghua Science & Technology* 14(1):133–138.
