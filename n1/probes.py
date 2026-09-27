#!/usr/bin/env python3
"""N1.1 probe evaluation (n1/PREREG.md + addendum 1). Reads n1/work renders of one stage, writes n1/probes.json
(merged per stage) and a diagnostic preview n1/renders/raw/n1_1<stage>_preview.png.
  tracks/temporal-glare-2009/py.sh n1/probes.py a|b|c"""
import json, os, sys
import numpy as np
import OpenImageIO as oiio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ST = sys.argv[1]; W = "n1/work"; K = 179.0; YW = np.array([0.2126, 0.7152, 0.0722])
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]


def ldml(p):
    """Blender multilayer EXR -> {pass: HxWx3}."""
    out = {}; n = oiio.ImageBuf(p).nsubimages                  # Blender 5.x writes one EXR part per pass
    for si in range(n):
        b = oiio.ImageBuf(p, si, 0); ch = b.spec().channelnames; a = b.get_pixels(oiio.FLOAT)
        for i, c in enumerate(ch):
            parts = c.split("."); pas, comp = parts[-2], parts[-1]
            if comp in ("R", "G", "B"): out.setdefault(pas, {})[comp] = a[..., i]
    return {k: np.stack([v["R"], v["G"], v["B"]], -1) for k, v in out.items() if len(v) == 3}
l1 = json.load(open(f"{W}/l1_{ST}.json")); A = l1["authored"]
res = json.load(open("n1/probes.json")) if os.path.exists("n1/probes.json") else {}
r = {"L1": {"lights": [(x["name"], x["type"]) for x in l1["lights"]], "emissive": [(x["material"], x["users"]) for x in l1["emissive_materials"]],
            "world_cdm2": l1["world_strength_cdm2"]}}
allowed = {"a": ({"moon"}, set()), "b": ({"moon", "luminaire"}, {"lamp_disc"}), "c": ({"moon", "luminaire"}, {"lamp_disc", "window"})}[ST]
r["L1"]["PASS"] = ({n for n, _ in r["L1"]["lights"]} == allowed[0] and {m for m, _ in r["L1"]["emissive"]} == allowed[1]
                   and abs(r["L1"]["world_cdm2"] / A["sky_cdm2"] - 1) < 1e-6)
E = {}
for k in json.load(open(f"{W}/probes_{ST}_xy.json")):
    E[k] = float(np.pi * K * np.median(ld(f"{W}/probe_{ST}_{k}.exr") @ YW))
r["illuminance_lx"] = E
P = ldml(f"{W}/hero_{ST}.exr"); img = P["Combined"]; Y = K * (img @ YW); H, Wd = Y.shape; px = json.load(open(f"{W}/hero_{ST}_px.json"))
Lh = {}
for k, v in px.items():
    if not v["in_frame"]: Lh[k] = None; continue
    x, y = int(round(v["x"])), int(round(v["y"])); w = 1 if k == "lamp_disc" else 3
    win = Y[max(y - w, 0):y + w + 1, max(x - w, 0):x + w + 1]; Lh[k] = float(win.max() if k == "lamp_disc" else np.median(win))
r["hero_luminance_cdm2"] = Lh
fo_a = (res.get("a", {}).get("hero_luminance_cdm2") or Lh)["field_open"] if ST != "a" else Lh["field_open"]
g_ = np.zeros_like(Y, bool); g_[394 * H // 820:] = True       # ground rows as in the addendum-2 check (below row 394 of 820)
r["dark_ground_frac_pct"] = float(100 * (g_ & (Y < 0.5 * fo_a)).mean())   # < 0.5 x moon-only open field (stage a)
r["lamp_lit_ground_frac_pct"] = float(100 * (g_ & (Y > 10 * fo_a)).mean())
M2 = {}
for k, v in px.items():                                        # M2: split of each probe window into light paths
    if not v["in_frame"] or k == "lamp_disc": continue
    x, y = int(round(v["x"])), int(round(v["y"])); sl = (slice(max(y - 3, 0), y + 4), slice(max(x - 3, 0), x + 4))
    M2[k] = {pn: float(np.median(K * (P[pn][sl] @ YW))) for pn in P if pn.startswith(("Diff", "Gloss", "Emit")) and not pn.endswith("Col")}
r["M2_paths_cdm2"] = M2
if ST == "a":
    fo = E["field_open"]
    r["L2"] = {"field_open_E_in_0.01_0.03": 0.01 <= fo <= 0.03,
               "sky_within_5pct": abs(Lh["sky_9deg"] / A["sky_cdm2"] - 1) <= 0.05,
               "field_L_vs_rhoE_over_pi": Lh["field_open"] / (A["materials"]["field"] * fo / np.pi),
               "sky_brighter_than_field": Lh["sky_9deg"] > Lh["field_open"],
               "tree_shadow_E_below_open": E["tree_shadow"] < fo, "tree_shadow_L_below_open": Lh["tree_shadow"] < Lh["field_open"],
               "barn_shadow_E_ratio_open_over_shadow_info": fo / E["barn_shadow"], "barn_shadow_L_ratio_info": Lh["field_open"] / Lh["barn_shadow"]}
    q = r["L2"]["field_L_vs_rhoE_over_pi"]
    r["L2"]["PASS"] = bool(r["L2"]["field_open_E_in_0.01_0.03"] and r["L2"]["sky_within_5pct"] and 1 / 3 <= q <= 3
                           and r["L2"]["sky_brighter_than_field"] and r["L2"]["tree_shadow_E_below_open"] and r["L2"]["tree_shadow_L_below_open"])
else:
    a = res["a"]["illuminance_lx"]; lamp = {k: E[k] - a[k] for k in E if k.startswith("lamp")}
    moon = a["field_open"] - np.pi * A["sky_cdm2"]                  # the moon's own horizontal illuminance (measured)
    far = {k: v for k, v in lamp.items() if k in ("lamp_y+30", "lamp_y-30", "lamp_x-30")}
    disc = float(K * np.median(ld(f"{W}/probe_{ST}_disc.exr") @ YW))
    pred_E0, pred_disc = A["lamp_I0_cd"] / A["lamp_height_m"] ** 2, A["lamp_disc_cdm2"]
    r["lamp_only_lx"] = lamp; r["moon_only_lx"] = moon
    r["L3"] = {"under_lamp_lx": lamp["lamp_y+0"], "under_in_5_30": 5 <= lamp["lamp_y+0"] <= 30,
               "at_30m_lx": far, "at_30m_below_10pct_moon": all(v < 0.1 * moon for v in far.values())}
    r["L3"]["PASS"] = bool(r["L3"]["under_in_5_30"] and r["L3"]["at_30m_below_10pct_moon"])
    r["L4"] = {"disc_cdm2": disc, "pred_I0_over_A": pred_disc, "disc_ratio": disc / pred_disc,
               "under_lamp_ratio_to_I0_over_h2": lamp["lamp_y+0"] / pred_E0, "pred_E0_lx": pred_E0}
    r["L4"]["PASS"] = bool(abs(r["L4"]["disc_ratio"] - 1) <= 0.1 and abs(r["L4"]["under_lamp_ratio_to_I0_over_h2"] - 1) <= 0.1)
    r["outside_unchanged_vs_a"] = {k: E[k] / a[k] for k in ("field_open", "tree_shadow") if k in a}
json.dump({**res, ST: r}, open("n1/probes.json", "w"), indent=1, default=float)
print(json.dumps(r, indent=1, default=float)[:3000])
# diagnostic preview: log10 luminance (false colour, decades) and one linear exposure (sky -> 0.25 display): NOT a render
os.makedirs("n1/renders/raw", exist_ok=True)
f, ax = plt.subplots(2, 1, figsize=(12, 11))
im = ax[0].imshow(np.log10(np.maximum(Y, 1e-6)), cmap="turbo", vmin=-5, vmax=0); plt.colorbar(im, ax=ax[0], label="log10 L [cd/m²]", fraction=0.025)
for k, v in px.items():
    if v["in_frame"]: ax[0].plot(v["x"], v["y"], "w+", ms=8); ax[0].text(v["x"] + 6, v["y"] - 6, k, color="w", fontsize=7)
ax[0].set_title(f"N1.1{ST} absolute luminance (log10 cd/m²), probe windows marked", fontsize=9)
g = 0.25 / res.get("a", r)["hero_luminance_cdm2"]["sky_9deg"]; lin = np.clip(img * K * g, 0, 1); srgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
ax[1].imshow(srgb); ax[1].set_title(f"diagnostic linear exposure (sky -> 0.25), x{g:.0f}: shows structure only, not a night rendering", fontsize=9)
for a_ in ax: a_.axis("off")
plt.tight_layout(); plt.savefig(f"n1/renders/raw/n1_1{ST}_preview.png", dpi=80)
