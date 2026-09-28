"""N1.7 addendum 2: stage-1 trace render. The frozen hero scene (n1/scene/scene.py, hash-checked) from a camera on the
B->C path, with n1/view_render.py's camera replacements but WITHOUT its OIDN insertion (scene.py keeps use_denoising =
False), 128 spp, same seed, full 1920x820.
  blender -b --factory-startup --python n1/n17/trace_render.py -- X Y Z YAW PITCH OUTDIR"""
import hashlib, os, sys
a = sys.argv[sys.argv.index("--") + 1:]; X, Y, Z, YAW, PITCH, OUTDIR = *map(float, a[:5]), a[5]
here = os.path.dirname(os.path.abspath(__file__)); p = os.path.join(here, "..", "scene", "scene.py")
code = open(p, "rb").read(); assert hashlib.sha256(code).hexdigest().startswith("3a4df7cf1423032a"), "scene.py is not the frozen scene"
src = code.decode()
for old, new in (("EYE_HEIGHT, HFOV_DEG, PITCH_DEG, YAW_DEG = 1.7, 60.0, -3.0, 10.0", f"EYE_HEIGHT, HFOV_DEG, PITCH_DEG, YAW_DEG = {Z}, 60.0, {PITCH}, {YAW}"),
                 ("    cam.location = (0, 0, EYE_HEIGHT)\n", f"    cam.location = ({X}, {Y}, EYE_HEIGHT)\n")):
    assert src.count(old) == 1, old
    src = src.replace(old, new)
sys.argv = [sys.argv[0], "--", "hero", "b", OUTDIR, "128", "1.0"]
exec(compile(src, p, "exec"))
