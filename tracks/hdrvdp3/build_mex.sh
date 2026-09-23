#!/usr/bin/env bash
# Compile the donor's own utils/gaussian_columns.c (unmodified) as an Octave MEX into research-cache
# (the release only ships MATLAB .mexa64/.mexw64/.mexglx binaries; needed by the 'civdm' task).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; C="$REPO/research-cache/hdrvdp3"
mkdir -p "$C/build"
"$C/nix/octave/bin/mkoctfile" --mex -o "$C/build/gaussian_columns.mex" "$C/src/hdrvdp-3.0.7/utils/gaussian_columns.c"
