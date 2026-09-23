#!/usr/bin/env python3
"""L5 metric-plumbing demo (label ADAPTED): visibility of the temporal change in stimulus S6
(unresolved white source moving 1.0 stimulus px = 1.9 arcmin over 2 s) against the static S6 frame 1
repeated, on PHONE_TARGET and DESKTOP_TARGET (stimuli/display_targets.json), with ColorVideoVDP 0.5.7
and FovVideoVDP 1.2.2 (fixation on the source vs 10 deg to the right of it).

It is NOT a perception model of the night scene and a high JOD is NOT physical correctness: the
metrics see a PHOTOPIC SDR display frame that we build with an ad-hoc display mapping (below).

Display formation (ADAPTED, documented, our own choice - no HVS model is implemented here):
  1. read S6_%04d.exr (linear Rec.709, Y in cd/m^2, 32 px/deg)
  2. resample the LINEAR cd/m^2 frames to the target's declared px/deg (73.0 phone, 48.4 desktop;
     bilinear, torch.nn.functional.interpolate, align_corners=False) - M2.6: form the display at the
     target resolution first; the point's luminance integral is checked and reported
  3. PHONE: crop the centred 1920x820 content window; DESKTOP: keep the whole 32x16 deg (1548x774 px)
  4. one fixed exposure for all frames: the brightest pixel of the STATIC reference frame (S6 frame 1)
     (variant 'allframes' for cvvdp: brightest pixel over all moving frames -> white, no clipping)
     maps to display white; relative = clip(exposure * RGB / peak_cd_m2, 0, 1) (frames whose point
     is sharper than frame 1 CLIP - counted and reported)
  5. display encoding: sRGB OETF, as float16 ("float") or quantised to 8 bit ("8bit")
  6. the metric's own display model (tracks/vdp-metrics/*display_models*) turns the code values back
     into cd/m^2 (peak, contrast/black level, 0 lux ambient)
Run each tool in its own process (both packages put a top-level module 'interp' on sys.path and
clash when imported together):
  nix develop .#video -c research-cache/vdp-metrics/venv/bin/python tracks/vdp-metrics/l5_s6_visibility.py cvvdp OUTDIR
  nix develop .#video -c research-cache/vdp-metrics/venv/bin/python tracks/vdp-metrics/l5_s6_visibility.py fvvdp OUTDIR
"""
import json, math, os, sys, time
import numpy as np
import torch
import torch.nn.functional as Fn
import OpenImageIO as oiio

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
tool, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
torch.set_num_threads(2)

targets = json.load(open(os.path.join(REPO, 'stimuli/display_targets.json')))
meta = json.load(open(os.path.join(REPO, 'stimuli/pack/S6/meta.json')))
FPS, PPD_STIM = meta['fps'], meta['px_per_deg']
exr = [f for f in meta['files'] if f.endswith('.exr')]


def read_exr(fn):
    buf = oiio.ImageBuf(os.path.join(REPO, 'stimuli/pack/S6', fn))
    return buf.get_pixels(oiio.FLOAT)[..., :3]


def srgb_oetf(x):
    return torch.where(x <= 0.0031308, 12.92 * x, 1.055 * torch.pow(x.clamp(min=0.0031308), 1 / 2.4) - 0.055)


def form_display(target_key, crop, expo_mode='frame1'):
    t = targets[target_key]
    ppd, peak = float(t['px_per_deg_centre']), float(t['peak_cd_m2'])
    s = ppd / PPD_STIM
    lin = torch.from_numpy(np.stack([read_exr(f) for f in exr])).permute(0, 3, 1, 2)  # F C H W, cd/m^2
    bg = float(np.median(lin[0, 1].numpy()))
    e_in = float((lin[0].sum(0) / 3 - bg).sum()) / PPD_STIM ** 2                      # ~ luminance integral (cd/m^2 deg^2)
    res = Fn.interpolate(lin, scale_factor=s, mode='bilinear', align_corners=False)
    e_out = float((res[0].sum(0) / 3 - bg).sum()) / ppd ** 2
    H, W = res.shape[2:]
    if crop is not None:
        cw, ch = crop
        x0, y0 = (W - cw) // 2, (H - ch) // 2
        res = res[:, :, y0:y0 + ch, x0:x0 + cw]
    else:
        x0 = y0 = 0
    Y = 0.2126 * res[:, 0] + 0.7152 * res[:, 1] + 0.0722 * res[:, 2]
    exposure = peak / float(Y[0].max() if expo_mode == 'frame1' else Y.max())
    rel = (exposure * res / peak)
    clipped_frames = int((rel.amax(dim=(1, 2, 3)) > 1.0 + 1e-5).sum())
    rel = rel.clamp(0, 1)
    V = srgb_oetf(rel)
    # source position on the display = luminance-weighted centroid of frame 1 in a 9x9 window at its peak
    iy, ix = divmod(int(torch.argmax(Y[0])), Y.shape[2])
    win = Y[0, iy - 4:iy + 5, ix - 4:ix + 5]
    gy, gx = torch.meshgrid(torch.arange(iy - 4, iy + 5), torch.arange(ix - 4, ix + 5), indexing='ij')
    src = (float((win * gx).sum() / win.sum()), float((win * gy).sum() / win.sum()))
    info = {'target': target_key, 'exposure_mode': expo_mode, 'declared_ppd': ppd, 'resample_scale': s, 'display_px': [int(V.shape[3]), int(V.shape[2])],
            'crop_offset_px': [int(x0), int(y0)], 'source_px_on_display': [round(src[0], 1), round(src[1], 1)],
            'luminance_integral_ratio_after_resample': e_out / e_in, 'exposure': exposure,
            'point_peak_cd_m2_frame1_before_exposure': float(Y[0].max()),
            'point_peak_cd_m2_all_frames_max_before_exposure': float(Y.max()),
            'frames_clipped': clipped_frames, 'frames': int(V.shape[0]), 'sky_relative_code_linear': float(exposure * bg / peak)}
    return V, info


def to_8bit(V):
    return torch.round(V * 255).to(torch.uint8)


def save_crops(V, info, tag):
    cx, cy = [int(round(c)) for c in info['source_px_on_display']]
    r = 12
    tiles = [V[f, :, cy - r:cy + r + 1, cx - r:cx + r + 1] for f in (0, len(V) // 2, len(V) - 1)]
    im = torch.cat([torch.cat([t, torch.full((3, 2 * r + 1, 2), 0.5, dtype=t.dtype)], 2) for t in tiles], 2)
    im = im.float().permute(1, 2, 0).numpy()
    im = np.kron(im, np.ones((12, 12, 1)))
    o = oiio.ImageOutput.create(os.path.join(out, f'ADAPTED_S6_{tag}_displayframes_1_24_48_crop.png'))
    spec = oiio.ImageSpec(im.shape[1], im.shape[0], 3, oiio.UINT8)
    o.open(os.path.join(out, f'ADAPTED_S6_{tag}_displayframes_1_24_48_crop.png'), spec)
    o.write_image((im * 255).clip(0, 255).astype(np.uint8)); o.close()


results = []
t_all = time.time()
cases = [('PHONE_TARGET', (1920, 820), 'phone'), ('DESKTOP_TARGET', None, 'desktop')]

if tool == 'cvvdp':
    import pycvvdp
    cfg = os.path.join(HERE, 'display_models_cvvdp_targets.json')
    for key, crop, tag in cases:
        V, info = form_display(key, crop)
        save_crops(V, info, tag)
        ref = V[0:1].repeat(V.shape[0], 1, 1, 1)
        runs = [('hnp_phone_target' if tag == 'phone' else 'hnp_desktop_target', 'float'),
                ('hnp_phone_target' if tag == 'phone' else 'hnp_desktop_target', '8bit')]
        if tag == 'desktop':
            runs.append(('hnp_desktop_target_physical_centre_ppd', 'float'))
        for disp, enc in runs:
            m = pycvvdp.cvvdp(display_name=disp, config_paths=[cfg], device=torch.device('cpu'), quiet=True)
            T, R = (V.half(), ref.half()) if enc == 'float' else (to_8bit(V), to_8bit(ref))
            t0 = time.time()
            q, _ = m.predict(T, R, dim_order='FCHW', frames_per_second=FPS)
            results.append({**info, 'tool': 'ColorVideoVDP 0.5.7', 'metric_id': m.get_info_string(), 'display_model': disp,
                            'encoding': enc, 'test': 'S6 moving (48 f)', 'reference': 'S6 frame 1 x48',
                            'JOD': float(q), 'seconds': round(time.time() - t0, 1)})
            print(results[-1]['display_model'], enc, results[-1]['JOD'], flush=True)
        # variant: exposure from the brightest frame of the MOVING clip (nothing clips)
        V2, info2 = form_display(key, crop, 'allframes')
        ref2 = V2[0:1].repeat(V2.shape[0], 1, 1, 1)
        m = pycvvdp.cvvdp(display_name=runs[0][0], config_paths=[cfg], device=torch.device('cpu'), quiet=True)
        q, _ = m.predict(V2.half(), ref2.half(), dim_order='FCHW', frames_per_second=FPS)
        results.append({**info2, 'tool': 'ColorVideoVDP 0.5.7', 'metric_id': m.get_info_string(), 'display_model': runs[0][0],
                        'encoding': 'float', 'test': 'S6 moving (48 f)', 'reference': 'S6 frame 1 x48', 'JOD': float(q)})
        print(runs[0][0], 'allframes exposure', float(q), flush=True)
        del V2, ref2
        # control: static vs static must give 10 JOD
        m = pycvvdp.cvvdp(display_name=runs[0][0], config_paths=[cfg], device=torch.device('cpu'), quiet=True)
        q, _ = m.predict(ref[:8].half(), ref[:8].half(), dim_order='FCHW', frames_per_second=FPS)
        results.append({**info, 'tool': 'ColorVideoVDP', 'display_model': runs[0][0], 'encoding': 'float',
                        'test': 'CONTROL S6 frame 1 x8', 'reference': 'S6 frame 1 x8', 'JOD': float(q)})
        del V, ref
elif tool == 'fvvdp':
    os.environ['FVVDP_PATH'] = os.path.join(HERE, 'fvvdp_config')
    import pyfvvdp
    from pyfvvdp.fvvdp_display_model import fvvdp_display_geometry
    for key, crop, tag in cases:
        V, info = form_display(key, crop)
        ref = V[0:1].repeat(V.shape[0], 1, 1, 1)
        disp = 'hnp_phone_target' if tag == 'phone' else 'hnp_desktop_content'
        m = pyfvvdp.fvvdp(display_name=disp, foveated=True, device=torch.device('cpu'), quiet=True)
        geo = m.display_geometry
        d, pitch = geo.distance_m, geo.display_size_m[0] / geo.resolution[0]
        sx, sy = info['source_px_on_display']
        off10 = d * math.tan(math.radians(10)) / pitch
        for fix_name, fix in [('fixation on source', (sx, sy)), ('fixation 10 deg right of source', (sx + off10, sy))]:
            t0 = time.time()
            q, _ = m.predict(V.float(), ref.float(), dim_order='FCHW', frames_per_second=FPS,  # fvvdp: float32 only
                             fixation_point=np.array([fix[0], fix[1]]))
            results.append({**info, 'tool': 'FovVideoVDP 1.2.2 (foveated=True)', 'metric_id': m.get_info_string(),
                            'display_model': disp, 'fvvdp_ppd_centre_physical': geo.get_ppd(), 'encoding': 'float32',
                            'fixation': fix_name, 'fixation_px': [round(fix[0], 1), round(fix[1], 1)],
                            'test': 'S6 moving (48 f)', 'reference': 'S6 frame 1 x48', 'JOD': float(q),
                            'seconds': round(time.time() - t0, 1)})
            print(disp, fix_name, float(q), flush=True)
        del V, ref
json.dump(results, open(os.path.join(out, f'ADAPTED_S6_{tool}_results.json'), 'w'), indent=1)
print('total seconds', round(time.time() - t_all, 1))
