#!/usr/bin/env python3
"""NATIVE check: cvvdp examples/ex_simple_image.py documents 'Noise 8.955 JOD, Blur 8.514 JOD'. In 0.5.6
(commit 49d15f9) the authors changed examples/ex_utils.imnoise from Gaussian np.random.randn*std to
seeded uniform rng.uniform*std without updating that comment. This script re-runs the example with the
authors' PREVIOUS imnoise (git show 49d15f9^:examples/ex_utils.py, restored verbatim at runtime from git)
to test whether the stale 8.955 reference is reproduced. Run from research-cache/vdp-metrics/cvvdp-src."""
import subprocess, sys, types, numpy as np
sys.path[:0] = ['.', 'examples']
old = subprocess.run(['git', 'show', '49d15f9^:examples/ex_utils.py'], capture_output=True, text=True, check=True).stdout
mod = types.ModuleType('examples.ex_utils'); exec(compile(old, 'ex_utils_pre_0.5.6.py', 'exec'), mod.__dict__)
import examples
sys.modules['examples.ex_utils'] = mod; examples.ex_utils = mod
import runpy
for seed in (0, 1, 2):
    np.random.seed(seed)
    print('seed', seed)
    runpy.run_path('examples/ex_simple_image.py', run_name='__main__')
