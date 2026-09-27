#!/usr/bin/env python3
"""D2-A2b stage 2, exactly as d2/a2/PREREG_A2b_stage2.md (committed before this code). The unchanged Q99.9 guard:
s_hist is loaded from the committed d2/a2/run_A2b.py @ bacfd86 (ast segment, sha256 asserted), not retyped.
  tracks/temporal-glare-2009/py.sh d2/a2/run_A2b2.py   -> d2/a2/results_A2b2.json, d2/a2/work/{views,final}/"""
import ast, hashlib, json, math, os, re, subprocess
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
S_HIST_SHA = "7f7b37537f27425b8d8c2e96169d364730ac5eae5b6cc96e8395b3c6a7449edf"
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"; NEW_LINE = "S_H = s_hist(Ya, axname); Yreq = LO + (HI - LO) * S_H * Ya"
YW = np.array([0.2126, 0.7152, 0.0722]); GUARD = {}; WK = "d2/a2/work"; os.makedirs(f"{WK}/views", exist_ok=True)
res = {"prereg": "d2/a2/PREREG_A2b_stage2.md", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}

# --- the policy: identical code from bacfd86 ---
a2b = subprocess.run(["git", "show", "bacfd86:d2/a2/run_A2b.py"], capture_output=True, text=True, check=True).stdout
fn = [n for n in ast.parse(a2b).body if isinstance(n, ast.FunctionDef) and n.name == "s_hist"][0]; seg = ast.get_source_segment(a2b, fn)
assert hashlib.sha256(seg.encode()).hexdigest() == S_HIST_SHA; assert f'src.replace(SCALE_LINE, "{NEW_LINE}")' in a2b and f'SCALE_LINE = "{SCALE_LINE}"' in a2b
exec(seg)                                                                            # defines s_hist (uses np, GUARD)
res["policy"] = {"source": "bacfd86:d2/a2/run_A2b.py::s_hist", "sha256": S_HIST_SHA}


def codes(png):
    return oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3]


def cf(png):
    cv = codes(png).astype(float); v = cv / 65535; lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    Yd = 0.1 + 99.9 * (lin @ YW); mx = cv.max(-1)
    return {"lum_ceiling": float((Yd >= 99.9).mean()), "any_ch_ceiling": float((mx == 65535).mean()), "floor": float((mx == 0).mean())}, mx


def bi(png, frozen):
    return bool(np.array_equal(codes(png), codes(frozen)))


def expo(ax):
    return float(re.search(r"EXPOSURE=([0-9.eE+-]+)", open(f"d1/a_extract/.cache/{ax}/out.header").read()).group(1))


def row(ax, png, frozen):
    gd = GUARD[ax]; m, _ = cf(png); fm, _ = cf(frozen)
    r = {"frozen_EXPOSURE": expo(ax), "q": gd["q"], "s_hist": gd["s_hist"], "d_stops": math.log2(gd["s_hist"]), "active": gd["active"], **m,
         "frozen": fm}
    if not gd["active"]: r["BI"] = bi(png, frozen)
    return r


# --- views: hero, B, C through the frozen display code with the one change ---
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, NEW_LINE); a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(RAX=r_ax, S_H=S_H, H=H, W=W,')
gv = {"__name__": "views", "__file__": f"{REPO}/d1/display_r/run.py", "s_hist": s_hist}; exec(compile(src, "d1/display_r/run.py[A2b2]", "exec"), gv)
V = {"hero": ("n1/work/hero_cdm2.exr", "N1_hero", "n1/renders/final/hero.png"), "B": ("n1/work/view_B/view_cdm2.exr", "N1_B", "n1/renders/final/cam_B.png"),
     "C": ("n1/work/view_C/view_cdm2.exr", "N1_C", "n1/renders/final/cam_C.png")}
views = {}
for k, (inp, ax, frozen) in V.items():
    out = f"{WK}/views/{k}.png"; g, v = gv["run_image"](inp, ax, "yprio", out); r = row(ax, out, frozen)
    r["R3_extraction"] = {kk: v["RAX"][kk] for kk in ("C0_bit_identical", "C2_frac_ok", "C3_frac_ok")}
    r["R3_display_gates"] = {kk: g[kk] for kk in ("finite", "G1", "G2", "G3", "S-1", "S-2", "S-3")}
    r["R3_PASS"] = r["R3_extraction"]["C0_bit_identical"] and min(r["R3_extraction"]["C2_frac_ok"], r["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(r["R3_display_gates"].values())
    if k == "C":
        _, mx = cf(out); ys, xs = np.mgrid[0:mx.shape[0], 0:mx.shape[1]]; rr = np.hypot(xs + 0.5 - 961.0, ys + 0.5 - 153.0)
        r["HO3_lamp_head_code_above_annulus"] = float(mx[rr <= 3.0].max() - np.median(mx[(rr > 4.5) & (rr <= 7.0)]))
        r["HO_PASS"] = r["lum_ceiling"] <= 0.004442 and r["floor"] <= 0.0062 and r["HO3_lamp_head_code_above_annulus"] >= 1
    else:
        r["CF_PASS"] = r["lum_ceiling"] <= r["frozen"]["lum_ceiling"] and r["floor"] <= 0.0062
    views[k] = r; print(k, {kk: r[kk] for kk in ("q", "s_hist", "d_stops", "active", "lum_ceiling", "floor")}, flush=True)
res["views"] = views

# --- corpus: frozen d1/final/run.py text with the stated replacements ---
CODES, s2rows = {}, {}
FRZ = "d0/work/out/d1_pipeline/final"


def S2_CAP(n, p):
    CODES[f"{n}.png"] = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)       # = display_model.read_code
    s2rows[n] = row(f"S2/{n}", p, f"{FRZ}/S2__PHONE_SDR100_DARK/{n}.png"); os.remove(p)


fsrc = open("d1/final/run.py").read()
reps = [('OUTF = "d0/work/out/d1_pipeline/final"', f'OUTF = "{WK}/final"'),
        ('src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0]',
         'src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0].replace("' + SCALE_LINE + '", "' + NEW_LINE + '").replace("return g, dict(H=H, W=W,", "return g, dict(H=H, W=W, S_H=S_H,")'),
        ("Yexp = np.clip(LO + (HI - LO) * YA, LO, HI)", 'Yexp = np.clip(LO + (HI - LO) * v["S_H"] * YA, LO, HI)'),
        ("s2.append(gates(g, v))", 's2.append(gates(g, v)); S2_CAP(n, f"{OUTF}/S2__PHONE_SDR100_DARK/{n}.png")'),
        ('open("d1/final/acceptance.json", "w")', f'open("{WK}/acceptance_A2b2.json", "w")')]
for a_, b_ in reps:
    assert fsrc.count(a_) == 1, a_
    fsrc = fsrc.replace(a_, b_)
gf = {"__name__": "__main__", "__file__": f"{REPO}/d1/final/run.py", "s_hist": s_hist, "S2_CAP": S2_CAP}
exec(compile(fsrc, "d1/final/run.py[A2b2]", "exec"), gf)
acc = json.load(open(f"{WK}/acceptance_A2b2.json")); corpus = {}
for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    r = row(s, f"{WK}/final/{s}__PHONE_SDR100_DARK.png", f"{FRZ}/{s}__PHONE_SDR100_DARK.png")
    r["P"] = {k_: acc["stills"][s][k_] for k_ in acc["stills"][s] if k_.startswith("P-") or k_ in ("S1", "S3_bar_weber")}
    r["CF_PASS"] = r["any_ch_ceiling"] <= 0.0435 and r["floor"] <= 0.0062; corpus[s] = r
r = row("F1", f"{WK}/final/F1__PHONE_SDR100_DARK.png", f"{FRZ}/F1__PHONE_SDR100_DARK.png"); r["P"] = {k_: acc["F1"][k_] for k_ in acc["F1"] if k_.startswith("P-")}; corpus["F1"] = r
res["corpus"] = corpus; res["S2_frames_gates"] = acc["S2_frames"]; res["S2_per_frame"] = s2rows

# --- P-7: frozen d0 clip_metrics, unchanged, on in-memory frames ---
mt = open("d0/metrics.py").read().split('\nif __name__ == "__main__":')[0]; gm = {"__name__": "d0metrics", "__file__": f"{REPO}/d0/metrics.py"}
exec(compile(mt, "d0/metrics.py[defs]", "exec"), gm); gm["read_code"] = lambda p: CODES[os.path.basename(p)]
p7 = gm["clip_metrics"]([f"mem/S2__PHONE_SDR100_DARK/frame_{f:04d}.png" for f in range(1, 49)], "SDR100", "DARK")
p7["PASS"] = p7["mean_max_step_rel"] <= 0.02 and p7["sky_median_max_step_rel"] <= 0.02 and p7["frames_with_isolated_flash"] <= 1
res["P7"] = p7; print("P-7", p7, flush=True)

# --- summaries: BI, ND, table ---
sv = [r["s_hist"] for r in s2rows.values()]
res["S2_summary"] = {"s_hist_min_median_max": [min(sv), float(np.median(sv)), max(sv)], "frames_active": sum(r["active"] for r in s2rows.values()),
                     "BI_all_inactive": all(r.get("BI", True) for r in s2rows.values())}
allrows = {**{f"view_{k}": r for k, r in views.items()}, **corpus, **{f"S2/{n}": r for n, r in s2rows.items()}}
res["BI_PASS"] = all(r.get("BI", True) for r in allrows.values())
nat = {"hero": views["hero"]["active"], "B": views["B"]["active"], "C": views["C"]["active"], **{s: corpus[s]["active"] for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5")},
       "S2": res["S2_summary"]["frames_active"] > 0}
res["ND"] = {"active": nat, "PASS": not all(nat.values())}
res["visual_needed"] = [k for k, v_ in nat.items() if v_]
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(res, open("d2/a2/results_A2b2.json", "w"), indent=1, default=dflt)
print(json.dumps({k: res[k] for k in ("S2_summary", "BI_PASS", "ND", "visual_needed")}, indent=1, default=dflt))
