# Datasets for cross-testing (round 8)

Full survey, licences, checksums and fetcher: [`../../tracks/datasets/`](../../tracks/datasets/README.md)
(`manifest.json`, `fetch.sh`). **No dataset pixels are committed**; everything is fetched into
`research-cache/datasets/` (gitignored).

| dataset | status here | licence | absolute cd/m² | use for us |
|---|---|---|---|---|
| **Fairchild HDR Photographic Survey** | fetched: 5 night EXRs + data sheets | © Fairchild; research and non-commercial publication only; no redistribution | per-scene multiplier. **Verified** on Golden Gate (2): sky median 0.633 vs metered 0.63 cd/m² | surround and layout of real night scenes. Lamp cores are clipped by the HDR merge (lower bounds only), and the camera lens's glare is already baked in |
| MPI HDR gallery (AtriumNight) | **BLOCKED**: HTTP 403 from resources.mpi-inf.mpg.de | "freely used", © authors | claimed 0.708–6846 cd/m². Greg Ward's RGBE copy gives 7518 max ×179 → scale only probable | a lit indoor atrium, not a dark exterior |
| MPI HDR video (Tunnel, Highway) | **BLOCKED** (403) | unknown | claimed | driving transitions, not night |
| Laval Photometric Indoor, UPIQ, HdM-HDR-2014, ISETHDR | metadata only | various, see manifest | Laval yes; the others relative, display-referred or synthetic | not night exteriors |

**S8 (candidate, not in the frozen pack):** Golden Gate (2) converted to the pack convention
(linear Rec.709, Y in cd/m²), resampled to 32 px/deg from an estimated 56.85 px/deg (nominal
18 mm lens), with a clip mask. It lives in `research-cache/datasets/S8/`; rebuild it with
`tracks/datasets/make_s8.py`.

**Missing:** a calibrated real night scene in which distant point lamps are **not** clipped
(a bracketed exposure series reaching the lamp cores). None of the reachable sets has one.
This matters most for the bright-point question.

The user can fetch the MPI files manually (the pages open in a normal browser) and drop them
into `research-cache/datasets/`. `fetch.sh --probe` re-checks the URLs.
