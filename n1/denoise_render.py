"""N1.2 addendum 5: the frozen hero scene (n1/scene/scene.py, byte-unchanged, hash-checked) rendered once with Cycles
render-time OIDN and the denoising data passes stored. Settings fixed in n1/PREREG.md addendum 5.
  blender -b --factory-startup --python n1/denoise_render.py -- hero b n1/work/oidn4096 4096 1.0"""
import hashlib, os, sys
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scene", "scene.py")
code = open(p, "rb").read()
assert hashlib.sha256(code).hexdigest().startswith("3a4df7cf1423032a"), "scene.py is not the frozen scene"
src = code.decode()
hook = '    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"          # Blender 5.x: multilayer EXR\n'
assert src.count(hook) == 1
src = src.replace(hook, hook + '''    sc.cycles.use_denoising = True                             # addendum 5, fixed settings
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.denoising_prefilter = "ACCURATE"
    sc.cycles.denoising_quality = "HIGH"
    sc.cycles.denoising_use_gpu = False
    vl.cycles.denoising_store_passes = True
''')
exec(compile(src, p, "exec"))
