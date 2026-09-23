# pcond `-x` reports display luminance 179/Ldmax too high in linear mode

Ready to post on the Radiance Discourse (https://discourse.radiance-online.org/). The GitHub
repository mirrors CVS and does not take issues. Not yet posted.

**Radiance version.** Master `bcffc2b52d99b908adfdc2543e4cddf83268a125` (CVS import of
2026-08-19), built on Linux (GCC 15, `-std=gnu17`).

**Symptom.** In linear mode, the second column of `pcond -x mapfile` is higher than the display
luminance pcond actually produces, by a factor of exactly WHTEFFICACY/Ldmax. Linear mode covers
`-l`, `-e`, and the automatic fallback when `mkbrmap()` finds that no compression is needed.
In histogram mode the table is correct.

**Repro.** [`pcond_x_linear_repro.sh`](pcond_x_linear_repro.sh) uses Radiance tools only. It
makes a grey ramp from 1e-3 to 1e3 cd/m² with `pcomb`, runs pcond, and compares each output pixel
with the `-x` table at the same world luminance. Output
([`pcond_x_linear_repro.out`](pcond_x_linear_repro.out)):

    histogram mode, pcond -s -u 100  (expect histogram-model ratio 1):
       528 px: histogram-model ratio 0.9997, linear-model ratio 0.8366   (Ldmax/179 = 0.5587)
    linear mode,    pcond -l -u 100  (linear-model ratio = 100/179 -> bug):
       184 px: histogram-model ratio 0.7095, linear-model ratio 0.5581   (Ldmax/179 = 0.5587)
    linear mode,    pcond -l -u 50   (linear-model ratio = 50/179  -> bug):
       184 px: histogram-model ratio 0.4329, linear-model ratio 0.2790   (Ldmax/179 = 0.2793)

"Linear model" means display luminance = Ldmax·v, which is what `sfscan()` writes
(v = scalef·radiance). "Histogram model" means Ldmin + v·(Ldmax − Ldmin), which is what
`mapscan()` inverts. **In linear mode the ratio follows `-u` exactly.**

**Likely cause** (`src/px/pcond.c`, `pcond3.c`):
- `mapimage()` sets `scalef *= WHTEFFICACY/(inpexp*ldmax)` for pixel scaling.
- `putmapping()` then prints `sf*wlum` with `sf = scalef*inpexp` (× WHTEFFICACY again for
  `cielum`). That is display luminance × WHTEFFICACY/Ldmax.
- The clamp to `[ldmin, ldmax]` inside `putmapping()` therefore also cuts at the wrong world
  luminance.

**Suggested fix (untested).** In the `DO_LINEAR` branch of `putmapping()`, print
`sf*wlum*ldmax/WHTEFFICACY` (with the `cielum` factor handled the same way).

**Side note.** Histogram mode and linear mode use different pixel → display-luminance models
(with and without Ldmin). This may be intended; it is mentioned only because it matters for
anyone reading `-x` tables.
