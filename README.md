# human-night-perception-experiments

Goal: a nighttime rural scene (East Kazakhstan–inspired) that looks like **human night
perception**, not a camera render, assembled from **existing** software.

- Research round 1: [`docs/research/human-night-vision-landscape.md`](docs/research/human-night-vision-landscape.md)
  and [`docs/research/source-ledger.md`](docs/research/source-ledger.md)
- M0 (existing operators on calibrated HDR): [`m0/`](m0/README.md)

Environment (Nix flakes; x86_64-linux):

    nix develop          # radiance (pcond), pfstools, oiiotool, imagemagick, ffmpeg, blender 5.2, python
    nix build .#radiance .#pfstools

`radiance` and `pfstools` are built from `nix/*.nix` because nixpkgs removed both in 2026.
