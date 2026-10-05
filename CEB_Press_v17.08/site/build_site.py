"""Build site/data.js and site/thumbs/*.png for ../index.html, the multi-machine drawing library.

Each machine is a drawing set with a manifest.json in the cinva_drawings schema: sheets[] with key, sheet,
file, name, and for parts item (> 0), qty, stock, mass, scale, size and 'sub' or 'group' (the module). Sets
that do not exist yet are listed as 'not built yet' and picked up on the next run.

    python3 CEB_Press_v17.08/site/build_site.py      (from the repo root; thumbnails in parallel, Pool(2))
"""
import glob
import json
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TW = 360

# key, drawings dir, thumb prefix, card / overview metadata. Paths are relative to CEB_Press_v17.08/.
MACHINES = [
    dict(key="v1708", dir="drawings", prefix="press", title="OSE CEB Press v17.08",
         kicker="Open Source Ecology · hydraulic", short="Hydraulic CEB press, Prototype 9 (2017)",
         desc=["OSE's <b>CEB Press v17.08</b> (Prototype 9, 2017) is the latest working build of the hydraulic "
               "Liberator line. A vertical main cylinder presses the block; a horizontal secondary cylinder drives "
               "the drawer that fills the chamber from the hopper and pushes the finished block out.",
               "These sheets are drawn from OSE's FreeCAD assembly. Identical and mirror parts are drawn once with "
               "their quantity, and flat plates have a DXF. Part names did not survive in OSE's file, so parts are "
               "named by sub-assembly and number. <b>Check each part against OSE's CAM nests before cutting.</b>"],
         source='<a href="https://wiki.opensourceecology.org/wiki/CEB_Press_v17.08">wiki.opensourceecology.org/wiki/'
                'CEB_Press_v17.08</a> (CC BY-SA). Originals are in <span class="mono">source/</span>.',
         animation="animation/index.html", readme="README.md", script="v1708_drawings.py"),
    dict(key="shaker", dir="shaker/drawings", prefix="shaker", title="OSE CEB Soil Shaker",
         kicker="Open Source Ecology · attachment", short="Hydraulic hopper vibrator (CEB a-z Build 1.0)",
         desc=["Hydraulic hopper vibrator from OSE's Press 6 build manual, <i>CEB a-z Build 1.0</i> (steps 3–5), and "
               "OSE weldments 001-0042…0048 and 001-0077. A hydraulic motor spins a flat-bar hammer that knocks "
               "the hopper so the soil keeps flowing.",
               "The part sheets follow the weldment drawings; the guard outline is from the manual. The assembly "
               "sheet's arrangement is indicative. It is shown running on the v17.08 in that press's animation."],
         source="OSE <i>CEB a-z Build 1.0</i> pp. 15–20; weldments in <span class=\"mono\">OSE/ceb_press_cnc_package"
                "/reference/weldment_drawings</span>.",
         animation="animation/index.html", animation_label="▶ Shown on the v17.08", readme="README.md",
         script="shaker/shaker.py"),
    dict(key="osrl", dir="osrl/drawings", prefix="osrl", title="OSRL Resilient Living CEB Press",
         kicker="Open Source Resilient Living · manual", short="Manual CINVA-type press, rev 1.1 (2011)",
         desc=["The <b>Resilient Living CEB Press</b> rev 1.1 by the Open Source Resilient Living group (design team "
               "Damien Gendron and Butte Metz, Dec 2011) is a manual CINVA-type toggle press for a 12 × 6 × 4 block "
               "with two cores. The lever's followers ride the lid rails into a scoop; the yoke head bolts to the "
               "yoke arms in 1 in steps to set the block thickness; a counterweighted lid opens and closes itself.",
               "These sheets are a build123d clone of their 11 drawing sheets, with the kinematics and strength "
               "checks of our other presses. Where their drawings leave a placement open the choice is noted on "
               "the sheet."],
         source="OSRL CEB Press Drawings 1-1 and manual (CC BY-SA 3.0, www.osrliving.org); scans in this folder.",
         animation="osrl/animation/index.html", readme=None, script="osrl/"),
    dict(key="press6", dir="press6/drawings", prefix="press6", title="OSE CEB Press 6",
         kicker="Open Source Ecology · hydraulic", short="Hydraulic Liberator press from the CEB a-z Build 1.0 manual",
         desc=["OSE's <b>CEB Press 6</b> (Prototype 6, 2013 'Beddingfield edition') is the best-documented machine of "
               "the Liberator line: the <i>CEB a-z Build 1.0</i> manual walks through it module by module, with a "
               "cut list, DXF plate libraries and weldment drawings.",
               "These sheets are drawn in build123d from that manual and OSE's 2D and weldment drawings. "
               "<b>Check each part against OSE's DXF libraries before cutting.</b>"],
         source="OSE <i>CEB a-z Build 1.0</i>, master BOM and DXF libraries "
                "(wiki.opensourceecology.org/wiki/CEB_Press_6, CC BY-SA).",
         animation="press6/animation/index.html", readme=None, script="press6/"),
]


def thumb(job):
    src, dst = job
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return dst
    import cairosvg
    cairosvg.svg2png(url=src, write_to=dst, output_width=TW, background_color="white")
    return dst


def stock_type(s):
    s = (s or "").lower()
    for k, v in (('1/2" plate', "1/2 plate"), ('1/4" plate', "1/4 plate"), ('1/8" plate', "1/8 plate"),
                 ('3/16" plate', "3/16 plate"), ('3/8" plate', "3/8 plate"), ('1" plate', "1 plate"),
                 ("0.500\" plate", "1/2 plate"), ("0.250\" plate", "1/4 plate"), ("1/2 plate", "1/2 plate"),
                 ("1/4 plate", "1/4 plate"), ("3/8 plate", "3/8 plate"), ("3/16 plate", "3/16 plate"),
                 ("1/8 plate", "1/8 plate"), ("sheet", "sheet"), ("plate", "plate, other"),
                 ("pipe", "pipe / tube"), ("tube", "pipe / tube"), ("round", "round bar"), ("crs", "round bar"),
                 ("channel", "channel"), ("c6x", "channel"), ("c3x", "channel"), ("angle", "angle"),
                 ("l4 ", "angle"), ("l2 ", "angle"), ("flat", "flat bar"), ("bar", "flat bar"),
                 ("aluminium", "insert"), ("plastic", "insert")):
        if k in s:
            return v
    return "other"


def resolve(m, d, man, field, ext):
    """PDF / STEP path relative to ROOT: the manifest's own field if it exists on disk, else the first *.ext."""
    v = man.get(field)
    if v:
        for cand in (v, os.path.join(d, v), os.path.join(d, os.path.basename(v))):
            if os.path.exists(os.path.join(ROOT, cand)):
                return cand.replace(os.sep, "/")
    hits = sorted(glob.glob(os.path.join(ROOT, d, f"*.{ext}")))
    return os.path.relpath(hits[0], ROOT).replace(os.sep, "/") if hits else None


def load(m, jobs):
    d = m["dir"]
    path = os.path.join(ROOT, d, "manifest.json")
    out = {k: v for k, v in m.items() if k not in ("dir", "prefix")}
    out["animation"] = m["animation"] if m.get("animation") and os.path.exists(os.path.join(ROOT, m["animation"])) else None
    out["readme"] = m["readme"] if m.get("readme") and os.path.exists(os.path.join(ROOT, m["readme"])) else None
    if not os.path.exists(path):
        out.update(missing=True, sheets=[])
        print(f"  {m['key']}: {d}/manifest.json not found yet — listed as not built")
        return out
    man = json.load(open(path))
    out["title"] = man.get("title") or m["title"]
    if man.get("source"):
        out["source_note"] = man["source"]
    dxfdir = os.path.join(ROOT, d, "dxf")
    dxfs = set(os.listdir(dxfdir)) if os.path.isdir(dxfdir) else set()
    sheets = []
    for s in man["sheets"]:
        s = dict(s)
        svg = os.path.join(ROOT, d, "sheets", s["file"])
        if not os.path.exists(svg):
            continue
        s["svg"] = f"{d}/sheets/{s['file']}"
        tn = f"{m['prefix']}_{s['file'][:-4]}.png"
        s["thumb"] = f"site/thumbs/{tn}"
        jobs.append((svg, os.path.join(HERE, "thumbs", tn)))
        part = bool(s.get("item")) and s.get("group") != "Assembly"
        s["part"] = part
        if part:
            s["module"] = s.get("sub") or s.get("group") or "Parts"
            s["stype"] = stock_type(s.get("stock"))
            s["mass"] = float(s.get("mass") or 0.0)
            s["qty"] = int(s.get("qty") or 1)
            name = None
            for cand in (f"{s['item']:02d}_{s['key']}.dxf", f"{s['item']:03d}_{s['key']}.dxf"):
                if cand in dxfs:
                    name = cand
            s["dxf"] = f"{d}/dxf/{name}" if name else None
        s.setdefault("name", "General assembly" if s["key"] == "assembly" else s["key"])
        if s["key"] == "assembly" and s["name"].lower() in ("general assembly", "assembly", "assembly"):
            s["name"] = "General assembly"
        sheets.append(s)
    out["sheets"] = sheets
    out["pdf"] = resolve(m, d, man, "pdf", "pdf")
    out["step"] = resolve(m, d, man, "step", "step")
    return out


def main():
    os.makedirs(os.path.join(HERE, "thumbs"), exist_ok=True)
    jobs = []
    machines = [load(m, jobs) for m in MACHINES]
    with Pool(2) as pool:
        for i, _ in enumerate(pool.imap_unordered(thumb, jobs), 1):
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} thumbnails", flush=True)
    with open(os.path.join(HERE, "data.js"), "w") as f:
        f.write("window.LIBRARY = " + json.dumps(dict(machines=machines), indent=1) + ";\n")
    for mm in machines:
        print(f"  {mm['key']:7s} {'not built' if mm.get('missing') else str(len(mm['sheets'])) + ' sheets'}")
    print(f"wrote site/data.js ({len(jobs)} thumbnails checked)")


if __name__ == "__main__":
    sys.exit(main())
