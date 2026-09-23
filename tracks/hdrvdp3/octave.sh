#!/usr/bin/env bash
# Launch the pinned Octave 11.3 (+image, statistics, signal) built from the repo's pinned nixpkgs
# (flake.lock nixpkgs rev 6774f7bc2537), without editing flake.nix.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
OCT="$REPO/research-cache/hdrvdp3/nix/octave"
if [ ! -x "$OCT/bin/octave-cli" ]; then
  mkdir -p "$REPO/research-cache/hdrvdp3/nix"
  nix build --impure -o "$OCT" --expr 'let p = import (builtins.fetchTarball { url = "https://releases.nixos.org/nixos/unstable/nixos-26.11pre1077996.6774f7bc2537/nixexprs.tar.xz"; sha256 = "sha256-OJe62m8gZx4xEAQnMcqH1u31/uu4Xf0q2ykAEHZfgrg="; }) {}; in p.octave.withPackages (ps: [ ps.image ps.statistics ps.signal ])'
fi
exec nice -n 10 "$OCT/bin/octave-cli" --no-gui --no-init-file "$@"
