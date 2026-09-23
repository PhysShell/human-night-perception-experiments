#!/usr/bin/env bash
# Replays the NATIVE trace (trace_glare_demo_psf.sh) with glretrace and dumps the RGB32F PSF framebuffer
# (fbo 1, before the demo's tone pass) at NSEL evenly spaced frames. Output: <trace_dir>/dumps/fNNNN.json
# Usage: dump_psf_floats.sh <trace_dir> [nsel=48]
set -euo pipefail
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
REPO=/home/user/human-night-perception-experiments
D=${1:?trace dir}; NSEL=${2:-48}
cd "$REPO"
MESA=$(nix build --inputs-from . --no-link --print-out-paths nixpkgs#mesa | sed -n 1p)
python3 - "$D" "$NSEL" > "$D/dump_list.txt" <<'PY'
import csv,sys
r=list(csv.DictReader(open(sys.argv[1]+'/frames.csv'))); n=int(sys.argv[2])
idx=[round(i*(len(r)-1)/(n-1)) for i in range(n)]
for i in idx: print(r[i]['frame'], r[i]['call_before_tone'])
PY
nix shell --inputs-from . nixpkgs#xvfb-run nixpkgs#apitrace -c bash -c "
export __GLX_VENDOR_LIBRARY_NAME=mesa GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1
export LIBGL_DRIVERS_PATH=$MESA/lib/dri LD_LIBRARY_PATH=$MESA/lib
while read fr call; do
  f=\$(printf '%s/dumps/f%04d.json' $D \$fr)
  [ -s \$f ] && continue
  xvfb-run -a -s '-screen 0 512x512x24 +extension GLX' nice -n 10 glretrace -b -D \$call $D/psf.trace > \$f.tmp 2>/dev/null && mv \$f.tmp \$f
  echo \"dumped frame \$fr call \$call \$(date +%T)\"
done < $D/dump_list.txt
"
