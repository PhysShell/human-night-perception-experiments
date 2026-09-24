#!/usr/bin/env bash
# HDR-VDP 3.0.7 wrapper (tracks/hdrvdp3). A METRIC wrapper: it predicts visibility of differences
# between two images on a named display; it never renders anything and says nothing about realism.
#
# usage: run_hdrvdp.sh TEST REF TARGET OUTDIR [--mtf hdrvdp|cie|none] [--age YEARS]
#                      [--display clip|none] [--surround none|mean|<cd/m2>] [--tasks "side-by-side flicker"]
#   TEST, REF : calibrated linear images in ABSOLUTE cd/m^2 = the luminance the display is asked to emit.
#               *.exr (linear Rec.709/D65 RGB, Y = 0.2126R+0.7152G+0.0722B cd/m^2) -> 'rgb-bt.709'
#               *.pfm (1 channel, cd/m^2)                                      -> 'luminance'
#   TARGET    : PHONE | DESKTOP  -> geometry + photometry read ONLY from stimuli/display_targets.json
#               (px_per_deg_centre, peak_cd_m2, contrast, E_ambient_lux). Pixels are shown 1:1.
#   --display clip (default): physical display limits, per channel: L_disp = min(max(L,0),peak) + peak/contrast
#               (+ E_ambient*0.005/pi reflected, = 0 for both targets). NOT a tone mapper: no rescaling.
#   --display none: pass values unchanged (an idealised unlimited display; reported as such).
#   --ppd N     : override the grid density (px/deg) of TARGET, e.g. for a finer world-reference grid
#   --mtf/--age : HDR-VDP options 'mtf' (default 'hdrvdp') and 'age' (only passed if given; donor default 24).
# Outputs in OUTDIR: hdrvdp_<task>.json, hdrvdp_<task>_pmap.png, run.json
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
[ $# -ge 4 ] || { sed -n 2,20p "$0"; exit 2; }
TEST="$(realpath "$1")"; REF="$(realpath "$2")"; TARGET="$3"; OUT="$4"; shift 4
MTF=hdrvdp; AGE=""; DISP=clip; SURR=none; TASKS="side-by-side flicker"
while [ $# -gt 0 ]; do case "$1" in
  --mtf) MTF="$2"; shift 2;; --age) AGE="$2"; shift 2;; --display) DISP="$2"; shift 2;;
  --surround) SURR="$2"; shift 2;; --tasks) TASKS="$2"; shift 2;; --ppd) export HV_PPD="$2"; shift 2;; *) echo "unknown option $1"; exit 2;; esac; done
mkdir -p "$OUT"; OUT="$(realpath "$OUT")"
[ -d "$REPO/research-cache/hdrvdp3/src/hdrvdp-3.0.7" ] || "$REPO/tracks/hdrvdp3/fetch_donor.sh"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
( cd "$REPO" && nix develop -c python3 tracks/hdrvdp3/img2raw.py "$TEST" "$TMP/test.raw" && \
                nix develop -c python3 tracks/hdrvdp3/img2raw.py "$REF" "$TMP/ref.raw" ) 2>/dev/null
cd "$REPO"
HV_TEST="$TEST" HV_REF="$REF" HV_TEST_RAW="$TMP/test.raw" HV_REF_RAW="$TMP/ref.raw" HV_TARGET="$TARGET" \
HV_OUT="$OUT" HV_MTF="$MTF" HV_AGE="$AGE" HV_DISP="$DISP" HV_SURR="$SURR" HV_TASKS="$TASKS" \
  tracks/hdrvdp3/octave.sh tracks/hdrvdp3/run_hdrvdp.m 2>&1 | grep -vE "^warning: (function .*shadows|called from)|^    [a-z_]+ at line" || true
test -f "$OUT/run.json"
