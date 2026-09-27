"""N1.2 step 3: the plain Blender comparator. The hero EXR (Cycles scene-linear units) through Blender 5.2's FACTORY
default view transform and look, exposure in whole stops. Writes one 8-bit sRGB PNG per stop.
  blender -b --factory-startup --python n1/comparator.py -- IN_RGB.exr OUTDIR STOP [STOP ...]"""
import json, os, sys
import bpy
a = sys.argv[sys.argv.index("--") + 1:]; src, out, stops = a[0], a[1], [float(s) for s in a[2:]]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; vs = sc.view_settings
info = {"view_transform": vs.view_transform, "look": vs.look, "display_device": sc.display_settings.display_device, "gamma": vs.gamma}
img = bpy.data.images.load(os.path.abspath(src))
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "8"
for s in stops:
    vs.exposure = s
    img.save_render(os.path.abspath(f"{out}/blender_{s:+.0f}.png"), scene=sc)
json.dump(info, open(f"{out}/factory_view.json", "w"), indent=1)
print("COMPARATOR", info)
