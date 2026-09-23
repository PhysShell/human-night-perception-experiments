#!/usr/bin/env bash
# Download + unpack the official HDR-VDP 3.0.7 release (unmodified) into research-cache.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
C="$REPO/research-cache/hdrvdp3"; mkdir -p "$C"; cd "$C"
[ -f hdrvdp-3.0.7.zip ] || curl -sSL -o hdrvdp-3.0.7.zip "https://sourceforge.net/projects/hdrvdp/files/hdrvdp/3.0.7/hdrvdp-3.0.7.zip/download"
echo "baa5c25cca2e38176345a2a5423793459fbf571282396640c5e4ac85bf8381b3  hdrvdp-3.0.7.zip" | sha256sum -c -
[ -d src/hdrvdp-3.0.7 ] || unzip -q hdrvdp-3.0.7.zip -d src
