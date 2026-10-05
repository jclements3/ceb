# OSE CEB Press 6 (a-z Build 1.0) — ISO 128 drawing set

Open Source Ecology's **CEB Press 6** ("The Liberator", Prototype 6, 2013, the Beddingfield edition): the
machine of the *CEB a-z Build 1.0* manual (`../CEB_a-z_Build_1.0.pdf`) and its cost / cut list
(`../CEB Press.ods`). Drawn with build123d and the repo's ISO 128 sheet code (`../../cinva_drawings.py`).

```
export LD_LIBRARY_PATH=$HOME/miniconda3/lib
python3 CEB_Press_v17.08/press6/press6_drawings.py -j 2          # full set
python3 CEB_Press_v17.08/press6/press6_drawings.py --only 1,35 --no-pdf
```

Output: `drawings/sheets/*.svg`, `drawings/dxf/*.dxf` (flat parts), `drawings/CEB_Press_6.pdf`,
`drawings/CEB_Press_6.step` (inches, coloured by module), `drawings/manifest.json` (same schema as
`../drawings/manifest.json`, plus `title`, `pdf`, `step`, `source`, `naming`, `purchased`, `dxf_checks`).

## Sources

| Source | Used for |
|---|---|
| `OSE/ceb_press_cnc_package/reference/full_assembly.stp` (OSE 01-001-00-6 main assembly) | All geometry. Read with OCP's XCAF reader so OSE's product names survive: every solid carries its OSE part number (`01-XXX-00-X`) and, for CNC plates, its library label (`L-XX`). |
| `../CEB Press.ods`, sheet *Final Cut List* | Manual part names. Its part numbers `100XXX` are OSE `01-XXX`; a cut-list name is used only when one of its lengths agrees with the model (±0.6 in). |
| *CEB a-z Build 1.0* (Simple Plates, Frame components, drawer, press feet pages) | A few more manual names (brick holder / dirt keeper plates, controller plate, feet, legs, press feet). |
| `OSE/.../reference/drawing_index.md` | 2011-12 BOM descriptions, 2015 weldment numbers / descriptions / stock. |
| `OSE/.../reference/2d_drawings/*.pdf` titles | Names of the assemblies; plates without a description are named after the assembly they are welded into (e.g. "Chamber Wall Plate L-F9"). |
| `OSE/.../dxf/*_steel_library.dxf` (original, not the 14x7 variant) | Cross-check of every `L-XX` plate: flat size and thickness against the model, noted on each sheet. Bent sheet parts get their flat blank from the DXF. |

## Organisation

Sheet 1 general assembly (modules ballooned S1-S9) · sheets 2-10 one per module of the manual
(Main Frame, Press Cylinder and Foot, Arms, Feet and Legs, Drawer, Hopper, Grate, Soil Shaker, Controls) ·
then one detail sheet per OSE part number (identical parts once, with the total quantity; the module is the one
that uses it most, the notes list every use). Purchased parts (cylinders, valves, hinges, bushings, printed
plastic, couplers, fittings) and fasteners are in the STEP and listed on the module sheets / in the manifest, not
detailed. Fasteners are left out of the assembly views.

## Naming and checks

See `naming` and `dxf_checks` in `drawings/manifest.json` and the summary at the end of `build.log`.
* 84 OSE part numbers detailed (238 fabricated pieces in 9 modules); 486 STEP solids in all, 141 of them
  fasteners and 107 other purchased / printed parts.
* Part identity: 84 / 84 (100 %) from the STEP's own OSE part numbers and L-labels.
* Descriptive names: 47 / 84 from the a-z cut list (length-checked), the manual or OSE's drawing index;
  35 more named after the OSE assembly they are welded into (2D drawing title, e.g. "Saddle Plate L-Q3");
  2 left as "Part 01-xxx" / "Plate L-H19" (parts of 01-236, which has no OSE drawing).
* DXF cross-check: 67 L-labelled plates; 57 match the original CNC outline (size and thickness within
  0.06 in); 4 are bent 1/8 sheet parts (L-H4, L-H5, L-H10, L-H12; blank size from the DXF);
  L-A6, L-Q12, L-G1, L-G2 differ from the library outline (noted "CHECK" on their sheets);
  L-Q2 and L-H19 have no outline in the original libraries.

## Known gaps and inconsistencies

* OSE's 2D set title blocks say **"CEB PRESS 5"** although the package is Press 6 (top-level 01-001-00-6).
* **The a-z Build 1.0 manual builds a later, structural-shape version** of parts of this machine; these are
  in the manual / cut list but not in the STEP (the STEP is the CNC-plate machine):
  - soil shaker from L4x4 angle (21 in and 8 in), 1 in rebar braces and a 2x2-angle-framed guard — drawn
    separately in `../shaker/` (the STEP's shaker is the plate version, L-O2..L-O5, drawn here);
  - roller guides (V-groove bearings on a 1/2 x 2 x 16 main plate) — the STEP uses 1 in guide rods in printed
    / nylon bushings (01-220, 01-236);
  - drawer outer / inner rails (3/16 x 2-1/2 and 1/2 x 2 x 36), back (L4x7 angle), spacer (6x6 tube);
  - main-frame small components: sensor holders, magnet holder, thin / wide cylinder supports, dirt blockers
    (2x2 angle), horizontal-member reinforcements;
  - hopper mounting plates and hinge plates; legs 2x2x1/4 x 48 (STEP legs 01-155 are 3/16 wall x 36);
  - the electronics (sensor unit, solenoid driver, controller box) and hydraulic hoses.
* Several OSE part numbers are reused between the 2011-12 set and the a-z cut list for different stock
  (e.g. the frame channels L-F1 / L-F2 are 1/2 plate in the STEP, C6x13 in the 2015 weldment redraw and the
  cut list); each sheet draws the STEP part and notes the alternative.
* The STEP has the same part number on mirror-image parts (left / right primary arms share 01-009, 01-010,
  01-272); they are drawn once, quantity 2.
* L-labels in the DXF libraries but not in the STEP: L-D9 is in the STEP as 01-028-00-2; L-H7 and L-Q10 are
  printed-plastic parts; L-H14, L-O10, L-Q16 have no STEP part. L-O9 is in the STEP as 01-143, typed "L-09".

## Rebuilding from a fresh clone

`press6_drawings.py` uses OSE's files from `OSE/ceb_press_cnc_package/` (from `OSE/get_ceb_plans.sh`) when that
folder exists. Otherwise it fetches OSE's main-assembly STEP (`01-001-00-6.stp`), the 2D drawing set
(`CEBVI_2D_DRAWING_PDF.zip`) and the three CNC DXF libraries from the OSE wiki into `source/ose/`, which is
gitignored. The drawing cross-reference index (`source/drawing_index.md`) and the DXF cluster extractor
(`extract_parts.py`, from `OSE/freecad/`) are kept here. The STEP export in `drawings/` is not tracked: run the
script to make it.
