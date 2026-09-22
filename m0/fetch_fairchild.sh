#!/usr/bin/env bash
# Fetch one luminance-calibrated night/dusk HDR from Mark Fairchild's HDR Photographic
# Survey and convert it to cd/m^2. Licence: research / non-commercial publication only,
# acknowledgement required (http://markfairchild.org/HDR.html) -> not committed to git.
# Per-scene multiplier (EXR Y -> cd/m^2) from the survey's scene page: McKeesPub x6.25.
set -euo pipefail
mkdir -p m0/data
curl -fsSL -o m0/data/McKeesPub.exr http://markfairchild.org/HDRPS/EXRs/McKeesPub.exr
# resize first, clamp after: Lanczos ringing creates negatives, which NaN pfstmo_pattanaik00
oiiotool m0/data/McKeesPub.exr --ch R,G,B --resize 1920x0 --clamp:min=0 --mulc 6.25 \
  -o m0/data/fairchild_McKeesPub_cdm2.exr
