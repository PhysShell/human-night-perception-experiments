# temporal-glare-2009 sources

Retrieved 2026-09-23. Binaries are in `research-cache/temporal-glare-2009/` (gitignored). sha256 abbreviated to 16 hex.

| id | claim / artefact | URL / file | type | size B, sha256 | confidence |
|---|---|---|---|---|---|
| T1 | paper (10 pp., CGF 28(2) 183-192); all model statements, equations, pages | http://people.compute.dtu.dk/jerf/papers/TemporalGlare.pdf (co-author J. R. Frisvad's DTU page) -> `TemporalGlare.pdf`, text `TemporalGlare.txt` | paper (author copy, EG 2009 final, PDF ModDate 2009-03-27) | 18 181 586, 6eb1b82ed3105334 | high |
| T2 | project page with PNG glare sequences (600- and 120-frame billboards), HQ AVI/MPEG video — **BLOCKED** HTTP 403 (curl, and WebFetch) | https://resources.mpi-inf.mpg.de/hdr/temporalglare/ (= http://www.mpi-inf.mpg.de/resources/hdr/TemporalGlare/ redirect) | project page | — | n/a |
| T3 | Wayback snapshot exists (2026-03-11) but web.archive.org is **blocked by egress policy** ("Blocked by egress policy", HTTP 403 via proxy) | http://web.archive.org/web/20260311020826/https://resources.mpi-inf.mpg.de/hdr/temporalglare/ (from archive.org availability API) | archive | — | n/a |
| T4 | EG digital library bitstreams need authentication (HTTP 401) | https://diglib.eg.org/items/7c0933a0-7ad3-43e9-95b2-b8c861c6c875 | paper (publisher) | — | n/a |
| T5 | supplemental video on YouTube, uploaded by author account "Tobias Ritschel" (oEmbed); download **BLOCKED** (yt-dlp: "Sign in to confirm you're not a bot") | https://www.youtube.com/watch?v=5ewKMOodT1Y | video | — | high (metadata) |
| T6 | author code: GPU glare demo, "partial implementation" (aperture model, Fresnel diffraction, chromatic blur, convolution, hippus); `glare.cpp` header "Code written by Jeppe Revall Frisvad, August 2009. Copyright (c) DTU Informatics 2009"; no licence text -> all rights reserved, not copied into tracks/ | https://people.compute.dtu.dk/jerf/code/glare_demo.zip ; described at https://people.compute.dtu.dk/jerf/code/ | code (author) | 751 333, bd2d89d3863c211f | high |
| T7 | reference screenshot of that demo on Windows (PSF / input / glare, fps 115.9 and 63.8) | https://people.compute.dtu.dk/jerf/code/images/glare_demo.png | image (author) | 760 972, 6be9ab60da2afffb | high |
| T8 | author Matlab hippus model (Eq. 1), "Jeppe Revall Frisvad, July 2008 (ported to Matlab May 2019)"; no licence | https://people.compute.dtu.dk/jerf/code/hippus/hippus_matlab.zip | code (author) | 2 033, 538e087f6fa8c7ea | high |
| T9 | WebGL hippus demonstrator + reference figure `hippus_matlab.svg` | https://people.compute.dtu.dk/jerf/code/hippus/ , .../hippus_webgl.zip | code/figure (author) | 67 286, 04718f364a60a32d | high |
| T10 | third-party re-implementation (OpenCL, Qt), student project, no licence file; **not author code**, not used | https://github.com/ASolot/temporal-glare @ 33247c45 (contains Results/TemporalGlare.mp4, 12.3 MB) | code (third party) | — | high |
| T11 | Frazetta ENB "Human Temporal Glare" game mod (third-party, unverified relation to MPI sequences; login-walled) | https://www.nexusmods.com/skyrim/mods/61405 | mod | — | low |
| T12 | co-author page links: "WebGL demonstrator of my procedural model for simulating pupillary hippus ... published in a paper at Eurographics 2009" | https://people.compute.dtu.dk/jerf/ (Code section) | doc | — | high |
| T13 | GPU FFT bug fix (May 2012) propagated to glare_demo | https://people.compute.dtu.dk/jerf/ ("GPU FFT code had a subtle bug ... glare_demo") | doc | — | high |
| T14 | Fry 1991 pupil-vs-time curves used to tune Eq. 1 | paper p. 185 [Fry91]; hippus.m comment | paper | — | high |
