"""
ISO 128 drawing set for the Open Source Ecology CEB Press v17.08 (Prototype 9, 2017), from OSE's FreeCAD
assembly File:CEB_17.08_CAD_Assembly.fcstd (wiki.opensourceecology.org/wiki/CEB_Press_v17.08, CC BY-SA).

The FreeCAD file is an A2plus assembly of eight sub-assemblies stored as BREP shells (source/fcstd/*.brp);
part names did not survive, so parts are named by sub-assembly and size. Identical parts (same volume and
area, mirror images included) are drawn once with their quantity. Each part is laid flat on its largest
face, long side along X, for its sheet.

Writes drawings/{sheets/*.svg, dxf/*.dxf, CEB_Press_v17.08.pdf, CEB_Press_v17.08.step, manifest.json}.

Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/v1708_drawings.py [--only 1,5,12] [--no-pdf]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from build123d import (  # noqa: E402
    Axis, Color, Compound, GeomType, Location, Plane, Solid, Unit, Vector, export_step, import_brep,
)

import cinva_drawings as D  # noqa: E402

SRC = os.path.join(HERE, "source", "fcstd")
OUT = os.path.join(HERE, "drawings")
MM = 1 / 25.4
STEEL = 0.2836

SUBS = [  # (brep, name, colour)
    ("PartShape.brp", "Frame", (0.55, 0.57, 0.60)),
    ("PartShape1.brp", "Hopper Seat", (0.80, 0.45, 0.15)),
    ("PartShape2.brp", "Main Cylinder", (0.15, 0.35, 0.75)),
    ("PartShape3.brp", "Drawer", (0.20, 0.55, 0.30)),
    ("PartShape4.brp", "Arms", (0.70, 0.20, 0.20)),
    ("PartShape5.brp", "Hopper", (0.85, 0.70, 0.15)),
    ("PartShape6.brp", "Grate", (0.45, 0.30, 0.60)),
    ("PartShape7.brp", "Secondary Cylinder", (0.10, 0.55, 0.60)),
]

# ---- hooks read by cinva_drawings ----
TITLE = "OSE CEB Press v17.08"
DWG_PREFIX = "OSE1708"
REVISIONS = {"A": ("2026-10-03", "Drawn from OSE CEB_17.08_CAD_Assembly.fcstd (Prototype 9, 2017)")}
CURRENT_REV = "A"
ATTACHMENT_GROUPS = ()


@dataclass
class P:
    label: str = "6x12"


@dataclass
class Part:
    key: str
    name: str
    qty: int
    stock: str
    color: str
    solid: Solid
    sub: str
    item: int = 0
    views: tuple = ("F", "L")
    front: str = "Z"
    flat: bool = True
    notes: tuple = ()
    group: str = ""
    paper: str = ""
    table: object = None
    insts: list = field(default_factory=list)

    def build(self, p):
        return self.solid

    def dims(self, p):
        return auto_dims(self.solid, self.flat)

    def weight(self, p):
        return self.solid.volume * STEEL


def frac(x):
    """Inches as a shop fraction to 1/16 where it is one, else 3 places."""
    f = Fraction(round(x * 16), 16)
    if abs(float(f) - x) > 0.004:
        return f"{x:.3f}"
    w, r = divmod(f.numerator, f.denominator)
    if r == 0:
        return f"{w}"
    return f"{w}-{r}/{f.denominator}" if w else f"{r}/{f.denominator}"


def load():
    """[(sub name, rgb, [world solids in inches])]."""
    out = []
    for brp, name, rgb in SUBS:
        c = import_brep(os.path.join(SRC, brp))
        sols = []
        for sh in c.shells():
            s = Solid(sh)
            if s.volume < 0:
                s = Solid(sh.reversed()) if hasattr(sh, "reversed") else s
            sols.append(s.scale(MM))
        out.append((name, rgb, sols))
    return out


def signature(s: Solid):
    return round(abs(s.volume), 2), round(s.area, 1)


def lay_flat(s: Solid) -> Solid:
    """Largest planar face down on XY (thickness +Z), longest straight edge of it along X, min corner at 0."""
    planar = [f for f in s.faces() if f.geom_type == GeomType.PLANE]
    if planar:
        f = max(planar, key=lambda f: f.area)
        n = f.normal_at()
        c = f.center()
        lines = [e for e in f.edges() if e.geom_type == GeomType.LINE]
        if lines:
            e = max(lines, key=lambda e: e.length)
            xd = (e.end_point() - e.start_point()).normalized()
        else:
            xd = n.cross(Vector(0, 0, 1)) if abs(n.Z) < 0.9 else Vector(1, 0, 0)
            xd = (xd - n * xd.dot(n)).normalized()
        pl = Plane(origin=c, x_dir=xd, z_dir=-n)        # face's outward normal points down
        s = pl.to_local_coords(s)
    bb = s.bounding_box()
    if bb.size.Z > bb.size.X + 1e-6 and bb.size.Z >= bb.size.Y:      # rod / tube standing on its end: lay it along X
        s = s.rotate(Axis.Y, 90)
        bb = s.bounding_box()
    if bb.size.Y > bb.size.X + 1e-6:
        s = s.rotate(Axis.Z, 90)
        bb = s.bounding_box()
    return s.moved(Location((-bb.min.X, -bb.min.Y, -bb.min.Z)))


def stock_of(s: Solid):
    bb = s.bounding_box()
    t, w, L = bb.size.Z, bb.size.Y, bb.size.X
    nominal = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2", 1.0: "1", 0.1875: "3/16", 0.375: "3/8"}
    planar_ratio = sum(f.area for f in s.faces() if f.geom_type == GeomType.PLANE) / s.area
    for v, n in nominal.items():
        if abs(t - v) < 0.012 and planar_ratio > 0.8:
            return f'{n}" plate, {frac(w)} x {frac(L)}', True
    cyl = [f for f in s.faces() if f.geom_type == GeomType.CYLINDER]
    if cyl and planar_ratio < 0.5:
        return f'round / tube, {frac(max(t, w))} dia x {frac(L)}', False
    return f"{frac(L)} x {frac(w)} x {frac(t)} (see model)", False


def holes_of(s: Solid, top):
    """(x, y, dia) of circular edges on the top face (z = top) with vertical axes, largest first, max 12."""
    seen = {}
    for e in s.edges():
        if e.geom_type != GeomType.CIRCLE:
            continue
        c = e.arc_center
        if abs(c.Z - top) > 0.01 or abs(e.length - 2 * math.pi * e.radius) > 1e-3:
            continue
        k = (round(c.X, 3), round(c.Y, 3))
        seen[k] = max(seen.get(k, 0), 2 * e.radius)
    hs = sorted(((x, y, round(d, 4)) for (x, y), d in seen.items()), key=lambda h: (-h[2], h[0], h[1]))
    return hs[:12]


def auto_dims(s: Solid, flat):
    bb = s.bounding_box()
    w, h, t = bb.size.X, bb.size.Y, bb.size.Z
    if flat:
        return D_plate(w, h, holes_of(s, t), t)
    return [("H", "F", (0, 0, 0), (w, 0, 0), -10), ("V", "F", (0, 0, 0), (0, h, 0), -10),
            ("H", "L", (0, 0, 0), (0, 0, t), -10)]


def D_plate(w, h, holes, t):
    from cinva_simple import _plate_dims
    return _plate_dims(w, h, holes, t)


def build_parts(subs):
    parts, items = [], 1
    asm = []                                           # (part key, instance name, world solid)
    for name, rgb, sols in subs:
        groups = {}
        for s in sols:
            groups.setdefault(signature(s), []).append(s)
        order = sorted(groups.items(), key=lambda kv: -kv[0][0])
        for n, (sig, ss) in enumerate(order, 1):
            local = lay_flat(ss[0])
            stock, flat = stock_of(local)
            bb = local.bounding_box()
            key = f"{name.lower().replace(' ', '_')}_{n:02d}"
            pname = f"{name} {n:02d}"
            notes = (f"Sub-assembly: {name}. {len(ss)} off, identical or mirror images.",
                     "Geometry from OSE CEB_17.08_CAD_Assembly.fcstd; check against the OSE CAM files "
                     "(source/CEB_v1708_CAM.zip) before cutting.")
            pt = Part(key, pname, len(ss), stock, name, local, name, item=items,
                      views=("F", "L") if flat else ("F", "T", "L"), flat=flat, notes=notes, group=name)
            pt.size = (bb.size.X, bb.size.Y, bb.size.Z)
            parts.append(pt)
            for j, s in enumerate(ss):
                asm.append((key, f"{pname} #{j + 1}", s))
            items += 1
    return parts, asm


def asm_sheet(p, title, subtitle, inst, plist, items, sheet_no, n, path, key, notes):
    sh = D.Sheet("A3")
    D.border(sh)
    comp = Compound([s for _, _, s in inst])
    iv = D.View(Vector(1, -1, 0.8).normalized(), Vector(0, 0, 1))
    iv.up = (iv.up - iv.d * iv.up.dot(iv.d)).normalized()
    bb = comp.bounding_box()
    span = max(bb.size.X, bb.size.Y, bb.size.Z) * 1.25
    area_x0, area_x1 = D.M_LEFT, sh.W - D.M_OTHER - D.TB_W
    k = None
    for sc in D.SCALES:
        kk = D.IN * sc[0] / sc[1]
        if span * kk < min(area_x1 - area_x0 - 40, sh.H - 2 * D.M_OTHER - 50):
            k, scale = kk, D.scale_str(sc)
            break
    pl = D._asm_view(sh, comp, iv, k, (area_x0 + area_x1) / 2, sh.H - D.M_OTHER - 28, hidden=False)
    D._view_label(sh, pl, "ISOMETRIC VIEW", below=20)
    D._balloons(sh, pl, inst, items)
    room = sh.H - D.M_OTHER - (4.0 * len(D.note_lines(notes, D.TB_W - 4)) + 6) - (D.M_OTHER + D.TB_H)
    y = D._parts_list(sh, p, plist, rowh=min(5.5, room / (len(plist) + 1)))
    D.general_notes(sh, notes, y0=y)
    D.title_block(sh, title, subtitle, f"{DWG_PREFIX}-{p.label}-{key}", sheet_no, n, scale, "See parts list", 1,
                  "Assembly drawing", key="assembly")
    sh.svg(path)


class SubNo(int):
    """Sub-assembly item number, printed S1..S8 in the parts list's drawing numbers."""
    def __format__(self, spec):
        return f"S{int(self)}"

    def __str__(self):
        return f"S{int(self)}"


class SubRow:
    """A sub-assembly as a row of the general assembly's parts list."""
    def __init__(self, i, name, qty, mass):
        self.item, self.qty, self.name, self.stock, self.m = i, qty, name, "Sub-assembly", mass

    def weight(self, p):
        return self.m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma list of item numbers")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    D.m = sys.modules[__name__]
    p = P()
    subs = load()
    parts, asm = build_parts(subs)
    only = {int(x) for x in a.only.split(",")} if a.only else None
    sheets = os.path.join(OUT, "sheets")
    dxf = os.path.join(OUT, "dxf")
    os.makedirs(sheets, exist_ok=True)
    os.makedirs(dxf, exist_ok=True)
    n0 = 1 + len(SUBS)
    n = n0 + len(parts)
    paths, manifest = [], []
    # sheet 1: general assembly, one balloon per sub-assembly
    if not only:
        inst = [(name, name, Compound(sols)) for name, _, sols in subs]
        rows = [SubRow(SubNo(i + 1), name, 1, sum(s.volume for s in sols) * STEEL) for i, (name, _, sols) in enumerate(subs)]
        path = os.path.join(sheets, "00_assembly.svg")
        tot = sum(r.m for r in rows)
        asm_sheet(p, TITLE, "General assembly", inst, rows, {r.name: r.item for r in rows}, 1, n, path, "00",
                  [f"Steel weight about {tot:,.0f} lb (all parts as steel).",
                   "Model: OSE CEB_17.08_CAD_Assembly.fcstd (A2plus), wiki.opensourceecology.org/wiki/CEB_Press_v17.08.",
                   "Sheets 2-9: sub-assemblies; then one sheet per distinct part."])
        paths.append(path)
        manifest.append(dict(key="assembly", sheet=1, file=os.path.basename(path), name="General assembly"))
        print("  00_assembly.svg")
        for i, (name, _, sols) in enumerate(subs):
            sp = [pt for pt in parts if pt.sub == name]
            inst = [x for x in asm if x[0] in {pt.key for pt in sp}]
            path = os.path.join(sheets, f"0{i + 1}_{name.lower().replace(' ', '_')}.svg")
            asm_sheet(p, f"{name}", f"{TITLE}, sub-assembly {i + 1}", inst, sp, {pt.key: pt.item for pt in sp},
                      2 + i, n, path, f"S{i + 1}",
                      [f"{sum(pt.qty for pt in sp)} parts, {len(sp)} distinct; about "
                       f"{sum(pt.weight(p) * pt.qty for pt in sp):,.0f} lb."])
            paths.append(path)
            manifest.append(dict(key=f"sub{i + 1}", sheet=2 + i, file=os.path.basename(path), name=name))
            print(f"  {os.path.basename(path)}")
    for pt in parts:
        if only and pt.item not in only:
            continue
        path = os.path.join(sheets, f"{pt.item:03d}_{pt.key}.svg")
        try:
            size, sc = D.part_sheet(p, pt, pt.item + n0, n, path, dxf if pt.flat else None)
        except Exception as ex:                         # noqa: BLE001
            print(f"  !! {pt.item:03d} {pt.name}: {ex}")
            continue
        paths.append(path)
        manifest.append(dict(key=pt.key, item=pt.item, name=pt.name, sheet=pt.item + n0, file=os.path.basename(path),
                             size=size, scale=D.scale_str(sc), qty=pt.qty, stock=pt.stock, sub=pt.sub,
                             mass=round(pt.weight(p), 1), dxf=pt.flat))
        print(f"  {pt.item:03d} {pt.name:22s} x{pt.qty:<3d} {pt.stock:40s} {size} {D.scale_str(sc)}")
    if not only:
        with open(os.path.join(OUT, "manifest.json"), "w") as f:
            json.dump(dict(model="OSE CEB Press v17.08", sheets=manifest), f, indent=1)
        kids = []
        for name, rgb, sols in subs:
            for s in sols:
                s.color = Color(*rgb)
                s.label = name
                kids.append(s)
        export_step(Compound(children=kids, label=TITLE), os.path.join(OUT, "CEB_Press_v17.08.step"), unit=Unit.IN)
    if not a.no_pdf and paths:
        D.to_pdf(paths, os.path.join(OUT, "CEB_Press_v17.08.pdf"))
        print(f"  {os.path.join(OUT, 'CEB_Press_v17.08.pdf')}")


if __name__ == "__main__":
    main()
