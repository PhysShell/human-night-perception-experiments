"""N5: photopic / scotopic / mesopic photometry of the test spectra with EXISTING tools only
(LuxPy 1.12.5 and colour-science 0.4.7); no model is re-implemented here.
 - S/P ratio: luxpy.spd_to_power(ptype='pu') with cieobs '1951_20_scotopic' over '1931_2'
 - CIE 1931 xy (colour.sd_to_XYZ), CCT (colour.xy_to_CCT, Ohno 2013) where Duv is small
 - mesopic: (a) luxpy.get_cie_mesopic_adaptation (claims CIE 191:2010) + luxpy.vlbar_cie_mesopic;
            (b) colour.sd_mesopic_luminous_efficiency_function (MOVE table lookup, Wikipedia source)
 - an invariant check: for S/P = 1 any CIE 191 implementation must return L_mes = L_p.
Usage: python n5_photometry.py <spectra.csv> <outdir>"""
import sys, os, json, csv, warnings
warnings.filterwarnings("ignore")
import numpy as np
import luxpy as lx
import colour

D = np.genfromtxt(sys.argv[1], delimiter=",", names=True)
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
wl = D["wavelength_nm"]; names = [n for n in D.dtype.names if n != "wavelength_nm"]
Lp_levels = [0.005, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 5.0]
shape = colour.SpectralShape(360, 830, 1)
rows, full = [], {"tools": {"luxpy": lx.__version__, "colour": colour.__version__}, "spectra": {}}

# invariant check of luxpy's CIE 191 routine
inv = []
for Lp in Lp_levels:
    Lmes, m = lx.get_cie_mesopic_adaptation(Lp, SP=1.0)
    inv.append({"Lp": Lp, "SP": 1.0, "luxpy_Lmes": float(Lmes[0]), "luxpy_m": float(m[0]),
                "expected_Lmes_for_SP1": Lp})
full["luxpy_invariant_SP1"] = inv

for n in names:
    L = D[n]
    spd = np.vstack([wl, L])
    P = float(lx.spd_to_power(spd, ptype="pu", cieobs="1931_2")[0, 0])
    S = float(lx.spd_to_power(spd, ptype="pu", cieobs="1951_20_scotopic")[0, 0])
    SP = S / P
    sd = colour.SpectralDistribution(dict(zip(wl, L)), name=n)
    XYZ = colour.sd_to_XYZ(sd, cmfs=colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"].copy().align(shape),
                           k=683.0, shape=shape)
    xy = colour.XYZ_to_xy(XYZ)
    try:
        cct, duv = colour.uv_to_CCT(colour.xy_to_UCS_uv(xy), method="Ohno 2013")
    except Exception:
        cct, duv = float("nan"), float("nan")
    rec = {"luxpy_photopic_cd_m2": P, "luxpy_scotopic_cd_m2": S, "S_over_P": SP,
           "Y_colour_cd_m2": float(XYZ[1]), "x": float(xy[0]), "y": float(xy[1]),
           "CCT_K_Ohno2013": float(cct), "Duv": float(duv), "mesopic": []}
    for Lp in Lp_levels:
        try:
            Lmes_lx, m_lx = lx.get_cie_mesopic_adaptation(Lp, SP=SP)
        except Exception as e:   # luxpy's fixed-point iteration can diverge (log10 of a negative)
            Lmes_lx, m_lx = [float("nan")], [float("nan")]
        # colour-science MOVE lookup: 'Blue Heavy' for S/P>=1, else 'Red Heavy' (the two classes it offers)
        src = "Blue Heavy" if SP >= 1 else "Red Heavy"
        Vm = colour.sd_mesopic_luminous_efficiency_function(Lp, source=src, method="MOVE").copy().align(
            shape, extrapolator_kwargs={"method": "Constant", "left": 0, "right": 0})
        Lscaled = L * Lp          # spectrum scaled so photopic luminance = Lp
        Lmes_col = 683.0 / Vm[555] * float(np.sum(Lscaled * Vm.values))
        r = {"Lp": Lp, "luxpy_Lmes": float(Lmes_lx[0]), "luxpy_m": float(m_lx[0]),
             "colour_MOVE_source": src, "colour_MOVE_Lmes": Lmes_col}
        rec["mesopic"].append(r)
        rows.append({"spectrum": n, "S_over_P": round(SP, 4), "x": round(float(xy[0]), 4), "y": round(float(xy[1]), 4),
                     "CCT_K": (round(float(cct)) if np.isfinite(cct) and abs(duv) < 0.05 else "n/a"), "Lp_cd_m2": Lp,
                     "luxpy_Lmes_FLAGGED": round(float(Lmes_lx[0]), 5), "luxpy_m_FLAGGED": round(float(m_lx[0]), 4),
                     "colour_MOVE_Lmes": round(Lmes_col, 5), "colour_MOVE_ratio_Lmes_over_Lp": round(Lmes_col / Lp, 4)})
    full["spectra"][n] = rec
    print(f"{n:9s} S/P={SP:6.3f}  xy=({xy[0]:.4f},{xy[1]:.4f})  CCT={cct:7.0f}K Duv={duv:+.4f}")
with open(os.path.join(out, "ADAPTED_n5_photometry.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(full, open(os.path.join(out, "ADAPTED_n5_photometry.json"), "w"), indent=1)
print("luxpy invariant (S/P=1 => Lmes must equal Lp):")
for r in inv: print(f"  Lp={r['Lp']:<6} luxpy Lmes={r['luxpy_Lmes']:.4f} m={r['luxpy_m']:.3f}")
for n in names:
    print(n, [(r["Lp"], round(r["colour_MOVE_Lmes"] / r["Lp"], 3)) for r in full["spectra"][n]["mesopic"]])
