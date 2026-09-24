#!/usr/bin/env bash
# iCAM06 V1.3 (Kuang, Johnson & Fairchild, RIT MCSL): fetch the authors' MATLAB code into d0/work/donors/icam06
# (gitignored: the zip states no licence, so it is not redistributed) and assemble the Octave shim path.
#   d0/donors/icam06/setup.sh
# Shims: ours (computer.m -> 'PCWIN' = the authors' sRGB branch; interp1q -> interp1; figure/imshow no-ops) are in
# d0/donors/icam06/shim; three AUTHOR files are only converted (old-Mac CR line endings -> LF; IDL_DIST.M name
# lower-cased) because Octave cannot parse or find them otherwise. No algorithm line is edited.
set -euo pipefail
cd "$(dirname "$0")/../../.."
W=d0/work/donors/icam06; mkdir -p "$W/shim"
Z=$W/iCAM06_V1.3.zip SHA=b26a0231bda9e74f0578ccbb43cbe22c0e588f3a442c1f3f7f622d71e6e5d4c3
[ -s "$Z" ] || curl -sSL --max-filesize 20000000 -o "$Z" http://www.rit-mcsl.org/StudentResearch/iCAM06_V1.3.zip
echo "$SHA  $Z" | sha256sum -c -
rm -rf "$W/src_pristine" "$W/_unz"; unzip -q "$Z" -d "$W/_unz"; mv "$W/_unz/iCAM06 V1.3" "$W/src_pristine"; rm -rf "$W/_unz"
tr '\r' '\n' < "$W/src_pristine/CMATRIX.M" > "$W/shim/cmatrix.m"
tr '\r' '\n' < "$W/src_pristine/changeColorSpace.m" > "$W/shim/changeColorSpace.m"
tr '\r' '\n' < "$W/src_pristine/IDL_DIST.M" > "$W/shim/idl_dist.m"
cp d0/donors/icam06/shim/*.m "$W/shim/"
echo "iCAM06 ready in $W (src_pristine + shim)"
