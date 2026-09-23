# mpi2005 sources

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| S1 | SCCG 2005 paper exists, pp. 195-202, doi 10.1145/1090122.1090154 | https://dl.acm.org/doi/10.1145/1090122.1090154 ; https://dblp.org/rec/conf/sccg/KrawczykMS05.html ; Semantic Scholar API (openAccessPdf: CLOSED) | metadata | high |
| S2 | project page + PDF + slides (BLOCKED, HTTP 403 from container and WebFetch) | https://resources.mpi-inf.mpg.de/hdr/peffects/ , .../krawczyk05sccg.pdf , .../krawczyk05sccg_slides.pdf | paper/slides | n/a (not read) |
| S3 | old MPI domino mirror (HTTP 503) | http://domino.mpi-inf.mpg.de/intranet/ag4/ag4publ.nsf/2a3e8aac13d8697cc125675300686237/a48310c4fdbe1ea6c1256fe9004d4776/$FILE/krawczyk05sccg.pdf | paper | n/a |
| S4 | Krawczyk PhD thesis, Ch. 4 = real-time TM with perceptual effects; all equations/pages in README | https://people.mpi-inf.mpg.de/alumni/d4/2014/krawczyk/phd/krawczyk07phd_final.pdf (sha256 d00196fd…4cc4a, 7 793 901 B; local research-cache/mpi2005/krawczyk07phd_final.pdf; text krawczyk07phd.txt) ; same bytes https://d-nb.info/1004355556/34 | thesis (paper-equivalent) | high for thesis content; medium that it equals SCCG text |
| S5 | SCCG "1st Best Paper Award"; author alumni page, links only to paper/project | https://people.mpi-inf.mpg.de/alumni/d4/2014/krawczyk/ | doc | high |
| S6 | SCCG Eq. numbers = thesis 4.n (Eq. 5 adaptation p. 3, Eq. 11 key p. 4) | Stride ToneMap.cs lines 203-213 (commit ecf78116) comments | third-party code comment | medium |
| S7 | RBDOOM-3-BFG key formula, disabled, log10 missing | github.com/RobertBeckebans/RBDOOM-3-BFG tags 1.1.0-preview3 `neo/renderer/tr_backend_draw.cpp:4366-4368`; 1.2.0-preview1 `neo/renderer/RenderBackend.cpp:4364-4365`; v1.3.0/v1.4.0 `RenderBackend.cpp:4686-4696`; absent from v1.5.0, v1.6.0, master ea29c006 | code (GPL v3) | high |
| S8 | TEKUUM-D3 active key formula with log10f | github.com/RobertBeckebans/TEKUUM-D3 5791f0bc `renderer/tr_backend_draw.cpp:4385-4386` | code (GPL v3) | high |
| S9 | ET: Legacy active key formula | github.com/etlegacy/etlegacy b93c534c `src/renderer2/tr_backend.c:2761-2762` | code (GPL v3) | high |
| S10 | stuntrally/delta3d sigma/tau/adaptation citing Equ(5,7,12), sigma constant 0.4 | github.com/stuntrally/stuntrally 9a7efa5a `data/compositor/hdr/hdr.hlsl:104-116`; github.com/delta3d/delta3d 44c5cccc `examples/data/shaders/hdr/luminance_adapted_fp.glsl:43-62` | code | high |
| S11 | tizian/tonemapper key per Eqs. (1),(11) | github.com/tizian/tonemapper dd9f7c86 `src/main.cpp:323-325` | code | high |
| S12 | CryEngine log2 variant of the key | github.com/MergHQ/CRYENGINE 8b63f61c `Engine/Shaders/HWScripts/CryFX/HDRPostProcess.cfx:289-290` | code (CRYENGINE licence) | high |
| S13 | pfstools reinhard02 port by Krawczyk (only the base TMO) | pfstools `src/tmo/reinhard02/tmo_reinhard02.cpp` header lines 2-15 (mirror github.com/Steve132/pfstools); https://sourceforge.net/projects/pfstools/ | code (GPL) | high |
| S14 | GitHub search: ~65 files cite the paper title; no author repository found | GitHub code search "Perceptual Effects in Real-time Tone Mapping", "1.03 - 2.0 / ( 2.0 + log10" (2026-09-23) | search | medium |
