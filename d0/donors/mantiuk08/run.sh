#!/usr/bin/env bash
# D0 donor B (pfstmo_mantiuk08) + D2 control (pfstmo_reinhard02), pfstools 2.2.0 from the repo flake.
# Reproduces every output from the frozen inputs d0/work/inputs (make them with d0/make_inputs.py first).
#   d0/donors/mantiuk08/run.sh            full run (all S2 frames written: ~350 MB per clip, ~7 clips)
#   D0_WRITE_S2=none d0/donors/mantiuk08/run.sh      stills + tone curves only
#   D0_WRITE_S2=mantiuk08:video_whiteauto:SDR100 d0/donors/mantiuk08/run.sh   (what the D0 round kept)
# Outputs: d0/work/out/{mantiuk08,reinhard02}/<config>/..., runs.json; d0/results/curves/mantiuk08/...;
#          d0/results/stills/mantiuk08/native_memorial_*.png; transient files in d0/work/mantiuk08_tmp (removed).
set -euo pipefail
cd "$(dirname "$0")/../../.."
export PATH=/root/.nix-profile/bin:$PATH
nix develop -c python3 d0/donors/mantiuk08/run_pfstmo.py native
nix develop -c python3 d0/donors/mantiuk08/run_pfstmo.py mantiuk08
nix develop -c python3 d0/donors/mantiuk08/run_pfstmo.py unfiltered
nix develop -c python3 d0/donors/mantiuk08/run_pfstmo.py reinhard02
nix develop -c python3 d0/donors/mantiuk08/curve_smoothness.py
rm -rf d0/work/mantiuk08_tmp
