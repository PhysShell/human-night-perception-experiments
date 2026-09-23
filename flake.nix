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
      pyEnv = pkgs.python3.withPackages (ps: [
        ps.numpy
        ps.scipy          # for colour-science (pure-Python, installed with uv --no-deps)
        ps.typing-extensions
        ps.openimageio
        # PyOpenColorIO: builtin ACES 2.0 / gamut-compression transforms (M1.1)
        (ps.toPythonModule (pkgs.opencolorio.override { pythonBindings = true; }))
      ]);
      # Regression tests for the version-specific adapters we rely on (M1.1).
      m1Test = name: inputs: script: pkgs.runCommand name { nativeBuildInputs = inputs; } ''
        export HOME=$TMPDIR
        cp -r ${./m1} m1 && chmod -R u+w m1 && patchShebangs m1
        ${script} | tee $out
      '';
    in {
      packages.${system} = {
        inherit radiance pfstools;
        default = pkgs.symlinkJoin { name = "hnp-tools"; paths = [ radiance pfstools ]; };
      };

      checks.${system} = {
        # our reading of pcond: -x table semantics (incl. the linear-mode 179/Ldmax quirk)
        # and pcond_colorimetric.sh == pcond on every unclipped photopic pixel
        pcond-mapping = m1Test "pcond-mapping-test" [ radiance pyEnv pkgs.openimageio ]
          "python3 m1/test_pcond_mapping.py";
        # Blender 5.2.2 Fog Glow at Size = ((180-FOV)/170)^3 must reproduce Spencer'95 Eq. 5
        fog-glow-psf = m1Test "fog-glow-psf-test" [ pkgs.blender pyEnv ]
          "bash m1/test_fog_glow.sh $TMPDIR/fg";
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
          pyEnv
        ];
        # Radiance runtime library path (cal files used by pcond/pvalue helpers)
        shellHook = ''
          export RAYPATH=.:${radiance}/lib
        '';
      };
    };
}
