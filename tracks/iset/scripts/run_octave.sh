#!/usr/bin/env bash
# Run one ISET script under GNU Octave 11 (nixpkgs pinned by the repo's flake) with the
# packages ISETCam's ieInit asks for. Usage: run_octave.sh <script.m> [logfile]
# Needs research-cache/iset/octave-env built by build_octave_env.sh.
set -u
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
C=$REPO/research-cache/iset
S=$(readlink -f "$1")
LOG=$(readlink -f "${2:-/dev/stdout}")
cd "$(dirname "$S")"
export PATH=$C/gnuplot/bin:$PATH GNUTERM=dumb
ISET_CACHE=$C ISET_OUT=${ISET_OUT:-$REPO/results/native/iset} timeout 1500 nice -n 10 \
 "$C/octave-env/bin/octave" --no-gui --no-window-system -q --eval "
warning('off','all'); graphics_toolkit('gnuplot'); set(0,'defaultfigurevisible','off');
addpath(genpath('$C/isetcam')); addpath(genpath('$C/isetbio')); addpath(genpath('$C/isetvalidate'));
addpath('$REPO/tracks/iset/scripts/octave_shim','-begin');
pkg load general image io optiminterp signal statistics; warning('off','all');
t0=time; try, run('$S'); printf('\nRESULT PASS %s (%.1fs)\n','$(basename $S)',time-t0);
catch err, printf('\nRESULT FAIL %s: %s\n','$(basename $S)',err.message);
 for s=1:min(numel(err.stack),8), printf('  at %s:%d (%s)\n',err.stack(s).name,err.stack(s).line,err.stack(s).file); end; end" > "$LOG" 2>&1
grep -E "^RESULT|^  at" "$LOG" | head -12
