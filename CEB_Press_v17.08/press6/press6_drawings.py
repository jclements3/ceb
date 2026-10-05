"""
ISO 128 drawing set for the Open Source Ecology CEB Press 6 ("The Liberator", 2013, the machine of OSE's
"CEB a-z Build 1.0" manual), from OSE's main-assembly STEP 01-001-00-6 (OSE/ceb_press_cnc_package/reference/
full_assembly.stp).

Part names come from the STEP's own product names (OSE part numbers 01-XXX-00-X and CNC plate labels L-XX),
looked up in OSE's drawing index (2011-12 BOM descriptions, 2015 weldment descriptions and stock), the 2D drawing
titles (2d_drawings/*.pdf) and checked against the CNC plate outlines in the original DXF libraries
(dxf/*_steel_library.dxf). Parts are grouped into the manual's modules. One detail sheet per OSE part number,
laid flat on its largest face, auto-dimensioned; purchased parts and fasteners are listed but not detailed.

Writes press6/drawings/{sheets/*.svg, dxf/*.dxf, CEB_Press_6.pdf, CEB_Press_6.step, manifest.json}.

Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/press6/press6_drawings.py [--only 3,7] [--no-pdf] [-j 2]
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(HERE))

from build123d import Color, Compound, Shape, Solid, Unit, Vector, export_brep, export_step, import_brep  # noqa: E402

import cinva_drawings as D  # noqa: E402
import v1708_drawings as V  # noqa: E402

# Inputs. OSE's files come from the untracked OSE/ download (OSE/get_ceb_plans.sh) when it is there; otherwise
# ensure_sources() fetches them from the OSE wiki into source/ose/ (gitignored). The drawing cross-reference index
# and the DXF cluster extractor are kept in this folder.
_OSE = os.path.join(ROOT, "OSE", "ceb_press_cnc_package")
_CACHE = os.path.join(HERE, "source", "ose")
_HAVE_OSE = os.path.exists(os.path.join(_OSE, "reference", "full_assembly.stp"))
REF = os.path.join(_OSE, "reference") if _HAVE_OSE else _CACHE
DXF_LIB = os.path.join(_OSE, "dxf") if _HAVE_OSE else os.path.join(_CACHE, "dxf")
STEP_IN = os.path.join(REF, "full_assembly.stp")
INDEX = os.path.join(HERE, "source", "drawing_index.md")
WIKI = "https://wiki.opensourceecology.org"
DXF_URLS = {"half_inch_steel_library.dxf": "/images/8/88/.5IN_STEEL_LIBRARY.dxf",
            "quarter_inch_steel_library.dxf": "/images/d/d2/.25_STEEL_LIBRARY.dxf",
            "eighth_inch_steel_library.dxf": "/images/a/a7/.125_STEEL_LIBRARY.dxf"}


def _fetch(url, dest):
    import urllib.request
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CEB-fab-download)"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest + ".part", "wb") as f:
        f.write(r.read())
    os.replace(dest + ".part", dest)
    print(f"  fetched {os.path.relpath(dest, ROOT)}")


def _wiki_file(title, dest):
    """Download an OSE wiki File: by scraping its description page for the /images/ link."""
    import urllib.request
    req = urllib.request.Request(f"{WIKI}/wiki/File:{title}", headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    m = [u for u in re.findall(r'href="(/images/[^"]+)"', page) if "/archive/" not in u]
    if not m:
        raise SystemExit(f"could not resolve {WIKI}/wiki/File:{title}; download it to {dest} by hand")
    _fetch(WIKI + m[0], dest)


def ensure_sources():
    """Fetch OSE's STEP, 2D drawing set and CNC DXF libraries if they are not on disk."""
    if not os.path.exists(STEP_IN):
        _wiki_file("01-001-00-6.stp", STEP_IN)
    d2 = os.path.join(REF, "2d_drawings")
    if not os.path.isdir(d2):
        import zipfile
        z = os.path.join(REF, "2d_drawings.zip")
        if not os.path.exists(z):
            _wiki_file("CEBVI_2D_DRAWING_PDF.zip", z)
        zipfile.ZipFile(z).extractall(d2)
    for name, path in DXF_URLS.items():
        if not os.path.exists(os.path.join(DXF_LIB, name)):
            _fetch(WIKI + path, os.path.join(DXF_LIB, name))
OUT = os.path.join(HERE, "drawings")
MM = 1 / 25.4
STEEL = 0.2836

# ---- hooks read by cinva_drawings ----
TITLE = "OSE CEB Press 6"
DWG_PREFIX = "OSEP6"
PART_SUBTITLE = "OSE CEB Press 6 (a-z Build 1.0)"
REVISIONS = {"A": ("2026-10-04", "Drawn from OSE full_assembly.stp (01-001-00-6, CEB Press 6)")}
CURRENT_REV = "A"
ATTACHMENT_GROUPS = ()


class P:
    label = "P6"


# ---- the manual's modules: top-level component (or 01-019 child) -> module ----
MODULES = [  # (name, colour, top-level part numbers)
    ("Main Frame", (0.55, 0.57, 0.60), ["01-019"]),
    ("Press Cylinder and Foot", (0.15, 0.35, 0.75), ["01-039", "01-169", "01-103", "01-109"]),
    ("Arms", (0.70, 0.20, 0.20), ["01-003", "01-018", "01-173", "01-174"]),
    ("Feet and Legs", (0.40, 0.40, 0.42), ["01-002", "01-155", "01-267"]),
    ("Drawer", (0.20, 0.55, 0.30), ["01-026", "01-220", "01-236", "01-185", "01-102", "01-127"]),
    ("Hopper", (0.85, 0.70, 0.15), ["01-063", "01-079", "01-080", "01-256", "01-259", "01-243", "01-276",
                                    "01-049", "01-186"]),
    ("Grate", (0.45, 0.30, 0.60), ["01-070", "01-251", "01-253"]),
    ("Soil Shaker", (0.80, 0.45, 0.15), ["01-076"]),
    ("Controls", (0.10, 0.55, 0.60), ["01-084", "01-119", "01-245"]),
]
HARDWARE_TOP = "202"
PURCHASED = re.compile(r"(MCMASTER|SURPLUS|HYDRAULIC CYLINDER|PRESS CYLINDER|PIANO HINGE|PLASTIC PRINTED|PRINTED PLASTIC|"
                       r"BUSHING|CLEVIS PIN|THREADED ROD|SOLENOID|VALVE|HYVAIR|DAMAN|SS-\d|Male Hex|Control Valve|"
                       r"5700K14|PMC-21012|25TL14|HNUT|HBOLT|HHCS|SHCS| HN$|^\.\d|\.313-18)", re.I)


def short_stock(st):
    """Fit the title block's material cell (about 34 characters)."""
    st = re.sub(r"\s+PER DETAIL|\s*PREFERABLY.*$|,?\s*STEEL\b|\bHR\s|\bCR\b\s*|\s+LONG|,?\s*OSE 4\.?[\d.]*", "", st, flags=re.I)
    st = re.sub(r"\s+", " ", st).strip(" ,")
    return st if len(st) <= 36 else st[:35] + "~"


def pn(name):
    m = re.match(r"(01-\d{3})", name)
    return m.group(1) if m else None


def label_of(name):
    name = re.sub(r"\bL-0(\d)", r"L-O\1", name)          # STEP typo 'L-09' for L-O9
    m = re.search(r"\bL-([A-Z])-?(\d+)", name)
    return f"L-{m.group(1)}{m.group(2)}" if m else None


# ==========================================================
# Sources: drawing index, 2D drawing titles, DXF library outlines
# ==========================================================

def read_index():
    out = {}
    for line in open(INDEX):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 5 and re.match(r"01-\d{3}$", c[0]):
            out[c[0]] = dict(bom=c[1], wdwg=c[2], wdesc=c[3].rstrip(", "), wmat=c[4], lib=c[5] if len(c) > 5 else "")
    return out


def read_titles():
    out = {}
    for f in os.listdir(os.path.join(REF, "2d_drawings")):
        m = re.match(r"(01-\d{3})-\d\d-\d (.+)\.pdf$", f)
        if m:
            out[m.group(1)] = m.group(2).title()
    return out


def dxf_outlines():
    """{L-label: (w, h, thickness)} from the original OSE CNC libraries (largest cluster per label)."""
    sys.path.insert(0, HERE)                      # extract_parts.py: copy of OSE/freecad/extract_parts.py
    import ezdxf
    import extract_parts as E
    out = {}
    for fname, t in (("half_inch_steel_library.dxf", 0.5), ("quarter_inch_steel_library.dxf", 0.25),
                     ("eighth_inch_steel_library.dxf", 0.125)):
        path = os.path.join(DXF_LIB, fname)
        if not os.path.exists(path):
            continue
        msp = ezdxf.readfile(path).modelspace()
        cl = E.label_clusters(msp, E.merge_interior(E.cluster(list(E.entity_records(msp)), E.TIGHT)))
        for c in cl:
            lab = c["label"]
            if not lab:
                continue
            lab = re.sub(r"L-([A-Z])-?0*(\d+)", r"L-\1\2", lab)
            bb = c["bbox"]
            w, h = sorted((bb[2] - bb[0], bb[3] - bb[1]), reverse=True)
            if lab not in out or w * h > out[lab][0] * out[lab][1]:
                out[lab] = (w, h, t)
    return out


# ==========================================================
# STEP -> named, placed solids
# ==========================================================

def read_step():
    """[(path of product names, leaf name, located OCP shape)] with world placement, mm."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopLoc import TopLoc_Location
    from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    r.ReadFile(STEP_IN)
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else ""

    out = []

    def walk(l, loc, path):
        comps = TDF_LabelSequence()
        st.GetComponents_s(l, comps)
        if comps.Length() == 0:
            out.append((path, name(l), st.GetShape_s(l).Moved(loc)))
            return
        for i in range(1, comps.Length() + 1):
            c = comps.Value(i)
            rl = TDF_Label()
            st.GetReferredShape_s(c, rl)
            walk(rl, loc.Multiplied(XCAFDoc_ShapeTool.GetLocation_s(c)), path + [name(rl)])

    labs = TDF_LabelSequence()
    st.GetFreeShapes(labs)
    walk(labs.Value(1), TopLoc_Location(), [])
    return out


def module_of(path):
    top = pn(path[0]) if path else None
    if path and path[0].startswith(HARDWARE_TOP):
        return "Hardware"
    if top == "01-019" and len(path) > 1 and pn(path[1]) in ("01-039", "01-169", "01-103", "01-109"):
        return "Press Cylinder and Foot"
    for m, _, tops in MODULES:
        if top in tops:
            return m
    return "Other"


def lay_flat(sol):
    """V.lay_flat, then turned about Z to the smallest bounding rectangle (so chamfered / angled plates are not
    laid along a chamfer), long side on X."""
    from build123d import Axis, GeomType, Location
    s = V.lay_flat(sol)
    best, best_a = None, 0.0
    angs = {0.0}
    for e in s.edges():
        if e.geom_type == GeomType.LINE:
            d = e.end_point() - e.start_point()
            if abs(d.Z) < 1e-6 and d.length > 0.2:
                angs.add(round(math.degrees(math.atan2(d.Y, d.X)) % 90.0, 3))
    lines = [(e.end_point() - e.start_point()) for e in s.edges() if e.geom_type == GeomType.LINE]
    lines = [d for d in lines if abs(d.Z) < 1e-6]
    cand = []
    for a in angs:
        b = s.rotate(Axis.Z, -a).bounding_box()
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        square = sum(d.length for d in lines                       # edge length left square to the axes
                     if min(abs(d.X * c + d.Y * sn), abs(-d.X * sn + d.Y * c)) < 1e-3 * d.length)
        cand.append((b.size.X * b.size.Y, -square, a))
    amin = min(cd[0] for cd in cand)
    best, _, best_a = min((cd for cd in cand if cd[0] <= amin * 1.02), key=lambda cd: (cd[1], cd[0]))
    if best_a:
        s = s.rotate(Axis.Z, -best_a)
    b = s.bounding_box()
    if b.size.Y > b.size.X + 1e-6:
        s = s.rotate(Axis.Z, 90)
        b = s.bounding_box()
    return s.moved(Location((-b.min.X, -b.min.Y, -b.min.Z)))


def to_inch_solids(shape):
    """Located OCP shape (mm) -> build123d solids in inches. The scale is applied with BRepBuilderAPI_Transform
    so the component placement (a TopLoc on the shape) is scaled too; build123d's scale() leaves it in mm."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Pnt, gp_Trsf
    if shape.IsNull():
        return []
    t = gp_Trsf()
    t.SetScale(gp_Pnt(0, 0, 0), MM)
    s = Compound(BRepBuilderAPI_Transform(shape, t, True).Shape())
    sols = s.solids()
    return list(sols) if sols else [Solid(sh) for sh in s.shells()]


# ==========================================================
# Parts
# ==========================================================

# names from the a-z Build 1.0 manual (cut list, Simple Plates, Frame components, drawer, press feet) where the
# part is identifiable by its OSE number / stock; everything else keeps OSE's index description
MANUAL_NAMES = {
    "01-079": "Brick Holder Plate", "01-080": "Dirt Keeper Plate", "01-081": "Controller Plate",
    "01-083": "Controller Mount Bottom", "01-082": "Controller Mount Back", "01-051": "Valve Plate",
    "01-006": "Foot Plate", "01-182": "Leg Holder Tube", "01-155": "Leg", "01-049": "Hopper Support",
    "01-186": "Grate Support Tube", "01-009": "Primary Arm", "01-010": "Primary Arm", "01-004": "Secondary Arm",
    "01-025": "Drawer Press Plate", "01-032": "Drawer Roof", "01-030": "Drawer Side", "01-029": "Drawer Vertical Support",
    "01-221": "Drawer Guide Rod", "01-162": "Upper Press Foot (AR300)", "01-035": "Lower Press Foot",
    "01-103": "Cylinder Pin", "01-109": "Cylinder Mount Tube", "01-071": "Grate Rod", "01-118": "Grate Cross Piece",
    "01-069": "Grate Angle", "01-068": "Grate Side", "01-060": "Hopper Sheet", "01-061": "Hopper Sheet",
    "01-062": "Hopper Side Sheet", "01-257": "Front Soil Deflector", "01-152": "Side Soil Deflector",
    "01-244": "Guard", "01-275": "Guard", "01-074": "Shaker Motor Guard", "01-042": "Shaker Mount Plate",
    "01-044": "Hammer Plate", "01-045": "Hammer Plate", "01-046": "Shaker Shaft", "01-120": "Frame Round Bar",
    "01-014": "Frame Channel", "01-041": "Main Frame Channel", "01-034": "Short Side Channel",
}


ODS = os.path.join(os.path.dirname(HERE), "CEB Press.ods")
STOCK_WORDS = {"Angle", "C-Channel", "Dom tubing", "Flat", "Pipe", "Rebar", "Round", "Tubing", "Sheet"}
LABEL_NAMES = {"L-D7": "Secondary Arms - Eye for 2nd Cylinder", "L-D9": "Soil Loading Drawer - Tongue"}


def read_cutlist():
    """{'01-XXX': 'Primary - Secondary'} from the a-z manual's Final Cut List (CEB Press.ods; its part numbers
    100XXX are OSE 01-XXX)."""
    import html
    import zipfile
    if not os.path.exists(ODS):
        return {}
    s = zipfile.ZipFile(ODS).read("content.xml").decode()
    m = re.search(r'<table:table table:name="Final Cut List"(.*?)</table:table>', s, re.S)
    out = {}
    for r in re.findall(r"<table:table-row[^>]*>(.*?)</table:table-row>", m.group(1) if m else "", re.S):
        cells = [html.unescape(re.sub("<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<table:table-cell[^>]*>(.*?)</table:table-cell>", r, re.S)]
        cells = [c for c in cells if c]
        nums = [c.replace(",", "") for c in cells if re.fullmatch(r"100,?\d{3}", c)]
        names = [c for c in cells if re.search(r"[A-Za-z]{3,}", c) and c not in STOCK_WORDS
                 and not re.search(r"\d\s*x|\bID\b|OD$|heavy", c)]
        if nums and names:
            name = " - ".join(n[:1].upper() + n[1:] for n in names[:2]).replace("Preparing the ", "")
            vals = {float(c) for c in cells[:cells.index(names[0])] if re.fullmatch(r"\d+(\.\d+)?", c)}
            for n in nums:
                out.setdefault("01-" + n[3:], (name, vals))
    return out


CUTLIST = None


def describe(num, leaf, idx, titles, dims=()):
    e = idx.get(num, {})
    lab = label_of(leaf)
    desc = e.get("wdesc") or ""
    bom = e.get("bom") or ""
    global CUTLIST
    if CUTLIST is None:
        CUTLIST = read_cutlist()
    cut = None
    if num in CUTLIST:                                  # accept the cut-list name only if a length agrees
        cname, vals = CUTLIST[num]
        if not vals or any(abs(v - d) < 0.6 for v in vals for d in dims):
            cut = cname
    if cut and " - " in cut:
        desc = cut
    elif num in MANUAL_NAMES:
        desc = MANUAL_NAMES[num]
    elif cut:
        desc = cut
    if lab in LABEL_NAMES:
        desc = LABEL_NAMES[lab]
    if not desc:
        desc = titles.get(num, "")
    if not desc and bom and not re.match(r"L-|SUBASSEMBLY", bom):
        desc = bom.title()
    named = bool(desc)
    if not desc:
        desc = "Plate" if lab else "Part"
    name = f"{desc} {lab}" if lab and lab not in desc else desc
    stock = e.get("wmat", "").replace(", OSE 4.1.1", "").replace(", OSE 4.1", "").replace(" OSE 4.1.", "").strip(", ")
    if not stock and bom and not re.match(r"L-|SUBASSEMBLY", bom):
        stock = bom
    return name.strip(), stock, named, lab


def build(cache):
    """Return (parts, instances, purchased, assemblies). parts: one per OSE part number (fabricated)."""
    idx, titles = read_index(), read_titles()
    leaves = read_step()
    groups, inst, purchased = {}, [], {}
    for path, leaf, shp in leaves:
        mod = module_of(path)
        num = leaf.split()[0] if pn(leaf) else leaf          # full OSE number: 01-028-00-0 (L-D7) vs -00-2 (L-D9)
        sols = to_inch_solids(shp)
        if not sols:
            continue
        key_bom = idx.get(pn(leaf) or "", {}).get("bom", "")
        is_buy = mod == "Hardware" or bool(PURCHASED.search(leaf)) or bool(PURCHASED.search(key_bom))
        for s in sols:
            inst.append(dict(mod=mod, num=num, leaf=leaf, buy=is_buy, solid=s, path=path))
        if is_buy:
            d = purchased.setdefault((mod, leaf), dict(mod=mod, name=leaf, desc=key_bom, qty=0))
            d["qty"] += 1
            continue
        g = groups.setdefault(num, dict(num=num, leaf=leaf, solids=[], mods={}, parents=set()))
        if len(path) > 1:
            g["parents"].add(path[-2].split()[0])
        g["solids"].extend(sols)
        g["mods"][mod] = g["mods"].get(mod, 0) + 1
    parts = []
    order = {m: i for i, (m, _, _) in enumerate(MODULES)}
    for num, g in groups.items():
        # a part number may be several solids (weldment modelled as one product): keep the largest as the part
        bbx = g["solids"][0].bounding_box().size
        name, stock, named, lab = describe(pn(num), g["leaf"], idx, titles, (bbx.X, bbx.Y, bbx.Z))
        how = "manual/index" if named else ""
        if not named:                                   # name by the assembly it is welded into (2D drawing title)
            ptitles = [titles.get(pn(x) or "", "") for x in g["parents"]]
            ptitles = [t for t in ptitles if t]
            if ptitles:
                base = re.sub(r"\s+(Assembly|Weldment)$", "", ptitles[0]).replace("Comp ", "Compression ").replace(" Left Hand", "").replace(" Right Hand", "")
                name = f"{base} {'Plate' if lab else 'Part'}" + (f" {lab}" if lab else f" {pn(num)}")
                how = "assembly"
        if name == "Part":
            name = f"Part {pn(num)}"
        mod = max(g["mods"].items(), key=lambda kv: (kv[1], -order.get(kv[0], 99)))[0]
        nsol = len(g["solids"])
        per = max(1, round(nsol / sum(g["mods"].values())))
        ref = max(g["solids"][:per], key=lambda s: s.volume)
        parts.append(dict(num=num, leaf=g["leaf"], name=name, stock=stock, named=named, lab=lab, mod=mod,
                          mods=g["mods"], qty=sum(g["mods"].values()), solid=ref, per=per, how=how,
                          parents=sorted(titles.get(pn(x) or "", x) for x in g["parents"])))
    parts.sort(key=lambda d: (order.get(d["mod"], 99), d["num"]))
    for i, d in enumerate(parts, 1):
        d["item"] = i
        d["key"] = d["num"].replace("-", "_") + ("_" + d["lab"].replace("-", "").lower() if d["lab"] else "")
    return parts, inst, sorted(purchased.values(), key=lambda d: (order.get(d["mod"], 99), d["name"])), idx


class Part:
    """Picklable part for D.part_sheet (geometry loaded from a BREP)."""
    def __init__(self, spec):
        self.__dict__.update(spec)
        self.views = tuple(spec["views"])
        self.notes = tuple(spec["notes"])
        self.paper = ""
        self.table = None
        self._solid = None

    @property
    def solid(self):
        if self._solid is None:
            self._solid = import_brep(self.brep)
        return self._solid

    def build(self, p):
        return self.solid

    def dims(self, p):
        if not self.flat:
            return V.auto_dims(self.solid, False)
        from cinva_simple import _plate_dims
        bb = self.solid.bounding_box()
        hs = V.holes_of(self.solid, bb.size.Z)
        lead = {}
        ny = len({round(y, 3) for x, y, dd in hs if 0.01 < y < bb.size.Y - 0.01})
        for dia in {h[2] for h in hs}:
            pts = [h for h in hs if h[2] == dia]
            i = max(range(len(pts)), key=lambda j: (round(pts[j][1], 2), pts[j][0]))
            lead[dia] = (i, 25, -(8 + 8 * max(ny, 1) + 2))
        return _plate_dims(bb.size.X, bb.size.Y, hs, bb.size.Z, lead)

    def weight(self, p):
        return self.solid.volume * STEEL


def _sheet_worker(args):
    spec, n0, n, sheets, dxf = args
    D.m = sys.modules[__name__]
    pt = Part(spec)
    path = os.path.join(sheets, f"{pt.item:03d}_{pt.key}.svg")
    try:
        size, sc = D.part_sheet(P(), pt, pt.item + n0, n, path, dxf if pt.flat else None)
    except Exception as ex:  # noqa: BLE001
        return dict(item=pt.item, error=str(ex))
    return dict(key=pt.key, item=pt.item, name=pt.name, sheet=pt.item + n0, file=os.path.basename(path), size=size,
                scale=D.scale_str(sc), qty=pt.qty, stock=pt.stock, sub=pt.sub, mass=round(pt.weight(None), 1),
                dxf=pt.flat, part_no=pt.num, label=pt.lab or "")


class Row:
    def __init__(self, item, name, qty, stock, mass):
        self.item, self.name, self.qty, self.stock, self.m = item, name, qty, stock, mass

    def weight(self, p):
        return self.m


class SubNo(int):
    def __format__(self, spec):
        return f"S{int(self)}"

    def __str__(self):
        return f"S{int(self)}"


def asm_sheet(p, title, subtitle, inst, rows, items, sheet_no, n, path, key, notes):
    sh = D.Sheet("A3")
    D.border(sh)
    comp = Compound([s for _, _, s in inst])
    iv = D.View(Vector(1, -1, 0.8).normalized(), Vector(0, 0, 1))
    iv.up = (iv.up - iv.d * iv.up.dot(iv.d)).normalized()
    bb = comp.bounding_box()
    span = max(bb.size.X, bb.size.Y, bb.size.Z) * 1.25
    area_x0, area_x1 = D.M_LEFT, sh.W - D.M_OTHER - D.TB_W
    k, scale = None, "1:20"
    for sc in D.SCALES + [(1, 50)]:
        kk = D.IN * sc[0] / sc[1]
        if span * kk < min(area_x1 - area_x0 - 40, sh.H - 2 * D.M_OTHER - 50):
            k, scale = kk, D.scale_str(sc)
            break
    pl = D._asm_view(sh, comp, iv, k, (area_x0 + area_x1) / 2, sh.H - D.M_OTHER - 28, hidden=False)
    D._view_label(sh, pl, "ISOMETRIC VIEW", below=20)
    D._balloons(sh, pl, inst, items)
    room = sh.H - D.M_OTHER - (4.0 * len(D.note_lines(notes, D.TB_W - 4)) + 6) - (D.M_OTHER + D.TB_H)
    y = D._parts_list(sh, p, rows, rowh=max(2.6, min(5.5, room / (len(rows) + 1))))
    D.general_notes(sh, notes, y0=y)
    D.title_block(sh, title, subtitle, f"{DWG_PREFIX}-{p.label}-{key}", sheet_no, n, scale, "See parts list", 1,
                  "Assembly drawing", key="assembly")
    sh.svg(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma list of item numbers (part sheets only)")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("-j", type=int, default=2, help="worker processes for part sheets")
    a = ap.parse_args()
    ensure_sources()
    D.m = sys.modules[__name__]
    p = P()
    parts, inst, purchased, idx = build(None)
    lib = dxf_outlines()
    sheets, dxf = os.path.join(OUT, "sheets"), os.path.join(OUT, "dxf")
    os.makedirs(sheets, exist_ok=True)
    os.makedirs(dxf, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="p6brep_")
    mods = [m for m, _, _ in MODULES if any(d["mod"] == m for d in parts)]
    n0 = 1 + len(mods)
    n = n0 + len(parts)

    # ---- lay flat, stock, cross-check with the DXF library ----
    specs, checks = [], []
    for d in parts:
        flat_solid = lay_flat(d["solid"])
        auto_stock, flat = V.stock_of(flat_solid)
        bb = flat_solid.bounding_box()
        note = []
        stock = d["stock"]
        if d["lab"] and d["lab"] in lib:
            w, h, t = lib[d["lab"]]
            pw, ph = sorted((bb.size.X, bb.size.Y), reverse=True)
            ok = abs(pw - w) < 0.06 and abs(ph - h) < 0.06 and abs(bb.size.Z - t) < 0.02
            bent = not ok and not flat and abs(bb.size.Z - t) > 0.02 and max(pw, ph) < w + 1.1
            checks.append((d["lab"], "bent" if bent else ok, (pw, ph, bb.size.Z), (w, h, t)))
            thick = {0.5: '1/2"', 0.25: '1/4"', 0.125: '1/8"'}[t]
            if bent:
                note.append(f"Bent from {thick} sheet: flat blank {V.frac(w)} x {V.frac(h)} per OSE DXF {d['lab']}.")
                stock = f"{thick} sheet, bent, {w:.1f} x {h:.1f}"
            else:
                note.append(f"DXF library {d['lab']}: {V.frac(w)} x {V.frac(h)} x {V.frac(t)} "
                            + ("- matches the model." if ok else f"- model {V.frac(pw)} x {V.frac(ph)} x {V.frac(bb.size.Z)}; CHECK."))
                if flat:
                    if d["stock"] and not d["stock"].upper().startswith("FLAT BAR"):
                        note.append(f"OSE 2015 weldment redraw makes it from {d['stock']} instead.")
                    stock = auto_stock
        elif d["lab"]:
            checks.append((d["lab"], None, None, None))
            note.append(f"{d['lab']} not found in the original DXF libraries.")
        uses = ", ".join(f"{m} {q}" for m, q in d["mods"].items())
        brep = os.path.join(tmp, f"{d['item']:03d}.brep")
        export_brep(flat_solid, brep)
        e = idx.get(pn(d["num"]), {})
        src = f"OSE {d['num']}" + (f" / weldment {e['wdwg']}" if e.get("wdwg") else "")
        if d["parents"]:
            src += ", in " + ", ".join(d["parents"][:3])
        notes = [f"{src}. Used in: {uses}."] + note + [
            "Geometry from OSE full_assembly.stp (CEB Press 6); title blocks of OSE's 2D set say 'CEB PRESS 5'."]
        if d["per"] > 1:
            notes.append(f"OSE models this part number as {d['per']} solids; the largest is drawn.")
        specs.append(dict(key=d["key"], name=d["name"][:40], qty=d["qty"], stock=short_stock(stock or auto_stock),
                          color=d["mod"], brep=brep, sub=d["mod"], item=d["item"], num=d["num"], lab=d["lab"],
                          views=("F", "L") if flat else ("F", "T", "L"), front="Z", flat=flat, notes=notes,
                          group=d["mod"]))

    manifest, paths = [], []
    only = {int(x) for x in a.only.split(",")} if a.only else None
    if not only:
        # ---- sheet 1: general assembly (fasteners left out of the views) ----
        draw = [x for x in inst if x["mod"] != "Hardware"]
        rows = []
        for i, m in enumerate(mods, 1):
            ms = [x for x in inst if x["mod"] == m]
            rows.append(Row(SubNo(i), m, 1, "Module", sum(x["solid"].volume for x in ms) * STEEL))
        tot = sum(x["solid"].volume for x in inst if not x["buy"]) * STEEL
        path = os.path.join(sheets, "00_assembly.svg")
        asm_sheet(p, TITLE, "General assembly", [(x["mod"], x["leaf"], x["solid"]) for x in draw], rows,
                  {r.name: r.item for r in rows}, 1, n, path, "00",
                  [f"Fabricated steel about {tot:,.0f} lb.",
                   "Model: OSE full_assembly.stp, 01-001-00-6 CEB Press 6 main assembly.",
                   f"Sheets 2-{1 + len(mods)}: modules of the a-z Build 1.0 manual; then one sheet per OSE part number.",
                   "Soil shaker as built in the a-z manual (angle version): see ../shaker."])
        paths.append(path)
        manifest.append(dict(key="assembly", item=0, name="General assembly", sheet=1, file="00_assembly.svg",
                             size="A3", scale="-", qty=1, stock="See parts list", sub="", mass=round(tot, 1), dxf=False))
        print("  00_assembly.svg", flush=True)
        for i, m in enumerate(mods, 1):
            used = [d for d in parts if m in d["mods"]]
            keyed = {d["num"]: d["key"] for d in used}
            draw_m = [(keyed.get(x["leaf"].split()[0] if pn(x["leaf"]) else x["leaf"], "buy"), x["leaf"], x["solid"])
                      for x in inst if x["mod"] == m]
            rows = [Row(d["item"], d["name"][:27], d["mods"][m],
                        next(sp for sp in specs if sp["item"] == d["item"])["stock"][:26], d["solid"].volume * STEEL)
                    for d in used]
            mp_ = [dict(qty=d["mods"][m], key=d["key"], item=d["item"]) for d in used]
            buys = [b for b in purchased if b["mod"] == m]
            notes = [f"{sum(s['qty'] for s in mp_)} fabricated pieces, {len(mp_)} part numbers."]
            if buys:
                notes.append("Purchased: " + "; ".join(f"{b['qty']}x {b['name']}" for b in buys[:8])
                             + (" ..." if len(buys) > 8 else ""))
            path = os.path.join(sheets, f"0{i}_{m.lower().replace(' ', '_')}.svg")
            items = {s["key"]: s["item"] for s in mp_}
            asm_sheet(p, m, f"{TITLE}, module {i}", [x for x in draw_m if x[0] in items], rows, items, 1 + i, n, path,
                      f"S{i}", notes)
            paths.append(path)
            manifest.append(dict(key=f"sub{i}", item=0, name=m, sheet=1 + i, file=os.path.basename(path), size="A3",
                                 scale="-", qty=1, stock="Module", sub=m, mass=round(sum(r.m * r.qty for r in rows), 1),
                                 dxf=False))
            print(f"  {os.path.basename(path)}", flush=True)

    todo = [(s, n0, n, sheets, dxf) for s in specs if not only or s["item"] in only]
    ctx = mp.get_context("spawn")
    with ctx.Pool(max(1, a.j)) as pool:
        for r in pool.imap(_sheet_worker, todo):
            if "error" in r:
                print(f"  !! {r['item']:03d}: {r['error']}", flush=True)
                continue
            manifest.append(r)
            paths.append(os.path.join(sheets, r["file"]))
            print(f"  {r['item']:03d} {r['name']:36s} x{r['qty']:<3d} {r['stock'][:34]:34s} {r['size']} {r['scale']}",
                  flush=True)
    if not only:
        named = sum(1 for d in parts if d["named"])
        lab_ok = sum(1 for c in checks if c[1] is True)
        with open(os.path.join(OUT, "manifest.json"), "w") as f:
            json.dump(dict(model=TITLE, title=TITLE, pdf="CEB_Press_6.pdf", step="CEB_Press_6.step",
                           source="OSE full_assembly.stp (01-001-00-6); OSE CEB a-z Build 1.0 manual",
                           naming=dict(parts=len(parts), described=named,
                                       by_assembly=sum(1 for d in parts if d["how"] == "assembly"),
                                       dxf_labels=len(checks), dxf_match=lab_ok,
                                       dxf_bent=sum(1 for c in checks if c[1] == "bent")),
                           purchased=[dict(module=b["mod"], name=b["name"], qty=b["qty"]) for b in purchased],
                           dxf_checks=[dict(label=c[0], match=c[1], model=c[2], dxf=c[3]) for c in checks],
                           sheets=manifest), f, indent=1)
        kids = []
        cols = {m: c for m, c, _ in MODULES}
        for x in inst:
            s = x["solid"]
            s.color = Color(*cols.get(x["mod"], (0.5, 0.5, 0.5)))
            s.label = x["leaf"]
            kids.append(s)
        export_step(Compound(children=kids, label=TITLE), os.path.join(OUT, "CEB_Press_6.step"), unit=Unit.IN)
        print(f"  named {named}/{len(parts)} part numbers; DXF outlines {lab_ok}/{len(checks)} match", flush=True)
    if not a.no_pdf and paths:
        D.to_pdf(paths, os.path.join(OUT, "CEB_Press_6.pdf"))
        print(f"  {os.path.join(OUT, 'CEB_Press_6.pdf')}", flush=True)


if __name__ == "__main__":
    main()
