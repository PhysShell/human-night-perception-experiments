"""M1 minimal night test scene: dark ground, poplar silhouettes, a distant dense chain of
warm sub-pixel lamps. Built and rendered headless with Cycles CPU:

    blender -b --factory-startup --python m1/scene.py -- OUT.exr [samples] [atmosphere]

atmosphere: none (M1: extinction baked into lamp intensities, V = 25 km), vacuum (M2
reference: M2 lamps, no medium, no baked extinction) or one of m2/atmospheres.py (clear /
mild / moderate): a homogeneous boundary-layer medium built from Cycles' Volume
Coefficients node, with the baked extinction switched off.

Photometric authoring (see m1/README.md, section 1): we adopt Radiance's 179 lm/W
equal-energy-white convention as the RGB radiometric -> photometric calibration. Every light
is specified in photometric units and divided by K = 179; luminance = 179 * Y (Rec.709 Y).
The EXR stays in Blender's scene-linear Rec.709; conversion to Radiance's own RGB/XYZ is
done by ra_xyze (m1/pcond_colorimetric.sh), not by relabelling.
  Verified by m1/calibrate.py: Cycles point-light intensity = P/(4 pi) W/sr, emission
  strength = radiance, world strength = radiance, sub-pixel emitters conserve energy.
Visible lamps are emissive spheres: Cycles point lights are not camera-visible.
"""
import math
import os
import random
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else "m1/out/scene.exr"
SAMPLES = int(args[1]) if len(args) > 1 else 256
ATMOSPHERE = args[2] if len(args) > 2 else "none"

K = 179.0                       # lm/W, Radiance's equal-energy-white convention (not a lamp efficacy)
HFOV_DEG = 60.0
RES = (1920, 820)
if os.environ.get("M2_HALF_RES"):            # M2 comparisons: same FOV, 4x fewer pixels
    RES = (960, 410)
# T2 test views of the SAME scene code (tests/): "golden" = full 60 deg view at 320x137 for
# render regression; "ribbon" = 8 deg x 2 deg window on the lamp ribbon around 4 km.
TEST_VIEW = os.environ.get("T2_VIEW", "")
if TEST_VIEW == "golden":
    RES = (320, 137)
elif TEST_VIEW == "ribbon":
    RES = (240, 60)
EYE_HEIGHT = 1.7                # m
SKY_CDM2 = 4e-4                 # moonless rural sky, with a little skyglow
VISIBILITY_M = 25_000.0 if ATMOSPHERE == "none" else math.inf   # baked extinction only without a medium
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


# M2 lamps (any atmosphere argument other than "none") are split into two parts carrying the
# same energy, a standard rendering technique that changes no physics:
#   * what the eye sees: the emissive sphere at M1 radiance, visible to CAMERA rays only;
#   * what the lamp lights (ground, haze): a spot light at the same place, 180 deg cone
#     pointing down (a shielded road luminaire: nothing above the horizontal), luminous
#     intensity LAMP_CD -> power 4*pi*I/K (Cycles spot = point light masked by the cone,
#     verified in m1/calibrate.py). Point/spot lights are sampled far better than mesh
#     emitters from inside a volume, which is what keeps the haze glow from being noise.
# M1 ("none") keeps the plain emissive spheres: without a medium the upward light is unseen.
SPLIT_LAMPS = ATMOSPHERE != "none"


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
    intensity_cd *= math.exp(-3.912 / VISIBILITY_M * d)   # baked extinction (Koschmieder); 1 with a medium
    radiance = intensity_cd / (math.pi * LAMP_RADIUS ** 2) / K
    key = (rgb, round(radiance, 4))
    if key not in lamp_mats:
        lamp_mats[key] = emission("lamp", unit_lum(rgb), radiance)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=LAMP_RADIUS, location=loc, segments=12, ring_count=6)
    sphere = bpy.context.active_object
    sphere.data.materials.append(lamp_mats[key])
    if SPLIT_LAMPS:
        for attr in ("visible_diffuse", "visible_glossy", "visible_transmission",
                     "visible_volume_scatter", "visible_shadow"):
            setattr(sphere, attr, False)
        ld = bpy.data.lights.new("lamp", "SPOT")
        ld.energy = 4 * math.pi * intensity_cd / K
        ld.color = unit_lum(rgb)
        ld.spot_size = math.pi
        ld.spot_blend = 0.0
        ld.shadow_soft_size = LAMP_RADIUS
        lo = bpy.data.objects.new("lamp", ld)
        lo.location = loc                                  # default orientation points down (-Z)
        sc.collection.objects.link(lo)


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
cd.angle = math.radians(8.0 if TEST_VIEW == "ribbon" else HFOV_DEG)
cd.clip_end = 60_000
cam = bpy.data.objects.new("Eye", cd)
cam.location = (0, 0, EYE_HEIGHT)
cam.rotation_euler = (math.radians(89.3), 0, math.radians(-4))
if TEST_VIEW == "ribbon":                   # level view at the road point u=0.2 (~4.2 km)
    cam.rotation_euler = (math.radians(90.0), 0, -math.atan2(300.0, 4140.0))
sc.collection.objects.link(cam)
sc.camera = cam

if ATMOSPHERE not in ("none", "vacuum"):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "m2"))
    import atmospheres
    atmospheres.add_boundary_layer(sc, atmospheres.CASES[ATMOSPHERE],
                                   bounces=int(os.environ.get("M2_VOLUME_BOUNCES", "0")))
    # Single scattering of ~500 tiny lamps in a thin medium is a hard sampling problem;
    # Cycles' own path guiding (Open PGL, CPU) is used rather than a denoiser, which would
    # smear the sub-pixel lamps. M2_SAMPLING=plain|guided|guided_biased selects the variant.
    # Measured (m2/README.md): guiding cut the sky-noise tail by only 3-5 % for +21 % time.
    mode = os.environ.get("M2_SAMPLING", "plain")
    if mode.startswith("guided"):
        sc.cycles.use_guiding = True
        sc.cycles.use_volume_guiding = True
        sc.cycles.use_surface_guiding = True
        sc.cycles.use_guiding_direct_light = True
    if mode.endswith("biased"):
        sc.cycles.volume_biased = True

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print(f"M1 scene: {n} road lamp slots, {len(lamp_mats)} lamp materials, samples={SAMPLES}, "
      f"atmosphere={ATMOSPHERE} -> {OUT}")
