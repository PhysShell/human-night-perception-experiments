"""Luminous intensity of the shielded lamp (lower-hemisphere emitter, 2x radiance) towards a
horizontal observer must equal the full-sphere lamp's; upward it must be ~0.

    blender -b --factory-startup --python m2/check_shielded_lamp.py
"""
import math, os, sys, tempfile
import bpy
import numpy as np

sys.argv = [sys.argv[0], "--", "unused", "1", "clear"]      # makes scene.py's emission() importable
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "..", "m1", "scene.py")).read()
ns = {}
exec(src[:src.index("# --- terrain")].replace("bpy.ops.wm.read_factory_settings(use_empty=True)", ""), ns)
emission = ns["emission"]
T = tempfile.mkdtemp()
res = {}
for label, shielded, cam in (("full", False, "side"), ("shielded", True, "side"), ("shielded", True, "above")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 512
    sc.cycles.use_denoising = False; sc.render.resolution_x = sc.render.resolution_y = 64
    sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "32"
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0; sc.world = w
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 0, 0), segments=48, ring_count=24)
    bpy.context.active_object.data.materials.append(emission("L", (1, 1, 1), 1.0, shielded))
    cd = bpy.data.cameras.new("C"); cd.angle = math.radians(1.0); cd.clip_end = 1e4
    co = bpy.data.objects.new("C", cd)
    if cam == "side":
        co.location = (0, -500, 0); co.rotation_euler = (math.radians(90), 0, 0)
    else:
        co.location = (0, 0, 500); co.rotation_euler = (0, 0, 0)
    sc.collection.objects.link(co); sc.camera = co
    sc.render.filepath = f"{T}/{label}_{cam}.exr"
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(sc.render.filepath)
    px = np.array(img.pixels[:]).reshape(64, 64, 4)[..., :3]
    pix = 2 * math.tan(math.radians(0.5)) / 64
    res[(label, cam)] = px.mean(-1).sum() * pix * pix * 500 ** 2    # intensity [radiance units * m^2]
full = res[("full", "side")]
print(f"full sphere, side view:     I = {full:.5f}  (expected pi r^2 = {math.pi * 0.25 ** 2:.5f})")
print(f"shielded,    side view:     I = {res[('shielded', 'side')]:.5f}  ratio to full {res[('shielded', 'side')] / full:.3f}")
print(f"shielded,    view from top: I = {res[('shielded', 'above')]:.5f}  ratio to full {res[('shielded', 'above')] / full:.3f}")
