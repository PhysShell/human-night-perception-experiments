# pfstools/pfstmo 2.2.0 (Mantiuk, Krawczyk et al.), rebuilt because nixpkgs
# dropped it (ImageMagick 6 dependency). ImageMagick, Qt, OpenGL, MATLAB and
# Octave front-ends are disabled: we only need the CLI filters.
# OpenEXR is disabled too: 2.2.0 only knows the OpenEXR-2 API (gone from nixpkgs),
# so EXR goes through oiiotool -> PFM/RGBE, which pfsin reads natively.
{ lib, stdenv, fetchurl, cmake, pkg-config, libtiff, netpbm, fftwFloat, gsl, zlib }:

stdenv.mkDerivation rec {
  pname = "pfstools";
  version = "2.2.0";

  src = fetchurl {
    url = "mirror://sourceforge/pfstools/pfstools/${version}/pfstools-${version}.tgz";
    hash = "sha256-m/aESYVmMibCGZjutDwmGsuOSziRuakbcpVUQGKJ18o=";
  };

  nativeBuildInputs = [ cmake pkg-config ];
  buildInputs = [ libtiff netpbm fftwFloat gsl zlib ];

  cmakeFlags = [
    "-DWITH_OpenEXR=OFF"
    "-DWITH_ImageMagick=OFF"
    "-DWITH_QT=OFF"
    "-DWITH_pfsglview=OFF"
    "-DWITH_MATLAB=OFF"
    "-DWITH_Octave=OFF"
    "-DWITH_OpenCV=OFF"
    "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"
  ];

  env.NIX_CFLAGS_COMPILE = "-std=c++14";

  meta = {
    description = "Command-line HDR image/video processing incl. pfstmo tone-mapping operators";
    homepage = "https://pfstools.sourceforge.net/";
    license = with lib.licenses; [ lgpl21Plus gpl2Plus ];
    platforms = lib.platforms.linux;
  };
}
