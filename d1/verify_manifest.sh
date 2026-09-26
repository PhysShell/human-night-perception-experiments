#!/usr/bin/env bash
# Verifies that the D1 baseline is intact.
#  1. every frozen tracked file is byte-identical to the accepted commit (d1/MANIFEST.sha256);
#  2. (if present) the locally generated corpus inputs are byte-identical (d1/MANIFEST_inputs.sha256);
#  3. the pinned Radiance source matches flake.lock (pcond is built from it).
# Any D2 run that claims "passes the D1 corpus" must run this first and report its output.
set -uo pipefail; cd "$(dirname "$0")/.."; rc=0
echo "== frozen files vs D1 accepted commit 0ee0765"; sha256sum -c --quiet d1/MANIFEST.sha256 && echo OK || rc=1
echo "== corpus inputs"; if [ -f d0/work/inputs/manifest.json ]; then sha256sum -c --quiet d1/MANIFEST_inputs.sha256 && echo OK || rc=1; else echo "SKIP (inputs not generated: python3 d0/make_inputs.py, then re-verify)"; fi
echo "== Radiance source (pcond)"; want=$(python3 -c "import json;print(json.load(open('flake.lock'))['nodes']['radiance-src']['locked']['narHash'])")
[ "$want" = "sha256-Cgs+2woqLUMKXMTLv+shf6bOUVfFMaydVNkPb0gJteQ=" ] && echo "OK flake.lock pins bcffc2b ($want)" || { echo "CHANGED: $want"; rc=1; }
exit $rc
