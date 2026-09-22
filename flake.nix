{
  description = "Human night-perception experiments: existing HVS/tone-mapping tools, pinned";

  inputs = {
    # Pinned nixos-unstable channel tarball (same content as github:NixOS/nixpkgs/<rev>).
    nixpkgs.url = "https://releases.nixos.org/nixos/unstable/nixos-26.11pre1077996.6774f7bc2537/nixexprs.tar.xz";
    # Radiance: GitHub mirror of the radiance-online.org CVS tree (master = daily CVS import).
    radiance-src = {
      url = "git+https://github.com/LBNL-ETA/Radiance?ref=master&rev=bcffc2b52d99b908adfdc2543e4cddf83268a125&shallow=1";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, radiance-src }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      radiance = pkgs.callPackage ./nix/radiance.nix { src = radiance-src; };
      pfstools = pkgs.callPackage ./nix/pfstools.nix { };
    in {
      packages.${system} = {
        inherit radiance pfstools;
        default = pkgs.symlinkJoin { name = "hnp-tools"; paths = [ radiance pfstools ]; };
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          radiance
          pfstools
          pkgs.openimageio   # oiiotool: EXR <-> HDR/PFM/PNG conversion, stats
          pkgs.imagemagick   # montage for side-by-side sheets
          pkgs.ffmpeg        # M2 sequences
          pkgs.blender       # M1 scene authoring / Cycles CPU
          pkgs.uv            # venv for colour-science / cvvdp (not in nixpkgs)
          (pkgs.python3.withPackages (ps: [ ps.numpy ps.openimageio ]))
        ];
        # Radiance runtime library path (cal files used by pcond/pvalue helpers)
        shellHook = ''
          export RAYPATH=.:${radiance}/lib
        '';
      };
    };
}
