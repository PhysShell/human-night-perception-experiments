"""T2 property test: lamp transmittance vs distance through the M2 boundary layer.

    t2/run_extinction.sh     (= blender -b --factory-startup --python-exit-code 1 --python t2/extinction_sweep.py)

Oracle: Beer-Lambert, T_c = exp(-sigma_ext,c * d) per RGB channel, with sigma_ext from the SAME
m2/atmospheres.py code the scene uses (aerosol absorption + aerosol scattering + Rayleigh).
The lamp is a physically small sphere (r = 2 m) resolved by narrowing the view to 5x its
angular diameter (64 px), so the disc pixels measure direct light, not sub-pixel sampling
luck. (A first version kept the ANGULAR size constant; at 15 km that is a 26 m emitter whose
own neighbourhood of lit haze scatters ~sigma_s * r * e^tau extra light onto the disc, and the
test failed for a reason that had nothing to do with extinction.) Checked only where the
expected T >= 0.02 (above the Monte Carlo noise floor at 256 spp). Forward-scattered light
landing on the disc can only ADD, so the tolerance is asymmetric: 0.99 <= T/T_BL <= 1.02
(measured: within 0.4 % over 1-15 km, clear and mild).
Also metamorphic: for every distance, T(vacuum) >= T(clear) >= T(mild).
"""
import math, os, sys, tempfile
import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "m2"))
import atmospheres

DIST = [1000.0, 3000.0, 5000.0, 10000.0, 15000.0]
TMP = tempfile.mkdtemp()
RES, R_LAMP, H = 64, 2.0, 9.0
res = {}
for case in ("vacuum", "clear", "mild"):
    for d in DIST:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 256
        sc.cycles.use_adaptive_sampling = False; sc.cycles.use_denoising = False
        sc.cycles.seed = 1
        sc.render.resolution_x = sc.render.resolution_y = RES
        sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "32"
        w = bpy.data.worlds.new("W"); w.use_nodes = True
        w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0; sc.world = w
        m = bpy.data.materials.new("E"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 1.0
        nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=R_LAMP, location=(0, d, H), segments=64, ring_count=32)
        bpy.context.active_object.data.materials.append(m)
        if case != "vacuum":
            atmospheres.add_boundary_layer(sc, atmospheres.CASES[case])
        cd = bpy.data.cameras.new("C"); cd.angle = 5 * 2 * math.atan(R_LAMP / d); cd.clip_end = 1e5
        co = bpy.data.objects.new("C", cd); co.location = (0, 0, H)
        co.rotation_euler = (math.radians(90), 0, 0); sc.collection.objects.link(co); sc.camera = co
        path = f"{TMP}/t2_ext_{case}_{int(d)}.exr"
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        res[(case, d)] = np.array(img.pixels[:], dtype=np.float64).reshape(RES, RES, 4)[..., :3]

fails = []
for case in ("clear", "mild"):
    sa, ss, sr, g = atmospheres.coefficients(**atmospheres.CASES[case])
    sig = np.array(sa) + np.array(ss) + np.array(sr)
    for d in DIST:
        vac = res[("vacuum", d)]
        disc = vac.mean(-1) > 0.5
        T = res[(case, d)][disc].sum(0) / vac[disc].sum(0)
        Tbl = np.exp(-sig * d)
        checked = Tbl >= 0.02
        r = T / Tbl
        ok = np.all((r[checked] >= 0.99) & (r[checked] <= 1.02))
        print(f"{case:6s} d={d / 1000:5.1f} km  T={np.round(T, 4)}  Beer-Lambert={np.round(Tbl, 4)}  "
              f"ratio={np.round(r, 3)}  checked={checked.tolist()}  {'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"{case}@{d / 1000:g}km")
for d in DIST:                                   # metamorphic: denser medium -> less direct light
    tv, tc, tm = (res[(c, d)][res[("vacuum", d)].mean(-1) > 0.5].sum() for c in ("vacuum", "clear", "mild"))
    if not (tv >= tc >= tm):
        fails.append(f"order@{d / 1000:g}km")
    print(f"monotonic in density @ {d / 1000:5.1f} km: vacuum {tv:.1f} >= clear {tc:.1f} >= mild {tm:.1f}  "
          f"{'ok' if tv >= tc >= tm else 'FAIL'}")
if fails:
    raise SystemExit("EXTINCTION SWEEP FAILED: " + ", ".join(fails))
print("PASS")
