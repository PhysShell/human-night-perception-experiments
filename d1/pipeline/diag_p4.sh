#!/usr/bin/env bash
# DIAGNOSTIC for the P-4 failure (not a gate, not a candidate): axis A with pcond -s only (no -c) on S4/S5, and
# Spearman(physical Y, axis-A output Y) for -s -c (frozen) vs -s, same 20k subsample convention (seed 0).
#   nix develop -c d1/pipeline/diag_p4.sh      (after run_axis_a.sh)
set -euo pipefail
cd "$(dirname "$0")/../.."; D=d1/pipeline/.cache/diag; mkdir -p $D
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
for s in S4 S5; do
  T=$(mktemp -d -p $D); IN=$(realpath d0/work/inputs/$s.exr)
  hf=$(python3 -c "import json;m=json.load(open('d0/work/inputs/manifest.json'))['scenes']['$s'];print(m['size'][0]/m['scene_px_per_deg'])")
  (cd $T; read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
   VF=$(awk -v h=$hf -v W=$W -v H=$H 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
   oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc 0.00558659 -o raw.hdr
   getinfo -a "VIEW= -vtv -vh $hf -vv $VF" "PRIMARIES= $REC709" < raw.hdr > in.hdr; ra_xyze in.hdr > x.hdr
   pcond -s -p $REC709 x.hdr > s.hdr; oiiotool s.hdr -o ../${s}_s_only.exr); rm -rf $T
done
tracks/temporal-glare-2009/py.sh - <<'PY'
import numpy as np, OpenImageIO as oiio
from scipy.stats import spearmanr
M = np.array([0.2126729, 0.7151522, 0.0721750]); rng = np.random.default_rng(0)
for s in ("S4", "S5"):
    Y = (oiio.ImageBuf(f"d0/work/inputs/{s}.exr").get_pixels(oiio.FLOAT)[..., :3] @ M).ravel()
    for tag, p in (("-s -c (frozen A)", f"d1/pipeline/.cache/A/{s}.exr"), ("-s only (DIAGNOSTIC)", f"d1/pipeline/.cache/diag/{s}_s_only.exr")):
        Yo = (oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3] @ M).ravel(); idx = rng.choice(len(Y), 20000, replace=False)
        print(s, tag, "spearman(phys Y, A output Y) =", round(spearmanr(Y[idx], Yo[idx]).statistic, 4))
PY
