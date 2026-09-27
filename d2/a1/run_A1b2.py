#!/usr/bin/env python3
"""D2-A1b stage 2, exactly as the stage-2 addendum in d2/a1/PREREG_A1b.md (committed before this code): the unchanged
shoulder f(Y) = Y/(1+Y) on hero/B/C and the whole D1 corpus (stills, F1, 48 S2 frames + P-7). Builds the sheets too.
  tracks/temporal-glare-2009/py.sh d2/a1/run_A1b2.py   -> d2/a1/results_A1b2.json, d2/a1/renders/A1b2_sheet_*.png"""
import json, os, subprocess
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"
SHOULDER_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"
assert f'SHOULDER_LINE = "{SHOULDER_LINE}"' in open("d2/a1/run_A1b.py").read()                        # the stage-1 operator, unchanged
YW = np.array([0.2126, 0.7152, 0.0722]); WK = "d2/a1/work/A1b2"; FRZ = "d0/work/out/d1_pipeline/final"
for d_ in (f"{WK}/views", f"{WK}/s2keep", "d2/a1/renders"): os.makedirs(d_, exist_ok=True)
res = {"prereg": "d2/a1/PREREG_A1b.md (stage-2 addendum)", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}


def m(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    Yd = 0.1 + 99.9 * (np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4) @ YW); mx = cv.max(-1)
    return {"lum_ceiling": float((Yd >= 99.9).mean()), "any_ch_ceiling": float((mx == 65535).mean()), "floor": float((mx == 0).mean()), "median_Y_disp": float(np.median(Yd))}, mx


def row(png, frozen, Ya):
    s, mx = m(png); f, _ = m(frozen)
    r = {"Y_A_Q": {str(p): float(np.percentile(Ya, p)) for p in (50, 90, 99, 99.9)}, "frac_YA_gt_0.0101": float((Ya > 0.0101).mean()), "shoulder": s, "frozen": f}
    r["CF_PASS"] = s["lum_ceiling"] <= f["lum_ceiling"] and s["any_ch_ceiling"] <= max(f["any_ch_ceiling"], 0.043545) and s["floor"] <= max(f["floor"], 0.006250)
    return r, mx


# --- views ---
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, SHOULDER_LINE); a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, H=H, W=W,')
gv = {"__name__": "a1b2", "__file__": f"{REPO}/d1/display_r/run.py"}; exec(compile(src, "d1/display_r/run.py[A1b2]", "exec"), gv)
V = {"hero": ("n1/work/hero_cdm2.exr", "N1_hero", "n1/renders/final/hero.png"), "B": ("n1/work/view_B/view_cdm2.exr", "N1_B", "n1/renders/final/cam_B.png"),
     "C": ("n1/work/view_C/view_cdm2.exr", "N1_C", "n1/renders/final/cam_C.png")}
views = {}
for k, (inp, ax, frozen) in V.items():
    out = f"{WK}/views/{k}.png"; g, v = gv["run_image"](inp, ax, "yprio", out); r, mx = row(out, frozen, v["YA"])
    r["R3_extraction"] = {kk: v["RAX"][kk] for kk in ("C0_bit_identical", "C2_frac_ok", "C3_frac_ok")}
    r["R3_display_gates"] = {kk: g[kk] for kk in ("finite", "G1", "G2", "G3", "S-1", "S-2", "S-3")}
    r["R3_PASS"] = r["R3_extraction"]["C0_bit_identical"] and min(r["R3_extraction"]["C2_frac_ok"], r["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(r["R3_display_gates"].values())
    if k == "C":
        ys, xs = np.mgrid[0:mx.shape[0], 0:mx.shape[1]]; rr = np.hypot(xs + 0.5 - 961.0, ys + 0.5 - 153.0)
        r["HO3_lamp_head_code_above_annulus"] = float(mx[rr <= 3.0].max() - np.median(mx[(rr > 4.5) & (rr <= 7.0)]))
        r["HO_PASS"] = r["shoulder"]["lum_ceiling"] <= 0.004442 and r["shoulder"]["floor"] <= 0.0062 and r["HO3_lamp_head_code_above_annulus"] >= 1
    views[k] = r; print(k, r["shoulder"], r["CF_PASS"], r["R3_PASS"], flush=True)
res["views"] = views

# --- corpus via the frozen d1/final/run.py text ---
CODES, stills, s2rows = {}, {}, {}


def CAP_STILL(s, v):
    stills[s] = row(f"{WK}/{s}__PHONE_SDR100_DARK.png", f"{FRZ}/{s}__PHONE_SDR100_DARK.png", v["YA"])[0]


def CAP_S2(n, p, v):
    CODES[f"{n}.png"] = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)                  # = display_model.read_code
    s2rows[n] = row(p, f"{FRZ}/S2__PHONE_SDR100_DARK/{n}.png", v["YA"])[0]
    if n in ("frame_0001", "frame_0048"): os.replace(p, f"{WK}/s2keep/{n}.png")
    else: os.remove(p)


fsrc = open("d1/final/run.py").read()
reps = [('OUTF = "d0/work/out/d1_pipeline/final"', f'OUTF = "{WK}"'),
        ('src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0]',
         'src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0].replace("' + SCALE_LINE + '", "' + SHOULDER_LINE + '")'),
        ("Yexp = np.clip(LO + (HI - LO) * YA, LO, HI)", "Yexp = np.clip(LO + (HI - LO) * (np.maximum(YA, 0) / (1 + np.maximum(YA, 0))), LO, HI)"),
        ('acc["stills"][s] = r; print(s, r, flush=True)', 'acc["stills"][s] = r; print(s, r, flush=True); CAP_STILL(s, v)'),
        ("s2.append(gates(g, v))", 's2.append(gates(g, v)); CAP_S2(n, f"{OUTF}/S2__PHONE_SDR100_DARK/{n}.png", v)'),
        ('open("d1/final/acceptance.json", "w")', f'open("{WK}/acceptance_A1b2.json", "w")')]
for a_, b_ in reps:
    assert fsrc.count(a_) == 1, a_
    fsrc = fsrc.replace(a_, b_)
gf = {"__name__": "__main__", "__file__": f"{REPO}/d1/final/run.py", "CAP_STILL": CAP_STILL, "CAP_S2": CAP_S2}
exec(compile(fsrc, "d1/final/run.py[A1b2]", "exec"), gf)
acc = json.load(open(f"{WK}/acceptance_A1b2.json"))
for s in stills: stills[s]["P"] = {k_: acc["stills"][s][k_] for k_ in acc["stills"][s] if k_.startswith("P-") or k_ in ("S1", "S3_bar_weber")}
res["stills"] = stills; res["F1"] = {k_: acc["F1"][k_] for k_ in acc["F1"] if k_.startswith("P-") or k_ == "monotone"}
res["S2_frames_gates"] = acc["S2_frames"]; res["S2_per_frame"] = s2rows
res["S2_CF_PASS"] = all(r["CF_PASS"] for r in s2rows.values())

# --- P-7 ---
mt = open("d0/metrics.py").read().split('\nif __name__ == "__main__":')[0]; gm = {"__name__": "d0metrics", "__file__": f"{REPO}/d0/metrics.py"}
exec(compile(mt, "d0/metrics.py[defs]", "exec"), gm); gm["read_code"] = lambda p: CODES[os.path.basename(p)]
p7 = gm["clip_metrics"]([f"mem/S2__PHONE_SDR100_DARK/frame_{f:04d}.png" for f in range(1, 49)], "SDR100", "DARK")
p7["PASS"] = p7["mean_max_step_rel"] <= 0.02 and p7["sky_median_max_step_rel"] <= 0.02 and p7["frames_with_isolated_flash"] <= 1; res["P7"] = p7
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(res, open("d2/a1/results_A1b2.json", "w"), indent=1, default=dflt)
print("P-7", p7, flush=True)

# --- sheets: frozen vs shoulder, every natural scene ---
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(float) / 65535


def pair_sheet(dst, pairs):
    ims = [(c, ld(a_), ld(b_)) for c, a_, b_ in pairs]; pw = 470; hs = [pw * im.shape[0] / im.shape[1] for _, im, _ in ims]
    H = sum(h + 40 for h in hs) + 20; fig = plt.figure(figsize=(9.6, H / 100), dpi=100, facecolor="black"); top = 10
    for (c, fz, sh), h in zip(ims, hs):
        top += 30
        for j, (lab, im) in enumerate((("frozen D1", fz), ("shoulder", sh))):
            ax = fig.add_axes([(10 + j * (pw + 10)) / 960, 1 - (top + h) / H, pw / 960, h / H]); ax.imshow(im, interpolation="lanczos"); ax.axis("off")
            ax.set_title(f"{c}: {lab}", color="w", fontsize=9)
        top += h + 10
    fig.savefig(dst, facecolor="black")


pair_sheet("d2/a1/renders/A1b2_sheet_views.png", [(k, V[k][2], f"{WK}/views/{k}.png") for k in ("hero", "B", "C")])
pair_sheet("d2/a1/renders/A1b2_sheet_corpus.png", [(s, f"{FRZ}/{s}__PHONE_SDR100_DARK.png", f"{WK}/{s}__PHONE_SDR100_DARK.png") for s in ("S0", "S3_bar", "S3_nobar", "S4", "S5")])
gap = np.zeros((6, 960, 3)); blocks = []
for f in (1, 48):
    for lab, p in (("frozen D1", f"{FRZ}/S2__PHONE_SDR100_DARK/frame_{f:04d}.png"), ("shoulder", f"{WK}/s2keep/frame_{f:04d}.png")):
        im = ld(p); blocks.append((f"S2 frame {f}: {lab}: full frame | band rows 100-420 1:1, left | right",
                                   np.concatenate([im.reshape(410, 2, 960, 2, 3).mean((1, 3)), gap, im[100:420, :960], gap, im[100:420, 960:]])))
lab_h = 26; H = sum(b.shape[0] + lab_h for _, b in blocks); canvas = np.zeros((H, 960, 3)); y = 0; ys_ = []
for c, b in blocks:
    ys_.append(y); canvas[y + lab_h:y + lab_h + b.shape[0]] = b; y += lab_h + b.shape[0]
fig = plt.figure(figsize=(9.6, H / 100), dpi=100, facecolor="black"); fig.figimage(canvas, 0, 0, origin="upper")
for (c, _), y0 in zip(blocks, ys_): fig.text(0.01, 1 - (y0 + 18) / H, c, color="w", fontsize=10)
fig.savefig("d2/a1/renders/A1b2_sheet_S2.png", dpi=100, facecolor="black")
print("sheets ok")
