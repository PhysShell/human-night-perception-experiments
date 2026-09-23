#!/usr/bin/env bash
# Build J. R. Frisvad's (co-author) glare_demo UNMODIFIED on Linux (NATIVE, author code).
# Source: https://people.compute.dtu.dk/jerf/code/glare_demo.zip (downloaded to research-cache).
# PORTABILITY PATCH (documented): the author's GLSL 1.10 shaders in Convolution.cpp name two samplers
# `input` and `output`, which are reserved words in GLSL and rejected by Mesa (NVIDIA's 2009 compiler
# accepted them). We copy the source to research-cache/.../src_portable and rename ONLY those two
# identifiers (-> in_tex / out_tex) in the shader strings and in the matching glGetUniformLocation calls.
# No numerical constant, model parameter or algorithm line is touched. The bundled Windows glew/glut libs are not used;
# nixpkgs freeglut + glew + libglvnd are linked instead (mesa llvmpipe at run time).
set -euo pipefail
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
REPO=/home/user/human-night-perception-experiments
ORIG=$REPO/research-cache/temporal-glare-2009/glare_demo
SRC=$REPO/research-cache/temporal-glare-2009/src_portable
rm -rf "$SRC"; cp -r "$ORIG" "$SRC"
sed -i -E '68,93s/\b(input)\b/in_tex/g; 68,93s/\b(output)\b/out_tex/g; 153,157s/"input"/"in_tex"/; 153,157s/"output"/"out_tex"/' "$SRC/glare/Convolution.cpp"
diff -u "$ORIG/glare/Convolution.cpp" "$SRC/glare/Convolution.cpp" | grep '^[-+][^-+]' | wc -l | sed 's/^/changed lines (+-): /' || true
OUT=$REPO/research-cache/temporal-glare-2009/build
mkdir -p "$OUT"
cd "$REPO"
P=""
for pkg in freeglut.dev freeglut glew.dev glew.out libGL.dev libGL libGLU.dev libGLU libx11.dev libx11 xorgproto; do
  P="$P:$(nix build --inputs-from . --no-link --print-out-paths nixpkgs#$pkg | sed -n 1p)"
done
PKG_CONFIG_PATH=$(echo "$P" | tr ':' '\n' | grep -v '^$' | awk '{print $0"/lib/pkgconfig:"$0"/share/pkgconfig"}' | paste -sd:)
export PKG_CONFIG_PATH
nix shell --inputs-from . nixpkgs#gcc nixpkgs#pkg-config -c bash -c "
  set -e
  FLAGS=\"\$(pkg-config --cflags glew glut gl glu x11)\"
  LIBS=\"\$(pkg-config --libs glew glut gl glu x11)\"
  cd $SRC
  for f in SOIL/image_DXT.c SOIL/image_helper.c SOIL/SOIL.c SOIL/stb_image_aug.c; do
    gcc -O2 -w \$FLAGS -c \$f -o $OUT/\$(basename \$f .c).o
  done
  cd glare
  for f in glare.cpp FFT.cpp Convolution.cpp simplex.cpp load_shaders.cpp; do
    g++ -O2 -w -fpermissive \$FLAGS -c \$f -o $OUT/\$(basename \$f .cpp).o
  done
  g++ -O2 -w \$FLAGS -I. -c $REPO/tracks/temporal-glare-2009/harness/fft_probe.cpp -o $OUT/probe_main.o.x
  RP=\$(pkg-config --variable=libdir glew):\$(pkg-config --variable=libdir glut):\$(pkg-config --variable=libdir gl)
  g++ -o $OUT/fft_probe $OUT/probe_main.o.x $OUT/FFT.o $OUT/load_shaders.o $OUT/SOIL.o $OUT/image_DXT.o $OUT/image_helper.o $OUT/stb_image_aug.o \$LIBS -Wl,-rpath,\$RP -lm
  g++ -o $OUT/glare_demo $OUT/*.o \$LIBS -Wl,-rpath,\$(pkg-config --variable=libdir glew):\$(pkg-config --variable=libdir glut):\$(pkg-config --variable=libdir gl) -lm
"
ls -la "$OUT/glare_demo"
