#!/usr/bin/env bash
# D0 donor A: the frozen V0 display path, UNCHANGED (m1/pcond_colorimetric.sh LC -> PBR Neutral on out-of-gamut
# pixels -> sRGB), i.e. the M2.6 frame() stack. Inputs are d0/work/inputs (absolute cd/m^2), hence SCALE = 1/179
# (the frozen stack used SCALE 1 on Cycles units, where luminance = 179 Y: the same numbers reach pcond).
# HFOV = image width / scene px/deg (pcond's acuity and veiling-glare model use the SCENE angles).
#   native_default : pcond defaults (Ldmax 100 cd/m^2, 100:1): the historical baseline, shown on SDR100
#   target_<LUM>   : DOCUMENTED_TARGET_CONFIG: pcond's own display flags -u peak -d peak/black for SDR200 and
#                    BRIGHT500; the frozen sRGB/PBR code values are re-encoded to the scenario's gamma 2.2
# Code values: 16-bit PNG per d0/README.md output contract.  nix develop -c d0/donors/pcond/run.sh
set -euo pipefail
I=d0/work/inputs; O=d0/work/out/pcond; mkdir -p $O d0/work/pcond_tmp
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
export CFG
one() {   # IN HFOV OUTPNG LUM [pcond flags...]
  local in=$1 hfov=$2 out=$3 lum=$4; shift 4; [ -s "$out" ] && [ -s "${out%.png}.expo" ] && return 0
  local t; t=$(mktemp -d -p d0/work/pcond_tmp)
  m1/pcond_colorimetric.sh "$in" "$hfov" LC "$t/lc.hdr" 0.00558659 "$@" 2>/dev/null
  oiiotool "$t/lc.hdr" -o "$t/lc.exr"
  oiiotool "$t/lc.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
  oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint16 -o "$t/std.png"
  oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint16 -o "$t/pbr.png"
  oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint16 -o "$t/srgb.png"
  if [ "$lum" = SDR100 ]; then cp "$t/srgb.png" "$out"
  else oiiotool "$t/srgb.png" --tocolorspace linear --powc 0.4545454545 -d uint16 -o "$out"; fi   # sRGB -> linear -> ^(1/2.2)
  getinfo < "$t/lc.hdr" | sed -nE 's/.*EXPOSURE= *([0-9.eE+-]+).*/\1/p' | head -1 > "${out%.png}.expo"
  rm -rf "$t"; }
export -f one
hfov() { python3 -c "import json;m=json.load(open('$I/manifest.json'))['scenes']['$1'];print(m['size'][0]/m['scene_px_per_deg'])"; }
jobs=()
for s in S0 S1 S3_bar S3_nobar S4 S5; do
  sc=${s%%_*}; h=$(hfov $sc)
  jobs+=("$I/$s.exr $h $O/native_default/${s}__PHONE_SDR100_DARK.png SDR100")
  jobs+=("$I/$s.exr $h $O/target_SDR200/${s}__PHONE_SDR200_DARK.png SDR200 -u 200 -d 1000")
  jobs+=("$I/$s.exr $h $O/target_BRIGHT500/${s}__PHONE_BRIGHT500_DARK.png BRIGHT500 -u 500 -d 100000")
done
h=$(hfov S2)
for f in $(seq -f %04g 1 48); do
  jobs+=("$I/S2/frame_$f.exr $h $O/native_default/S2__PHONE_SDR100_DARK/frame_$f.png SDR100")
  jobs+=("$I/S2/frame_$f.exr $h $O/target_BRIGHT500/S2__PHONE_BRIGHT500_DARK/frame_$f.png BRIGHT500 -u 500 -d 100000")
done
mkdir -p $O/native_default/S2__PHONE_SDR100_DARK $O/target_SDR200 $O/target_BRIGHT500/S2__PHONE_BRIGHT500_DARK
printf '%s\n' "${jobs[@]}" | xargs -P 2 -L 1 bash -c 'one "$@"' _
python3 - <<'PY'
import json
json.dump({"donor": "pcond (Radiance pcond -s -c via m1/pcond_colorimetric.sh LC, frozen V0 display path)",
           "configs": {"native_default": {"label": "NATIVE_DEFAULT", "pcond": "defaults: Ldmax 100 cd/m^2, 100:1", "scenario": "PHONE_SDR100_DARK"},
                       "target_SDR200": {"label": "DOCUMENTED_TARGET_CONFIG", "pcond": "-u 200 -d 1000", "encoding": "gamma 2.2"},
                       "target_BRIGHT500": {"label": "DOCUMENTED_TARGET_CONFIG", "pcond": "-u 500 -d 100000", "encoding": "gamma 2.2"}},
           "scale": "1/179 (inputs in cd/m^2)", "hfov": "image width / scene px/deg", "not_supported": "HDR1000: pcond has no PQ/HDR output"},
          open("d0/work/out/pcond/runs.json", "w"), indent=1)
PY
rm -rf d0/work/pcond_tmp; echo pcond done
