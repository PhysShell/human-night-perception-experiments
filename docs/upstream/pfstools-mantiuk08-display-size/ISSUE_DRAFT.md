**Draft, not sent.** For the pfstools tracker (https://sourceforge.net/p/pfstools/). It is in the same backlog as
`docs/upstream/hdrvdp-otf-cie99/`.

---

**pfstmo_mantiuk08: `--display-size` is parsed but has no effect on the result (2.2.0 and current master)**

Hello,

The man page describes `--display-size` (`-s`, `vres=…:vd=…:d=…` or `ppd=…:d=…`) as the viewing geometry for
the display-adaptive tone mapping. It says the default is 30 pixels per visual degree, and that the effect of the
parameter is moderate.

In our tests the option does not change the output at all.

**Repro** (`repro.sh`, a synthetic 256² HDR image, no external data)

| option | output sha256 (first 16), 2.2.0 | master c8606912 (2025-09-20) |
|---|---|---|
| `-s ppd=5` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| `-s ppd=30` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| `-s ppd=73` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| `-s ppd=150` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| `-s vres=480:vd=3:d=0.5` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| `-s vres=2160:vd=0.8:d=0.5` | f3ed3b10f2fd7288 | f3ed3b10f2fd7288 |
| control: `-s ppd=30 -e 2` | 57e4dca28ac2ccca | 57e4dca28ac2ccca |

Our 1920 × 820 renders gave the same result: `ppd=73:d=0.3` and `ppd=48.4:d=0.6` were byte-identical.

**Where it seems to get lost** (line numbers are for 2.2.0; master is the same apart from small offsets)

- `display_size.cpp`, `createDisplaySizeFromArgs()`: parses the option into a `DisplaySize`, and
  `DisplaySize::print()` reports the pixels per degree with `-v`.
- `pfstmo_mantiuk08.cpp`: passes `ds` to `datmo_compute_tone_curve(tc, C, df, ds, …)`.
- `display_adaptive_tmo.cpp`, `optimize_tonecurve(C_pub, dm, ds, …)`: receives `ds` but never dereferences it.
  `ds->`, `getPixPerDeg()` and `getViewD()` do not appear in the file.
- `datmo_compute_conditional_density()` (l. 391) builds `new conditional_density()`. That uses the constructor's
  default `pix_per_deg = 30.f` (l. 323). The band frequencies are `f_scale[i] = 0.5 * pix_per_deg / 2^i`, so the
  CSF is always evaluated as for 30 ppd.
- `csf_daly(rho, 0, l_adapt, 1)` is called with image size 1 and the default viewing distance, not `ds->getViewD()`.

So the geometry never reaches the visual model. Passing `ds->getPixPerDeg()` into
`datmo_compute_conditional_density()` (and on to `conditional_density(pix_per_deg)`) would look like the
intended behaviour. We have not tested such a change, because we run the operator unmodified.

Is this intentional, e.g. a fixed 30 ppd chosen for stability? If so, a note in the man page would help, because
the option currently reads as effective.

Thanks for pfstools.
