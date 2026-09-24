"""d0 driver for iCAM06 V1.3 (original RIT MCSL MATLAB code, run in GNU Octave with shims in ./shim).
EXR -> raw float32 (no pixel change) -> Octave iCAM06_HDR -> native uint8 sRGB code values
-> 16-bit PNG by code16 = code8 * 257 (ADAPTED container change only, exact 8-bit values preserved)."""
import json, os, subprocess, hashlib, time
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
WORK = os.path.join(REPO, 'd0/work/donors/icam06')   # author code, made by d0/donors/icam06/setup.sh
D0 = os.path.join(REPO, 'd0'); TMP = os.path.join(D0, 'work/optional_tmp'); os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(D0, 'work/out/icam06')
man = json.load(open(os.path.join(D0, 'work/inputs/manifest.json')))
scenes = {'S0': 'S0.exr', 'S1': 'S1.exr', 'S3_bar': 'S3_bar.exr', 'S3_nobar': 'S3_nobar.exr', 'S4': 'S4.exr', 'S5': 'S5.exr'}
CONFIGS = {
  'native_default': dict(label='NATIVE_DEFAULT', args='', params=dict(max_L=20000, p=0.7, gamma_value=1),
     note='iCAM06_HDR(img): code defaults; rescales image so max Y = 20000 cd/m^2 (absolute calibration discarded)'),
  'target_abs_dark_readme': dict(label='DOCUMENTED_TARGET_CONFIG', args='0 0.7 1.2', params=dict(max_L=0, p=0.7, gamma_value=1.2),
     note='max_L=0: Readme "original images stored as physical luminance data" (input used as absolute cd/m^2); gamma_value=1.2: Readme "dark -> 1.2"; p=0.7 default'),
  'target_abs_dark_paper': dict(label='DOCUMENTED_TARGET_CONFIG', args='0 0.7 1.5', params=dict(max_L=0, p=0.7, gamma_value=1.5),
     note='as target_abs_dark_readme but surround exponent from the JVCIR 2007 paper Eq. 27 (c_dark = 1.5), which differs from the code Readme (1.2)'),
}
octave = os.path.join(REPO, 'tracks/hdrvdp3/octave.sh')
ver = subprocess.run([octave, '--eval', 'disp(version)'], capture_output=True, text=True, env=dict(os.environ, REPO=REPO)).stdout.strip()
runs = []
for cfg, c in CONFIGS.items():
    os.makedirs(os.path.join(OUT, cfg), exist_ok=True)
    for sc, fn in scenes.items():
        src = os.path.join(D0, 'work/inputs', fn)
        a = oiio.ImageBuf(src).get_pixels(oiio.FLOAT)[..., :3]
        H, W = a.shape[:2]
        fin, fout = os.path.join(TMP, 'icam_in.f32'), os.path.join(TMP, 'icam_out.u8')
        np.ascontiguousarray(a, dtype=np.float32).tofile(fin)
        env = dict(os.environ, REPO=REPO, ICAM_SRC=os.path.join(WORK, 'src_pristine'), ICAM_SHIM=os.path.join(WORK, 'shim'), ICAM_IN=fin, ICAM_OUT=fout, ICAM_H=str(H), ICAM_W=str(W), ICAM_ARGS=c['args'])
        t = time.time()
        r = subprocess.run([octave, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_scene.m')], capture_output=True, text=True, env=env)
        if r.returncode: raise SystemExit(r.stdout + r.stderr)
        u8 = np.fromfile(fout, dtype=np.uint8).reshape(H, W, 3)
        os.remove(fin); os.remove(fout)
        u16 = u8.astype(np.uint16) * 257
        dst = os.path.join(OUT, cfg, f'{sc}__PHONE_SDR100_DARK.png')
        o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(), u16)
        o.specmod().attribute('oiio:ColorSpace', 'sRGB'); o.write(dst)
        runs.append(dict(scene=sc, input=os.path.relpath(src, REPO), config=cfg, label=c['label'], output=os.path.relpath(dst, REPO),
            command=f"iCAM06_HDR(img{', ' + ', '.join(c['args'].split()) if c['args'] else ''})", parameters=c['params'], note=c['note'],
            code8_min=int(u8.min()), code8_max=int(u8.max()), frac_code0=float((u8.max(-1) == 0).mean()),
            frac_code255=float((u8.min(-1) == 255).mean()), seconds=round(time.time() - t, 1),
            octave_log=[l for l in (r.stdout + r.stderr).splitlines() if l.startswith('out ') or 'rror' in l]))
        print(cfg, sc, runs[-1]['code8_min'], runs[-1]['code8_max'], runs[-1]['seconds'], flush=True)
zsha = hashlib.sha256(open(os.path.join(WORK, 'iCAM06_V1.3.zip'), 'rb').read()).hexdigest()
json.dump(dict(
  donor='iCAM06 (Kuang, Johnson, Fairchild, JVCIR 18(5) 2007)',
  implementation='iCAM06 V1.3 (Readme last updated 2007-08-06), original MATLAB code by J. Kuang, RIT Munsell Color Science Laboratory',
  source_url='http://www.rit-mcsl.org/StudentResearch/iCAM06_V1.3.zip (linked from https://www.rit.edu/cos/colorscience/re_iCAM06.php, Wayback 20190320142121)',
  source_zip_sha256=zsha, runtime=f'GNU Octave {ver} (pkg image) via tracks/hdrvdp3/octave.sh',
  shims='d0/donors/icam06/shim (ours) + d0/work/donors/icam06/shim (author files, line endings/name only; setup.sh): computer.m (-> PCWIN, selects author sRGB branch), interp1q.m (-> interp1 linear), figure.m/imshow.m (no-op preview), cmatrix.m/changeColorSpace.m (CR->LF line endings only), idl_dist.m (lower-case filename only). No algorithm file edited.',
  scenario='PHONE geometry, SDR100 (sRGB piecewise, Rec.709), DARK ambient. iCAM06 has no display-peak, black, ambient-light or px/deg input; outputs are identical for any geometry/peak with sRGB encoding.',
  output_encoding='ADAPTED: native iCAM06 uint8 sRGB code values (PCWIN branch: 1st/99th percentile clip, sRGB OETF, uint8(x*255), which rounds to nearest) stored as 16-bit PNG code16 = code8*257',
  S2='skipped: still-image model with per-frame percentile normalisation, no temporal adaptation',
  runs=runs), open(os.path.join(OUT, 'runs.json'), 'w'), indent=1)
