"""
ISO 128 drawing set for the OSRL Resilient Living CEB press (osrl_press.py) via ../../cinva_drawings.py.

Writes osrl/drawings/{sheets/*.svg, dxf/, OSRL-CEB-Press_12x6x4.pdf, OSRL-CEB-Press_12x6x4.step, manifest.json}.
The manifest uses the same schema as CEB_Press_v17.08/drawings/manifest.json (plus title/pdf/step/source).

Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/osrl/build_drawings.py [--only key,key] [--no-pdf]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from build123d import Unit, export_step  # noqa: E402

import cinva_drawings as D  # noqa: E402
import osrl_press as M  # noqa: E402

OUT = os.path.join(HERE, "drawings")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma list of part keys (and/or 'assembly')")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    D.m = M
    p = M.Params()
    only = set(a.only.split(",")) if a.only else None
    print(f"{M.TITLE} {p.label} -> {OUT}")
    paths = D.build_all(p, OUT, only)
    base = f"{M.FILE_PREFIX}_{p.label}"
    if only:
        return
    export_step(M.assembly_compound(p, "locked"), os.path.join(OUT, base + ".step"), unit=Unit.IN)
    if not a.no_pdf:
        D.to_pdf(paths, os.path.join(OUT, base + ".pdf"))
    path = os.path.join(OUT, "manifest.json")
    with open(path) as f:
        man = json.load(f)
    for s in man["sheets"]:
        s["sub"] = s.get("group", "Assembly")
        if s.get("item"):
            s["dxf_file"] = f"{s['item']:02d}_{s['key']}.dxf" if s.get("dxf") else None
    man.update(model=M.TITLE, title=f"{M.TITLE} rev 1.1 clone, {p.label} block", pdf=base + ".pdf",
               step=base + ".step",
               source="OSRL CEB Press Drawings rev 1.1 (Dec 2011, D. Gendron and B. Metz, CC BY-SA 3.0, "
                      "www.osrliving.org) and the OSRL Manual CEB Press")
    with open(path, "w") as f:
        json.dump(man, f, indent=1)
    print(f"  {base}.pdf, {base}.step, manifest.json")


if __name__ == "__main__":
    main()
