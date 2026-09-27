"""N1 hero night scene (n1/PREREG.md + addendum 1). Built and rendered headless with Cycles CPU:

    blender -b --factory-startup --python n1/scene/scene.py -- MODE STAGE OUTDIR [samples] [res_scale]

MODE  hero   -> OUTDIR/hero_<stage>.exr + OUTDIR/hero_<stage>_px.json (pixel windows of the luminance probes)
      probes -> OUTDIR/probe_<stage>_<name>.exr per illuminance probe (a 0.6 m albedo-1 patch seen by a tiny
                orthographic camera 0.3 m above it; cameras do not block light, so E = pi * L)
STAGE a = moon + sky only; b = + the one street luminaire; c = + the barn window (only after b passes)
Always writes OUTDIR/l1_<stage>.json: every light object, every emissive material, the world (gate L1).

Units: the D1/M1 convention (m1/README.md section 1): K = 179 lm/W, luminance = 179 * Y (Rec.709 Y) of the EXR.
Calibration relied on (m1/calibrate.py; re-checked by L2/L4 here in Blender 5.2): sun strength = irradiance
normal to the beam (W/m^2), point/spot intensity = P/(4 pi) W/sr masked by the cone, emission strength and world
strength = radiance.
"""
import json
import math
import os
import random
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
MODE, STAGE, OUT = args[0], args[1], args[2]
SAMPLES = int(args[3]) if len(args) > 3 else 256
RES_SCALE = float(args[4]) if len(args) > 4 else 1.0
assert MODE in ("hero", "probes") and STAGE in ("a", "b", "c")
os.makedirs(OUT, exist_ok=True)

K = 179.0
EYE_HEIGHT, HFOV_DEG, PITCH_DEG, YAW_DEG = 1.7, 60.0, -3.0, 10.0      # yaw > 0 turns the view left (towards -x)
RES = (round(1920 * RES_SCALE), round(820 * RES_SCALE))
# --- authored photometry (PREREG table) ---
MOON_E_H_LX, MOON_ELEV_DEG, MOON_BEARING_DEG = 0.02, 25.0, 50.0       # bearing clockwise from +y; view centre = -10
SKY_CDM2 = 1e-3
LAMP_LM, LAMP_HALF_DEG, LAMP_BLEND, LAMP_R, LAMP_POS = 2000.0, 70.0, 0.3, 0.15, (4.5, 45.0, 5.9)   # addendum 3 (was 30: pool erased the barn shadow)
WINDOW_CDM2 = 10.0
# Cycles >= 4.0 spot mask: smoothstep((cos t - c0) / ((1 - c0) * blend)), no extra cosine. Flux through the cone
# for uniform on-axis intensity I0: 2 pi I0 (1 - c0)(1 - blend/2)  ->  I0 for 2000 lm.
C0 = math.cos(math.radians(LAMP_HALF_DEG))
LAMP_I0 = LAMP_LM / (2 * math.pi * (1 - C0) * (1 - LAMP_BLEND / 2))
SKY_TINT = (0.85, 0.9, 1.0)


def unit_lum(rgb):
    y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    return tuple(c / y for c in rgb)


def planck_rgb(T):
    """Planckian chromaticity (Kim et al. 2002 cubic, 1667-4000 K) -> linear Rec.709 at luminance 1."""
    x = -0.2661239e9 / T ** 3 - 0.2343589e6 / T ** 2 + 0.8776956e3 / T + 0.179910
    y = -0.9549476 * x ** 3 - 1.37418593 * x ** 2 + 2.09137015 * x - 0.16748867
    X, Y, Z = x / y, 1.0, (1 - x - y) / y
    return unit_lum((3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z, -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z,
                     0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z))


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 4
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "32"
sc.render.image_settings.exr_codec = "ZIP"

world = bpy.data.worlds.new("NightSky")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (*unit_lum(SKY_TINT), 1)
bg.inputs["Strength"].default_value = SKY_CDM2 / K
sc.world = world


def material(name, albedo, tint=(1, 1, 1), rough=0.9, ior=1.5, spec=0.5):
    """Principled BSDF, base colour = albedo at the tint's chromaticity (Rec.709 luminance = albedo), no emission."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*(albedo * c for c in unit_lum(tint)), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["IOR"].default_value = ior
    p.inputs["Specular IOR Level"].default_value = spec          # 0 = no Fresnel layer (vegetation canopy)
    m["albedo"] = albedo
    return m


def emitter(name, rgb, radiance_cdm2):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = radiance_cdm2 / K
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def add(obj_op, mat, **kw):
    obj_op(**kw)
    o = bpy.context.active_object
    o.data.materials.append(mat)
    return o


def mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


MAT = {"field": material("field", 0.08, (0.9, 1.0, 0.7), 0.95, spec=0.0), "asphalt": material("asphalt", 0.07, (1, 1, 1), 0.85),
       "poplar": material("poplar", 0.06, (0.8, 1.0, 0.7), 0.95, spec=0.0), "wall": material("wall", 0.45, (1.0, 0.95, 0.85), 0.9),
       "roof": material("roof", 0.10, (1, 1, 1), 0.7), "pole": material("pole", 0.3, (1, 1, 1), 0.5),
       "hill": material("hill", 0.08, (0.9, 1.0, 0.8), 0.95, spec=0.0),
       "puddle": material("puddle", 0.035, (1, 1, 1), 0.02, 1.33)}              # water film over wet asphalt

# --- ground, lane, puddle ---
mesh("field", [(-20000, -5000, 0), (20000, -5000, 0), (20000, 30000, 0), (-20000, 30000, 0)], [(0, 1, 2, 3)], MAT["field"])
mesh("lane", [(-1, -5, 0.003), (5, -5, 0.003), (5, 400, 0.003), (-1, 400, 0.003)], [(0, 1, 2, 3)], MAT["asphalt"])
PUDDLE_C, PUDDLE_AX = (1.0, 10.1), (0.9, 1.8)                      # addendum 3: lamp mirror point
n = 48; rp = random.Random(3)
pv = [(PUDDLE_C[0] + PUDDLE_AX[0] * (1 + 0.12 * math.sin(3 * t) * rp.uniform(0.6, 1)) * math.cos(t),
       PUDDLE_C[1] + PUDDLE_AX[1] * (1 + 0.12 * math.sin(2 * t + 1)) * math.sin(t), 0.006)
      for t in (2 * math.pi * i / n for i in range(n))]
mesh("puddle", [PUDDLE_C + (0.006,)] + pv, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)], MAT["puddle"])

# --- distant low hills (M1), poplar row across the view (left of the lane), barn (right, behind the lamp) ---
for x, y, sx, sz in ((-9000, 21000, 9000, 420), (4000, 23000, 12000, 560), (16000, 20000, 7000, 350)):
    h = add(bpy.ops.mesh.primitive_uv_sphere_add, MAT["hill"], radius=1, location=(x, y, 0), segments=64, ring_count=32)
    h.scale = (sx, 1500, sz)
rng = random.Random(7)
TREES = []
for i in range(8):
    x, y, hgt = -80 + i * 10 + rng.uniform(-2, 2), 125 + rng.uniform(-4, 4), rng.uniform(16, 22)   # tops <= 10 deg: whole crowns in frame
    t = add(bpy.ops.mesh.primitive_uv_sphere_add, MAT["poplar"], radius=1, location=(x, y, hgt / 2), segments=24, ring_count=16)
    t.scale = (rng.uniform(1.8, 2.6), rng.uniform(1.8, 2.6), hgt / 2)
    TREES.append((x, y, hgt))
BX0, BX1, BY0, BY1, BH, BR = 7.0, 17.0, 22.0, 32.0, 5.0, 8.5   # addendum 2
wall_v = [(BX0, BY0, 0), (BX1, BY0, 0), (BX1, BY1, 0), (BX0, BY1, 0), (BX0, BY0, BH), (BX1, BY0, BH), (BX1, BY1, BH),
          (BX0, BY1, BH), ((BX0 + BX1) / 2, BY0, BR), ((BX0 + BX1) / 2, BY1, BR)]
mesh("barn_walls", wall_v, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 8), (6, 7, 9)], MAT["wall"])
mesh("barn_roof", wall_v, [(4, 8, 9, 7), (8, 5, 6, 9)], MAT["roof"])
if os.environ.get("N1_DIAG_NO_BARN_BOUNCE"):                   # diagnostic only (M2 attribution), never a scene setting
    for nm in ("barn_walls", "barn_roof"):
        bpy.data.objects[nm].visible_diffuse = False

# --- luminaire geometry (all stages: the scene is fixed; only the light and its emitter are staged) ---
PX, PY = 6.3, LAMP_POS[1]                                  # addendum 3: pole beside the lane, behind the barn
add(bpy.ops.mesh.primitive_cylinder_add, MAT["pole"], radius=0.08, depth=6.2, location=(PX, PY, 3.1))
arm = add(bpy.ops.mesh.primitive_cube_add, MAT["pole"], size=1, location=((PX + LAMP_POS[0]) / 2, PY, 6.15))
arm.scale = (PX - LAMP_POS[0] + 0.3, 0.08, 0.06)
head = add(bpy.ops.mesh.primitive_cube_add, MAT["pole"], size=1, location=(LAMP_POS[0], PY, 6.0))
head.scale = (0.5, 0.4, 0.14)
LIGHTS = []
if STAGE in ("b", "c"):
    lrgb = planck_rgb(3000)
    ld = bpy.data.lights.new("luminaire", "SPOT")
    ld.energy = 4 * math.pi * LAMP_I0 / K
    ld.color = lrgb
    ld.spot_size = 2 * math.radians(LAMP_HALF_DEG)
    ld.spot_blend = LAMP_BLEND
    ld.shadow_soft_size = LAMP_R
    lo = bpy.data.objects.new("luminaire", ld)
    lo.location = LAMP_POS                                     # default orientation: pointing straight down (-z)
    lo.visible_camera = False                                  # the camera sees the emitter disc below instead
    sc.collection.objects.link(lo)
    disc = add(bpy.ops.mesh.primitive_circle_add, emitter("lamp_disc", lrgb, LAMP_I0 / (math.pi * LAMP_R ** 2)),
               radius=LAMP_R, fill_type="NGON", location=(LAMP_POS[0], LAMP_POS[1], 5.92), vertices=48)
    disc.rotation_euler = (math.pi, 0, 0)                      # normal facing down
    for a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(disc, a, False)                                # camera only: the spot carries all the light
if STAGE == "c":
    w = mesh("window", [(11.4, BY0 - 0.01, 1.3), (12.6, BY0 - 0.01, 1.3), (12.6, BY0 - 0.01, 2.4), (11.4, BY0 - 0.01, 2.4)],
             [(0, 1, 2, 3)], emitter("window", planck_rgb(2700), WINDOW_CDM2))

# --- moon ---
md = bpy.data.lights.new("moon", "SUN")
e, b = math.radians(MOON_ELEV_DEG), math.radians(MOON_BEARING_DEG)
to_moon = Vector((math.sin(b) * math.cos(e), math.cos(b) * math.cos(e), math.sin(e)))
md.energy = MOON_E_H_LX / (K * math.sin(e))                   # irradiance normal to the beam
md.angle = math.radians(0.52)
mo = bpy.data.objects.new("moon", md)
mo.rotation_euler = to_moon.to_track_quat("Z", "Y").to_euler()   # +Z to the moon -> light travels along -Z
sc.collection.objects.link(mo)

# --- gate L1: every light, every emissive material, the world ---
l1 = {"stage": STAGE, "lights": [], "emissive_materials": [], "world_strength_cdm2": bg.inputs["Strength"].default_value * K}
for o in sc.objects:
    if o.type == "LIGHT":
        l1["lights"].append({"name": o.name, "type": o.data.type, "energy": o.data.energy, "normalize": getattr(o.data, "normalize", None)})
for m in bpy.data.materials:
    for nd in (m.node_tree.nodes if m.node_tree else []):
        s = nd.inputs.get("Emission Strength") if nd.type == "BSDF_PRINCIPLED" else (nd.inputs.get("Strength") if nd.type == "EMISSION" else None)
        col = nd.inputs.get("Emission Color") if nd.type == "BSDF_PRINCIPLED" else None
        if s is not None and s.default_value > 0 and (col is None or max(col.default_value[:3]) > 0):
            l1["emissive_materials"].append({"material": m.name, "node": nd.type, "radiance_cdm2": s.default_value * K,
                                             "users": [o.name for o in sc.objects if o.type == "MESH" and m.name in [x.name for x in o.data.materials if x]]})
l1["authored"] = {"moon_E_h_lx": MOON_E_H_LX, "sky_cdm2": SKY_CDM2, "lamp_I0_cd": LAMP_I0, "lamp_lm": LAMP_LM,
                  "lamp_disc_cdm2": LAMP_I0 / (math.pi * LAMP_R ** 2), "lamp_height_m": LAMP_POS[2], "window_cdm2": WINDOW_CDM2,
                  "lamp_rgb": planck_rgb(3000), "trees": TREES, "materials": {k: v["albedo"] for k, v in MAT.items()}}
json.dump(l1, open(f"{OUT}/l1_{STAGE}.json", "w"), indent=1)


def shadow_point(tree, frac=0.5):
    x, y, hgt = tree
    L = hgt / math.tan(e) * frac
    return (x - math.sin(b) * L, y - math.cos(b) * L)


if MODE == "hero":
    cd = bpy.data.cameras.new("hero")
    cd.sensor_fit = "HORIZONTAL"
    cd.angle = math.radians(HFOV_DEG)
    cam = bpy.data.objects.new("hero", cd)
    cam.location = (0, 0, EYE_HEIGHT)
    cam.rotation_euler = (math.radians(90 + PITCH_DEG), 0, math.radians(YAW_DEG))
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = RES
    bpy.context.view_layer.update()
    pts = {"field_open": (-4, 25, 0), "tree_shadow": shadow_point(TREES[5]) + (0,), "lane_near": (2.5, 6, 0),
           "puddle": PUDDLE_C + (0.006,), "lane_under_lamp": (LAMP_POS[0], LAMP_POS[1] - 2, 0.003),
           "barn_front": (12, BY0, 2.5), "barn_west": (BX0, 27, 2.5), "barn_shadow": (3, 16, 0), "sky_9deg": (3000 * math.sin(math.radians(1)), 3000 * math.cos(math.radians(1)), 3000 * math.tan(math.radians(9))),   # bearing +1 deg: clear of trees, lamp, barn
           "lamp_disc": (LAMP_POS[0], LAMP_POS[1], 5.92)}
    px = {}
    for k, p in pts.items():
        c = world_to_camera_view(sc, cam, Vector(p))
        px[k] = {"x": c.x * RES[0], "y": (1 - c.y) * RES[1], "in_frame": 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0, "world": list(p)}
    json.dump(px, open(f"{OUT}/hero_{STAGE}_px.json", "w"), indent=1)
    vl = bpy.context.view_layer                                # M2 attribution passes (multilayer EXR)
    for pn in ("use_pass_diffuse_direct", "use_pass_diffuse_indirect", "use_pass_diffuse_color",
               "use_pass_glossy_direct", "use_pass_glossy_indirect", "use_pass_glossy_color", "use_pass_emit"):
        setattr(vl, pn, True)
    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"          # Blender 5.x: multilayer EXR
    sc.render.filepath = f"{OUT}/hero_{STAGE}.exr"
    bpy.ops.render.render(write_still=True)
else:
    white = bpy.data.materials.new("probe_white")                # pure Lambertian, albedo 1: E = pi * L
    white.use_nodes = True
    _nt = white.node_tree; _nt.nodes.clear(); _d = _nt.nodes.new("ShaderNodeBsdfDiffuse")
    _d.inputs["Color"].default_value = (1, 1, 1, 1); _d.inputs["Roughness"].default_value = 0.0
    _nt.links.new(_d.outputs[0], _nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    probes = {"barn_shadow": (3, 16), "field_open": (-4, 25), "field_open_right": (25, 20), "tree_shadow": shadow_point(TREES[5]),
              "lane_near": (2.5, 6)}
    if True:                                                   # lamp probes in every stage: stage a gives their moon+sky part
        for d in (0, 5, 10, 15, 20, 30):
            probes[f"lamp_y+{d}"] = (LAMP_POS[0], LAMP_POS[1] + d)
        for d in (10, 20, 30):
            probes[f"lamp_y-{d}"] = (LAMP_POS[0], LAMP_POS[1] - d)
        probes["lamp_x-30"] = (LAMP_POS[0] - 30, LAMP_POS[1])
    sc.render.resolution_x = sc.render.resolution_y = 8
    for name, (x, y) in probes.items():
        z = 0.02 if not name.startswith(("lamp", "lane")) else 0.025
        pa = mesh(f"patch_{name}", [(x - 0.3, y - 0.3, z), (x + 0.3, y - 0.3, z), (x + 0.3, y + 0.3, z), (x - 0.3, y + 0.3, z)],
                  [(0, 1, 2, 3)], white)
        cd = bpy.data.cameras.new(f"c_{name}")
        cd.type = "ORTHO"
        cd.ortho_scale = 0.3
        cam = bpy.data.objects.new(f"c_{name}", cd)
        cam.location = (x, y, z + 0.3)
        sc.collection.objects.link(cam)
        sc.camera = cam
        sc.render.filepath = f"{OUT}/probe_{STAGE}_{name}.exr"
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(pa)                            # one patch at a time: no patch lights another
    if STAGE in ("b", "c"):                                    # L4: the emitter disc seen straight from below
        cd = bpy.data.cameras.new("c_disc"); cd.type = "ORTHO"; cd.ortho_scale = 0.1
        cam = bpy.data.objects.new("c_disc", cd); cam.location = (LAMP_POS[0], LAMP_POS[1], 5.0)
        cam.rotation_euler = (math.pi, 0, 0); sc.collection.objects.link(cam); sc.camera = cam
        sc.render.filepath = f"{OUT}/probe_{STAGE}_disc.exr"; bpy.ops.render.render(write_still=True)
    json.dump({k: list(v) for k, v in probes.items()}, open(f"{OUT}/probes_{STAGE}_xy.json", "w"), indent=1)
