# D2 PREREG template (copy into `d2/<id>/PREREG.md` and commit before any code)

D2 is **not** "make the model more realistic". Each D2 item addresses exactly one documented D1 residual
(`d1/MANIFEST.md`, limitations) or one new capability, named up front.

| # | field | content |
|---|---|---|
| 1 | **Question** | one question, one sentence, e.g. *D2-B1: is S5 twilight chroma perceptually too strong?* |
| 2 | **Necessary condition** | what must be true for this item to be worth doing at all |
| 3 | **Cheapest falsifier** | the smallest test that could show condition 2 is false, run first |
| 4 | **KILL** | the explicit outcome that ends the item, with no rescue by re-tuning |
| 5 | **Budget** | the maximum effort before the next gate; exceeding it = stop and report |
| 6 | **Baseline check** | `d1/verify_manifest.sh` passes (output attached) before any comparison with D1 |
| 7 | **No regression** | any claimed improvement passes the full D1 corpus and gates P-1…P-9 (`d1/final/PREREG.md`) |

Outcomes follow the D1 discipline: FAIL → cause → new PREREG → fix → new run. A failed run is never rewritten as green.
