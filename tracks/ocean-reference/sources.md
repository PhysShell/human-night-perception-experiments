# Sources: ocean-reference

Retrieved 2026-09-23. Local copies are in `research-cache/ocean-reference/` (html and txt dumps).

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| O1 | Ocean 2025 docs (13.2.6); the filter list incl. Human Vision Drago/Glare, Spectral to Human Vision; "filters ... are chained in the output node"; version tree 2013–2025 on the server | https://docs.eclat-digital.com/ocean2025-docs/nodes/filter.html ; https://docs.eclat-digital.com/ (index) ; searchindex.js | doc | H |
| O2 | Glare filter: Spencer-based PSF; three regimes with cd/m² ranges; age; dispersion; threshold rule I > mean(Y)·threshold, default 10; XYZ input; denoise before; XML example | https://docs.eclat-digital.com/ocean2025-docs/nodes/filter/glare.html ; python API https://docs.eclat-digital.com/ocean2025-docs/api/python/_autosummary/ocean.abyss.nodes.filter.Glare.html | doc | H |
| O3 | Drago filter: b (0..1, best 0.85), ld (100 cd/m² CRT reference) | https://docs.eclat-digital.com/ocean2025-docs/nodes/filter/drago.html | doc | H |
| O4 | Spectral to Human Vision: time_adaptation (none/light/dark), luminance regime, illuminance 0.01–1000, age 0–120, time (s); "Glare filter could be applied afterwards to simulate the bloom effect" | https://docs.eclat-digital.com/ocean2025-docs/nodes/filter/spectraltohv.html | doc | H |
| O5 | C++/Python API: Glare getAge→int32, getLuminanceChoices; Purkinje node with a float `visionmode` | https://docs.eclat-digital.com/ocean2025-docs/api/cpp/nodes/filter/Glare.html ; .../api/cpp/nodes/filter/Purkinje.html | doc (API) | H |
| O6 | Glare Map output (UGR/DGP/GR indices) exists as an output node | https://docs.eclat-digital.com/ocean2025-docs/nodes/output/glaremap.html | doc | H |
| O7 | Blog "Ocean™ Module: Human Vision" (L. Raimbault, 2023-06-21): post-processing filters; Drago; Spencer/Vos PSF (section 3); photopic halo versus mesopic/scotopic lenticular halo and random lines; threshold purpose; night example scotopic, age 40, dispersion | https://eclat-digital.com/ocean-module-human-vision/ | blog (vendor) | M |
| O8 | Blog "Human Vision Simulation to improve Product Design" (L. Raimbault, 2023-11-10): 683 / 1700 lm/W gains; mesopic after Shin/Shioiri 2004; age after Jackson & Owsley 2000 and Jackson, Owsley & McGwin; time adaptation as luminosity-function gain changes, 1 s / 1 min / 20 min examples | https://eclat-digital.com/human-vision-simulation-to-improve-product-design/ | blog (vendor) | M |
| O9 | EGSR 2025 talk on Glare Map (UGR, DGP, GR); paper on EG diglib; dataset Zenodo 15396471 | https://eclat-digital.com/egsr-2025-glare-simulation-ocean/ ; https://diglib.eg.org/items/7841406a-030c-4834-ad27-95ba4dec4e27 ; https://zenodo.org/records/15396471 | blog / paper / data | M (not downloaded) |
| O10 | The Human Vision node pages return HTTP 500 in the ocean2021–2024 doc trees (same relative path) | https://docs.eclat-digital.com/ocean2024-docs/nodes/filter/glare.html (500) | doc probe | M |
| O11 | Ocean licensing / registration (why NATIVE is BLOCKED) | https://eclat-digital.com/register/ ; https://docs.eclat-digital.com/ocean2025-docs/licensing/index.html | doc | H |
| LA | Vangorp 2015 order: glare → retinal image → local adaptation | research-cache/local-adaptation-2015/paper.txt l.12, 305–313 | paper | H |
| L24/L38 | Spencer 1995 photopic Eq. 5 mix pinned in Blender Fog Glow; baseline order and Fog Glow OFF | docs/research/source-ledger.md L24, L38, R10, R14 ; docs/research/human-night-vision-landscape.md l.325, 462, 579, 611 | ledger | H |
