#!/usr/bin/env bash
# Build GNU Octave + the Octave-Forge packages named in ISETCam utility/ieInit.m, from the
# repo-pinned nixpkgs, without editing flake.nix. Output link: research-cache/iset/octave-env
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
nix build --impure --out-link "$REPO/research-cache/iset/octave-env" --expr \
 'let p = (builtins.getFlake "path:'"$REPO"'").inputs.nixpkgs.legacyPackages.x86_64-linux;
  in p.octave.withPackages (ps: with ps; [general image io optiminterp signal statistics])'
nix build --inputs-from "$REPO" nixpkgs#gnuplot --out-link "$REPO/research-cache/iset/gnuplot"
