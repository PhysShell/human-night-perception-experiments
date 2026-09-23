"""NATIVE: run the official Mitsuba 3 quickstart (mitsuba-tutorials/quickstart/mitsuba_quickstart.ipynb)
unchanged except for the variant list: the notebook's llvm_ad_rgb fallback, plus scalar_spectral and
llvm_ad_spectral (llvm_spectral is not shipped in the PyPI wheel). Writes EXR+PNG and a stats JSON.
Usage: venv/bin/python n2_native_quickstart.py <mitsuba-tutorials dir> <outdir>"""
import sys, os, json, time
import numpy as np
import mitsuba as mi

tut, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
scene_path = os.path.join(tut, "scenes", "cbox.xml")
stats = {"mitsuba": mi.__version__, "scene": scene_path, "spp": 256, "runs": {}}
imgs = {}
for variant in ["llvm_ad_rgb", "scalar_spectral", "llvm_ad_spectral"]:
    mi.set_variant(variant)
    t0 = time.time()
    scene = mi.load_file(scene_path)
    img = mi.render(scene, spp=256)
    dt = time.time() - t0
    a = np.array(img)
    imgs[variant] = a
    mi.util.write_bitmap(os.path.join(out, f"NATIVE_cbox_{variant}.exr"), img)
    mi.util.write_bitmap(os.path.join(out, f"NATIVE_cbox_{variant}.png"), img)
    stats["runs"][variant] = {"seconds": round(dt, 1), "shape": list(a.shape),
                              "mean_rgb": a.reshape(-1, a.shape[-1]).mean(0).tolist(),
                              "finite": bool(np.isfinite(a).all())}
    print(variant, stats["runs"][variant], flush=True)
ref = imgs["llvm_ad_rgb"]
for v in ["scalar_spectral", "llvm_ad_spectral"]:
    stats["runs"][v]["rel_mean_diff_vs_rgb"] = float(np.abs(imgs[v].mean((0, 1)) - ref.mean((0, 1))).max() / ref.mean())
stats["rel_mean_diff_scalar_vs_llvm_spectral"] = float(np.abs(imgs["scalar_spectral"].mean((0,1)) - imgs["llvm_ad_spectral"].mean((0,1))).max() / ref.mean())
json.dump(stats, open(os.path.join(out, "NATIVE_cbox_stats.json"), "w"), indent=1)
