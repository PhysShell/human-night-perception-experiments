#!/usr/bin/env bash
# Minimal repro: pfstmo_mantiuk08 --display-size (ppd / vres+vd) has no effect on the output.
# Synthetic HDR test image (log-luminance gradient + multi-frequency texture, 256x256, no external data),
# rendered with ppd = 5, 30, 73, 150 and with vres/vd forms; control: -e (contrast enhancement) DOES change it.
#   PFSBIN=<pfstools bin dir> docs/upstream/pfstools-mantiuk08-display-size/repro.sh
set -euo pipefail
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
python3 - "$T/in.pfm" <<'PY'
import sys, numpy as np
h = w = 256; y, x = np.mgrid[0:h, 0:w] / 256.0
L = 10 ** (-2 + 5 * x) * (1 + 0.5 * np.sin(2 * np.pi * 4 * y) + 0.3 * np.sin(2 * np.pi * 40 * y) * np.sin(2 * np.pi * 40 * x))
rgb = np.repeat(L[..., None], 3, -1).astype('<f4')
with open(sys.argv[1], 'wb') as f:
    f.write(b'PF\n%d %d\n-1.0\n' % (w, h)); f.write(rgb[::-1].tobytes())
PY
run() { "$PFSBIN/pfsinpfm" "$T/in.pfm" | "$PFSBIN/pfstmo_mantiuk08" -q -d pd=lcd "$@" 2>/dev/null | "$PFSBIN/pfsoutpfm" "$T/o.pfm" 2>/dev/null && sha256sum < "$T/o.pfm" | cut -c1-16; }
echo "binary: $(readlink -f "$PFSBIN/pfstmo_mantiuk08")"
for s in "ppd=5" "ppd=30" "ppd=73" "ppd=150" "vres=480:vd=3:d=0.5" "vres=2160:vd=0.8:d=0.5"; do
  printf '%-26s %s\n' "-s $s" "$(run -s "$s")"
done
printf '%-26s %s\n' "-s ppd=30 -e 2 (control)" "$(run -s ppd=30 -e 2)"
