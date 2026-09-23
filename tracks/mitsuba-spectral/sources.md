# Sources: track mitsuba-spectral

Local paths are relative to `research-cache/mitsuba-spectral/` or to the venv site-packages. Clone commits are in `clone_heads.txt`.

| id | claim | URL / file | type | confidence |
|---|---|---|---|---|
| M1 | The PyPI wheel ships scalar_spectral and llvm_ad_spectral but not llvm_spectral | mitsuba3/docs/src/key_topics/variants.rst ("when installing Mitsuba on your system with pip, only a subset"); `mi.variants()` on mitsuba 3.9.1 | doc/test | high |
| M2 | Spectral mode spans 360-830 nm; CIE Y normalisation constant 1/106.7502593994140625 ("unit-valued spectrum integrates to a luminance of 1.0") | mitsuba3/include/mitsuba/core/spectrum.h:123-129 | code | high |
| M3 | Mitsuba is "ordinarily a unitless system"; blackbody gives W m^-2 sr^-1 nm^-1 | mitsuba3/src/spectra/blackbody.cpp:61-64 | code/doc | high |
| M4 | Point emitter `intensity` = power per steradian; area emitter `radiance` = power per area per sr | mitsuba3/src/emitters/point.cpp:21; area.cpp:23 | doc | high |
| M5 | specfilm stores the SRF-weighted radiance per channel; wavelengths are importance-sampled from the sum of the SRFs | mitsuba3/src/films/specfilm.cpp:178-250; docs in that file | code | high |
| M6 | hdrfilm pixel formats are luminance/rgb/xyz(+alpha); spectral samples go through spectrum_to_xyz | mitsuba3/src/films/hdrfilm.cpp:33-36,142-147,221-227 | code | high |
| M7 | Emission spectra: `<rgb>` becomes d65-modulated in spectral mode; `value="λ:v,..."` gives regular/irregular | mitsuba3/docs/src/plugin_reference/section_spectra.rst:76-110 | doc | high |
| M8 | PostProcess (bloom etc.) is only an abstract interface; no concrete bloom plugin ships | mitsuba3/include/mitsuba/render/postprocess.h; `ls mitsuba3/src` | code | high |
| M9 | Official quickstart (cbox.xml, 256 spp) | mitsuba-tutorials/quickstart/mitsuba_quickstart.ipynb; scenes/cbox.xml | code | high |
| M10 | Licence: BSD-3-style with an "Enhancements" clause | mitsuba3/LICENSE | licence | high |
| M11 | luxpy.get_cie_mesopic_adaptation (claims CIE 191:2010) computes Lmes = (m*Lp + (1-m)*SP*683/1699)/(...). It is missing the Lp factor on the scotopic term, so with S/P=1 it returns Lmes≠Lp (0.245 for Lp=0.01) and diverges for S/P=22 | venv/.../luxpy/spectrum/basics/spectral.py:975-981 (luxpy 1.12.5); results/native/mitsuba-spectral/ADAPTED_n5_photometry.json "luxpy_invariant_SP1" | code/test | high |
| M12 | colour-science mesopic function = MOVE/LRC table lookup (Lp steps 0.01, 0.1, 1, 10; "Blue/Red Heavy"), cites Wikipedia rather than CIE 191 | venv/.../colour/colorimetry/lefs.py:45-100; colour/colorimetry/datasets/lefs.py:2838-2864 | code | high |
| M13 | CIE illuminants HP1 (standard HPS) and LED-B1 (phosphor LED) from CIE 15:2018, shipped in colour-science | colour.SDS_ILLUMINANTS['HP1'], ['LED-B1'] | data | high (colour's transcription, not checked against the CIE PDF) |
| M14 | luxpy 1.12.5 fails to import with numpy 2.4 (TypeError in blackbody at import); works with numpy 2.2.6 | test in this track | test | high |
| M15 | Na D lines at 588.995 / 589.592 nm | NIST Atomic Spectra Database (standard values; used only to place the constructed LPS lines) | data | high |
| M16 | CIE 191:2010 Recommended System for Mesopic Photometry | http://cie.co.at/publications/recommended-system-mesopic-photometry-based-visual-performance (cited by luxpy; not read here) | paper (paywalled) | reference only |
| M17 | Licences: luxpy GPLv3; colour-science BSD-3-Clause | dist-info METADATA in the venv | licence | high |
