#!/usr/bin/env python3
"""D2-G1 gates G0.1-G0.3, exactly as d2/g1/PREREG_D2_G1.md + amendment 1 (committed before this code). No render.
  tracks/temporal-glare-2009/py.sh d2/g1/g0.py   -> d2/g1/results_G0.json
G0.1 pure math; G0.2/G0.3 call the frozen A through the -I copies (nix develop), the frozen display and the A1b shoulder."""
import json, math, os, re, shutil, subprocess
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
WK = "d2/g1/work"; os.makedirs(WK, exist_ok=True); ENV = dict(os.environ, PATH="/root/.nix-profile/bin:" + os.environ["PATH"])
YW = np.array([0.2126, 0.7152, 0.0722]); P_PIG = 0.5; VIS = 25_000.0; EYE = (0.5, 0.0, 1.7); RADIUS = 0.105; PPD_PHONE = 73.0
res = {"prereg": "d2/g1/PREREG_D2_G1.md (+ amendment 1)", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
save = lambda: json.dump(res, open("d2/g1/results_G0.json", "w"), indent=1, default=dflt)

# ---------- geometry, scene, masks (as T0 / A1b) ----------
H_, W_ = 820, 1920; F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W_]; dx, dy = xs + 0.5 - 960, ys + 0.5 - 410
below = dy > 0.5; t_ = np.where(below, EYE[2] / np.maximum(dy / F, 1e-9), np.nan); gx = EYE[0] + t_ * dx / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)
rgb = oiio.ImageBuf("n1/roadline/work/A6/canonical_cdm2.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); L = rgb @ YW
sky_med = float(np.median(L[~below])); sky = ~below & (L <= 2 * sky_med)
lamps = json.load(open("n1/roadline/work/A/lamps.json"))["lamps"]
T = lambda d: np.exp(-3.912 * d / VIS)


def ray(px, py):
    v = np.stack([(np.asarray(px, float) + 0.5 - 960) / F, np.ones_like(np.asarray(px, float)), (410 - (np.asarray(py, float) + 0.5)) / F], -1)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def cie146(th, A):                                                  # th in degrees; caller clamps / masks the domain
    return 10 / th ** 3 + (5 / th ** 2 + 0.1 * P_PIG / th) * (1 + (A / 62.5) ** 4) + 0.0025 * P_PIG


def veil_T0b(A):                                                    # the T0b point-lamp veil map (control vs results_T0.json)
    pix = ray(xs, ys); v = np.zeros((H_, W_))
    for l in lamps:
        u = ray(l["px"][0] - 0.5, l["px"][1] - 0.5); c = np.clip(pix @ u, -1, 1); th = np.degrees(np.arccos(c))
        v += float(T(l["r_m"])) * l["I_table_cd"] / l["r_m"] ** 2 * np.maximum(c, 0) * cie146(np.maximum(th, 0.1), A)
    return v


VEIL = {A: veil_T0b(A) for A in (25, 70)}
res["V_control"] = {str(A): {"centre": float(VEIL[A][410, 960]), "T0b": ref} for A, ref in ((25, 0.08378759548543854), (70, 0.1903839326375625))}
res["V_control"]["PASS"] = all(abs(res["V_control"][k]["centre"] / res["V_control"][k]["T0b"] - 1) <= 1e-6 for k in ("25", "70")); assert res["V_control"]["PASS"]
rng = np.random.default_rng(0); TG = {}
for name, m in (("road", road), ("field", field), ("sky", sky)):
    idx = np.flatnonzero(m.ravel()); TG[name] = rng.choice(idx, 500, replace=False)

# ---------- G0.1: WORLD inventory, veil by category at the targets ----------
diam = {l["d"]: 2 * RADIUS / l["r_m"] * F for l in lamps if l["in_frame"]}
ap = np.zeros((H_, W_), bool)
for l in lamps:
    if l["in_frame"]: ap |= np.hypot(xs + 0.5 - l["px"][0], ys + 0.5 - l["px"][1]) <= diam[l["d"]] / 2 + 1.5
om_px = (F / np.sqrt(F ** 2 + dx ** 2 + dy ** 2)) ** 3 / F ** 2                     # pinhole pixel solid angle (sr)
Eb = np.where(ap, 0.0, L * om_px).reshape(205, 4, 480, 4).sum((1, 3)).ravel()         # extended blocks, lamp apertures excluded
bx, by = np.meshgrid(np.arange(480) * 4 + 1.5, np.arange(205) * 4 + 1.5); Bdir = ray(bx.ravel(), by.ravel()); B_SIZE = math.degrees(4 / F)
Lb_ground = float(L[-10:].max())
az, el = np.meshgrid(np.radians(np.arange(-179.75, 180, 0.5)), np.radians(np.arange(-89.75, 90, 0.5)))
Odir = np.stack([np.sin(az) * np.cos(el), np.cos(az) * np.cos(el), np.sin(el)], -1).reshape(-1, 3)
inside = (Odir[:, 1] > 0) & (np.abs(Odir[:, 0] / np.maximum(Odir[:, 1], 1e-9) * F) <= 960) & (np.abs(Odir[:, 2] / np.maximum(Odir[:, 1], 1e-9) * F) <= 410)
Oom = (np.cos(el) * np.radians(0.5) ** 2).ravel(); OL = np.where(Odir[:, 2] < 0, Lb_ground, sky_med)
keep = ~inside; Odir, OE = Odir[keep], (OL * Oom)[keep]
inv = [{"source_id": f"lamp_{l['d']}m", "kind": "world point", "E_axis_lx": float(T(l["r_m"])) * l["I_table_cd"] / l["r_m"] ** 2,
        "angular_size_deg": math.degrees(2 * RADIUS / l["r_m"]), "inside_camera_frame": l["in_frame"], "inside_display": l["in_frame"]} for l in lamps]
inv += [{"source_id": "extended_in_frame_blocks", "kind": "world extended (4x4 px blocks, lamp apertures excluded)", "E_axis_lx_total": float(Eb.sum()),
         "angular_size_deg": B_SIZE, "inside_camera_frame": True, "inside_display": True},
        {"source_id": "extended_off_frame_bound", "kind": "world extended, conservative bound (ground L<=max of bottom 10 rows; sky median)",
         "L_ground_bound": Lb_ground, "L_sky": sky_med, "E_axis_lx_total": float(OE.sum()), "angular_size_deg": 0.5, "inside_camera_frame": False, "inside_display": False}]
res["G01_inventory"] = inv


def contrib(tdir, sdir, E, A, size_deg, offframe, extended):
    """per target: veil components; sources as rows. returns dict of (n_targets,) arrays."""
    c = np.clip(tdir @ sdir.T, -1, 1); th = np.degrees(np.arccos(c)); dom = th <= 100
    v = np.where(dom, E[None, :] * np.maximum(c, 0) * cie146(np.maximum(th, 0.1), A), 0.0)
    pv = (th >= 0.1) & (np.asarray(size_deg)[None, :] <= th / 10)                     # our operational point-source criterion
    uns = (th < 0.1) | np.asarray(offframe)[None, :] | ~pv
    o = {"total": v.sum(1), "lt0.1": (v * (th < 0.1)).sum(1), "b0.1_1": (v * ((th >= 0.1) & (th < 1))).sum(1),
         "b1_30": (v * ((th >= 1) & (th < 30))).sum(1), "b30_100": (v * (th >= 30)).sum(1),
         "offframe": (v * np.asarray(offframe)[None, :]).sum(1), "extended": (v * np.asarray(extended)[None, :]).sum(1), "unsupported": (v * uns).sum(1),
         "ext_self_lt0.1": (v * ((th < 0.1) & np.asarray(extended)[None, :])).sum(1)}                  # diagnostic: the fixated region itself
    o["E_beyond_100deg"] = (np.where(~dom, E[None, :] * np.maximum(c, 0), 0.0)).sum(1); return o


def accumulate(acc, o):
    for k, x in o.items(): acc[k] = acc.get(k, 0) + x


g01 = {}
for A in (25, 70):
    g01[str(A)] = {}
    for name, idx in TG.items():
        tdir = ray(xs.ravel()[idx], ys.ravel()[idx]); acc, acc_nb = {}, {}
        lp = np.array([ray(l["px"][0] - 0.5, l["px"][1] - 0.5) for l in lamps]); lE = np.array([x["E_axis_lx"] for x in inv[:len(lamps)]])
        o = contrib(tdir, lp, lE, A, [x["angular_size_deg"] for x in inv[:len(lamps)]], [not l["in_frame"] for l in lamps], [False] * len(lamps)); accumulate(acc, o); accumulate(acc_nb, o)
        for s0 in range(0, len(Eb), 20000):
            sl = slice(s0, s0 + 20000); n = len(Eb[sl])
            o = contrib(tdir, Bdir[sl], Eb[sl], A, [B_SIZE] * n, [False] * n, [True] * n); accumulate(acc, o); accumulate(acc_nb, o)
        for s0 in range(0, len(OE), 20000):
            sl = slice(s0, s0 + 20000); n = len(OE[sl])
            accumulate(acc, contrib(tdir, Odir[sl], OE[sl], A, [0.5] * n, [True] * n, [True] * n))
        Lt = L.ravel()[idx]; sh = lambda a, k: float(np.median(a[k] / a["total"]))
        r = {"median_veil_over_scene": float(np.median(acc["total"] / Lt)), "median_veil_cd_m2": float(np.median(acc["total"])),
             "shares_median": {k: sh(acc, k) for k in ("lt0.1", "b0.1_1", "b1_30", "b30_100", "offframe", "extended", "unsupported")},
             "unsupported_share_without_offframe_bound": sh(acc_nb, "unsupported"), "median_veil_without_bound_cd_m2": float(np.median(acc_nb["total"])),
             "median_E_beyond_100deg_lx": float(np.median(acc["E_beyond_100deg"])),
             "diag_excluding_extended_self_lt0.1": {"unsupported_share": float(np.median((acc["unsupported"] - acc["ext_self_lt0.1"]) / (acc["total"] - acc["ext_self_lt0.1"]))),
                                                    "median_veil_over_scene": float(np.median((acc["total"] - acc["ext_self_lt0.1"]) / Lt)),
                                                    "share_of_total_from_ext_self": sh(acc, "ext_self_lt0.1")}}
        r["relevant"] = r["median_veil_over_scene"] >= 0.01
        r["KILL_frame_pixel_arch"] = r["relevant"] and r["shares_median"]["unsupported"] > 0.10
        r["KILL_only_with_bound"] = r["KILL_frame_pixel_arch"] and r["unsupported_share_without_offframe_bound"] <= 0.10
        r["B1_needed_lt0.1"] = r["relevant"] and r["shares_median"]["lt0.1"] > 0.10
        g01[str(A)][name] = r
g01["KILL_frame_pixel_arch"] = any(g01[a][n]["KILL_frame_pixel_arch"] for a in ("25", "70") for n in TG)
g01["KILL_only_with_bound"] = g01["KILL_frame_pixel_arch"] and all(g01[a][n]["KILL_only_with_bound"] or not g01[a][n]["KILL_frame_pixel_arch"] for a in ("25", "70") for n in TG)
res["G01"] = g01; save(); print("G0.1", json.dumps(g01, indent=1, default=dflt)[:3000], flush=True)

# ---------- G0.2 / G0.3: pcond -I runs ----------
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"
assert 'SHOULDER_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"' in open("d2/a1/run_A1b.py").read()
for fz, cp, R in (("d1/pipeline/axis_a.sh", "d2/g1/axis_a_I.sh", [('OUT=$(realpath -m "$3")', 'OUT=$(realpath -m "$3") HIST=$(realpath "$4")'),
                                                                    ('pcond -s -c -p $REC709 inX.hdr > out.hdr', 'pcond -s -c -I -p $REC709 inX.hdr < "$HIST" > out.hdr')]),
                  ("d1/a_extract/axis_a_x.sh", "d2/g1/axis_a_x_I.sh", [('O=$(realpath -m "$3")', 'O=$(realpath -m "$3") HIST=$(realpath "$4")'),
                                                                        ('pcond -s -c -p $REC709 -x map.txt inX.hdr > out.hdr', 'pcond -s -c -I -p $REC709 -x map.txt inX.hdr < "$HIST" > out.hdr'),
                                                                        ('pcond -s -p $REC709 inX.hdr > s.hdr', 'pcond -s -I -p $REC709 inX.hdr < "$HIST" > s.hdr')])):
    t = open(fz).read()
    for a_, b_ in R: assert t.count(a_) == 1; t = t.replace(a_, b_)
    assert t == open(cp).read(), cp                                                    # the copies differ exactly by -I + stdin histogram
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, "Yreq = LO + (HI - LO) * (Ya if MODE == 'frozen' else np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))")
src = src.replace('return g, dict(H=H, W=W,', 'return g, dict(RAX=r_ax, H=H, W=W,')
gv = {"__name__": "g1", "__file__": f"{REPO}/d1/display_r/run.py", "MODE": "frozen"}; exec(compile(src, "d1/display_r/run.py[G1]", "exec"), gv)
a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)


def wexr(path, lum_add):
    out = rgb + lum_add[..., None]; o = oiio.ImageBuf(oiio.ImageSpec(W_, H_, 3, oiio.FLOAT))
    o.set_pixels(oiio.ROI(0, W_, 0, H_, 0, 1, 0, 3), np.ascontiguousarray(out, np.float32)); o.write(path)


def disp(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    return 0.1 + 99.9 * (np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4) @ YW)


HCACHE = {}


def run(tag, content_add, adapt_add, hkey):
    """content = L + content_add, adaptation histogram from L + adapt_add; returns EXPOSURE, C1/C2/presence, Y_disp maps."""
    hk = hkey
    if hk not in HCACHE:
        wexr(f"{WK}/adapt.exr", adapt_add); hp = f"{WK}/h{len(HCACHE)}.hist"
        subprocess.run(["nix", "develop", "-c", "d2/g1/hist.sh", f"{WK}/adapt.exr", "60", hp], check=True, env=ENV, capture_output=True); os.remove(f"{WK}/adapt.exr"); HCACHE[hk] = hp
    hp = HCACHE[hk]; ax = f"G1_{tag}"; wexr(f"{WK}/c.exr", content_add)
    subprocess.run(["nix", "develop", "-c", "d2/g1/axis_a_I.sh", f"{WK}/c.exr", "60", f"d1/pipeline/.cache/A/{ax}.exr", hp], check=True, env=ENV, capture_output=True)
    subprocess.run(["nix", "develop", "-c", "d2/g1/axis_a_x_I.sh", f"{WK}/c.exr", "60", f"d1/a_extract/.cache/{ax}", hp], check=True, env=ENV, capture_output=True)
    hdr = open(f"d1/a_extract/.cache/{ax}/out.header").read(); m = re.search(r"EXPOSURE=([0-9.eE+-]+)", hdr)
    ev = {"EXPOSURE": float(m.group(1)) if m else None}; Y = {}
    for mode in ("frozen", "shoulder"):
        gv["MODE"] = mode; png = f"{WK}/{mode}.png"; g, v = gv["run_image"](f"{WK}/c.exr", ax, "yprio", png)
        Yd = disp(png); rows = ns["display_rows"](png); os.remove(png); Y[mode] = Yd
        ev[mode] = {"road_lum_ceiling": float((Yd[road] >= 99.9).mean()), "C0": v["RAX"]["C0_bit_identical"], "tone_map_mode": v["RAX"]["tone_map"]["mode"],
                    "present": {d_: rows[d_]["present"] for d_ in rows}}
    ev["C1"] = ev["frozen"]["road_lum_ceiling"] >= 0.5; ev["C2"] = ev["shoulder"]["road_lum_ceiling"] <= 0.001
    shutil.rmtree(f"d1/a_extract/.cache/{ax}"); os.remove(f"d1/pipeline/.cache/A/{ax}.exr"); os.remove(f"{WK}/c.exr")
    print(tag, {k: ev[k] for k in ("EXPOSURE", "C1", "C2")}, flush=True); return ev, Y


ZERO = np.zeros((H_, W_)); g02 = {}
ev, _ = run("ctrl_a0", ZERO, ZERO, "L"); g02["control_alpha0"] = {"EXPOSURE": ev["EXPOSURE"], "frozen_ref": 444.77, "rel": ev["EXPOSURE"] / 444.77 - 1}
g02["control_alpha0"]["PASS"] = abs(g02["control_alpha0"]["rel"]) <= 0.05; res["G02"] = g02; save()
if not g02["control_alpha0"]["PASS"]:
    res["G02"]["INVALID"] = "alpha=0 -I path does not reproduce the frozen EXPOSURE within 5 %: G0.2/G0.3 not evaluated"; save(); raise SystemExit(0)

# G0.3 display geometry (phone, small-angle), 4x4 display blocks
ODISP = (math.pi / 180 / PPD_PHONE) ** 2; dbx, dby = (np.arange(480) * 4 + 1.5 - 960) / PPD_PHONE, (410 - (np.arange(205) * 4 + 1.5)) / PPD_PHONE
DB = np.stack(np.meshgrid(dbx, dby), -1).reshape(-1, 2)


def vscreen(Yd, A, idx):
    Eblk = (Yd * ODISP).reshape(205, 4, 480, 4).sum((1, 3)).ravel(); tx = (xs.ravel()[idx] + 0.5 - 960) / PPD_PHONE; ty = (410 - (ys.ravel()[idx] + 0.5)) / PPD_PHONE
    th = np.hypot(tx[:, None] - DB[None, :, 0], ty[:, None] - DB[None, :, 1]); c = np.cos(np.radians(th))
    dom = (th >= 0.1) & (th <= 100)
    return (np.where(dom, Eblk[None] * c * cie146(np.maximum(th, 0.1), A), 0).sum(1), np.where(th < 0.1, Eblk[None] * c * cie146(0.1, A), 0).sum(1))


g03 = {"rows": {}}
for A in (25, 70):
    V = VEIL[A]; g02[str(A)] = {}
    for alpha in (0.0, 0.08, 1.0):
        ad = ZERO if alpha == 0 else alpha * V
        hk = "L" if alpha == 0 else f"A{A}_a{alpha}"
        ev_w, Yw = run(f"A{A}_a{alpha}_with", V, ad, hk); ev_o, Yo = run(f"A{A}_a{alpha}_without", ZERO, ad, hk)
        g02[str(A)][str(alpha)] = {"with": ev_w, "without_same_mapping": ev_o}
        for pipe in ("frozen", "shoulder"):
            row = {}
            for name, idx in TG.items():
                dY = (Yw[pipe] - Yo[pipe]).ravel()[idx]; ok = dY > 1e-6; vs, vs_lt = vscreen(Yw[pipe], A, idx)
                row[name] = {"relevant_region": g01[str(A)][name]["relevant"], "n_valid": int(ok.sum()), "n_excluded_dY_le_1e-6": int((~ok).sum()),
                             "r_median": float(np.median(vs[ok] / dY[ok])) if ok.any() else None, "median_dYsim": float(np.median(dY)),
                             "median_Vscreen": float(np.median(vs)), "median_Vscreen_lt0.1_indicator": float(np.median(vs_lt))}
            g03["rows"][f"A{A}_a{alpha}_{pipe}"] = row
        res["G02"] = g02; res["G03"] = g03; save()
for A in ("25", "70"):
    a8, a1 = g02[A]["0.08"]["with"], g02[A]["1.0"]["with"]
    g02[A]["differs_0.08_vs_1"] = {k: a8[k] != a1[k] for k in ("C1", "C2")} | {f"present_{p}": a8[p]["present"] != a1[p]["present"] for p in ("frozen", "shoulder")}
g02["KILL_one_alpha_convention"] = any(any(g02[A]["differs_0.08_vs_1"].values()) for A in ("25", "70"))
gated = [(k, n, v["r_median"]) for k, row in g03["rows"].items() if "_a0.0_" not in k for n, v in row.items() if v["relevant_region"] and v["r_median"] is not None]
g03["r"] = max(x[2] for x in gated) if gated else None; g03["r_argmax"] = max(gated, key=lambda x: x[2])[:2] if gated else None
g03["verdict"] = None if g03["r"] is None else ("negligible" if g03["r"] < 0.01 else "bounded correction" if g03["r"] < 0.10 else "KILL")

# report-only per-source r_E,i and r_V,i on the no-glare display images
rep = {}
for pipe, png in (("frozen", "n1/roadline/renders/A2_canonical_final.png"), ("shoulder", "d2/a1/renders/roadline_A1b.png")):
    Yd = disp(png); rep[pipe] = {}
    for l in lamps:
        if not l["in_frame"]: continue
        cx, cy = l["px"]; rap = diam[l["d"]] / 2 + 1.5; rr = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
        bg = float(np.median(Yd[(rr > rap + 1) & (rr <= rap + 3.5)])); Ed = float(((Yd - bg) * (rr <= rap)).sum() * ODISP)
        Er = float(T(l["r_m"])) * l["I_table_cd"] / l["r_m"] ** 2; idx = TG["road"]
        th_s = np.degrees(np.arccos(np.clip(ray(xs.ravel()[idx], ys.ravel()[idx]) @ ray(cx - 0.5, cy - 0.5), -1, 1)))
        th_d = np.hypot((xs.ravel()[idx] + 0.5 - cx) / PPD_PHONE, (ys.ravel()[idx] + 0.5 - cy) / PPD_PHONE)
        rV = np.median((Ed * cie146(np.maximum(th_d, 0.1), 25)) / (Er * cie146(np.maximum(th_s, 0.1), 25)))
        rep[pipe][str(l["d"])] = {"E_disp_lx": Ed, "E_real_lx": Er, "r_E": Ed / Er, "r_V_road_targets_A25": float(rV)}
g03["per_source_report"] = rep
# whole-screen illuminance diagnostic (not gated)
g03["whole_screen_E_lx_diag"] = {p: float((disp(png) * ODISP).sum()) for p, png in (("frozen", "n1/roadline/renders/A2_canonical_final.png"), ("shoulder", "d2/a1/renders/roadline_A1b.png"))}
res["G02"] = g02; res["G03"] = g03
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout; save()
for h in HCACHE.values(): os.remove(h)
print(json.dumps({"G01_KILL": g01["KILL_frame_pixel_arch"], "G01_only_with_bound": g01["KILL_only_with_bound"], "G02_KILL": g02["KILL_one_alpha_convention"],
                  "G03_r": g03["r"], "G03_argmax": g03["r_argmax"], "G03": g03["verdict"]}, indent=1, default=dflt))
