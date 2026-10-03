# Handoff — simple CINVA-Ram press, 14 x 7 x 4 (rev G)

For the next Claude session picking this up. Owner: JC (6'1"; direct; wants working deliverables, not
documentation; correct reasoning errors immediately; no unnecessary questions or verbosity).

## State

- Branch `next` = upstream `master` (9cdb75c) + 16 commits; `patches/0001-0016` are the same commits.
- Drawings rev G (sheets 1, 2, 4, 23), rev F (the other 42). 42 items: press 1-23, feeder 24-38, stand 39-42.
- Working pressure 150 psi (assumption, see open items), design load 306 psi. Handle 90 in, 2 sch 160.
- `cinva_simple.py --check`: 19 functional checks pass, every strength check within allowable.
- `sysml_sync.py`: exit 0, no drift. All three SysML files pass the OMG pilot (2026-08).

## Environment

```
pip install "build123d==0.11.1" cairosvg jupyter_client   # 0.12+ removed Vertex.to_tuple (cinva_drawings)
# SysML pilot kernel (Java 17+), pinned + hash-checked:
curl -LO https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/2026-08/jupyter-sysml-kernel-0.62.0.zip
sha256sum jupyter-sysml-kernel-0.62.0.zip  # 5a015ed3f2b3d2dae14e9c3fb9602d9e1fef5f9ce33cf396c422329405cc3cb2
unzip jupyter-sysml-kernel-0.62.0.zip -d sysml-kernel && python3 sysml-kernel/install.py --user
```
JC's own machine needs `LD_LIBRARY_PATH=$HOME/miniconda3/lib` for build123d (see CLAUDE.md).

## Commands (each full run is ~3-6 min)

| Command | What |
|---|---|
| `python3 cinva_simple.py --check` | strength rows + 19 functional checks incl. full collision sweep |
| `python3 sysml_sync.py [--update] [--no-sweep]` | drift model<->code, run solver, write `CinvaRamResults.sysml`; exit 1 drift, 2 failed check/requirement |
| `python3 sysml_lint.py CinvaRam.sysml CinvaRamResults.sysml CinvaRamTrade.sysml` | parse/resolve with the pilot |
| `python3 sysml_trade.py` | cam pin x side plate trade, cached in `trade_cache.json` (delete it after any design change) |
| `python3 cinva_drawings.py --model simple [--only key,...] [--no-pdf]` | ISO 128 sheets, DXF, STEP, PDF |
| `python3 cinva_animation.py` | `animation/press.json` for `animation/index.html` |

## Conventions (learned the hard way)

- **Revisions:** `REVISIONS`, `CURRENT_REV`, `SHEET_REV` in `cinva_simple.py`. Bump only sheets whose
  content changed: regenerate with `--no-pdf`, compare sorted SVG path sets against `HEAD`, set `SHEET_REV`
  for those, regenerate with PDF, then `git checkout` the other sheets and all unchanged DXFs (they differ
  only by timestamps/GUIDs/path order).
- **Model sync:** design params in `CinvaRam.sysml` use `default` (variants can override), derived values
  are bound. `sysml_sync.py --update` rewrites params/BOM from the code; requirement limits are read from
  the model and checked in Python (the pilot cannot evaluate unit-bearing expressions).
- **SysML pitfalls:** `frame` is a keyword; nested states are referenced as `fill.returned` from outside.
- **Requirements are sourced:** HandleForceLimit 120 lbf = CCOHS Table 2 "pull down, above head height"
  (the peak pull comes 71% through the head rotation with the grip ~76 in up). PartHandlingLimit 51 lb =
  NIOSH RNLE load constant. No total-steel cap (no basis for one).
- **Run long jobs detached** (`setsid nohup ... &`) and poll; tool calls time out at 300 s.

## Open items / decisions pending

1. **Soil test (blocking).** The press compresses a fixed 6.75 -> 4.0 fill (1.69:1); the pressure is set by
   the soil, not the operator. Test JC's mix at 1.69:1 in a pipe mold under a jack with a gauge. On the 90 in
   handle: peak pull ~0.65 lbf per psi (98 lbf at 150 psi, 120 lbf at ~183 psi, 190 lbf at 290 psi).
   Literature: 1-2 MPa minimum molding pressure, 2-4 MPa for good stabilized blocks; CINVA-Ram ~2 MPa.
2. **One-person at 290 psi** is not possible with this knee: sweeping `psi0` bottoms out at 155 lbf and
   breaks the eject-grip check. Average pull is 87 lbf, so a profiled cam (shaped track) could reach
   ~100-110 lbf; alternatives: hydraulic bottle jack, two operators. JC has not chosen.
3. **Margins to watch:** handle 50.3 lb vs the 51 lb part limit; yoke arms 0.16 above the stand top at eject;
   peak pull at 150 psi is fine, but the 150 psi itself is unverified.
4. **Unverified:** animation feeder motion not viewed in a browser (JS syntax-checked only); feeder chute
   flow and gate shear are design assumptions; no prototype or load test (ASSEMBLY.md Step 8).
5. **Known compromise:** the open knife gate leaves the far 3/16 of the mold width under the gate.
