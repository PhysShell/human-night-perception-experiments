#!/usr/bin/env python3
"""M2.5 gate: the two-pass render (haze + lamps) is the one-pass M2 render.

Why the decomposition is exact in expectation: the lamp spheres are seen by camera rays
only and light is additive, so full = haze pass (everything but the spheres) + the spheres
seen along unscattered camera rays. Links, each tested once:
  1. haze pass == full render away from the lamps               (here: background)
  2. unscattered camera ray through the medium == Beer-Lambert  (t2-extinction, 0.4 %),
     which is what the lamps pass's absorbing medium (same total extinction) gives exactly
  3. an unresolved sphere enlarged to M25_LAMP_PX pixels at the same intensity (cd) lands
     the same energy on the same pixels                         (here: lamp energy)
Checks, golden view, clear atmosphere:
  * background (pixels > 2 px from any lamp): median haze/full within 2 %;
  * lamp energy: lamps pass as in the clips (0.7 px; 4x resolution, box filter, 256 spp, resampled
    with Blackman-Harris 1.5 px) vs lamps pass with the true
    0.25 m spheres (16384 spp, mean of two seeds): total within 2 %;
    every 20-column bin of the ribbon within max(10 %, 2 x the two reference seeds'
    spread): far away a true sphere gets only ~2 hits per 16k samples, so there the
    reference, not the lamps pass, is the noisy side; spot shape (peak-row energy share)
    within 0.08 of Cycles' own filtering;
  * finite everywhere.
The one-pass render cannot be the reference for the lamps: at 320 px a lamp covers ~0.1 % of
a pixel, so even 1024 spp gives it a couple of hits (bins scattered 0.5-2.6x when tried).
  python3 m25/test_decomposition.py [workdir]
"""
import os, subprocess, sys, tempfile
import numpy as np
import OpenImageIO as oiio

W = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="m25dec")
os.makedirs(W, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "..", "m1", "scene.py")
Yw = np.array([0.2126, 0.7152, 0.0722])


def render(name, spp, **env):
    out = f"{W}/{name}.exr"
    if not os.path.exists(out):
        e = dict(os.environ, T2_VIEW="golden", **env)
        ss = int(env.get("M25_SS", "1"))
        raw = f"{W}/{name}_ss.exr" if ss > 1 else out
        subprocess.run(["blender", "-b", "--factory-startup", "--python", SCENE, "--", raw, str(spp), "clear"],
                       env=e, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ss > 1:
            subprocess.run([sys.executable, os.path.join(HERE, "resample.py"), str(ss), raw, out], check=True)
    return oiio.ImageBuf(out).get_pixels(oiio.FLOAT)[..., :3] * 179.0


full = render("full", 512)
haze = render("haze", 128, M25_PASS="haze")
lamps = render("lamps", 256, M25_PASS="lamps", M25_LAMP_PX="0.7", M25_SS="4")
ref = render("lamps_true_radius", 16384, M25_PASS="lamps")
ref2 = render("lamps_true_radius_seed1", 16384, M25_PASS="lamps", M25_SEED="1")
ok = all(np.isfinite(x).all() for x in (full, haze, lamps, ref, ref2))
print(f"finite: {ok}")

Lf, Lh, Ll, Lr1, Lr2 = full @ Yw, haze @ Yw, lamps @ Yw, ref @ Yw, ref2 @ Yw
Lr = 0.5 * (Lr1 + Lr2)
lampmask = (Ll > 0) | (Lr > 0)
near = lampmask.copy()
for dy in range(-2, 3):
    for dx in range(-2, 3):
        near |= np.roll(np.roll(lampmask, dy, 0), dx, 1)
bg = ~near
r = np.median(Lh[bg] / np.maximum(Lf[bg], 1e-12))
ok_bg = abs(r - 1) < 0.02
print(f"1. background ({bg.mean() * 100:.0f} % of pixels): median haze/full {r:.4f}  {'ok' if ok_bg else 'FAIL'}")

tot = Ll.sum() / Lr.sum()
ok_tot = abs(tot - 1) < 0.02
print(f"3. lamp energy, total: enlarged 0.7 px / true radius = {tot:.4f}  {'ok' if ok_tot else 'FAIL'}")
ratios, bad = [], 0
for k in range(0, Ll.shape[1] - 19, 20):
    a, b = Ll[:, k:k + 20].sum(), Lr[:, k:k + 20].sum()
    if b > 0.2 * Lr.sum() / (Ll.shape[1] / 20):                  # bins carrying lamps
        # the two reference seeds differ by ~2 sigma of their mean: 2 x spread ~ 4 sigma
        tol = max(0.10, 2 * abs(Lr1[:, k:k + 20].sum() / Lr2[:, k:k + 20].sum() - 1))
        bad += abs(a / b - 1) > tol
        ratios.append(f"{a / b:.3f}±{tol:.2f}")
ok_bin = bad == 0
print(f"   per 20-column bin, ratio and tolerance max(10 %, 2 x reference seed spread):")
print(f"   {' '.join(ratios)}")
print(f"   bins outside tolerance: {bad}  {'ok' if ok_bin else 'FAIL'}")
# spot shape: share of the ribbon's energy in its peak row (the pixel filter's footprint;
# the resampling must reproduce Cycles' own Blackman-Harris, not a sharper or wider one)
pk = lambda X: X.sum(1).max() / X.sum()
ok_shape = abs(pk(Ll) - pk(Lr)) < 0.08
print(f"   spot shape, energy share of the peak row: {pk(Ll):.3f} vs {pk(Lr):.3f}  {'ok' if ok_shape else 'FAIL'}")
# for information only: the one-pass render's own (very noisy) view of the lamps
print(f"   info: lamps pass / (full - haze), whole image = {Ll.sum() / (Lf - Lh).sum():.3f} "
      f"(the one-pass lamp estimate has a few hits per lamp)")
good = ok and ok_bg and ok_tot and ok_bin and ok_shape
print("PASS" if good else "FAIL")
sys.exit(0 if good else 1)
