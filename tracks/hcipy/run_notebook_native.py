#!/usr/bin/env python3
"""NATIVE wrapper: execute the official HCIPy tutorial notebook
doc/getting_started/3_atmosphere_adaptive_optics.ipynb (tag v0.7.1) cell by cell, unchanged,
except: IPython magics are dropped and every plt.show() saves the current figure to PNG.
Also dumps the reference PNG outputs stored in the notebook by the HCIPy authors for comparison.
  usage: run_notebook_native.py NOTEBOOK OUTDIR
"""
import base64, json, os, sys, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

nb_path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
nb = json.load(open(nb_path))
counter = {'n': 0}
cur = {'cell': -1}

def _show(*a, **k):
    counter['n'] += 1
    fn = os.path.join(outdir, f'NATIVE_nb3_cell{cur["cell"]:02d}_fig{counter["n"]:02d}.png')
    plt.savefig(fn, dpi=80); plt.close('all'); print('saved', fn)
plt.show = _show

# API-drift patch (the ONLY source change, logged): the v0.7.1 notebook still calls
# make_focal_grid(8, 16, wavelength=wavelength), a keyword that hcipy 0.7.1's make_focal_grid
# (field/util.py) no longer accepts. Equivalent current call: spatial_resolution = lambda / D.
PATCHES = [("make_focal_grid(8, 16, wavelength=wavelength)",
            "make_focal_grid(8, 16, spatial_resolution=wavelength / D_tel)")]
g = {}
log = []
for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code':
        continue
    # reference outputs stored by the authors
    for j, o in enumerate(c.get('outputs', [])):
        png = o.get('data', {}).get('image/png')
        if png:
            with open(os.path.join(outdir, f'REFERENCE_nb3_cell{i:02d}_out{j}.png'), 'wb') as f:
                f.write(base64.b64decode(png))
    src = ''.join(c['source'])
    src = '\n'.join(l for l in src.splitlines() if not l.strip().startswith('%'))
    if not src.strip():
        continue
    cur['cell'] = i
    applied = []
    for old, new in PATCHES:
        if old in src:
            src = src.replace(old, new); applied.append(new)
    t0 = time.time()
    try:
        exec(compile(src, f'cell{i}', 'exec'), g)
        status = 'ok'
    except Exception as e:  # record, do not hide
        status = f'ERROR {type(e).__name__}: {e}'
    log.append({'cell': i, 'status': status, 'patched': applied, 'seconds': round(time.time() - t0, 2)})
    print(i, status)
json.dump(log, open(os.path.join(outdir, 'NATIVE_nb3_cells.json'), 'w'), indent=1)
