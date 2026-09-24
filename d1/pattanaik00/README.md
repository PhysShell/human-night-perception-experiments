# D1-A donor: Pattanaik et al. 2000 (`pfstmo_pattanaik00`, pfstools 2.2.0 = master c860691)

This donor is run natively on the frozen D0 inputs. It is a native donor, not a production candidate. No ranking.

## Files

| file | what |
|---|---|
| `audit.md` | equation audit: paper (authors' copy) vs source |
| `input-contract.md` | what the input numbers mean; min of each input; ADAPTED floors |
| `native_timecourse.py/.json/.png` | native check: uniform-field step sequences through `-t` |
| `run.py`, `common.py`, `runs.json` | all runs with labels; outputs in `.cache/out/` (not committed) |
| `measure.py`, `metrics.jsonl` | d0/metrics.py on the outputs, emitted cd/m² via d0/display_model.py |
| `sheet_S1.png`, `sheet_S1_ladder.png`, `clip_history.png` | previews and the clip/history time course |

## Reproduce

    nix develop -c python3 d1/pattanaik00/native_timecourse.py && tracks/temporal-glare-2009/py.sh d1/pattanaik00/plot_timecourse.py
    nix develop -c python3 d1/pattanaik00/run.py all          # stills, ladder, clips, long history (~10 min)
    nix develop -c python3 d1/pattanaik00/measure.py          # HDR-VDP P_det for the S3 pairs, ~1 h
    tracks/temporal-glare-2009/py.sh d1/pattanaik00/sheets.py

## Key numbers

S1, PHONE, DARK, emitted cd/m². pcond V0 SDR100 is given for reference.

| run | sky median | dark median | silhouette | lamp saturation kept | plateaus (n / max ⌀) |
|---|---|---|---|---|---|
| pcond V0 (reference) | 0.32 | 0.14 | 0.56 | 0.35 | 2 / 0.9′ |
| NATIVE_DEFAULT (`\| pfsgamma -g 2.2`) | 8.7 | 2.7 | 0.65 | 0.00 | 60 / 84′ |
| DOCUMENTED_TARGET_CONFIG, SDR100 | 8.5 | 2.3 | 0.69 | 0.00 | 60 / 84′ |
| DOCUMENTED_TARGET_CONFIG, BRIGHT500 | 42 | 10.9 | 0.69 | 0.00 | 60 / 84′ |
| SENSITIVITY_RUN, output × 125 cd/m² absolute, SDR100 / BRIGHT500 | 10.5 / 10.5 | 2.7 | 0.69 | 0.00 | 27 / 98′ ; 0 |
| SENSITIVITY_RUN, `--local`, SDR100 | 13.8 | 16.2 | −0.08 | 0.26 | 0 |
| SENSITIVITY_RUN, ladder ×10⁰ / 10² / 10⁴ / 10⁶ | 8.5 / 8.8 / 8.6 / 13.0 | 2.3–2.8 | 0.63–0.76 | 0.00 | 60 → 505 |

- **S3 (bar next to the lamp).** P_det of the bar ≈ 1.00 (EVAL_VIEWER and EVAL_OFF) in every config. The sky is
  4.0 cd/m² (SDR100); the bar's Weber contrast is 0.98.
- **`--local` on S3.** It renders the zero bar **white** (Weber −6.4). The ADAPTED floor fixes this (0.81).
- **S4 sky.** 6.8 cd/m² (SDR100); the physical sky is 0.69.

## Clip S2 (SDR100 sky median)

| run | sky median over the clip |
|---|---|
| no `-t` | 8.5, constant |
| `-t --fps 24` | 8.5 → 44 within 0.5 s (a start-up transient, see `audit.md`); mean max step 19 % per frame; no isolated flashes |
| 2 s at 100 cd/m², then S2 | 0.1 (black) for 2 frames → 3.3 after 1 s |
| 2 s at 100 cd/m², then S1 held (long run) | 6.6 at 1 min, 19 at 5 min, 29.5 at 10 min (rod regeneration, τ = 400 s) |
