#!/usr/bin/env bash
# Contact sheets per common stimulus: RAW (log10 luminance false-grey, 4 decades), BASELINE, and
# every donor's COMMON/ADAPTED output that exists, each labelled with its file and label.
# Diagnostic only; the donor outputs are shown as their tracks produced them.
#   nix develop -c results/reports/make_contact_sheets.sh
set -euo pipefail
R=results/reports; T=$(mktemp -d)
rawlog() { # stimulus -> crop PNG: log10(Y) from Ymax-4 decades to Ymax
  python3 - "$1" "$2" "$3" <<'PY'
import sys, numpy as np, OpenImageIO as oiio
src, out, crop = sys.argv[1], sys.argv[2], sys.argv[3]
Y = oiio.ImageBuf(src).get_pixels(oiio.FLOAT)[..., 0]
if crop != "full":
    x, y, w, h = map(int, crop.split(","))
    Y = Y[y:y + h, x:x + w]
L = np.log10(np.maximum(Y, 1e-9)); hi = L.max()
g = np.clip((L - (hi - 4)) / 4, 0, 1)
b = oiio.ImageBuf(oiio.ImageSpec(g.shape[1], g.shape[0], 1, oiio.UINT8)); b.set_pixels(b.roi, (g * 255).astype(np.uint8)[..., None]); b.write(out)
PY
}
cropimg() { oiiotool "$1" --cut "$2" -o "$3"; }
lab() { magick "$1" -resize x300 -background "#1a1a1a" -fill white -pointsize 12 -gravity north -splice 0x18 -annotate +0+2 "$2" "$3"; }
# S0 and S1: 4 x 2 deg around the source (source at 512,256; 32 px/deg)
for S in S0 S1; do
  rawlog stimuli/pack/$S/${S}_Y.pfm $T/raw.png 448,224,128,64
  lab $T/raw.png "$S RAW log10 Y, 4 decades (4x2 deg)" $T/a.png
  cropimg results/baseline/$S/${S}_BASELINE.png 128x64+448+224 $T/b0.png; lab $T/b0.png "BASELINE pcond LC + PBR (same crop)" $T/b.png
  set -- $T/a.png $T/b.png
  for f in results/common/temporal-glare-2009/ADAPTED_${S}_noglare_phone.png results/common/temporal-glare-2009/ADAPTED_${S}_montage_phone.png results/common/iset/COMMON_${S}_iset_wvfhuman.png; do
    [ -f "$f" ] || continue; n=$(basename "$f"); lab "$f" "${f#results/common/}" "$T/$n"; set -- "$@" "$T/$n"
  done
  magick "$@" -background "#1a1a1a" +append -resize '3000x>' "$R/${S}_contact_sheet.png"; echo "$R/${S}_contact_sheet.png"
done
# S7: baseline vs VSS (identity) and HDR-VDP maps
rawlog stimuli/pack/S7/S7_Y.pfm $T/raw7.png full; lab $T/raw7.png "S7 RAW log10 Y, 4 decades" $T/a7.png
lab results/baseline/S7/S7_BASELINE.png "BASELINE" $T/b7.png
set -- $T/a7.png $T/b7.png
for f in results/common/vss/ADAPTED_S7_BASELINE.vss.srgbfix.png results/common/hdrvdp3/COMMON_S7v2_vs_S7_PHONE/hdrvdp_flicker_pmap.png; do
  [ -f "$f" ] || continue; n=$(basename "$(dirname "$f")")_$(basename "$f"); lab "$f" "${f#results/common/}" "$T/$n"; set -- "$@" "$T/$n"
done
magick "$@" -background "#1a1a1a" -append -resize 'x2400>' "$R/S7_contact_sheet.png"; echo "$R/S7_contact_sheet.png"
rm -rf "$T"
