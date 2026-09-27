"""N1.5: the frozen hero scene (n1/scene/scene.py, byte-unchanged, hash-checked) seen from another camera
(n1/views.json), rendered once exactly as the accepted hero: stage b, 4096 spp, same seed, Cycles OIDN with the
addendum-5 settings and the noisy pass stored.
  blender -b --factory-startup --python n1/view_render.py -- VIEW OUTDIR"""
import hashlib, json, os, sys
a = sys.argv[sys.argv.index("--") + 1:]; VIEW, OUTDIR = a[0], a[1]
here = os.path.dirname(os.path.abspath(__file__)); p = os.path.join(here, "scene", "scene.py")
code = open(p, "rb").read(); assert hashlib.sha256(code).hexdigest().startswith("3a4df7cf1423032a"), "scene.py is not the frozen scene"
v = json.load(open(os.path.join(here, "views.json")))[VIEW]
src = code.decode()
for old, new in (
        ("EYE_HEIGHT, HFOV_DEG, PITCH_DEG, YAW_DEG = 1.7, 60.0, -3.0, 10.0",
         f"EYE_HEIGHT, HFOV_DEG, PITCH_DEG, YAW_DEG = {v['loc'][2]}, {v['hfov_deg']}, {v['pitch_deg']}, {v['yaw_deg']}"),
        ("    cam.location = (0, 0, EYE_HEIGHT)\n", f"    cam.location = ({v['loc'][0]}, {v['loc'][1]}, EYE_HEIGHT)\n"),
        ('    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"          # Blender 5.x: multilayer EXR\n',
         '    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"          # Blender 5.x: multilayer EXR\n'
         '    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"\n'
         '    sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"; sc.cycles.denoising_use_gpu = False\n'
         '    vl.cycles.denoising_store_passes = True                  # addendum-5 settings, unchanged\n')):
    assert src.count(old) == 1, old
    src = src.replace(old, new)
sys.argv = [sys.argv[0], "--", "hero", "b", OUTDIR, "4096", "1.0"]
exec(compile(src, p, "exec"))
