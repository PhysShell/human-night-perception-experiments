# Donor G: Tariq et al. 2023, input contract

**Classification: REFERENCE_ONLY (no public implementation found; not reproduced)**

Reference: Taimoor Tariq, Nathan Matsuda, Eric Penner, Jerry Jia, Douglas Lanman, Ajit Ninan, Alexandre Chapiro, "Perceptually Adaptive Real-Time Tone Mapping", SIGGRAPH Asia 2023 Conference Papers, doi:10.1145/3610548.3618222.
Affiliations: Meta (all authors); Tariq also at the University of Lugano (USI). The author list was checked on the paper's first page.

## Search (one pass, as instructed)

| What | URL | Finding |
|---|---|---|
| Web search "Tariq Perceptually Adaptive Real-Time Tone Mapping SIGGRAPH Asia 2023 code" | none | no code repository or supplementary implementation turned up |
| ACM DL entry | https://dl.acm.org/doi/fullHtml/10.1145/3610548.3618222 | listed in the results; no code artifact was indicated |
| Author PDF (Chapiro's site) | https://achapiro.github.io/Tar23/Tar23.pdf | opened. It has no code, GitHub or supplementary-implementation link, and its ACM reference line has a placeholder DOI. |
| Project page guess | https://achapiro.github.io/Tar23/ | HTTP 404 |

## What the method expects (from the paper, for the record only)

- **Input.** A linear HDR frame in physical **nits** (cd/m^2). The pipeline works on luminance and restores colour with colour-to-luminance ratios (Schlick).
- **Processing.**
  - A Gaussian/Laplacian pyramid gives band contrasts. Local adaptation is taken 2 pyramid levels up (about 0.5 deg, following Vangorp et al. 2015), so it needs the **pixels per degree** of the display (the HMD prototype was 20 ppd).
  - Band contrasts are scaled by thresholds from the **Barten (2003) CSF** and matched in supra-threshold contrast (Eq. 5, min of test and reference contrast).
  - The result drives the parameters of a **Reinhard (2002) Photographic TMO** curve: global, or local with region-size options.
- **Output.** For a target display **peak luminance**; the study used 50, 100, 500 and 1000 nits against a 5000-nit reference.
- **Runtime.** GPU fragment shaders (a parameter shader and a tone-mapping shader), under 1 ms/frame on Quest 2. The evaluation used HDR-VR content only.

## Why not run

- No genuine implementation is publicly available.
- Reproducing it from the paper would be a reimplementation, which is out of scope.
