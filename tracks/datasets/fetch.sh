#!/usr/bin/env bash
# Idempotent fetch of calibrated night HDR data into research-cache/datasets/ (gitignored).
# Nothing here is redistributed by this repo: every file is fetched from its origin and verified
# by SHA-256.  Re-running skips files whose checksum already matches; a mismatch is re-downloaded
# once and then reported as FAIL.  BLOCKED sources are probed and their HTTP status printed.
#
# Usage:  tracks/datasets/fetch.sh            # fetch everything allowed + reachable
#         tracks/datasets/fetch.sh --probe    # only probe BLOCKED sources
# Then:   nix develop -c python3 tracks/datasets/make_s8.py   # regenerate the S8 candidate
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DST="$ROOT/research-cache/datasets"
mkdir -p "$DST"
fail=0

# rel_path | url | sha256   (licence: see tracks/datasets/manifest.json)
FILES=$(cat <<'EOF'
fairchild/EXRs/GoldenGate(2).exr|http://markfairchild.org/HDRPS/EXRs/GoldenGate(2).exr|ab5b18efccc6a8f04535cd6bae3b9853ff0c72ff4c71ebe2304706171e0b0175
fairchild/EXRs/Zentrum.exr|http://markfairchild.org/HDRPS/EXRs/Zentrum.exr|9e0c5945a4aac1ed46d16083a5fdf757d8b130813c0e57b7070de9aefb0ed1a9
fairchild/EXRs/McKeesPub.exr|http://markfairchild.org/HDRPS/EXRs/McKeesPub.exr|db22f70c506575ed2fbca9e9cbdb783eecdb609540d3dbd554d1df1246caa46d
fairchild/EXRs/WaffleHouse.exr|http://markfairchild.org/HDRPS/EXRs/WaffleHouse.exr|af209c830f379d009dad49a04967eba489f912799c3fa97478c62e48e48d6f53
fairchild/EXRs/OCanadaLights.exr|http://markfairchild.org/HDRPS/EXRs/OCanadaLights.exr|286f40d91d4038ef0e5c2974f9a0b4b374e83afa852195644a4fa4f9218565a9
fairchild/Data/GoldenGateData.xls|http://markfairchild.org/HDRPS/Data/GoldenGateData.xls|5dfbf40474b9d0852bf9e00f5f411b65a98f8f58f749d81f216d93b89acdd0a0
fairchild/Data/OCanadaLightsData.xls|http://markfairchild.org/HDRPS/Data/OCanadaLightsData.xls|802bfe005b749007be032666bb29e955ecb3c300cd0e5444660cb27505f0c1af
fairchild/docs/CIC15HDRSurvey.pdf|http://markfairchild.org/HDRPS/CIC15HDRSurvey.pdf|b3764c2e9640abd220d53176f2bf1be725748d44717e885a344182b142d75082
fairchild/docs/D2xCharacterization.pdf|http://markfairchild.org/HDRPS/D2xCharacterization.pdf|d39352a70bc8971bba6a2f4ff3494827288cdd146a4bcfef5e6bf8bd433bf7d5
fairchild/docs/D2xSimpleSpectralModel.pdf|http://markfairchild.org/HDRPS/D2xSimpleSpectralModel.pdf|00249632a8463e223e9e483b4618396be38b750afbb189186b6ea41211e74659
ward_anyhere/AtriumNight_oA9D.hdr|http://www.anyhere.com/gward/hdrenc/pages/img/AtriumNight_oA9D.hdr|0b3016351750cf992982e88ba80ad8b97bdf904e8e76ca4e48921abbd068b4ca
EOF
)

# Sources that were unreachable from the build container (server-side 403) - probe only.
BLOCKED=$(cat <<'EOF'
https://resources.mpi-inf.mpg.de/hdr/gallery.html
https://resources.mpi-inf.mpg.de/hdr/img_hdr/AtriumNight.exr
https://resources.mpi-inf.mpg.de/hdr/img_hdr/AtriumMorning.exr
https://resources.mpi-inf.mpg.de/hdr/video/
EOF
)

check() { [ -f "$1" ] && [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ]; }

if [ "${1:-}" != "--probe" ]; then
  while IFS='|' read -r rel url sum; do
    [ -z "$rel" ] && continue
    f="$DST/$rel"; mkdir -p "$(dirname "$f")"
    if check "$f" "$sum"; then echo "OK      $rel"; continue; fi
    curl -sSfL --retry 3 -o "$f.part" "$url" && mv "$f.part" "$f"
    if check "$f" "$sum"; then echo "FETCHED $rel"; else echo "FAIL    $rel ($url)"; fail=1; fi
  done <<< "$FILES"
fi

while read -r url; do
  [ -z "$url" ] && continue
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$url" || true)
  echo "PROBE   $code $url"
done <<< "$BLOCKED"
exit $fail
