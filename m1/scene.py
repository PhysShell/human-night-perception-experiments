"""M1 minimal night test scene: dark ground, poplar silhouettes, a distant dense chain of
warm sub-pixel lamps. Built and rendered headless with Cycles CPU:

    blender -b --factory-startup --python m1/scene.py -- OUT.exr [samples]

Photometric authoring (see m1/README.md, "Calibration"):
  K = 179 lm per Blender-watt (Radiance's white efficacy). Every light is specified in
  photometric units and divided by K, so the rendered EXR is directly a Radiance picture
  (luminance = 179 * Y) and cd/m^2 = 179 * Y.
  Verified by m1/calibrate.py: Cycles point-light intensity = P/(4 pi) W/sr, emission
  strength = radiance, world strength = radiance, sub-pixel emitters conserve energy.
Visible lamps are emissive spheres: Cycles point lights are not camera-visible.
"""
import math
import random
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else "m1/out/scene.exr"
SAMPLES = int(args[1]) if len(args) > 1 else 256

K = 179.0                       # lm/W, Radiance WHTEFFICACY
HFOV_DEG = 60.0
RES = (1920, 820)
EYE_HEIGHT = 1.7                # m
SKY_CDM2 = 4e-4                 # moonless rural sky, with a little skyglow
VISIBILITY_M = 25_000.0         # meteorological visibility for baked extinction (Koschmieder)
LAMP_CD = 800.0                 # luminous intensity of a road luminaire toward the observer
LAMP_RADIUS = 0.25              # m, luminaire size (sub-pixel at km range)
LAMP_HEIGHT = 9.0               # m
LAMP_SPACING = 35.0             # m
rng = random.Random(7)

# linear Rec.709 chromaticities, normalised below to luminance 1
SODIUM = (1.0, 0.45, 0.08)
LED_4000K = (1.0, 0.86, 0.72)
WARM_3000K = (1.0, 0.72, 0.42)
SKY_TINT = (0.85, 0.9, 1.0)


def unit_lum(rgb):
    y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    return tuple(c / y for c in rgb)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False          # a denoiser would smear sub-pixel lamps
sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "32"
sc.render.image_settings.exr_codec = "ZIP"

# --- sky: uniform radiance SKY_CDM2 (world strength = radiance, verified) -----------------
world = bpy.data.worlds.new("NightSky")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (*unit_lum(SKY_TINT), 1)
bg.inputs["Strength"].default_value = SKY_CDM2 / K
sc.world = world


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


def emission(name, rgb, radiance):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = radiance
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


# --- terrain -----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=40_000, location=(0, 15_000, 0))
bpy.context.active_object.data.materials.append(diffuse("field", (0.07, 0.08, 0.06)))

# distant low hills (~20 km, beyond the road), barely darker than the sky
hill_mat = diffuse("hill", (0.08, 0.08, 0.07))
for x, y, sx, sz in ((-9000, 21000, 9000, 420), (4000, 23000, 12000, 560), (16000, 20000, 7000, 350)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, 0), segments=64, ring_count=32)
    h = bpy.context.active_object
    h.scale = (sx, 1500, sz)
    h.data.materials.append(hill_mat)

# --- poplar silhouettes: tall ellipsoids, imperfect sizes and spacing ---------------------
tree_mat = diffuse("poplar", (0.04, 0.05, 0.035))
rows = [(-140 + i * 11 + rng.uniform(-3, 3), 170 + rng.uniform(-6, 6)) for i in range(8)]
rows += [(260 + i * 9 + rng.uniform(-2, 2), 420 + rng.uniform(-8, 8)) for i in range(5)]
rows += [(95, 110)]
for x, y in rows:
    hgt = rng.uniform(16, 24)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, hgt / 2), segments=24, ring_count=16)
    t = bpy.context.active_object
    t.scale = (rng.uniform(1.8, 2.8), rng.uniform(1.8, 2.8), hgt / 2)
    t.data.materials.append(tree_mat)

# --- lamps: emissive spheres, luminous intensity I = L * pi * r^2 -------------------------
lamp_mats = {}


def lamp(loc, intensity_cd, rgb):
    d = math.dist((0, 0, EYE_HEIGHT), loc)
    intensity_cd *= math.exp(-3.912 / VISIBILITY_M * d)   # baked extinction (Koschmieder)
    radiance = intensity_cd / (math.pi * LAMP_RADIUS ** 2) / K
    key = (rgb, round(radiance, 4))
    if key not in lamp_mats:
        lamp_mats[key] = emission("lamp", unit_lum(rgb), radiance)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=LAMP_RADIUS, location=loc, segments=12, ring_count=6)
    bpy.context.active_object.data.materials.append(lamp_mats[key])


# distant road receding diagonally across the valley, ~2.2 km (left) .. ~14 km (right):
# real 30-40 m spacing compresses with distance into a near-continuous ribbon
a, b = (-1500.0, 1800.0), (7500.0, 13500.0)
n = int(math.dist(a, b) / LAMP_SPACING)
for i in range(n):
    if rng.random() < 0.05:                       # a few dead lamps
        continue
    u = i / n
    x = a[0] + (b[0] - a[0]) * u + rng.uniform(-1, 1)
    y = a[1] + (b[1] - a[1]) * u + rng.uniform(-1, 1)
    rgb = SODIUM if rng.random() < 0.85 else LED_4000K
    lamp((x, y, LAMP_HEIGHT), LAMP_CD * rng.uniform(0.7, 1.3), rgb)

# sparse village clusters further away
for cx, cy, count in ((1200, 6500, 40), (-3800, 9000, 25), (5400, 15500, 30)):
    for _ in range(count):
        rgb = WARM_3000K if rng.random() < 0.7 else LED_4000K
        lamp((cx + rng.gauss(0, 250), cy + rng.gauss(0, 150), rng.uniform(3, 8)),
             rng.uniform(150, 1500), rgb)

# --- camera: eye height, looking across the valley, not along a road ---------------------
cd = bpy.data.cameras.new("Eye")
cd.sensor_fit = "HORIZONTAL"
cd.angle = math.radians(HFOV_DEG)
cd.clip_end = 60_000
cam = bpy.data.objects.new("Eye", cd)
cam.location = (0, 0, EYE_HEIGHT)
cam.rotation_euler = (math.radians(89.3), 0, math.radians(-4))
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print(f"M1 scene: {n} road lamp slots, {len(lamp_mats)} lamp materials, samples={SAMPLES} -> {OUT}")
