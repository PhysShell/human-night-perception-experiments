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
      # ColorVideoVDP (Mantiuk et al. 2024; gfxdisp/ColorVideoVDP, MIT): spatio-temporal colour
      # video difference predictor, in JOD. Not in nixpkgs: the PyPI wheel on nixpkgs deps.
      # CPU torch is enough for short clips. M2.5 diagnostic, not a gate.
      cvvdp = pkgs.python3Packages.buildPythonPackage rec {
        pname = "cvvdp";
        version = "0.5.7";
        format = "wheel";
        src = pkgs.fetchurl {
          url = "https://files.pythonhosted.org/packages/e6/92/39734ff9b5d00792abf1e4f6719112c25389c5f5736074fb2f05ff992db7/cvvdp-0.5.7-py3-none-any.whl";
          sha256 = "5e0f0d0a83896da27dc1d0fe68dd9e6e8f89cbf872114546468c15ca39727583";
        };
        dependencies = with pkgs.python3Packages; [
          numpy scipy ffmpeg-python torch torchvision imageio matplotlib huggingface-hub einops
        ];
        # "ffmpeg" on PyPI is an unrelated stub (the binary comes from nixpkgs); PyEXR is only
        # used for .exr input, which we do not feed it (display-referred PNG/video only).
        pythonRemoveDeps = [ "ffmpeg" "PyEXR" ];
        makeWrapperArgs = [ "--prefix PATH : ${pkgs.ffmpeg}/bin" ];
        doCheck = false;
      };
      videoEnv = pkgs.python3.withPackages (ps: [ cvvdp ps.numpy ps.openimageio ]);
      # Regression tests for the version-specific adapters we rely on (M1.1).
      m1Test = name: inputs: script: pkgs.runCommand name { nativeBuildInputs = inputs; } ''
        export HOME=$TMPDIR
        cp -r ${./m1} m1 && chmod -R u+w m1 && patchShebangs m1
        ${script} | tee $out
      '';
      # T2/M2.5: tests that need the scene (m1), the atmospheres (m2) and the baselines (t2, m25)
      t2Test = name: inputs: script: pkgs.runCommand name { nativeBuildInputs = inputs; } ''
        export HOME=$TMPDIR
        for d in m1 m2 t2 m25; do cp -r ${./.}/$d $d; done
        chmod -R u+w m1 m2 t2 m25 && patchShebangs m1 m2 t2 m25
        ${script} | tee $out
      '';
      t2Inputs = [ radiance pyEnv pkgs.openimageio pkgs.blender ];
    in {
      packages.${system} = {
        inherit radiance pfstools cvvdp;
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
        # M2.5: two-pass clip render (haze + lamps) == the one-pass M2 render
        m25-decomposition = t2Test "m25-decomposition-test" t2Inputs
          "python3 m25/test_decomposition.py $TMPDIR/dec";
        # M2.5: canonical 4-frame walking clip: hard invariants + per-frame regression vs m25/golden
        m25-golden-clip = t2Test "m25-golden-clip-test" (t2Inputs ++ [ pkgs.ffmpeg ])
          "m25/golden_clip.sh check $TMPDIR/gc";
        # Blender 5.2.2 Fog Glow at Size = ((180-FOV)/170)^3 must reproduce Spencer'95 Eq. 5
        fog-glow-psf = m1Test "fog-glow-psf-test" [ pkgs.blender pyEnv ]
          "bash m1/test_fog_glow.sh $TMPDIR/fg";
      };

      # M2.5 video diagnostics: nix develop .#video (cvvdp + ffmpeg; torch CPU)
      devShells.${system} = {
      video = pkgs.mkShell {
        packages = [ videoEnv pkgs.ffmpeg pkgs.openimageio ];
      };

      default = pkgs.mkShell {
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
    };
}
