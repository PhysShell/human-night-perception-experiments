# Donor matrix (round 8)

✅ modelled / available. ◐ partial, approximate, or only in one mode. ✗ not modelled. ? undocumented.
"run" = what actually ran in this container:
- NATIVE: the donor's own example;
- COMMON: our stimulus pack;
- DOC: documents, papers or author videos only.

Evidence is in `tracks/<donor>/README.md`. This matrix is not a ranking.

| donor | verdict | run | normal night | photopic | mesopic | scotopic | spectral | rods | cones | glare / PSF | temporal glare | local adapt. | global adapt. | acuity | gaze | afterimages | display-aware | HDR cd/m² | realtime | video | open source | Linux here | validation | licence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **baseline: Radiance pcond** (frozen) | — | ✅ | ✅ | ✅ | ✅ (`-c`) | ✅ (`-c`) | ✗ | ◐ (tvi) | ◐ | ◐ `-v` veil, 1° grid | ✗ | ✗ | ✅ histogram | ✅ `-a` | ✗ | ✗ | ✅ Ldmax, Lddyn | ✅ | ✗ | frame by frame | ✅ | ✅ | Ward 1997 psychophysics | Radiance licence |
| temporal-glare-2009 | BEHAVIORAL ORACLE | NATIVE (co-author demo, qualitative) + COMMON S0/S1 (ADAPTED) | ◐ | ✅ | ✗ | ✗ | ◐ (3 λ chromatic blur) | ✗ | ✗ | ✅ diffraction PSF | ✅ hippus (demo); particles, lashes (paper only) | ✗ | ◐ pupil only | ✗ | ✗ | ✗ | ◐ gamma | ◐ | ✅ GPU | ✅ | ◐ demo has no licence | ✅ (Mesa, 2 fixes) | user study (brightness) | none stated (paper ©) |
| mpi2005 (Krawczyk) | HISTORICAL REFERENCE | DOC (thesis) | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ◐ Deeley, added | ✗ | ✅ | ✅ temporal | ✅ | ✗ | ✗ | ◐ | ✅ | ✅ GPU | ✅ | ✗ code | ✗ | none | paper © |
| gazehdr-2015 (Jacobs) | BEHAVIORAL ORACLE | NATIVE (measurements of the authors' video) | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ stochastic | ✅ | ✅ | ◐ | ✅ | ✅ | ✅ | ✗ code (NVIDIA patent 9,773,473) | ✗ | user studies | paper © |
| pa-tonemapping-2023 (Tariq) | HISTORICAL REFERENCE | DOC (author video stills) | ✗ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ◐ | ✅ | ✗ | ✗ | ✗ | ✅ peak | ✅ | ✅ | ✅ | ✗ code | ✗ | user study | paper © |
| local-adaptation-2015 (Vangorp) | BLOCKED (code) | DOC (paper) | ◐ photopic fit | ✅ | ✗ | ✗ | ✗ | ✗ | ◐ | ✅ Deeley OTF / CIE 135 GSF, feeds adaptation | ✗ | ✅ ~0.5° pooling | ◐ | ✗ | ◐ (application) | ◐ (application) | ✗ | ✅ | ✗ | ✗ | ◐ (Matlab/Octave, unobtained) | ✗ | 5 psychophysical experiments | unknown |
| hdrvdp3 (metric) | SCIENTIFIC ORACLE | NATIVE (examples) + COMMON | ◐ | ✅ | ◐ | ◐ | ✗ | ◐ | ✅ | ✅ MTF / CIE option, age | ✗ | ✅ | ✅ | ✅ CSF | ✗ | ✗ | ✅ explicit | ✅ | ✗ | flicker task | ✅ | ✅ Octave | calibrated datasets | see donor |
| ISETBio / ISETCam | SCIENTIFIC ORACLE | NATIVE partial (Octave: human WVF optics, rod/cone calibration validations) + COMMON S0 | ◐ | ✅ | ◐ | ◐ absorptions only | ✅ | ◐ no rod mosaic or current | ✅ mosaic + photocurrent (MATLAB only) | ✅ Thibos aberrations + LCA; no straylight in oiCompute | ✗ | ✗ | ✅ cone adaptation | ✅ via optics and mosaic | ✗ | ✗ | ✗ | ✅ spectral radiance | ✗ | ◐ | ✅ | ◐ Octave; cMosaic and ISET3d need MATLAB / Docker | validation scripts | MIT code; Thibos data research-only |
| VisSimFramework | CODE DONOR (PSF) | DOC (code audit, published images); build BLOCKED | ✗ | ✅ | ✗ | ✗ | ◐ 3 λ | ✗ | ✗ | ✅ wavefront PSF: pupil, focus, field angle | ✗ | ✅ TM | ✅ TM | ◐ | ✗ | ✗ | ◐ | ✅ fp16 | ✅ GPU | ✅ | ✅ BSD-2 | ✗ Windows / VS / GL 4.3 / MATLAB | papers | BSD-2 |
| VSS Stuttgart | NOT RELEVANT (impairments) | NATIVE + COMMON (identity on the normal eye) | ✗ | ◐ | ✗ | ✗ | ✗ | ◐ density map | ◐ | ◐ impairment lens only | ✗ | ✗ | ✗ | ✗ | ✅ | ✗ | ✗ | ✗ 8-bit | ✅ | ✅ | ✅ Apache-2.0 | ✅ lavapipe | none for normal vision | Apache-2.0 |
| OpenVisSim | HISTORICAL REFERENCE | DOC (audit) | ✗ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ LDR bloom | ✗ | ✗ | ✗ | ✗ | ✅ | ✗ | ✗ | ✗ | ✅ | ✅ | ✅ GPLv3 (paper: "non-commercial") | ✗ Unity | npj 2020 study (impairments) | GPLv3 vs paper conflict |
| Speos (commercial) | BEHAVIORAL ORACLE | DOC (public help, blog) | ✅ | ✅ | ✅ | ✅ | ✅ (spectral renderer) | ? | ? | ✅ Vos 1984 recommended | ✗ | ✅ Dynamic 2019 | ✅ time adaptation | ? | ✗ | ✗ | ✅ | ✅ | ✗ | ◐ | ✗ | ✗ | ? | commercial |
| Ocean (commercial) | SCIENTIFIC ORACLE (documentation) | DOC | ✅ | ✅ | ✅ | ✅ | ✅ | ? | ? | ✅ Spencer-based, P/M/S PSF, age, dispersion, 10× threshold | ✗ | ◐ | ✅ gains | ? | ✗ | ✗ | ◐ Drago | ✅ | ✗ | ◐ | ✗ | ✗ | ? | commercial |
| HCIPy (atmosphere) | SCIENTIFIC ORACLE | NATIVE (tests + tutorial) + analysis for our path | n/a | n/a | n/a | n/a | ✅ λ | n/a | n/a | ✅ atmospheric PSF, seeing | ✅ scintillation, tip-tilt | n/a | n/a | n/a | n/a | n/a | ✗ | ✗ | ✗ | ✅ time series | ✅ MIT | ✅ | textbook theory agreement | MIT |
| ColorVideoVDP / FovVideoVDP (metrics) | BEHAVIORAL ORACLE | NATIVE (authors' numbers reproduced) + ADAPTED S6 | ◐ (≥ 0.005 cd/m²) | ✅ | ◐ | ✗ | ✗ | ✗ | ✅ | ✗ | measures it | ✗ | ✅ | ✅ CSF | Fov: ✅ | ✗ | ✅ explicit | ✅ | ✗ | ✅ | ✅ MIT / CC BY-NC | ✅ | psychophysical datasets | MIT / CC BY-NC 4.0 |
| Mitsuba 3 (spectral) | SCIENTIFIC ORACLE (radiometry) | NATIVE (Cornell box, 3 variants) + units verified | n/a | photometry via V(λ) | ◐ (tools) | V′(λ) | ✅ | n/a | n/a | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ with units | ✗ | ✗ | ✅ BSD-3-style | ✅ | renderer tests | BSD-3-style + enhancements clause |
| datasets (Fairchild HDRPS) | data | calibration check PASS (Golden Gate 2: 1.005) | real | | | | ✗ | | | camera glare baked in | ✗ | | | | | | | ✅ multiplier | | ✗ | research-only | ✅ fetch | CS-100 spot readings | © Fairchild, non-commercial |
