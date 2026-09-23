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
      # T2: tests that need the scene (m1), the atmospheres (m2) and the golden baseline (t2)
      t2Test = name: inputs: script: pkgs.runCommand name { nativeBuildInputs = inputs; } ''
        export HOME=$TMPDIR
        for d in m1 m2 t2; do cp -r ${./.}/$d $d; done
        chmod -R u+w m1 m2 t2 && patchShebangs m1 m2 t2
        ${script} | tee $out
      '';
      t2Inputs = [ radiance pyEnv pkgs.openimageio pkgs.blender ];
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
        # LC composition adds no temporal seams to pcond (colour ramp through the clip point)
        pcond-continuity = m1Test "pcond-continuity-test" [ radiance pyEnv pkgs.openimageio pkgs.blender ]
          "python3 m1/test_continuity_sweep.py synthetic $TMPDIR/sweep LC";
        # T2: Beer-Lambert per channel vs distance (1-15 km), clear + mild, and density order
        t2-extinction = t2Test "t2-extinction-test" [ pkgs.blender ]
          "blender -b --factory-startup --python-exit-code 1 --python t2/extinction_sweep.py 2>&1 | grep -E 'km|PASS|FAIL' && test \${PIPESTATUS[0]} -eq 0";
        # T2: vacuum -> clear -> mild on the real scene: energy, contrast, ribbon width, finiteness
        t2-haze = t2Test "t2-haze-metamorphic-test" t2Inputs "t2/run_haze_metamorphic.sh $TMPDIR/haze";
        # T2: golden renders vacuum/clear/mild (scene cd/m^2 + displayed image) vs t2/golden
        t2-golden = t2Test "t2-golden-test" t2Inputs "t2/golden.sh check $TMPDIR/golden";
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
          pkgs.flip          # NVlabs FLIP 1.2: LDR/HDR perceptual error maps (T2 report, not a gate)
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
