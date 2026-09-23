#!/usr/bin/env bash
# NATIVE, non-invasive extraction of the author demo's floating-point PSF frames.
# 1) runs the unmodified glare_demo (same build + runtime workaround as run_glare_demo_native.sh) under
#    `apitrace trace` in PSF view (the demo's own 'c' key: convolution off), for SECS wall seconds;
# 2) `apitrace dump` -> text: per simulate() step the hippus pupil uniform (glUniform1f "pupil" = (D/10mm)^2)
#    and the call number just before the tone-mapping pass (framebuffer 1 = RGB32F PSF sum, not yet
#    divided/gamma-encoded);
# 3) `glretrace -D <call>` for NSEL evenly spaced frames -> JSON with the float framebuffer (PFM inside).
# Usage: trace_glare_demo_psf.sh <outdir> [secs=90] [nsel=24]
set -euo pipefail
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
REPO=/home/user/human-night-perception-experiments
BIN=$REPO/research-cache/temporal-glare-2009/build/glare_demo
SRC=$REPO/research-cache/temporal-glare-2009/glare_demo/glare
OUT=${1:?outdir}; SECS=${2:-90}; NSEL=${3:-24}
mkdir -p "$OUT/dumps"
cd "$REPO"
MESA=$(nix build --inputs-from . --no-link --print-out-paths nixpkgs#mesa | sed -n 1p)
cat > "$OUT/inner.sh" <<INNER
cd "$SRC"
GLIBC_TUNABLES=glibc.malloc.tcache_count=0:glibc.malloc.perturb=1 nice -n 10 apitrace trace -o "$OUT/psf.trace" "$BIN" candle.png overlay.png > "$OUT/stdout.txt" 2>&1 &
sleep 10
W=\$(xdotool search --name "Glare demo" | head -1)
xdotool key --window \$W c
sleep $SECS
pkill -x glare_demo; sleep 2
INNER
nix shell --inputs-from . nixpkgs#xvfb-run nixpkgs#xdotool nixpkgs#apitrace -c bash -c "
export __GLX_VENDOR_LIBRARY_NAME=mesa GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1
export LIBGL_DRIVERS_PATH=$MESA/lib/dri LD_LIBRARY_PATH=$MESA/lib
xvfb-run -a -s '-screen 0 512x512x24 +extension GLX' bash $OUT/inner.sh
apitrace dump --color=never $OUT/psf.trace > $OUT/psf.dump
# per step: pupil uniform value; per frame: the glDisable(GL_BLEND) that ends the spectral PSF sum into fbo 1 (before the tone pass, program 6)
awk '/glUniform1f\(location = 1, v0 = / && prev ~ /name = \"pupil\"/ {gsub(/.*v0 = |\)/,\"\"); print \"P\", \$0} {prev=\$0}
     /glDisable\(cap = GL_BLEND\)/ {lastblend=\$1}
     /glUseProgram\(program = 6\)/ {print \"T\", lastblend}' $OUT/psf.dump > $OUT/events.txt
python3 - <<PY
ev=[l.split() for l in open('$OUT/events.txt')]
# frames rendered in PSF mode: tone pass happens after each step; attach the latest pupil value
rows=[];p=None
for k,v in ev:
    if k=='P': p=float(v)
    else: rows.append((int(v), p))
open('$OUT/frames.csv','w').write('frame,call_before_tone,pupil_uniform,pupil_diameter_mm\n'+''.join('%d,%d,%s,%s\n'%(i,c,('' if p is None else repr(p)),('' if p is None else '%.6f'%(10*p**0.5))) for i,(c,p) in enumerate(rows)))
print(len(rows),'frames')
PY
"
echo "events written"
