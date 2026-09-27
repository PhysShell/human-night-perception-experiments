# N1.6 RoadLine-B0: does a real legacy/drop-refractor roadway luminaire send light towards a distant eye?

Committed **before any candidate file is downloaded**. Analysis only: no scene, no render.

**Why.** The modern Archeon optic (stimulus A, `LUMINAIRE.md`) has a measured LM-63 intensity of 0 cd at V = 90°.
Along the road axis (H = 90°) it gives 25.5 cd at V = 87.5° and about 2.3 cd towards an eye 1600 m away.
- M1/S1 assumed 800 cd towards the observer. Stimulus B is to test D1 on a *visible* distant string of luminaires.
- It is built only on a real luminaire that physically sends light near the horizon.

**Candidates.** At most **3 official roadway families** from Cooper Lighting's public IES directory, in this order:
1. OVZ (Drop Lens Refractor);
2. OVX (Drop Prismatic Glass);
3. one further legacy roadway family if both fail.

For each family, one file is taken: 3000 K if offered, else the closest CCT; Type II or III; the file closest to
Archeon's 5813 lm. Provenance is recorded exactly as in `LUMINAIRE.md` (URL, sha256, header, terms). Files are not
committed.

**Checks per file:**
- the file parses as LM-63 type C;
- the integrated flux matches the stated (or absolute) lumens within 1 %;
- intensity in the **along-road plane towards the observer**. For type C that is H = 90° or 270° with the street side
  at H = 0°; with the other convention in the file header, it is the plane that points along the road.
- I is reported at V = 82.5°, 85°, 87.5°, 90°, and towards an eye 1.7 m high at 50–1600 m on a 8 m pole (the same
  geometry as A).

**B0 PASS** (fixed now, anchored to stimulus A so the comparison is the point):
- I(V = 87.5°) ≥ **10 ×** Archeon's 25.5 cd, i.e. **≥ 255 cd**; **and**
- I(V = 90°) > 0.

**Outcome:**
- **First PASS:** that file becomes stimulus B.
- **All ≤ 3 fail:** B0 KILL for real donors. The M1 string stays a synthetic, historical-style stimulus (800 cd, not a
  measured luminaire) and is labelled as such. RoadLine proceeds with A only.
- No threshold changes after a file is seen.
