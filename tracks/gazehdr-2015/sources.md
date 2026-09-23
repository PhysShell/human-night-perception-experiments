# Sources: gazehdr-2015

Retrieved 2026-09-23. Local copies are in `research-cache/gazehdr-2015/` (gitignored; © ACM and
the authors; not redistributed).

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| G1 | Equations 1–15, Appendix A parameters, §2.4 display adjustments (100 cd/m² floor, dithering, afterimage blur), §3 implementation, §4 psychophysics (PSEs, p-values), no glare model (p.2) | https://graphics.stanford.edu/papers/gazehdr/gazehdr.pdf (55,677,587 B, sha256 d5774d0b…49e7); text via pdftotext → research-cache/gazehdr-2015/gazehdr.txt | paper (preprint) | H |
| G2 | Project page: links to PDF, MP4, KEY, PPTX, and the DOI; no code link | https://graphics.stanford.edu/papers/gazehdr/ (index.html, sha256 fd7dbccc…) | doc | H |
| G3 | Demo video: lamp scene with three passes (global adaptation / +afterimages / +low-light), afterimage comparisons, experiments, Frontier and sunset "additional results" | https://graphics.stanford.edu/papers/gazehdr/gazehdr.mp4 (304,583,417 B, sha256 88275cd7…21bc; 10:20.45, 1366×720, 60 fps) | video | H |
| G4 | Talk slides with speaker notes (slide 11: glare listed as a bright-light epiphenomenon; slide 14: gaze-aware TM "similar to Rahardja"; slide 21: ≈25 % darker; notes 43: ≈5 %, not significant) | https://graphics.stanford.edu/papers/gazehdr/gazehdr_s2015_talk_exported.pptx (248,007,660 B, sha256 2dac49d8…); text dump research-cache/gazehdr-2015/pptx_text.txt | slides | H |
| G5 | Keynote original of the talk | https://graphics.stanford.edu/papers/gazehdr/gazehdr_s2015_talk.key (259,967,188 B, sha256 9ec2c869…) | slides | H (not parsed; same talk as G4) |
| G6 | Gallo's publication page links only the PDF, video and project page; no code | https://oraziogallo.github.io/publication/jacobs2015gaze/ (WebFetch) | doc | M |
| G7 | NVIDIA Research page attaches GazeAwareDisplays.pdf (53.1 MB) and tmp.txt; no code | https://research.nvidia.com/publication/2015-03_simulating-visual-experience-very-bright-and-very-dark-scenes (WebFetch) | doc | M |
| G8 | ACM DL landing page, supplementary material list: **BLOCKED** (HTTP 403 via curl and WebFetch) | https://dl.acm.org/doi/10.1145/2714573 | doc | — |
| G9 | Patent US 9,773,473 B2 "Physiologically based adaptive image generation": NVIDIA; Gallo, Pulli, Jacobs; filed 2015-05-26, granted 2017-09-26; afterimage via per-photoreceptor-type adaptation | https://patents.justia.com/patent/9773473 (403 to curl; details from a WebSearch listing); https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9773473 | patent | M |
| G10 | Code search negatives: GitHub repositories "gazehdr" (0); code search on the full title (21 hits, all bibliographies); code search `Jacobs 2015 afterimage bleaching calcium "Naka-Rushton" gaze` (0); repositories `afterimage bleaching gaze tone mapping mesopic` (0); web searches `"Simulating the Visual Experience of Very Bright and Very Dark Scenes" code implementation github` and `Jacobs Gallo Pulli Levoy gaze-aware display afterimages mesopic source code OR patent` | GitHub MCP search, WebSearch, 2026-09-23 | search log | M (absence) |
| G11 | NATIVE measurements of G3: time courses, desaturation, edge energy, sun-disk code values | results/native/gazehdr-2015/NATIVE_*.csv, NATIVE_measurements_summary.json; scripts tracks/gazehdr-2015/scripts/*.py | measurement | M (sRGB decode assumed; H.264) |
| G12 | Krawczyk, Myszkowski, Seidel 2005 abstract: real-time local contrast compression with visual acuity, glare, day and night vision | https://dblp.org/rec/conf/sccg/KrawczykMS05.html ; PDF https://resources.mpi-inf.mpg.de/hdr/peffects/krawczyk05sccg.pdf (known 403 from this container) | paper (abstract via search listing) | M |
| LA | Vangorp et al. 2015 order: glare → retinal image → local adaptation (Fig. 1; §3, L_O = I ∗ O with CIE 135/1-6 GSF) | research-cache/local-adaptation-2015/paper.txt lines 12, 305–313 | paper | H |
| L31 | Repo ledger: Jacobs 2015 has no code | docs/research/source-ledger.md L31 | ledger | H |
