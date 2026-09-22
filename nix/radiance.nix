# Radiance (LBNL), headless CLI build. nixpkgs dropped its `radiance`
# attribute ("broken for a long time"); upstream master builds fine with CMake.
# We need: pcond (Ward Larson et al. 1997 human-visibility operator),
# pvalue / getinfo / pfilt / phisto / ra_tiff for format glue.
{ lib, stdenv, src, cmake, libtiff, zlib, tcsh, libGL, libGLU, libX11 }:

let
  # Radiance calls libtiff's LogLuv helpers (uv_encode/uv_decode), which the
  # shared libtiff does not export. Upstream's BUILD_LIBTIFF downloads a static
  # libtiff at configure time; we build the same thing from nixpkgs' source.
  libtiffStatic = stdenv.mkDerivation {
    pname = "libtiff-static-for-radiance";
    inherit (libtiff) version src;
    nativeBuildInputs = [ cmake ];
    cmakeFlags = [
      "-DBUILD_SHARED_LIBS=OFF" "-Djpeg=OFF" "-Dzlib=OFF" "-Dwebp=OFF" "-Dlzma=OFF"
      "-Dzstd=OFF" "-Djbig=OFF" "-Dlerc=OFF" "-Dlibdeflate=OFF"
      "-Dtiff-tools=OFF" "-Dtiff-tests=OFF" "-Dtiff-docs=OFF" "-Dtiff-contrib=OFF"
    ];
  };
in

stdenv.mkDerivation {
  pname = "radiance";
  version = "6.0-unstable-2026-08-19";

  # `src` = GitHub mirror of the official radiance-online.org CVS tree,
  # pinned as the `radiance-src` flake input.
  inherit src;

  nativeBuildInputs = [ cmake ];
  # upstream CMake requires OpenGL headers even for BUILD_HEADLESS
  buildInputs = [ zlib tcsh libGL libGLU libX11 ];

  cmakeFlags = [
    "-DBUILD_HEADLESS=ON"
    "-DBUILD_LIBTIFF=OFF"
    "-DTIFF_LIBRARY=${libtiffStatic}/lib/libtiff.a"
    "-DTIFF_INCLUDE_DIR=${libtiffStatic}/include"
    "-DBUILD_QT=OFF"
    "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"
  ];

  # K&R-style prototypes: GCC >= 15 defaults to C23, where `f()` means `f(void)`.
  env.NIX_CFLAGS_COMPILE = "-std=gnu17 -Wno-error=incompatible-pointer-types";

  meta = {
    description = "Validated lighting simulation suite (used here for pcond -h)";
    homepage = "https://www.radiance-online.org/";
    license = lib.licenses.bsd3; # Radiance License 1.0 (BSD-style, LBNL)
    platforms = lib.platforms.linux;
  };
}
