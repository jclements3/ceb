# OSE CEB Press v17.08

Open Source Ecology's **CEB Press v17.08**, Prototype 9 (2017). This is the latest working build in OSE's
CEB press genealogy: the hydraulic "Liberator" line, after v16.09. It simplified how the drawer bushings
are mounted.

Source: https://wiki.opensourceecology.org/wiki/CEB_Press_v17.08 (CC BY-SA).

## Contents

| Path | What it is |
|---|---|
| `source/CEB_17.08_CAD_Assembly.fcstd` | OSE's FreeCAD assembly (A2plus): eight sub-assemblies stored as BREP shells (unzipped in `source/fcstd/`) |
| `source/CEB_v1708_CAM.zip` | OSE master CAM nests: 1/8, 1/4 and 1/2 plate DXFs |
| `source/CEB_DXFs.zip` | OSE individual-part DXFs (partial; some fail to import) |
| `source/Seamanandschuske.zip` | OSE's 1/2 plate order, nested on 5 x 10 sheets |
| `source/subassemblies/` | OSE's per-sub-assembly FreeCAD files (with named parts), part folders, DXFs, pictures and the wiki page (from JC's download) |
| `source/*.html` | Owner's manual and genealogy wiki pages |
| `v1708_drawings.py` | Builds the ISO 128 set from the FreeCAD model (build123d + `../cinva_drawings.py`) |
| `drawings/` | `sheets/*.svg`, `dxf/` (flat parts), `CEB_Press_v17.08.pdf`, `CEB_Press_v17.08.step`, `manifest.json` |
| `shaker/` | Soil shaker (hopper vibrator) from OSE's *CEB a-z Build 1.0* manual: `shaker.py`, plus its own `drawings/` |

## Drawing set

* Sheet 1: general assembly, with a balloon for each of the eight sub-assemblies (S1-S8).
* Sheets 2-9: one per sub-assembly (Frame, Hopper Seat, Main Cylinder, Drawer, Arms, Hopper, Grate,
  Secondary Cylinder), with balloons and a parts list.
* Then one detail sheet for each distinct part: 76 parts, 246 pieces in total.
  * Mirror pairs and identical parts are drawn once, with their quantity.
  * Each part is laid flat on its largest face.
  * Flat plates also get a DXF.

The part names did not survive in OSE's file, so parts are named `<sub-assembly> NN` with stock and size.
Before cutting, check each part against OSE's CAM nests in `source/CEB_v1708_CAM.zip`.

```
export LD_LIBRARY_PATH=$HOME/miniconda3/lib
python3 CEB_Press_v17.08/v1708_drawings.py            # full set (~8 min)
python3 CEB_Press_v17.08/v1708_drawings.py --only 1,40 --no-pdf
python3 CEB_Press_v17.08/shaker/shaker.py             # shaker set
```

## Shaker

The shaker is modelled from two OSE sources:
* *CEB a-z Build 1.0*, steps 3-5 (pp. 15-20);
* OSE's weldment drawings 001-0042..0048 and 001-0077, in `OSE/ceb_press_cnc_package/reference/weldment_drawings`.

Where the two disagree, the weldment drawing is used. The guard outline comes from the manual. The
assembly sheet's arrangement is indicative: it follows the section on weldment 001-0048, sheet 2.
