"""N1.6 RoadLine scene (n1/roadline/PREREG.md + addendum 1). Headless Cycles CPU:

    blender -b --factory-startup --python n1/roadline/scene.py -- MODE STIM OUTDIR [samples]

MODE  full          the RoadLine still: 7 luminaires at DISTANCES with poles and arms, the eye camera, OIDN with the
                    N1 addendum-5 settings and the noisy pass stored -> OUTDIR/roadline.exr, lamps.json
      a0probes      one luminaire at (5.5, 30, 8); albedo-1 patches facing it at 5 m in the addendum-1 directions and
                    one on the road under it. DIRECT LIGHT ONLY (max_bounces 0, world off): a measurement setting,
                    so ground bounce cannot pose as luminaire intensity. -> OUTDIR/a0_<name>.exr, a0_dirs.json
      a0emit_D      one luminaire at (5.5, D, 8), the full frozen sky/ground, seen from the eye; render border around
                    the lamp -> OUTDIR/a0emit_D.exr, a0emit_D.json
STIM  A | B (the LM-63 file from n1/roadline/work, fetched by fetch.sh)

Units as N1/M1: K = 179 lm/W; luminance = 179 * Y. IES mapping (addendum 2, from the Cycles source): the IES node
outputs candela * 4 pi / 177.83, so a point light of power P = 177.83 / K W gives I(dir) = candela(dir) exactly.
Orientation (svm/ies.h: H = atan2(x, y) + pi): table H = 0 is the light's local -y; the light is rotated -90 deg
about z so that H = 0 (street side) faces world -x. Lights are hidden from the camera; each has a camera-only emitter sphere, L = I_table(eye) / (pi r^2) (addendum 3).
"""
import json, math, os, sys
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lm63

a = sys.argv[sys.argv.index("--") + 1:]; MODE, STIM, OUT = a[0], a[1], a[2]; SPP = int(a[3]) if len(a) > 3 else 1024
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
K = 179.0
IES = {"A": f"{HERE}/work/A_archeon.ies", "B": f"{HERE}/work/B_rma.ies"}[STIM]
TAB = lm63.read(IES); IMAX = float(TAB["C"].max())
SKY_CDM2, SKY_TINT = 4e-4, (0.85, 0.9, 1.0)
EYE = (0.5, 0.0, 1.7); HFOV, RES = 60.0, (1920, 820)
LUM_X, LUM_Z, RADIUS = 5.5, 8.0, 0.105
DISTANCES = (25, 50, 100, 200, 400, 800, 1600)
POLE_X = 7.5


def unit_lum(rgb):
    y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]; return tuple(c / y for c in rgb)


def planck_rgb(T):
    x = -0.2661239e9 / T ** 3 - 0.2343589e6 / T ** 2 + 0.8776956e3 / T + 0.179910
    y = -0.9549476 * x ** 3 - 1.37418593 * x ** 2 + 2.09137015 * x - 0.16748867
    return xy_rgb(x, y)


def xy_rgb(x, y):
    X, Y, Z = x / y, 1.0, (1 - x - y) / y
    return unit_lum((3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z, -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z,
                     0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z))


COLOUR = planck_rgb(3000) if STIM == "A" else xy_rgb(0.52, 0.42)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SPP; sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False; sc.cycles.max_bounces = 4
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "32"; sc.render.image_settings.exr_codec = "ZIP"
world = bpy.data.worlds.new("NightSky"); world.use_nodes = True; bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (*unit_lum(SKY_TINT), 1); bg.inputs["Strength"].default_value = SKY_CDM2 / K; sc.world = world


def material(name, albedo, rough=0.9, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (albedo, albedo, albedo, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec; return m


def mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o); o.data.materials.append(mat); return o


FIELD = material("field", 0.08, 0.95, 0.0)                         # N1 round-1 vegetation: Lambertian
ASPHALT = material("asphalt", 0.07, 0.85, 0.5)
mesh("field", [(-20000, -5000, 0), (20000, -5000, 0), (20000, 30000, 0), (-20000, 30000, 0)], [(0, 1, 2, 3)], FIELD)
mesh("road", [(0, -5, 0.003), (7, -5, 0.003), (7, 3000, 0.003), (0, 3000, 0.003)], [(0, 1, 2, 3)], ASPHALT)


def luminaire(y):
    ld = bpy.data.lights.new(f"lum_{y}", "POINT"); ld.energy = 177.83 / K                                     # addendum 2; ld.color = COLOUR
    ld.shadow_soft_size = RADIUS; ld.use_nodes = True; nt = ld.node_tree
    ies = nt.nodes.new("ShaderNodeTexIES"); ies.mode = "EXTERNAL"; ies.filepath = IES
    nt.links.new(ies.outputs[0], nt.nodes["Emission"].inputs["Strength"])
    o = bpy.data.objects.new(f"lum_{y}", ld); o.location = (LUM_X, y, LUM_Z); o.rotation_euler = (0, 0, -math.pi / 2)
    o.visible_camera = False                                    # addendum 3: the IES light only illuminates
    sc.collection.objects.link(o)
    # addendum 3: camera-only emitter, radiance = I_table(towards the eye) / (pi r^2) (Cycles does not evaluate the IES
    # towards the eye for camera rays on the visible sphere; verified in A0 run 2)
    e = Vector(EYE) - Vector((LUM_X, y, LUM_Z)); r = e.length
    V = math.degrees(math.acos(-e.z / r)); H = math.degrees(math.atan2(-e.y, -e.x)) % 360
    I_eye = lm63.intensity(TAB, V, H)
    m = bpy.data.materials.new(f"emit_{y}"); m.use_nodes = True; nt2 = m.node_tree; nt2.nodes.clear()
    em = nt2.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*COLOUR, 1)
    em.inputs["Strength"].default_value = I_eye / (math.pi * RADIUS ** 2) / K
    nt2.links.new(em.outputs[0], nt2.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=RADIUS, location=(LUM_X, y, LUM_Z), segments=24, ring_count=12)
    sp = bpy.context.active_object; sp.data.materials.append(m)
    for att in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(sp, att, False)
    return o


def white_patch(name, centre, normal, size=0.3):
    n = Vector(normal).normalized(); t = n.orthogonal().normalized(); b = n.cross(t); c = Vector(centre); h = size / 2
    vs = [tuple(c + h * (sx * t + sy * b)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = bpy.data.materials.new("white"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    d = nt.nodes.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(d.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return mesh(name, vs, [(0, 1, 2, 3)], m)


def ortho_cam(name, loc, look_dir, scale=0.1):
    cd = bpy.data.cameras.new(name); cd.type = "ORTHO"; cd.ortho_scale = scale; o = bpy.data.objects.new(name, cd)
    o.location = loc; o.rotation_euler = Vector(look_dir).to_track_quat("-Z", "Y").to_euler(); sc.collection.objects.link(o); return o


if MODE == "a0probes":
    sc.cycles.max_bounces = 0; bg.inputs["Strength"].default_value = 0.0      # direct light only (measurement setting)
    L = Vector((LUM_X, 30.0, LUM_Z)); luminaire(30.0)
    sc.render.resolution_x = sc.render.resolution_y = 8; R = 5.0; out = {}
    dirs = [(0, 0), (45, 0), (60, 0), (60, 90), (60, 180), (75, 90), (82.5, 90), (87.5, 90), (90, 90)]
    for V, H in dirs:
        v, h = math.radians(V), math.radians(H)
        d = Vector((-math.sin(v) * math.cos(h), math.sin(v) * math.sin(h), -math.cos(v)))   # H=0 -> world -x (street side)
        P = L + R * d; name = f"V{V}_H{H}"
        pa = white_patch(f"p_{name}", P, -d); cam = ortho_cam(f"c_{name}", P - 0.2 * d, d)
        sc.camera = cam; sc.render.filepath = f"{OUT}/a0_{name}.exr"; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(pa); out[name] = {"V": V, "H": H, "r_m": R, "I_table_cd": lm63.intensity(TAB, V, H)}
    pa = white_patch("p_ground", (LUM_X, 30.0, 0.02), (0, 0, 1)); cam = ortho_cam("c_ground", (LUM_X, 30.0, 0.3), (0, 0, -1))
    sc.camera = cam; sc.render.filepath = f"{OUT}/a0_ground.exr"; bpy.ops.render.render(write_still=True)
    out["ground"] = {"V": 0, "H": 0, "r_m": LUM_Z - 0.02, "I_table_cd": lm63.intensity(TAB, 0, 0)}
    json.dump({"stim": STIM, "I_max": IMAX, "energy_W": 177.83 / K, "probes": out}, open(f"{OUT}/a0_dirs.json", "w"), indent=1)
elif MODE.startswith("a0emit_"):
    D = float(MODE.split("_")[1]); luminaire(D)
    cd = bpy.data.cameras.new("eye"); cd.sensor_fit = "HORIZONTAL"; cd.angle = math.radians(HFOV)
    cam = bpy.data.objects.new("eye", cd); cam.location = EYE; cam.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(cam); sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = RES
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update(); c = world_to_camera_view(sc, cam, Vector((LUM_X, D, LUM_Z)))
    px, py = c.x * RES[0], (1 - c.y) * RES[1]; half = 32
    sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = (px - half) / RES[0], (px + half) / RES[0]
    sc.render.border_min_y, sc.render.border_max_y = 1 - (py + half) / RES[1], 1 - (py - half) / RES[1]
    Evec = Vector(EYE) - Vector((LUM_X, D, LUM_Z)); r = Evec.length
    V = math.degrees(math.acos(-Evec.z / r)); H = math.degrees(math.atan2(-Evec.y, -Evec.x)) % 360
    sc.render.filepath = f"{OUT}/a0emit_{int(D)}.exr"; bpy.ops.render.render(write_still=True)
    json.dump({"stim": STIM, "D": D, "px": [px, py], "r_m": r, "V": V, "H": H, "I_table_cd": lm63.intensity(TAB, V, H),
               "pixel_solid_angle_sr_at_centre": (math.radians(HFOV) / RES[0]) ** 2}, open(f"{OUT}/a0emit_{int(D)}.json", "w"), indent=1)
elif MODE == "full":
    POLE = material("pole", 0.3, 0.5, 0.5)
    lamps = []
    for d in DISTANCES:
        luminaire(float(d))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=LUM_Z + 0.2, location=(POLE_X, d, (LUM_Z + 0.2) / 2)); bpy.context.active_object.data.materials.append(POLE)
        bpy.ops.mesh.primitive_cube_add(size=1, location=((POLE_X + LUM_X) / 2, d, LUM_Z + 0.15)); arm = bpy.context.active_object
        arm.scale = (POLE_X - LUM_X + 0.3, 0.08, 0.06); arm.data.materials.append(POLE)
    cd = bpy.data.cameras.new("eye"); cd.sensor_fit = "HORIZONTAL"; cd.angle = math.radians(HFOV)
    cam = bpy.data.objects.new("eye", cd); cam.location = EYE; cam.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(cam); sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = RES
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    for d in DISTANCES:
        c = world_to_camera_view(sc, cam, Vector((LUM_X, d, LUM_Z))); e = Vector(EYE) - Vector((LUM_X, d, LUM_Z)); r = e.length
        V = math.degrees(math.acos(-e.z / r)); H = math.degrees(math.atan2(-e.y, -e.x)) % 360
        lamps.append({"d": d, "px": [c.x * RES[0], (1 - c.y) * RES[1]], "in_frame": 0 <= c.x <= 1 and 0 <= c.y <= 1,
                      "r_m": r, "V": V, "H": H, "I_table_cd": lm63.intensity(TAB, V, H)})
    json.dump({"stim": STIM, "lamps": lamps, "eye": EYE, "hfov": HFOV, "res": RES}, open(f"{OUT}/lamps.json", "w"), indent=1)
    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"; sc.cycles.denoising_use_gpu = False
    bpy.context.view_layer.cycles.denoising_store_passes = True           # N1 addendum-5 settings, unchanged
    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"
    sc.render.filepath = f"{OUT}/roadline.exr"; bpy.ops.render.render(write_still=True)
