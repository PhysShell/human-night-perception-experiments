# Sources: datasets track

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| D1 | HDRPS: 106 images, 28 with colorimetric + appearance data, the rest at least absolute-luminance calibrated; multipliers are on the pages or in the data files; copyright and non-commercial terms | http://markfairchild.org/HDR.html (cached `research-cache/datasets/fairchild/`) | doc | high |
| D2 | List of scene pages; night scenes and their luminance factors (GoldenGate(2) 0.28, Zentrum 7, McKeesPub 6.25, WaffleHouse 94, Frontier 42, Peppermill 60, Flamingo 280, LasVegasStore 140) | http://markfairchild.org/HDRPS/HDRthumbs.html, http://markfairchild.org/HDRPS/Scenes/<name>.html (cached `fairchild/scenes/`) | doc | high |
| D3 | Nikon D2x, Photoshop CS2 merge, white-balanced to the in-camera white point, EXR 32-bit float claimed (the files are actually half), luminance multiplier definition, Eq. 1 matrix | http://markfairchild.org/HDRPS/CIC15HDRSurvey.pdf, pp. 1–3 | paper | high |
| D4 | D65-normalised camera→XYZ matrix "to use for most, if not all, HDR images"; Luxo factor 7.68 | http://markfairchild.org/HDRPS/D2xCharacterization.pdf, p. 1 | doc | high |
| D5 | GoldenGate(2): 18 mm, f/8, 9±4 exposures, CS-100 sky reading 0.63 cd/m² (x 0.26, y 0.23), multiplier 0.28 | http://markfairchild.org/HDRPS/Data/GoldenGateData.xls | data | high |
| D6 | OCanadaLightsData.xls holds the "No Lights" scene (multiplier 40.8) | http://markfairchild.org/HDRPS/Data/OCanadaLightsData.xls | data | high (read with xlrd) |
| D7 | EXRs are half-float PIZ RGB; sizes; clipping plateaus; zero and negative counts | `oiiotool --info`, `tracks/datasets/stats.py`, `research-cache/datasets/stats.json` | measurement | high |
| D8 | S8 calibration check ratio 1.005; geometry 56.85 px/deg (estimated) | `tracks/datasets/make_s8.py` → `research-cache/datasets/S8/meta.json` | measurement | high (calibration) / medium (geometry) |
| D9 | MPI gallery and video return HTTP 403 | `curl -I https://resources.mpi-inf.mpg.de/hdr/gallery.html`; WebFetch; `fetch.sh --probe` | measurement | high |
| D10 | MPI gallery content: 7 images, absolute cd/m² claims, AtriumNight min 0.707749 / max 6,846.03 cd/m², 1:9,673; licence sentence; © Drago / Mantiuk | page copy at https://github.com/hxa7241/p3tonemapper/blob/master/images/mpg-gallery.html (dated 20 June 2005); QUALINET entry https://github.com/QUALINET/databases/blob/master/_posts/2020-01-01-mpi_hdr_image_gallery.md | doc (mirror) | medium (mirror, 2005) |
| D11 | AtriumNight.hdr "Image courtesy Karol Myszkowski", Source photo, log10 DR 4.1 | http://www.anyhere.com/gward/hdrenc/pages/originals.html | doc | high |
| D12 | Ward copy: RGBE, Rec.709 primaries, 760×1016; ×179 max 7518 cd/m² | `research-cache/datasets/ward_anyhere/AtriumNight_oA9D.hdr`, `stats.json` | measurement | high (numbers) / low (interpretation) |
| D13 | MPI HDR video Tunnel/Highway description (640×480, 30 fps, by G. Krawczyk) | WebSearch summary of https://resources.mpi-inf.mpg.de/hdr/video/ (page itself 403) | secondary | low |
| D14 | Lars III "returned linear radiance values", calibrated with a Kodak 80 % grey card | Mantiuk et al. 2004, https://www.cl.cam.ac.uk/~rkm38/pdfs/mantiuk04pmhdrve.pdf, Sect. 4 (cached `datasets/papers/`) | paper | high |
| D15 | Laval Photometric Indoor HDR: calibrated with a chroma meter; licence agreement; 100-sample subset | https://arxiv.org/abs/2304.12372; http://www.hdrdb.com/indoor_hdr_photometric/ (404 here) | paper | medium |
| D16 | UPIQ is in absolute display-emitted units | https://www.cl.cam.ac.uk/research/rainbow/projects/upiq/; https://www.repository.cam.ac.uk/items/c2d00e29-07b5-4b67-bcfc-80893b17fa53 | doc | medium |
| D17 | HdM-HDR-2014: educational use, commercial licence, redistribution restricted; graded for 0.005–4000 cd/m² | https://hdm-stuttgart.de/vmlab/hdm-hdr-2014/ | doc | high |
| D18 | HDR-VDP FAQ: most public HDR images are relative, not cd/m² | https://hdrvdp.sourceforge.net/wiki/index.php/Frequently_Asked_Questions | doc | high |
| D19 | ISETHDR: synthetic night-driving radiance | https://arxiv.org/pdf/2408.12048 | paper | medium |
| D20 | Nikon D2x sensor 23.7 × 15.7 mm, 4288 × 2848 px | manufacturer specification (not fetched in this session; consistent with the EXR's 4288 × 2847) | spec | medium |
