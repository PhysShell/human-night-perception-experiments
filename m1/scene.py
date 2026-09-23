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
# M2.5 (m25/): render passes and camera motion for the video test. Same scene; the
# full image is the sum of the two passes (lamp spheres are seen by camera rays only):
#   "haze"  = everything except the camera-visible lamp spheres;
#   "lamps" = only the lamp spheres, seen through an absorbing medium with the same total
#             extinction (the direct, unscattered part), occluders black, no sky, no lights.
#             M25_LAMP_PX > 0 enlarges each sphere to that many pixels across at its distance
#             and lowers its radiance by the same area, so its intensity (cd) is unchanged: an
#             unresolved source is defined by intensity alone, and a larger disc is hit by
#             many more camera samples (less Monte Carlo twinkle in motion).
#   "occluders" = (test aid) white poplars on black, same band as "lamps": where a lamp may
#             legitimately blink by passing behind a tree edge (m25/check_clip.py)
M25_PASS = os.environ.get("M25_PASS", "")
M25_LAMP_PX = float(os.environ.get("M25_LAMP_PX", "0"))
M25_FRAMES = int(os.environ.get("M25_FRAMES", "0"))        # > 0: render an animation
M25_FPS = int(os.environ.get("M25_FPS", "24"))
M25_WALK = float(os.environ.get("M25_WALK", "0"))          # m/s, camera moves along +x
M25_SEED = int(os.environ.get("M25_SEED", "0"))            # Cycles seed (0 = default)
# lamps pass only: render at M25_SS x the resolution with a 1-pixel box filter; the caller
# (m25/render_clip.sh) resamples it to RES with Blackman-Harris 1.5 px (Cycles' own pixel
# filter). The filter tails then come from many well-sampled pixels instead of rare
# Monte Carlo hits, which blinked at pcond's exposure (M2.5 pilot).
M25_SS = int(os.environ.get("M25_SS", "1")) if M25_PASS == "lamps" else 1
RES_OUT = RES
RES = (RES[0] * M25_SS, RES[1] * M25_SS)
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
sc.cycles.seed = M25_SEED
if M25_PASS == "haze" and os.environ.get("M25_DENOISE", "0") == "1":
    # the haze pass has no camera-visible sub-pixel emitters (those are in the lamps pass),
    # so Cycles' own OIDN denoiser can be tested on it (bias checked in m25/README.md)
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.denoising_prefilter = "ACCURATE"
if M25_PASS == "lamps":
    sc.cycles.transparent_max_bounces = 256         # see-through lamp spheres (emission())
    if M25_SS > 1:
        sc.cycles.pixel_filter_type = "BOX"
        sc.cycles.filter_width = 1.0
if M25_PASS == "lamps" and os.environ.get("M25_ADAPTIVE", "0") == "1":
    # NOT used for clips: a pixel in the tail of a lamp's filter footprint then stops at the
    # minimum with zero hits in one frame and continues in the next, so it blinks (seen in the
    # M2.5 pilot). Without it, a fixed seed keeps every pixel's sample positions fixed and a
    # slowly moving lamp changes its pixels smoothly; cost is bounded by rendering only the
    # band that contains the lamps (below).
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_min_samples = int(os.environ.get("M25_MIN_SAMPLES", "256"))
    sc.cycles.adaptive_threshold = float(os.environ.get("M25_THRESHOLD", "0.002"))
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
bg.inputs["Strength"].default_value = 0.0 if M25_PASS in ("lamps", "occluders") else SKY_CDM2 / K
sc.world = world


def diffuse(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    if M25_PASS == "occluders":       # mask of the only near occluders of the lamps: poplars
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.0 if name == "poplar" else 0.0
        nt.links.new(e.outputs[0], o.inputs["Surface"])
        return m
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (0, 0, 0, 1) if M25_PASS == "lamps" else (*rgb, 1)
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
    if M25_PASS == "lamps":
        # enlarged unresolved lamps overlap on screen where the road recedes; they must add
        # up, not hide each other: emit from the front face only and let rays pass through
        g = nt.nodes.new("ShaderNodeNewGeometry")
        front = nt.nodes.new("ShaderNodeMath")
        front.operation = "MULTIPLY"
        front.inputs[1].default_value = -radiance
        nt.links.new(g.outputs["Backfacing"], front.inputs[0])
        strength = nt.nodes.new("ShaderNodeMath")                 # radiance * (1 - backfacing)
        strength.inputs[1].default_value = radiance
        nt.links.new(front.outputs[0], strength.inputs[0])
        nt.links.new(strength.outputs[0], e.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(e.outputs[0], add.inputs[0])
        nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], o.inputs["Surface"])
        return m
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


# --- terrain -----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=40_000, location=(0, 15_000, 0))
bpy.context.active_object.data.materials.append(diffuse("field", (0.07, 0.08, 0.06)))
# lamps pass: the flat ground never hides a lamp from eye height, but it would cut the
# enlarged unresolved spheres of distant low lamps in half
bpy.context.active_object.hide_render = M25_PASS == "lamps"

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


LAMP_LOCS = []


def lamp(loc, intensity_cd, rgb):
    LAMP_LOCS.append(loc)
    if M25_PASS == "occluders":
        return
    d = math.dist((0, 0, EYE_HEIGHT), loc)
    intensity_cd *= math.exp(-3.912 / VISIBILITY_M * d)   # baked extinction (Koschmieder); 1 with a medium
    r = LAMP_RADIUS
    if M25_PASS == "lamps" and M25_LAMP_PX > 0:
        r = max(r, 0.5 * M25_LAMP_PX * math.radians(HFOV_DEG) / RES_OUT[0] * d)
    radiance = intensity_cd / (math.pi * r ** 2) / K
    key = (rgb, round(radiance, 4 if r == LAMP_RADIUS else 9))
    if key not in lamp_mats:
        lamp_mats[key] = emission("lamp", unit_lum(rgb), radiance)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=12, ring_count=6)
    sphere = bpy.context.active_object
    sphere.data.materials.append(lamp_mats[key])
    sphere.hide_render = M25_PASS == "haze"
    if SPLIT_LAMPS:
        if M25_PASS == "lamps":
            for attr in ("visible_diffuse", "visible_glossy", "visible_transmission",
                         "visible_volume_scatter", "visible_shadow"):
                setattr(sphere, attr, False)
            return
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

if ATMOSPHERE not in ("none", "vacuum") and M25_PASS != "occluders":
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "m2"))
    import atmospheres
    atmospheres.add_boundary_layer(sc, atmospheres.CASES[ATMOSPHERE],
                                   bounces=int(os.environ.get("M2_VOLUME_BOUNCES", "0")),
                                   absorb_only=M25_PASS == "lamps")
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

if M25_PASS in ("lamps", "occluders"):
    # render only the image band that contains every lamp over the whole camera path (+6 px);
    # the rest of the lamps pass is black by construction
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    ys = []
    for x in (0.0, M25_WALK * max(M25_FRAMES - 1, 0) / M25_FPS):
        cam.location.x = x
        bpy.context.view_layer.update()
        ys += [world_to_camera_view(sc, cam, Vector(p)).y for p in LAMP_LOCS]
    cam.location.x = 0.0
    pad = 6.0 / RES_OUT[1]
    sc.render.use_border, sc.render.use_crop_to_border = True, False
    sc.render.border_min_x, sc.render.border_max_x = 0.0, 1.0
    sc.render.border_min_y = max(0.0, min(ys) - pad)
    sc.render.border_max_y = min(1.0, max(ys) + pad)
    print(f"M2.5 lamps pass: band y {sc.render.border_min_y:.3f}..{sc.render.border_max_y:.3f}")

sc.render.filepath = OUT
if M25_FRAMES:
    sc.render.fps, sc.frame_start, sc.frame_end = M25_FPS, 1, M25_FRAMES
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"   # constant speed
    for f, x in ((1, 0.0), (M25_FRAMES, M25_WALK * (M25_FRAMES - 1) / M25_FPS)):
        cam.location.x = x
        cam.keyframe_insert("location", index=0, frame=f)
    bpy.ops.render.render(animation=True)
else:
    bpy.ops.render.render(write_still=True)
print(f"M1 scene: {n} road lamp slots, {len(lamp_mats)} lamp materials, samples={SAMPLES}, "
      f"atmosphere={ATMOSPHERE} -> {OUT}")
