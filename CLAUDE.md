# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CAD models and fabrication documentation for compressed earth block (CEB) construction. Three machine designs plus a dome structure, all producing/using 12" x 6" x ~4" bricks:

- **CINVA-Ram** (repo root) — manual block press, modeled from the scanned engineering drawings `cinva1-7.jpg` and reference photos `Blockpress*.jpg`
- **CETA-RAM** (`ceta-ram/`) — cored-brick press, modeled from the OHO e.V. drawings (CC-BY-SA 4.0); metric and imperial variants
- **OSE CEB Press 6** (`OSE/`, untracked) — downloaded fabrication package from the Open Source Ecology wiki
- **Geodesic dome** — generated brick-by-brick model of a 32 ft CEB dome

There is no build system, linter, or test suite. "Building" means rendering models in OpenSCAD or FreeCAD (both installed: `/usr/bin/openscad`, `/usr/bin/freecad`).

## Commands

Render a CINVA-Ram animation frame (t goes 0→1, roller travels across the ramp):

```
openscad -o frame.png -D '_t_override=0.5' cinva_ram.scad
```

Note `_t_override` is currently hardcoded to 0.5 inside `cinva_ram.scad`; set it negative to fall back to OpenSCAD's `$t` animation variable.

Parametric build123d model of the 14x7x4 CINVA-Ram type press and its ISO 128 drawing set (brick size is a parameter; `LD_LIBRARY_PATH` works around conda's pyexpat being linked against the older system libexpat):

```
export LD_LIBRARY_PATH=$HOME/miniconda3/lib
python3 cinva_ram_b123d.py --check                   # summary, strength checks, pose clearance; --step out.step
python3 cinva_drawings.py --brick 14x7x4             # -> drawings/14x7x4/{sheets/*.svg, dxf/, .pdf, .step, manifest.json}
python3 cinva_drawings.py --only side,rib --no-pdf   # a few sheets only (keys from parts(); 'assembly' = sheets 1-4)
python3 cinva_animation.py                           # animation/press.json for the three.js viewer animation/index.html
```

Regenerate the dome model (writes `ceb_dome.scad` and `ceb_molds.scad`):

```
python3 dome.py
```

Re-download the OSE CEB Press 6 fabrication package (DXFs, BOM, build manual) and rebuild its tarball:

```
bash OSE/get_ceb_plans.sh
```

FreeCAD scripts (`cinva_ram.py`, `ceta-ram/ceta_ram_imperial.py`) import the `FreeCAD` module and cannot run under plain `python3` — run them inside FreeCAD via Macro → Execute Macro, or `exec(open("...").read())` in the FreeCAD Python console. `ceta-ram/CETA_RAM_Imperial.FCStd` is the pre-built result and can be opened directly.

## Architecture

**Units convention:** OpenSCAD files use inches throughout. FreeCAD scripts work in mm internally (FreeCAD native) and convert with `IN = 25.4` / `inch()` helpers. Default plate stock is 1/4" (`T = 0.250`) for the CINVA-Ram.

**CINVA-Ram model is split in two files:**
- `cinva_ram.scad` — the part library: ~19 named modules (one per plate/part), with a flat "spread all parts" layout at the bottom for viewing/export. Parts are color-coded by sub-assembly (brown=pivot, orange=lever, pink=clamp, purple=pins, teal=shelf, red=ramps/top, gray=structure, white=hinge, green=base) — the README tables mirror this color scheme.
- `cinva_assembly.scad` — `use <cinva_ram.scad>` and places every part in its assembled position, with the `$t`-driven toggle/lever animation. Key reference positions (mold dimensions, pivot locations) are defined as named constants at the top.
- `cinva_ram.py` is the FreeCAD equivalent of the part library.
- `cinva_ram_b123d.py` is a redesign, not a port: the SCAD model's lever never moved the piston through a stroke. It implements the real CINVA-Ram mechanism (yoke from piston pin P up to stub pins Q, handle head with saddle roller on an arm, roller on a concave R10 track on AR400 lid ribs, over-centre handle stop, lid hinged at the eject end with an opening stop, central gravity latch claw on a tie between horns on the yoke bars hooking a catch bar between the handle cheeks (`claw_geom()` lays it out so latch loads run along the claw arm), eject roller). `verify()` runs the functional checks (brick thickness, steady rise, lock, lid balance, brick path). `Params` derives all sizes from the brick and `rise`; `poses()` solves the fill/start/locked/eject positions, `sweep_poses()` + `interference()` check clearances, `checks()` does the strength calcs, `parts()` holds each part's builder, BOM data and drawing dimensions. `cinva_drawings.py` turns it into first-angle ISO 128 sheets. Units are inches. `cinva_assembly.scad` is stale and calls modules that no longer exist.

**Generated files — do not hand-edit:** `ceb_dome.scad` (1010 hexagon polyhedra) and `ceb_molds.scad` are outputs of `dome.py`. To change the dome, edit the parameters block at the top of `dome.py` (`R_OUTER`, `WALL`, `FREQ`) and rerun it.

**CETA-RAM:** `ceta-ram/ceta_ram.scad` is the metric original; `ceta_ram_imperial.scad` / `ceta_ram_imperial.py` are the imperial conversion using standard US steel sizes (the metric→imperial stock mapping is tabulated in README.md). `CETA-RAM_Reference.md` holds the complete BOM and dimensions transcribed from the OHO drawings and is the source of truth for dimensions.

**Documentation:**
- `README.md` — part tables per assembly, imperial steel size table, CINVA vs CETA brick/wall weight comparison, cabin wall assembly recommendations. Keep its part tables in sync when adding/renaming modules in the SCAD files.
- `ASSEMBLY.md` — welding and assembly sequence for the 14x7x4 press in `drawings/14x7x4/` (fabrication instructions, not code); keep its numbers in sync with the model.
- `animation/` — three.js viewer (`index.html`, no build step) fed by `press.json` from `cinva_animation.py`; group transforms mirror the build123d assembly frames.
- `ceb-press-partstree.md` — a performance specification with pandoc/LaTeX frontmatter (intended for PDF generation via pandoc).

**Known inconsistency:** README.md references an `export_dxf.sh` script for exporting part DXFs, but that script does not exist in the repo.

**Repo layout note:** the git root is `~/projects/ceb`. The `OSE/` directory (downloaded DXF/PDF package and tarball) is intentionally untracked.
