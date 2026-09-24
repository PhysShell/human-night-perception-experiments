#!/usr/bin/env python3
"""B0 labelled sheets (open AFTER the blind set): 4 x 2 deg crops around the lamp, 1:1 pixels (PHONE,
73 px/deg). Sheet 1: variant rows x source intensity x1/x10/x100 (Ldmax 100). Sheet 2: variant rows x
phone peak Ldmax 50/100/200 (source x1). Both with the silhouette (bar) images."""
import subprocess
VAR = ["V0_none", "V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V4_spencer", "V5_temporal"]
D, R = "b0/out/display", "b0/results"
def sheet(cols, name, fn):
    rows = []
    for v in VAR:
        cells = []
        for c in cols:
            out = f"/tmp/b0_{v}_{c}.png"
            subprocess.run(["oiiotool", fn(v, c), "--cut", "292x146+292+146", "-o", out], check=True)
            cells.append(out)
        row = f"/tmp/b0_row_{v}.png"
        subprocess.run(["magick", *cells, "+append", "-background", "#202020", "-gravity", "west", "-splice", "150x0",
                        "-fill", "white", "-pointsize", "14", "-annotate", "+6+0", v, row], check=True)
        rows.append(row)
    hdr = f"/tmp/b0_hdr.png"
    subprocess.run(["magick", "-size", f"{150 + 292 * len(cols)}x22", "xc:#202020", "-fill", "white", "-pointsize", "14",
                    *sum([["-annotate", f"+{150 + 292 * i + 110}+16", str(c)] for i, c in enumerate(cols)], []), hdr], check=True)
    subprocess.run(["magick", hdr, *rows, "-append", f"{R}/{name}"], check=True)
sheet(["k1", "k10", "k100"], "REVEAL_sheet_variants_x_source_intensity_LD100_bar.png",
      lambda v, c: f"{D}/{v}_{c}_bar_LD100.png")
sheet(["LD50", "LD100", "LD200"], "REVEAL_sheet_variants_x_phone_peak_k1_bar.png",
      lambda v, c: f"{D}/{v}_k1_bar_{c}.png")
print("ok")
