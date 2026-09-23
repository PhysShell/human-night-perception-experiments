#!/usr/bin/env bash
# Python (numpy, scipy, matplotlib, OpenImageIO) from the repo's pinned nixpkgs, without editing flake.nix.
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
PY=$(nix build --no-link --print-out-paths --impure --expr 'let f = builtins.getFlake (toString /home/user/human-night-perception-experiments); pkgs = import f.inputs.nixpkgs { system = "x86_64-linux"; }; in pkgs.python3.withPackages (p: [ p.numpy p.scipy p.matplotlib p.openimageio ])' 2>/dev/null)
exec nice -n 10 "$PY/bin/python3" "$@"
