#!/usr/bin/env python3
"""D0 measurements on the pattanaik00 outputs, WITHOUT modifying d0/: imports d0/metrics.py (still_metrics,
clip_metrics; pdet re-implemented here only to keep its temporary files under d1/pattanaik00/.cache, same HDR-VDP call).
Every PNG is decoded by d0/display_model.py with its scenario -> emitted cd/m^2.
  nix develop -c python3 d1/pattanaik00/measure.py      -> d1/pattanaik00/metrics.jsonl, key_numbers.json
"""
import glob, json, os, subprocess, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, "d0")
import metrics as M                                       # noqa: E402  (d0/metrics.py, unmodified)
from display_model import decode, read_code, save_exr     # noqa: E402

HERE = "d1/pattanaik00"; OUT = f"{HERE}/.cache/out"; TMPM = f"{HERE}/.cache/metrics_tmp"


def pdet(bar_png, nobar_png, lum, amb, tag):
    """= d0/metrics.py pdet(), temp dir moved to d1/pattanaik00/.cache"""
    res = {}
    t = f"{TMPM}/{tag}"; os.makedirs(t, exist_ok=True)
    for nm, p in (("bar", bar_png), ("nobar", nobar_png)):
        save_exr(f"{t}/{nm}.exr", decode(read_code(p), lum, amb)[1])
    for ev, mtf in (("EVAL_VIEWER", "hdrvdp"), ("EVAL_OFF", "none")):
        subprocess.run(f"tracks/hdrvdp3/run_hdrvdp.sh {t}/bar.exr {t}/nobar.exr PHONE {t}/{ev} --display none --mtf {mtf} --tasks side-by-side",
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            txt = open(f"{t}/{ev}/run.json").read(); res[f"P_det_bar_{ev}"] = float(txt.split('"side-by-side":{"P_det":')[1].split(",")[0])
        except Exception:
            res[f"P_det_bar_{ev}"] = None
    subprocess.run(["rm", "-rf", t])
    return res


def main():
    runs = {(r["config"], r["scene"], r["luminance"]): r["label"] for r in json.load(open(f"{HERE}/runs.json"))["runs"]}
    out = open(f"{HERE}/metrics.jsonl", "w")
    for cfgdir in sorted(glob.glob(f"{OUT}/*/")):
        cfg = os.path.basename(cfgdir.rstrip("/"))
        for p in sorted(glob.glob(f"{cfgdir}*.png")):
            mm = M.PAT.search(os.path.basename(p)); d = mm.groupdict(); lum = d["lum"]
            code = read_code(p); XYZ, _ = decode(code, lum, d["amb"])
            row = {"donor": "pattanaik00", "config": cfg, "label": runs.get((cfg, d["scene"], lum)), **d, "file": p,
                   **M.still_metrics(XYZ, code, d["scene"], lum, M.scene_ref(d["scene"]))}
            if d["scene"] == "S3_bar":
                nb = p.replace("S3_bar__", "S3_nobar__")
                if os.path.exists(nb):
                    row.update(pdet(p, nb, lum, d["amb"], f"{cfg}_{lum}"))
                    Y = XYZ[..., 1]; mk = M.masks("S3")
                    row["bar_weber_displayed"] = float((Y[mk["beside_bar"]].mean() - Y[mk["bar"]].mean()) / max(Y[mk["beside_bar"]].mean(), 1e-12))
            out.write(json.dumps(row) + "\n"); out.flush(); print(cfg, os.path.basename(p), flush=True)
        for dd in sorted(glob.glob(f"{cfgdir}S2__*/")):
            d = M.PAT.search(os.path.basename(dd.rstrip("/"))).groupdict()
            frames = sorted(glob.glob(f"{dd}frame_*.png"))
            out.write(json.dumps({"donor": "pattanaik00", "config": cfg, "label": runs.get((cfg, "S2", "SDR100,BRIGHT500 (stats)")), **d,
                                  "file": dd, **M.clip_metrics(frames, d["lum"], d["amb"])}) + "\n"); out.flush()
            print(cfg, "S2", flush=True)
    out.close()


if __name__ == "__main__":
    main()
