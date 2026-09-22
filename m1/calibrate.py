"""Blender 5.2 / Cycles radiometric calibration renders (run headless):

    blender -b --factory-startup --python m1/calibrate.py -- m1/out/calib

Each case renders a tiny linear EXR whose expected pixel value follows from
closed-form radiometry. m1/check_calibration.py compares them. Nothing here
is a vision model: it only establishes what Cycles' numbers mean.
"""
import math, os, sys
import bpy

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "m1/out/calib"
os.makedirs(OUT, exist_ok=True)


def reset(res=(64, 64), samples=64):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.filter_size = 1.5
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "ZIP"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)   # default is 0.05 grey
    bg.inputs["Strength"].default_value = 0.0
    sc.world = w
    return sc


def camera(sc, loc, rot, lens_type="PERSP", fov_deg=10.0, ortho=1.0):
    cd = bpy.data.cameras.new("C")
    cd.type = lens_type
    cd.sensor_fit = "HORIZONTAL"
    if lens_type == "PERSP":
        cd.angle = math.radians(fov_deg)
    else:
        cd.ortho_scale = ortho
    cd.clip_end = 1e5
    co = bpy.data.objects.new("C", cd)
    co.location, co.rotation_euler = loc, rot
    sc.collection.objects.link(co)
    sc.camera = co
    return co


def diffuse(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (*rgb, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(d.outputs[0], o.inputs["Surface"])
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def plane(sc, size, mat, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    p = bpy.context.active_object
    p.data.materials.append(mat)
    return p


def render(sc, name):
    sc.render.filepath = os.path.join(OUT, name + ".exr")
    bpy.ops.render.render(write_still=True)


# 1) Sun, E = 1 W/m^2 at normal incidence, on albedo-0.5 Lambertian plane.
#    expected L = rho*E/pi = 0.159155
sc = reset()
plane(sc, 100, diffuse("g", (0.5, 0.5, 0.5)))
ld = bpy.data.lights.new("S", "SUN"); ld.energy = 1.0; ld.angle = 0.0
lo = bpy.data.objects.new("S", ld); sc.collection.objects.link(lo)
camera(sc, (0, 0, 10), (0, 0, 0), "ORTHO", ortho=2.0)
render(sc, "c1_sun_E1_rho05")

# 2) Point light P = 1000 W, radius 0, 10 m above the same plane; look straight down
#    at the spot below it. Expected if I = P/(4 pi): L = rho*P/(4 pi d^2)/pi = 0.126651
sc = reset()
plane(sc, 1000, diffuse("g", (0.5, 0.5, 0.5)))
ld = bpy.data.lights.new("P", "POINT"); ld.energy = 1000.0; ld.shadow_soft_size = 0.0
lo = bpy.data.objects.new("P", ld); lo.location = (0, 0, 10); sc.collection.objects.link(lo)
camera(sc, (0, 0, 9.0), (0, 0, 0), "ORTHO", ortho=0.2)
render(sc, "c2_point_P1000_d10_rho05")

# 3) World background colour 1, strength 1e-3, seen directly: expected L = 1e-3.
#    Plus the same world lighting a rho=0.5 plane: expected L = rho*B = 5e-4.
sc = reset()
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1e-3
camera(sc, (0, 0, 1), (math.radians(90), 0, 0), "PERSP", 10.0)
render(sc, "c3_world_B1e-3")
plane(sc, 1e5, diffuse("g", (0.5, 0.5, 0.5)))
camera(sc, (0, 0, 10), (0, 0, 0), "ORTHO", ortho=1.0)
render(sc, "c3b_world_B1e-3_plane_rho05")

# 4) Emission shader, strength 2, on a plane filling the view: expected L = 2 (if strength = radiance).
sc = reset()
plane(sc, 10, emissive("e", (1, 1, 1), 2.0))
camera(sc, (0, 0, 5), (0, 0, 0), "ORTHO", ortho=1.0)
render(sc, "c4_emission_S2")

# 5) Sub-pixel emitters seen by the camera at 500 m, black world, 1 deg FOV (0.0156 deg/pixel):
#    (a) point light P=1000 W radius 0.1 m (is it camera-visible? energy?)
#    (b) emissive sphere r=0.1 m, strength S=100.
#    Energy check: sum(L_pix * Omega_pix) must equal I / d^2.
for tag, kind in (("a_pointlight", "light"), ("b_emissive_sphere", "mesh")):
    sc = reset(res=(64, 64), samples=1024)
    if kind == "light":
        ld = bpy.data.lights.new("P", "POINT"); ld.energy = 1000.0; ld.shadow_soft_size = 0.1
        lo = bpy.data.objects.new("P", ld); lo.location = (0, 500, 0); sc.collection.objects.link(lo)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 500, 0), segments=32, ring_count=16)
        bpy.context.active_object.data.materials.append(emissive("e", (1, 1, 1), 100.0))
    camera(sc, (0, 0, 0), (math.radians(90), 0, 0), "PERSP", 1.0)
    render(sc, "c5" + tag + "_d500")
print("calibration renders written to", OUT)
