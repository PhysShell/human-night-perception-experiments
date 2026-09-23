# Donor bake-off (round 8): rules for every track worker

Repository: /home/user/human-night-perception-experiments (NixOS-style Nix is installed:
`export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt`;
start the daemon if `pgrep nix-daemon` is empty: `nohup nix-daemon >/tmp/nd.log 2>&1 &`).
The repo pins nixpkgs; get tools from it WITHOUT editing flake.nix, e.g.
`nix shell --inputs-from . nixpkgs#octave -c octave ...`, `nix shell --inputs-from . nixpkgs#cargo nixpkgs#rustc ...`,
`nix develop` (radiance, oiiotool, blender, python with numpy/OpenImageIO), `nix develop .#video` (ColorVideoVDP 0.5.7).

FROZEN, never modify: m0/ m1/ m2/ m25/ m26/ t2/ flake.nix flake.lock nix/ docs/ README.md stimuli/.
You may RUN baseline scripts (e.g. m1/pcond_colorimetric.sh) but not change them.
Do NOT git commit, push, or change branches. The coordinator commits.

Write ONLY into your own: tracks/<track>/ (README.md, sources.md, scripts, small notes),
results/native/<track>/, results/common/<track>/ (small outputs: PNG/JPG/MP4/CSV/JSON, keep each
track's committed results < ~30 MB), and research-cache/<track>/ (downloads, clones, builds,
big intermediates; gitignored). Disk is limited (~14 GB free for everyone): keep research-cache
per track under ~2 GB, delete build trees you no longer need.
CPU is 4 cores shared by 7 parallel workers: run heavy jobs with `nice -n 10`, prefer
single-threaded runs, no job longer than ~30 min wall; if something needs hours, document and stop.

Network: outbound HTTPS via a proxy. KNOWN: resources.mpi-inf.mpg.de returns HTTP 403 (server
side) to this container, and web.archive.org connections are reset. GitHub, SourceForge, PyPI,
crates.io, Stanford work. Try your WebFetch / WebSearch tools for pages the container cannot
reach (they may use a different network), and look for mirrors (GitHub, Zenodo, author/lab pages,
cam.ac.uk, gfxdisp). Never route around a proxy policy denial; if a primary artifact is
unreachable, record the exact URL + error and mark it BLOCKED (the user can download it manually).

Method (mandatory):
1. PHASE NATIVE first: reproduce an original example/demo/figure in the donor's intended
   environment. If it cannot reproduce its own reference behaviour, mark FAILED/BLOCKED and do
   not adapt it.
2. PHASE COMMON only after NATIVE passes: feed compatible stimuli from stimuli/pack/<S>/
   (read stimuli/pack/manifest.json and each meta.json: linear Rec.709 EXR, Y = cd/m^2, 32 px/deg,
   plus luminance-only *_Y.pfm). Display/viewing geometry comes ONLY from
   stimuli/display_targets.json (PHONE_TARGET 73 px/deg, DESKTOP_TARGET 48.4 px/deg); no silent
   defaults. Do not force an LDR-only system to eat HDR and call it a failure.
3. No reimplementation of any model (HVS, PSF, glare, adaptation, tone mapper, turbulence,
   spectral renderer). Wrappers, launch scripts, format conversion and report scripts are allowed.
   If only a paper exists, document it; do not implement it.
4. Label every output exactly one of NATIVE / COMMON / ADAPTED / HYBRID (in file names or a
   results index). HYBRID is informational only.
5. Provenance for every factual claim (URL, file, line, page). Never present a paper as code,
   a third-party port as author code, marketing as validation, a metric as a renderer, an
   impairment simulator as a normal-vision model.
6. License discipline: record license, reuse/redistribution/academic-only status. Never copy
   all-rights-reserved code into tracks/.

Each tracks/<track>/README.md must have these sections: IDENTITY, PURPOSE, HVS COMPONENTS
(optics, glare, adaptation, rods/cones, mesopic/scotopic, acuity, temporal state, gaze, display
model, spectrum), NATIVE ENVIRONMENT, NATIVE REPRODUCTION (exact example, exact command, result,
PASS/FAIL/BLOCKED), COMMON STIMULUS, ASSUMPTIONS (cd/m^2? RGB/XYZ/spectral? viewing geometry?
absolute scale? display?), VALIDATION, REUSE, FAILURES / SURPRISES, BRIGHT POINT SOURCE (answer
for this donor: 1 where the optical PSF is applied; 2 before/after adaptation; 3 before/after tone
reproduction; 4 energy preserved?; 5 absolute-luminance aware?; 6 PSF depends on adaptation level
/pupil/age/wavelength/field angle?; 7 how an HDR source is shown on an LDR/HDR display; 8 does the
halo change perceived brightness; 9 temporal PSF variation?; 10 clip before or after convolution?
"not applicable" / "unknown" are valid answers), VERDICT (one of RUNNABLE DONOR, SCIENTIFIC ORACLE,
BEHAVIORAL ORACLE, CODE DONOR, HISTORICAL REFERENCE, BLOCKED, NOT RELEVANT). Also tracks/<track>/
sources.md: a table of sources (id, claim, URL/file, type paper/code/doc/video, confidence).
Do not rank donors globally.

Context: the baseline (frozen) renders a rural night scene in Blender/Cycles with calibrated
cd/m^2, physically tested extinction, and Radiance pcond (Ward Larson 1997) as the night
perception step; M2.6 showed the display must be formed at the target resolution before pcond,
32 px/deg converges, and an unresolved lamp currently shows as a 2x2-pixel clipped white core.
The open question this round serves: how existing human-vision systems represent an unresolved,
very bright point source on a display of limited range and resolution, and what (if anything)
makes distant lights appear to "breathe" (eye optics / temporal glare vs atmosphere vs display).

Final message to the coordinator: a compact summary (<= 40 lines): per donor verdict, NATIVE and
COMMON status, the bright-point answers in one line each, blockers with exact URLs, and the list
of files you created.
