#!/usr/bin/env bash
# Filament scotopicAdaptation() (Apache-2.0, google/filament) built headless, VERBATIM:
# sparse-clones the pinned commit, extracts the function text from ColorGrading.cpp by its first/last lines (no
# edit), and compiles it with Filament's own header-only math library + d1/filament/driver.cpp.
#   d1/filament/setup.sh      -> d1/filament/.cache/scotopic (binary)
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p .cache; cd .cache
REV=ef1a133d6777299ad971a0f9612adf4aad281f46
SHA_CG=dd047e8084ba71fdd57fed361a5f817451bbd7020f9404dcca4855ec226764c3
if [ ! -d fil ]; then
  git clone -q --filter=blob:none --no-checkout https://github.com/google/filament.git fil
fi
git -C fil fetch -q --depth 1 origin $REV 2>/dev/null || true
git -C fil sparse-checkout set --no-cone /libs/math/include/ /filament/src/details/ColorGrading.cpp /tools/rgb-to-lmsr/
git -C fil checkout -q $REV
echo "$SHA_CG  fil/filament/src/details/ColorGrading.cpp" | sha256sum -c -
awk '/^static float3 scotopicAdaptation\(float3 v, float nightAdaptation\) noexcept \{/{p=1} p{print} p&&/^}$/{exit}' \
    fil/filament/src/details/ColorGrading.cpp > scotopicAdaptation.inc
grep -q 'return (LMS_to_RGB \* qHat) / logExposure;' scotopicAdaptation.inc
export PATH=/root/.nix-profile/bin:$PATH
nix shell nixpkgs#gcc -c g++ -std=c++20 -O2 -ffp-contract=off -I fil/libs/math/include -I . ../driver.cpp -o scotopic
echo "built .cache/scotopic from filament $REV"
