"""Plot repro_profile.csv (log bins): expected, control and actual radial profiles; actual's bin minimum."""
import csv, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = [list(map(float, r)) for r in list(csv.reader(open("repro_profile.csv")))[1:] if "" not in r]   # bins with no pixel centre skipped
r, am, amin, c, e = zip(*rows)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
ax[0].loglog(r, e, "k-", lw=2.5, label="CIE 135/1 GSF, direct 2-D (expected)")
ax[0].loglog(r, c, "g--", lw=1.5, label="Hankel-transform OTF -> inverse FFT (control)")
ax[0].loglog(r, [x if x > 0 else float("nan") for x in am], "r-", label="hdrvdp_otf_cie99 -> inverse FFT (actual), bin mean")
ax[0].set(xlim=(0.6, 60), xlabel="radius [arcmin]   (0.01 - 1 deg)", ylabel="PSF [sr$^{-1}$]", title="point image, radial profile (log bins)")
ax[0].legend(fontsize=7, loc="lower left"); ax[0].grid(True, which="both", lw=0.3)
sel = [i for i, x in enumerate(r) if 5 <= x <= 120]
X = [r[i] for i in sel]
ax[1].plot(X, [e[i] for i in sel], "k-", lw=2.5, label="expected")
ax[1].plot(X, [c[i] for i in sel], "g--", label="control")
ax[1].plot(X, [am[i] for i in sel], "r-", label="actual, bin mean")
ax[1].plot(X, [amin[i] for i in sel], "r:", label="actual, bin minimum")
ax[1].axhline(0, color="grey", lw=0.8); ax[1].set_yscale("symlog", linthresh=10); ax[1].set_xscale("log")
ax[1].set(xlabel="radius [arcmin]", ylabel="PSF [sr$^{-1}$]", title="symlog scale (linear within +-10): actual goes below zero")
ax[1].legend(fontsize=8); ax[1].grid(True, which="both", lw=0.3)
fig.tight_layout(); fig.savefig("repro_profile.png", dpi=110)
