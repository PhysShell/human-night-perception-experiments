"""N4 (ADAPTED: native Mitsuba 3 plugins driven by our own test spectra; no scene port).
Two tiny controlled scenes per spectrum (LPS, HPS=CIE HP1, LED_warm=CIE LED-B1, E, BLUE):
 A) a directly viewed spherical AREA emitter with spectral radiance L(lambda) normalised to
    1 cd/m^2, rendered to (i) specfilm with SRF bands = CIE 1931 x,y,z-bar + CIE 1951 V'(lambda)
    (from colour-science) and (ii) hdrfilm pixel_format=xyz (Mitsuba's built-in CIE tables);
 B) a POINT emitter of spectral intensity I(lambda) (1 cd per unit-luminance spectrum) 1 m in
    front of a white Lambertian plane, viewed head-on -> checks L = rho*I/(pi*d^2).
Variant: llvm_ad_spectral (CPU). Usage: python n4_emitters.py <spectra.csv> <outdir>"""
import sys, os, json
import numpy as np
import mitsuba as mi
import colour

mi.set_variant(os.environ.get("MI_VARIANT", "llvm_ad_spectral"))
csv, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
D = np.genfromtxt(csv, delimiter=",", names=True)
wl = D["wavelength_nm"]
names = [n for n in D.dtype.names if n != "wavelength_nm"]
shape = colour.SpectralShape(360, 830, 1)
cmf = np.clip(colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"].copy().align(shape).values, 0, None)  # clip ~1e-9 negative interpolation residue
Vs = colour.colorimetry.SDS_LEFS_SCOTOPIC["CIE 1951 Scotopic Standard Observer"].copy().align(
    shape, extrapolator_kwargs={"method": "Constant", "left": 0, "right": 0}).values
def reg(v):  # regular spectrum plugin 360..830 nm
    return {"type": "regular", "wavelength_min": 360.0, "wavelength_max": 830.0, "values": ",".join(f"{x:.8g}" for x in v)}

SPP = int(os.environ.get("SPP", "256"))
res = {"variant": mi.variant(), "mitsuba": mi.__version__, "spp": SPP, "spectra": {}}
for n in names:
    L = D[n]
    # analytic reference (colour-science integrals, 1 nm)
    ref = dict(Y_cd_m2=683 * np.sum(L * cmf[:, 1]), X=683 * np.sum(L * cmf[:, 0]), Z=683 * np.sum(L * cmf[:, 2]),
               Lscot_cd_m2=1700 * np.sum(L * Vs))
    # ---- A: directly viewed area emitter
    sceneA = mi.load_dict({
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 2},
        "sensor": {"type": "perspective", "fov": 10,
                   "to_world": mi.ScalarTransform4f().look_at(origin=[0, 0, 5], target=[0, 0, 0], up=[0, 1, 0]),
                   "sampler": {"type": "independent", "sample_count": SPP},
                   "film": {"type": "specfilm", "width": 32, "height": 32, "component_format": "float32",
                            "rfilter": {"type": "box"},
                            "b1_X": reg(cmf[:, 0]), "b2_Y": reg(cmf[:, 1]), "b3_Z": reg(cmf[:, 2]), "b4_Vscot": reg(Vs)}},
        "lamp": {"type": "sphere", "radius": 0.2, "emitter": {"type": "area", "radiance": reg(L)}},
    })
    imgA = np.array(mi.render(sceneA))
    c = imgA[12:20, 12:20]                      # pixels fully inside the sphere's disc
    sensorB = {"type": "perspective", "fov": 10,
               "to_world": mi.ScalarTransform4f().look_at(origin=[0, 0, 5], target=[0, 0, 0], up=[0, 1, 0]),
               "sampler": {"type": "independent", "sample_count": SPP},
               "film": {"type": "hdrfilm", "width": 32, "height": 32, "pixel_format": "xyz",
                        "component_format": "float32", "rfilter": {"type": "box"}}}
    sceneA2 = mi.load_dict({"type": "scene", "integrator": {"type": "path", "max_depth": 2}, "sensor": sensorB,
                            "lamp": {"type": "sphere", "radius": 0.2, "emitter": {"type": "area", "radiance": reg(L)}}})
    imgA2 = np.array(mi.render(sceneA2))
    c2 = imgA2[12:20, 12:20]
    # ---- B: point emitter 1 m in front of a white Lambertian plane (camera behind the lamp's plane)
    sceneB = mi.load_dict({
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 2},
        "sensor": {"type": "perspective", "fov": 2,
                   "to_world": mi.ScalarTransform4f().look_at(origin=[0, 0, 3], target=[0, 0, 0], up=[0, 1, 0]),
                   "sampler": {"type": "independent", "sample_count": SPP},
                   "film": {"type": "specfilm", "width": 16, "height": 16, "component_format": "float32",
                            "rfilter": {"type": "box"}, "b2_Y": reg(cmf[:, 1]), "b4_Vscot": reg(Vs)}},
        "lamp": {"type": "point", "position": [0, 0, 1.0], "intensity": reg(L)},
        "wall": {"type": "rectangle", "to_world": mi.ScalarTransform4f().scale([5, 5, 1]),
                 "bsdf": {"type": "diffuse", "reflectance": {"type": "uniform", "value": 1.0}}},
    })
    imgB = np.array(mi.render(sceneB))
    cB = imgB[6:10, 6:10]
    mA = c.reshape(-1, c.shape[-1]).mean(0)
    sA = c.reshape(-1, c.shape[-1]).std(0)
    r = {
        "reference_colour_science": ref,
        "A_specfilm_mean": {"X": 683 * mA[0], "Y": 683 * mA[1], "Z": 683 * mA[2], "Lscot": 1700 * mA[3]},
        "A_specfilm_pixel_rel_std": {"Y": float(sA[1] / mA[1]), "Vscot": float(sA[3] / max(mA[3], 1e-30))},
        "A_hdrfilm_xyz_mean_raw": c2.reshape(-1, 3).mean(0).tolist(),
        "A_hdrfilm_Y_times_683x106.75": float(c2[..., 1].mean() * 683 * 106.7502593994140625),
        "B_plane_Y_cd_m2": float(683 * cB[..., 0].mean()),
        "B_expected_Y_cd_m2_rho_I_over_pi_d2": float(ref["Y_cd_m2"] / np.pi),
        "B_plane_Lscot": float(1700 * cB[..., 1].mean()),
    }
    r["SP_render"] = r["A_specfilm_mean"]["Lscot"] / r["A_specfilm_mean"]["Y"]
    r["SP_reference"] = ref["Lscot_cd_m2"] / ref["Y_cd_m2"]
    res["spectra"][n] = r
    print(n, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "A_hdrfilm_xyz_mean_raw"}, default=float), flush=True)
json.dump(res, open(os.path.join(out, "ADAPTED_n4_emitter_units.json"), "w"), indent=1, default=float)
