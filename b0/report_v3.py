#!/usr/bin/env python3
"""B0 v3 report: the achromatic B0-optics layer split by role (b0/README.md "Roles").
  RETINAL TARGETS   what a model eye puts on the retina for the physical stimulus. Two routes that must
                    agree for the same optics: donor optics applied, evaluator optics OFF, 73 px/deg
                    (sweep_ach RETINAL_TARGET), and the evaluator's own optics on the physical stimulus at
                    146 px/deg (sweep_world_ach). ISET 550 nm has only the first route.
  DISPLAY ENCODINGS the image D shown on the phone through the frozen pcond stack, judged by the viewer's
                    eye at the phone (EVAL_VIEWER, HDR-VDP MTF) and, as a diagnostic, with evaluator optics
                    OFF. Retinal-forward images shown on the display are PSF x PSF (informational rows).
  GAP               the inverse problem: |P_det(viewer_eye(D)) - P_det(target_retina)| per target.
All P_det are HDR-VDP-3 side-by-side detection of the trunk: a diagnostic under HDR-VDP's observer model,
not a measured human probability. Vangorp L_la likewise (HDR-VDP local adaptation, fitted 1-5000 cd/m^2).
  tracks/temporal-glare-2009/py.sh b0/report_v3.py -> b0/results/b0_v3_tables.md, sweep_ach_curves.png
"""
import glob, json, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = json.load(open("b0/results/sweep_ach.json"))
K = np.geomspace(0.1, 100, 31); E1 = 800 / 3000 ** 2
COLS = [0, 10, 20, 30]                                            # x0.1, x1, x10, x100
ser = {}
for r in rows:
    ser.setdefault(r["variant"], {})[int(np.argmin(abs(K - r["k"])))] = r
world = {}
for f in glob.glob("b0/out/sweep_world_ach/w*_*/run.json"):
    m = re.search(r"w(\d+)_(cie|hdrvdp)", f); t = open(f).read()
    try: world[(m.group(2), int(m.group(1)))] = float(t.split('"side-by-side":{"P_det":')[1].split(",")[0])
    except Exception: pass
NAME = {"V0_none": "no optics (physical stimulus)", "V1_iset": "ISETBio wvf human, 550 nm, 6 mm, ZERO_DEFOCUS_550",
        "V2_hdrvdpmtf": "HDR-VDP-3 eye MTF", "V3_cie99": "HDR-VDP 3.0.7 otf_cie99 (1-D transform used as 2-D OTF: NOT CIE 135/1), age 24",
        "V4_spencer": "Spencer 1995 via Blender Fog Glow", "V5_temporal": "Temporal Glare 2009 (Frisvad demo), frame 1"}
wl = lambda v, i: " wl" if ser[v][i]["plateau_window_limited"] else ""   # glare cut at the demo window: P_det too
f3 = lambda x: "n/a" if x is None else f"{max(x, 0.0):.3f}"            # HDR-VDP returns ~-1e-5 for "none"
hdr = "| " + " | ".join(f"x{K[i]:.3g} ({K[i] * E1:.1e} lx)" for i in COLS) + " |"
sep = "|---" * (len(COLS) + 2) + "|"
RL = {"V1_iset": "WAVEFRONT", "V2_hdrvdpmtf": "STRAYLIGHT", "V3_cie99": "STRAYLIGHT", "V0_none": "none"}
out = ["## RETINAL TARGETS (achromatic B0-optics; trunk P_det, HDR-VDP-3 observer model)", "",
       "WAVEFRONT = aberration optics (central PSF); STRAYLIGHT = low-frequency scatter / disability-glare veil only "
       "(no diffraction, no chromatic aberration). The otf_cie99 rows are a donor defect kept for the record "
       "(b0/cie_otf_check.py); the 2-D CIE 135/1 row is the CIE straylight target. ISET's wavefront core alone puts "
       "~20x less light at the trunk than straylight does; a complete target needs both (B1).", "",
       "| target (observer model X) | kind | route " + hdr, "|---" * (len(COLS) + 3) + "|"]
for v in ("V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V0_none"):
    out.append(f"| {NAME[v]} | {RL[v]} | donor optics, evaluator OFF, 73 px/deg | " +
               " | ".join(f3(ser[v][i]["P_det_trunk_RETINAL_TARGET"]) for i in COLS) + " |")
C135 = json.load(open("b0/results/cie135_target.json"))["P_det_trunk_RETINAL_TARGET"]
c135 = {i: C135[f"x{K[i]:.3g}"] for i in COLS}
out.append("| CIE 135/1 GSF in 2-D (b0/cie135_target.py, erratum check) | STRAYLIGHT | donor optics, evaluator OFF, 73 px/deg | " +
           " | ".join(f3(c135[i]) for i in COLS) + " |")
for m, v in (("hdrvdp", "V2_hdrvdpmtf"), ("cie", "V3_cie99")):
    out.append(f"| {NAME[v]} | {RL[v]} | evaluator optics on the physical stimulus, 146 px/deg | " +
               " | ".join(f3(world.get((m, i))) for i in COLS) + " |")
out += ["", "Vangorp L_la at the trunk under each target's retinal image [cd/m², HDR-VDP local adaptation, "
        "extrapolated below its fitted 1 cd/m²] (diagnostic under observer model X):", "",
        "| target " + hdr, "|---" * (len(COLS) + 1) + "|"]
for v in ("V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V0_none"):
    out.append(f"| {NAME[v]} | " + " | ".join(f"{ser[v][i]['Vangorp_Lla_trunk']:.3g}" for i in COLS) + " |")
out += ["", "## DISPLAY ENCODINGS (image D on the phone through the frozen pcond stack, Ldmax 100)", "",
        "| encoding | evaluator " + hdr, sep]
for v in ("V0_none", "V4_spencer", "V5_temporal", "V1_iset", "V2_hdrvdpmtf", "V3_cie99"):
    flag = " (PSF x PSF, informational)" if ser[v][0]["display_PSF_x_PSF"] else ""
    for ev, lab in (("EVAL_VIEWER", "viewer's eye at the phone"), ("EVAL_OFF", "optics OFF (diagnostic)")):
        out.append(f"| {NAME[v]}{flag} | {lab} | " + " | ".join(f3(ser[v][i][f"P_det_trunk_{ev}"]) + wl(v, i) for i in COLS) + " |")
out += ["", "Plateau: equivalent-area diameter of the pixels with displayed luminance above black >= 0.99 Ldmax [arcmin]; "
        "`wl` = window-limited (>= 0.8 of the 57.7' temporal window): neither the plateau nor the P_det is a result there:", "", "| encoding " + hdr, "|---" * (len(COLS) + 1) + "|"]
for v in ("V0_none", "V4_spencer", "V5_temporal", "V1_iset", "V2_hdrvdpmtf", "V3_cie99"):
    out.append(f"| {NAME[v]} | " + " | ".join(f"{ser[v][i]['plateau_Y99_equiv_diam_arcmin']:.1f}" +
                                               (" wl" if ser[v][i]["plateau_window_limited"] else "") for i in COLS) + " |")
out += ["", "## GAP: |P_det(viewer_eye(D)) - P_det(target_retina)| (display encodings, EVAL_VIEWER)", "",
        "| encoding D | target " + hdr, sep]
targets = {"ISET 550 nm ZERO_DEFOCUS (wavefront core only)": lambda i: ser["V1_iset"][i]["P_det_trunk_RETINAL_TARGET"],
           "CIE 135/1 in 2-D (straylight)": lambda i: c135[i],
           "HDR-VDP otf_cie99, defective (world 146 px/deg)": lambda i: world.get(("cie", i)),
           "HDR-VDP MTF (straylight, world 146 px/deg)": lambda i: world.get(("hdrvdp", i))}
for v in ("V0_none", "V4_spencer", "V5_temporal"):
    for tn, tf in targets.items():
        cells = []
        for i in COLS:
            a, b = ser[v][i]["P_det_trunk_EVAL_VIEWER"], tf(i)
            cells.append("n/a" if a is None or b is None else f"{abs(a - b):.3f}" + wl(v, i))
        out.append(f"| {NAME[v]} | {tn} | " + " | ".join(cells) + " |")
open("b0/results/b0_v3_tables.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))

fig, ax = plt.subplots(1, 3, figsize=(17, 5))
for v, s in ser.items():
    idx = sorted(s); E = [K[i] * E1 for i in idx]
    ls = "-" if s[idx[0]]["role"] == "DISPLAY_ENCODING" else ":"
    pl = np.array([s[i]["plateau_Y99_equiv_diam_arcmin"] for i in idx], float)
    wl = np.array([s[i]["plateau_window_limited"] for i in idx])
    ax[0].semilogx(np.array(E)[~wl], pl[~wl], ls, label=v)
    if wl.any(): ax[0].semilogx(np.array(E)[wl], pl[wl], "x", color="grey")
    ax[1].semilogx(E, [s[i]["P_det_trunk_EVAL_VIEWER"] for i in idx], ls, label=f"{v} on display")
    if s[idx[0]]["P_det_trunk_RETINAL_TARGET"] is not None:
        ax[2].semilogx(E, [s[i]["P_det_trunk_RETINAL_TARGET"] for i in idx], "-", label=f"{v} retinal, eval OFF")
for m, mk in (("cie", "ko"), ("hdrvdp", "k^")):
    pts = sorted((K[i] * E1, p) for (mm, i), p in world.items() if mm == m)
    for a in ax[1:]: a.semilogx([p[0] for p in pts], [p[1] for p in pts], mk, label=f"target {m} (world, 146 px/deg)")
ax[0].set_title("display plateau, Y >= 0.99 Ldmax [arcmin]\n(grey x: temporal, window-limited)")
ax[1].set_title("DISPLAY ENCODINGS: trunk P_det, viewer's eye at the phone\n(dotted: retinal-forward on display = PSF x PSF)")
ax[2].set_title("RETINAL TARGETS: trunk P_det, evaluator optics OFF\n(points: evaluator optics on the physical stimulus)")
for a in ax:
    a.set_xlabel("illuminance at the eye from the lamp [lx]"); a.grid(True, which="both", lw=0.3); a.legend(fontsize=7)
plt.tight_layout(); plt.savefig("b0/results/sweep_ach_curves.png", dpi=95)
