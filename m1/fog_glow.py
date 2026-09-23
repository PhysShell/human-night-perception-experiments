"""Apply Blender's stock Fog Glow (Spencer et al. 1995 photopic PSF) to a linear EXR,
headless, as a pure PSF convolution calibrated to the camera field of view.

    blender -b --factory-startup --python m1/fog_glow.py -- in.exr out.exr HFOV_DEG

Settings, all from reading node_composite_glare.cc / fog_glow_kernel.cc (Blender 5.2.2):
  * kernel degrees/pixel = FOV_k / max(width, height), FOV_k = lerp(180, 10, Size^(1/3))
    -> Size = ((180 - FOV) / 170)^3 makes FOV_k equal the camera FOV across the larger
       image dimension (FOV must be >= 10 deg).
  * Threshold 0 -> the adaptive smooth clamp becomes max(0, x): every pixel scatters.
  * Quality High -> no 2x/4x downsampling of the highlights.
  * the "Glare" output socket = normalised PSF (*) image; the "Image" socket would be
    image + glare, i.e. double-counting the unscattered light, so it is not used.
"""
import os
import sys

import bpy

# The Size <-> FOV relation below is read from Blender 5.2.2's source, not a public API
# contract. Other versions must pass m1/test_fog_glow.sh before being trusted.
TESTED_VERSION = (5, 2, 2)
if bpy.app.version != TESTED_VERSION and not os.environ.get("FOG_GLOW_ALLOW_UNTESTED"):
    sys.exit(f"fog_glow.py: adapter verified for Blender {TESTED_VERSION}, running {bpy.app.version}; "
             "run m1/test_fog_glow.sh with FOG_GLOW_ALLOW_UNTESTED=1 and update TESTED_VERSION")

in_path, out_path, fov = sys.argv[sys.argv.index("--") + 1:][:3]
fov = float(fov)
if fov < 10.0:
    sys.exit("fog glow kernel cannot represent FOV < 10 deg")
size = ((180.0 - fov) / 170.0) ** 3

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
img = bpy.data.images.load(in_path)
img.colorspace_settings.name = "Linear Rec.709"
sc.render.resolution_x, sc.render.resolution_y = img.size
sc.render.resolution_percentage = 100
sc.render.compositor_device = "CPU"  # headless: no GPU/EGL
sc.render.engine = "CYCLES"          # the 3D render is empty; only the compositor matters
sc.cycles.device = "CPU"
sc.cycles.samples = 1
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
sc.collection.objects.link(cam)
sc.camera = cam
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "32"

tree = bpy.data.node_groups.new("FogGlowPSF", "CompositorNodeTree")
tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
sc.compositing_node_group = tree
n_img = tree.nodes.new("CompositorNodeImage")
n_img.image = img
g = tree.nodes.new("CompositorNodeGlare")
g.inputs["Type"].default_value = "Fog Glow"
g.inputs["Quality"].default_value = "High"
g.inputs["Highlights Threshold"].default_value = 0.0
g.inputs["Highlights Smoothness"].default_value = 0.0
g.inputs["Clamp Highlights"].default_value = False
g.inputs["Strength"].default_value = 1.0
g.inputs["Saturation"].default_value = 1.0
g.inputs["Size"].default_value = size
out = tree.nodes.new("NodeGroupOutput")
tree.links.new(n_img.outputs["Image"], g.inputs["Image"])
tree.links.new(g.outputs["Glare"], out.inputs[0])

sc.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"fog glow: fov={fov} deg size={size:.6f} -> {out_path}")
