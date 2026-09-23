#!/usr/bin/env bash
# Build VSS (wgpu branch) desktop app from source with cargo/rustc from the repo-pinned nixpkgs.
# Only extra system inputs: cmake + X11 headers (needed by openxr-sys's static OpenXR loader build script).
set -euo pipefail
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
R=/home/user/human-night-perception-experiments; cd $R
X=$(nix build --no-link --print-out-paths --inputs-from . nixpkgs#libx11.dev nixpkgs#libx11.out nixpkgs#xorgproto)
XD=$(echo "$X" | grep 'libx11.*-dev'); XL=$(echo "$X" | grep -v dev | grep libx11); XP=$(echo "$X" | grep xorgproto)
export CMAKE_INCLUDE_PATH=$XD/include:$XP/include CMAKE_LIBRARY_PATH=$XL/lib CPATH=$XD/include:$XP/include LIBRARY_PATH=$XL/lib
export CARGO_HOME=$R/research-cache/vss/cargo-home SSL_CERT_FILE=/root/.ccr/ca-bundle.crt CARGO_HTTP_CAINFO=/root/.ccr/ca-bundle.crt
export CARGO_INCREMENTAL=0
nice -n 10 nix shell --inputs-from . nixpkgs#cargo nixpkgs#rustc nixpkgs#gcc nixpkgs#pkg-config nixpkgs#cmake -c \
  sh -c "cd research-cache/vss/visual-system-simulator && cargo build -p vss-desktop --release -j 2"
