#!/usr/bin/env bash
# Kirk & O'Brien 2011 low-light tone mapping, via Y. J. Lee's GIMP plug-in (2012). Fetches the plug-in source from
# the authors' paper page into d1/kirk2011/.cache (gitignored: GPL-3 per COPYING/headers, not redistributed here),
# verifies sha256, and builds, UNMODIFIED:
#   - FredoToneMap/tone_mapping (Paris & Durand 2006 bilateral tone mapping, bundled; its own Makefile, only the
#     library path variables are overridden on the make command line)
#   - d1/kirk2011/driver.cpp + the plug-in's core files hdrToLMSR.cc purkinje.cc lms2display.cc tonemapping.cc
#     reduceRange.cc exrIO.cc, against OpenCV 4 / OpenEXR 3 with header shims in d1/kirk2011/shim (no arithmetic).
#   d1/kirk2011/setup.sh
set -euo pipefail
export PATH=/root/.nix-profile/bin:$PATH
cd "$(dirname "$0")"
C=.cache; mkdir -p "$C/tmp" "$C/build"
Z=$C/LOWLIGHT_LINUX.zip
SHA=203e613b5b8f9312632959c91ae60aca168701829be0c9a0e43b7e336624a89e
URL=https://jamesobrien.com/papers/Kirk-PBT-2011-08/GimpPlugin/Welcome_files/LOWLIGHT_LINUX.zip
[ -s "$Z" ] || curl -sSL --max-filesize 50000000 -o "$Z" "$URL"
echo "$SHA  $Z" | sha256sum -c -
rm -rf "$C/src"; mkdir -p "$C/src"; unzip -q "$Z" -x '__MACOSX/*' -d "$C/src"
S=$C/src/LOWLIGHT_LINUX
# the zip ships stale 2012 build products; remove them so everything below is built here
# exrIO.cc: the UNUSED ReadTxt() (C++98 `bool ok = stream >> x`) does not compile as C++11+, which OpenEXR 3
# requires; a build copy drops just that function. WriteExrRGB() (used by tonemapping.cc) is untouched.
sed '/^void ReadTxt(/,/^}/d' "$S/src/exrIO.cc" > "$C/build/exrIO_noReadTxt.cc"
rm -f "$S/FredoToneMap/tone_mapping" "$S"/FredoToneMap/*.o "$S"/FredoToneMap/fft_3D/*.o

PC=""
for a in openexr.dev imath fftw.dev opencv libpng.dev zlib.dev; do
  o=$(nix build --no-link --print-out-paths "nixpkgs#$a" | tail -1); PC="$PC:$o/lib/pkgconfig"
done
export PKG_CONFIG_PATH="${PC#:}"
nix shell nixpkgs#gcc nixpkgs#gnumake nixpkgs#pkg-config -c bash -euo pipefail -c '
S='"$S"'
EXR_CF=$(pkg-config --cflags OpenEXR); EXR_LIBS=$(pkg-config --libs OpenEXR)
FFTW_CF=$(pkg-config --cflags fftw3); FFTW_L=$(pkg-config --libs fftw3)
# 1. Durand/Paris tone_mapping (bundled), with its own Makefiles; only the library variables are overridden.
make -s -C "$S/FredoToneMap" CC="g++ -std=gnu++11 -w" LINK=g++ \
  EXR_INCDIR="$EXR_CF" EXR_LIBS="$EXR_LIBS" FFTW_INCDIR="-I./fft_3D/ $FFTW_CF" FFTW_LIBS="$FFTW_L"
# 2. the plug-in core + our driver (-g -O2 = CXXFLAGS of the plug-in src/Makefile)
OCV_CF=$(pkg-config --cflags opencv4); OCV_L=$(pkg-config --libs opencv4)
PNG_CF=$(pkg-config --cflags libpng)
g++ -std=gnu++14 -g -O2 -w -o .cache/build/kirk_driver \
  -Ishim -I"$S/src" -iquote "$S/src" $OCV_CF $EXR_CF $PNG_CF \
  driver.cpp "$S/src/hdrToLMSR.cc" "$S/src/purkinje.cc" "$S/src/lms2display.cc" \
  "$S/src/tonemapping.cc" "$S/src/reduceRange.cc" .cache/build/exrIO_noReadTxt.cc \
  $OCV_L $EXR_LIBS -Wl,-rpath,$(pkg-config --variable=libdir opencv4)
'
echo "built: $C/build/kirk_driver, $S/FredoToneMap/tone_mapping"
sha256sum "$Z"
