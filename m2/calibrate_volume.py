"""M2: does Cycles' Volume Coefficients node follow Beer-Lambert per channel?

    blender -b --factory-startup --python m2/calibrate_volume.py -- m2/out/vcal

An emissive sphere (r = 1 m, radiance 1) at d = 1000 m, 2 deg camera, black world, inside a
homogeneous medium box. Cases (coefficients in 1/m, scene unit = m):
  vacuum                     reference
  abs_grey    sigma_a = 1e-3                      -> T = exp(-1) = 0.3679
  abs_rgb     sigma_a = (0.5, 1, 2) e-3           -> T = (0.6065, 0.3679, 0.1353)
  sca_hg07    sigma_s = 1e-3, Henyey-Greenstein g = 0.7, single scattering
              -> direct (disc pixels) T = 0.3679; extra light around the disc = aureole
Checked by m2/check_volume.py.
"""
import math, os, sys
import bpy

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "m2/out/vcal"
os.makedirs(OUT, exist_ok=True)
CASES = {
    "vacuum": None,
    "abs_grey": ((1e-3,) * 3, (0.0,) * 3, 0.0),
    "abs_rgb": ((0.5e-3, 1e-3, 2e-3), (0.0,) * 3, 0.0),
    "sca_hg07": ((0.0,) * 3, (1e-3,) * 3, 0.7),
}

for name, coeff in CASES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 1024
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.cycles.volume_bounces = 0
    sc.render.resolution_x = sc.render.resolution_y = 128
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    sc.world = w

    e = bpy.data.materials.new("E"); e.use_nodes = True; nt = e.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 1000, 0), segments=64, ring_count=32)
    bpy.context.active_object.data.materials.append(e)

    if coeff:
        sa, ss, g = coeff
        m = bpy.data.materials.new("M"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        v = nt.nodes.new("ShaderNodeVolumeCoefficients")
        v.phase = "HENYEY_GREENSTEIN"
        v.inputs["Absorption Coefficients"].default_value = sa
        v.inputs["Scatter Coefficients"].default_value = ss
        v.inputs["Anisotropy"].default_value = g
        nt.links.new(v.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
        bpy.ops.mesh.primitive_cube_add(size=4000, location=(0, 500, 0))
        bpy.context.active_object.data.materials.append(m)

    cd = bpy.data.cameras.new("C"); cd.angle = math.radians(2.0); cd.clip_end = 1e5
    co = bpy.data.objects.new("C", cd); co.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(co); sc.camera = co
    sc.render.filepath = f"{OUT}/{name}.exr"
    bpy.ops.render.render(write_still=True)
