"""
CINVA-Ram Block Press — ISO 128 detail drawings from the build123d model.

One sheet per part (plus an assembly sheet with balloons and a parts list),
first-angle projection (ISO 128-30 method E), line types per ISO 128-20/24:
    visible edges      continuous thick 0.50
    hidden edges       dashed thin 0.25            (ISO type 02)
    centre lines       long-dash-dot thin 0.25     (ISO type 04)
    dimensions/leaders continuous thin 0.25
Border and ISO 7200-style title block; dimensions in decimal inches.

Outputs (default drawings/<LxWxH>/):
    sheets/NN_<part>.svg   one SVG per sheet
    CINVA-Ram_<LxWxH>.pdf  all sheets, multi-page
    dxf/<part>.dxf         1:1 flat patterns (inches) for plate parts
    CINVA-Ram_<LxWxH>.step assembly, coloured, inches

Usage:
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 cinva_drawings.py --brick 14x7x4
    ... --model simple         # the permies-style simple press (cinva_simple.py) -> drawings/simple-14x7x4/
    ... --only side,ramp       # just some sheets
"""

from __future__ import annotations

import argparse
import datetime
import math
import os
from dataclasses import dataclass, field

from build123d import (
    Align, Axis, Color, Compound, Edge, ExportDXF, ExportSVG, Face, GeomType, LineType,
    Location, Pos, Rot, Unit, Vector, Wire, export_step,
)
from build123d.exporters import ColorIndex

import cinva_ram_b123d as m

MODELS = {"full": "cinva_ram_b123d", "simple": "cinva_simple"}


def _dwg():
    return getattr(m, "DWG_PREFIX", "CR")


def sheet_rev(key):
    """(rev letter, issue date) for a sheet: the model's REVISIONS / SHEET_REV hooks, else A + today."""
    revs = getattr(m, "REVISIONS", None)
    if not revs:
        return "A", datetime.date.today().isoformat()
    letter = getattr(m, "SHEET_REV", {}).get(key, getattr(m, "CURRENT_REV", next(iter(revs))))
    return letter, revs[letter][0]


def _title():
    return getattr(m, "TITLE", "CINVA-Ram Block Press")

IN = 25.4
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PAPER = {"A4": (297.0, 210.0), "A3": (420.0, 297.0)}
SCALES = [(5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10), (1, 20)]  # ISO 5455
TB_W, TB_H = 180.0, 32.0          # title block
M_LEFT, M_OTHER = 20.0, 10.0      # ISO 5457 filing / other margins
ARROW = 3.0                       # arrowhead length
TXT = 3.5                         # lettering height (ISO 3098 h)
TXT_SMALL = 2.5
EXT_GAP, EXT_OVER = 1.0, 2.0      # extension line gap / overshoot
CHAR_W = 0.9                      # glyph advance / lettering height (DejaVu Sans)
OWNER = "J. Clements III"


# ==========================================================
# Views (first-angle): d = direction toward viewer, up = paper up
# ==========================================================

@dataclass
class View:
    d: Vector
    up: Vector

    @property
    def right(self):
        return self.up.cross(self.d)

    def uv(self, p) -> tuple[float, float]:
        p = Vector(*p)
        return p.dot(self.right), p.dot(self.up)


def views_for(front: str) -> dict[str, View]:
    """Front view + first-angle top (below) and left (right of front)."""
    d, up = {"Z": (Vector(0, 0, 1), Vector(0, 1, 0)),
             "-Y": (Vector(0, -1, 0), Vector(0, 0, 1))}[front]
    f = View(d, up)
    return {"F": f, "T": View(up, -d), "L": View(-f.right, up)}


# ==========================================================
# Sheet: collects paper-space (mm) geometry by layer
# ==========================================================

class Sheet:
    LAYERS = {
        "visible": dict(line_weight=0.50),
        "hidden": dict(line_weight=0.25, line_type=LineType.ISO_DASH),
        "center": dict(line_weight=0.25, line_type=LineType.ISO_LONG_DASH_DOT),
        "thin": dict(line_weight=0.25),
        "border": dict(line_weight=0.70),
        "fill": dict(line_weight=0.01, fill_color=ColorIndex.BLACK),
        "page": dict(line_weight=0.01, line_color=Color(1, 1, 1)),
    }

    def __init__(self, size="A4"):
        self.size = size
        self.W, self.H = PAPER[size]
        self.layers = {k: [] for k in self.LAYERS}

    # --- primitives ---
    def line(self, a, b, layer="thin"):
        if (Vector(*a) - Vector(*b)).length > 1e-6:
            self.layers[layer].append(Edge.make_line(Vector(*a), Vector(*b)))

    def poly(self, pts, layer="thin", close=True):
        pts = list(pts) + ([pts[0]] if close else [])
        for a, b in zip(pts, pts[1:]):
            self.line(a, b, layer)

    def circle(self, c, r, layer="thin"):
        self.layers[layer].append(Edge.make_circle(r).moved(Location((c[0], c[1], 0))))

    def text(self, s, x, y, h=TXT, ha="left", va="bottom", angle=0.0):
        if not s:
            return
        halign = {"left": Align.MIN, "center": Align.CENTER, "right": Align.MAX}[ha]
        valign = {"bottom": Align.MIN, "center": Align.CENTER, "top": Align.MAX}[va]
        t = Compound.make_text(s, h / 0.73, font_path=FONT, align=(halign, valign))
        self.layers["fill"].append(Pos(x, y) * Rot(0, 0, angle) * t)

    def arrow(self, tip, direction):
        """Filled arrowhead with its tip at `tip`, pointing along `direction`."""
        d = Vector(*direction).normalized()
        n = Vector(-d.Y, d.X)
        tip = Vector(*tip)
        base = tip - d * ARROW
        w = ARROW * math.tan(math.radians(9))
        pts = [tip, base + n * w, base - n * w]
        self.layers["fill"].append(Face(Wire.make_polygon(pts, close=True)))

    # --- output ---
    def svg(self, path):
        exp = ExportSVG(unit=Unit.MM, margin=0, fit_to_stroke=False)
        for name, opts in self.LAYERS.items():
            exp.add_layer(name, **opts)
        self.poly([(0, 0), (self.W, 0), (self.W, self.H), (0, self.H)], "page")
        for name, shapes in self.layers.items():
            if shapes:
                exp.add_shape(shapes, layer=name)
        exp.write(path)


# ==========================================================
# Border, title block, projection symbol
# ==========================================================

def border(sh: Sheet):
    x0, y0, x1, y1 = M_LEFT, M_OTHER, sh.W - M_OTHER, sh.H - M_OTHER
    sh.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "border")
    # centring marks (ISO 5457)
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    sh.line((xm, 0), (xm, M_OTHER), "border")
    sh.line((xm, sh.H), (xm, sh.H - M_OTHER - 5), "border")
    sh.line((0, ym), (M_LEFT + 5, ym), "border")
    sh.line((sh.W, ym), (sh.W - M_OTHER - 5, ym), "border")


def projection_symbol(sh: Sheet, x, y, h=6.0):
    """ISO 128 first-angle symbol, lower-left at (x, y)."""
    r1, r2 = h / 2, h / 4
    cx = x + 2.0 * h
    sh.circle((cx, y + r1), r1, "visible")
    sh.circle((cx, y + r1), r2, "visible")
    sh.line((cx - r1 - 1, y + r1), (cx + r1 + 1, y + r1), "center")
    sh.poly([(x, y + r1 - r2), (x + 1.2 * h, y), (x + 1.2 * h, y + h), (x, y + r1 + r2)], "visible")
    sh.line((x - 1, y + r1), (x + 1.2 * h + 1, y + r1), "center")


def title_block(sh: Sheet, title, subtitle, dwg_no, sheet_no, n_sheets, scale, material, qty, doc_type, key=None):
    x1, y0 = sh.W - M_OTHER, M_OTHER
    x0, y1 = x1 - TB_W, y0 + TB_H
    L = lambda a, b: sh.line(a, b, "border")
    sh.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "border")
    # rows: bottom 16 (identification), middle 8, top 8
    L((x0, y0 + 16), (x1, y0 + 16))
    L((x0, y0 + 24), (x1, y0 + 24))
    lab = lambda s, x, y: sh.text(s, x + 1, y - 1, TXT_SMALL * 0.7, va="top")
    val = lambda s, x, y, h=TXT_SMALL: sh.text(s, x + 1.5, y + 1.2, h)

    # top row: material | qty | scale | units | projection
    cols = [0, 62, 88, 116, 144, 180]
    for c in cols[1:-1]:
        L((x0 + c, y0 + 24), (x0 + c, y1))
    for c, (k, v) in zip(cols, [("Material", material), ("Qty", str(qty)), ("Scale", scale),
                                ("Units", "inch"), ("Projection", "")]):
        lab(k, x0 + c, y1)
        val(v, x0 + c, y0 + 24)
    projection_symbol(sh, x0 + 147, y0 + 25.2, 4.5)

    # middle row: created by | approved by | document type | status
    cols = [0, 50, 90, 144, 180]
    for c in cols[1:-1]:
        L((x0 + c, y0 + 16), (x0 + c, y0 + 24))
    for c, (k, v) in zip(cols, [("Created by", OWNER), ("Approved by", "-"),
                                ("Document type", doc_type), ("Status", "Draft")]):
        lab(k, x0 + c, y0 + 24)
        val(v, x0 + c, y0 + 16)

    # bottom: owner | title | dwg no | rev | date | sheet
    cols = [0, 40, 116, 144, 180]
    for c in cols[1:-1]:
        L((x0 + c, y0), (x0 + c, y0 + 16))
    L((x0 + 116, y0 + 8), (x0 + 144, y0 + 8))
    L((x0 + 124, y0), (x0 + 124, y0 + 8))
    lab("Legal owner", x0, y0 + 16)
    sh.text(OWNER, x0 + 1.5, y0 + 6, TXT_SMALL)
    sh.text("CEB Project", x0 + 1.5, y0 + 2, TXT_SMALL)
    lab("Title", x0 + 40, y0 + 16)
    sh.text(title, x0 + 41.5, y0 + 6.5, TXT)
    sh.text(subtitle, x0 + 41.5, y0 + 2, TXT_SMALL)
    lab("Identification number", x0 + 116, y0 + 16)
    sh.text(dwg_no, x0 + 117.5, y0 + 9.5, TXT_SMALL)
    lab("Rev", x0 + 116, y0 + 8)
    rev, issued = sheet_rev(key)
    sh.text(rev, x0 + 118, y0 + 1.5, TXT_SMALL)
    lab("Date of issue", x0 + 124, y0 + 8)
    sh.text(issued, x0 + 125.5, y0 + 1.5, TXT_SMALL)
    lab("Sheet", x0 + 144, y0 + 16)
    sh.text(f"{sheet_no}/{n_sheets}", x0 + 145.5, y0 + 5, TXT)


BASE_NOTES = ["All dimensions in inches. Tolerance ±1/32 unless noted.",
              "Break sharp edges, remove burrs.",
              "Material per title block. Fillet welds 1/4 unless noted."]


def note_lines(notes, width_mm):
    import textwrap
    chars = int(width_mm / (TXT_SMALL * CHAR_W))
    lines = ["NOTES:"]
    for i, n in enumerate(BASE_NOTES + list(notes), 1):
        lines += textwrap.wrap(f"{i}. {n.upper()}", chars, subsequent_indent="   ")
    return lines


def notes_height(notes):
    return 4.0 * len(note_lines(notes, TB_W - 4)) + 3


def general_notes(sh: Sheet, notes, y0=M_OTHER + TB_H):
    """Notes block right-aligned directly above the title block (or above `y0`)."""
    lines = note_lines(notes, TB_W - 4)
    y = y0 + 3 + 4.0 * (len(lines) - 1)
    for s in lines:
        sh.text(s, sh.W - M_OTHER - TB_W + 1.5, y, TXT_SMALL)
        y -= 4.0


# ==========================================================
# Projection & view placement
# ==========================================================

def fmt(v):
    return f"{abs(v):.3f}"


@dataclass
class Placed:
    view: View
    k: float          # paper mm per model inch
    ox: float
    oy: float
    bbox: tuple       # model-space u/v bbox (umin, vmin, umax, vmax)

    def P(self, p3):
        u, v = self.view.uv(p3)
        return Vector(self.ox + self.k * u, self.oy + self.k * v)

    @property
    def paper_bbox(self):
        u0, v0, u1, v1 = self.bbox
        return (self.ox + self.k * u0, self.oy + self.k * v0, self.ox + self.k * u1, self.oy + self.k * v1)


def project(shape, view: View):
    vis, hid = shape.project_to_viewport(view.d * 10000, view.up, (0, 0, 0))
    return list(vis), list(hid)


def uv_bbox(edges):
    b = Compound(edges).bounding_box()
    return (b.min.X, b.min.Y, b.max.X, b.max.Y)


def to_paper(edges, pl: Placed):
    return [e.scale(pl.k).moved(Location((pl.ox, pl.oy, 0))) for e in edges]


def cylinders(shape):
    """(axis_origin, axis_dir, radius, (tmin, tmax)) for full-round cylinder faces."""
    out = []
    for f in shape.faces().filter_by(GeomType.CYLINDER):
        ax = f.axis_of_rotation
        r = f.radius
        pts = [v.to_tuple() for v in f.vertices()] or [f.center().to_tuple()]
        ts = [(Vector(*q) - ax.position).dot(ax.direction) for q in pts]
        h = max(ts) - min(ts) if len(ts) > 1 else 0
        if h <= 0 or f.area < 0.95 * 2 * math.pi * r * h:
            continue
        key = tuple(round(c, 3) for c in (*ax.position.to_tuple(), r))
        o = ax.position + ax.direction * (-(ax.position.dot(ax.direction)))  # canonical
        out.append((ax.position, ax.direction, r, (min(ts), max(ts))))
    # de-dup coaxial (split cylinder faces)
    uniq = []
    for c in out:
        if not any((c[0] - u[0]).cross(u[1]).length < 1e-4 and abs(c[2] - u[2]) < 1e-4 for u in uniq):
            uniq.append(c)
    return uniq


def center_lines(sh: Sheet, shape, pl: Placed):
    ext = 2.5  # mm beyond outline
    for pos, d, r, (t0, t1) in cylinders(shape):
        if abs(d.dot(pl.view.d)) > 0.999:           # end-on: crosshair
            c = pl.P(pos)
            R = r * pl.k + ext
            sh.line((c.X - R, c.Y), (c.X + R, c.Y), "center")
            sh.line((c.X, c.Y - R), (c.X, c.Y + R), "center")
        elif abs(d.dot(pl.view.d)) < 1e-3:          # side-on: axis line
            a, b = pl.P(pos + d * t0), pl.P(pos + d * t1)
            u = (b - a).normalized() * ext
            sh.line(a - u, b + u, "center")


# ==========================================================
# Dimensions (ISO 129-1 style)
# ==========================================================

def dim_linear(sh: Sheet, pl: Placed, p1, p2, off, horizontal, mode="bbox", label=None):
    a, b = pl.P(p1), pl.P(p2)
    bx0, by0, bx1, by1 = pl.paper_bbox
    v1, v2 = pl.view.uv(p1), pl.view.uv(p2)
    if horizontal:
        value = abs(v2[0] - v1[0])
        ref = (max(a.Y, b.Y) if off > 0 else min(a.Y, b.Y)) if mode == "p" else (by1 if off > 0 else by0)
        yd = ref + off
        for q in (a, b):
            s = 1 if yd > q.Y else -1
            if abs(yd - q.Y) > EXT_GAP:
                sh.line((q.X, q.Y + s * EXT_GAP), (q.X, yd + s * EXT_OVER))
        xa, xb = sorted((a.X, b.X))
        _dim_line(sh, Vector(xa, yd), Vector(xb, yd), label or fmt(value), angle=0)
    else:
        value = abs(v2[1] - v1[1])
        ref = (max(a.X, b.X) if off > 0 else min(a.X, b.X)) if mode == "p" else (bx1 if off > 0 else bx0)
        xd = ref + off
        for q in (a, b):
            s = 1 if xd > q.X else -1
            if abs(xd - q.X) > EXT_GAP:
                sh.line((q.X + s * EXT_GAP, q.Y), (xd + s * EXT_OVER, q.Y))
        ya, yb = sorted((a.Y, b.Y))
        _dim_line(sh, Vector(xd, ya), Vector(xd, yb), label or fmt(value), angle=90)


def _dim_line(sh, a, b, label, angle):
    L = (b - a).length
    if L < 1e-6:
        return
    d = (b - a).normalized()
    n = Vector(-d.Y, d.X)                       # text side (above / left)
    tw = len(label) * TXT * CHAR_W
    if L >= 2 * ARROW + 2:
        sh.line(a, b)
        sh.arrow(a, -d)
        sh.arrow(b, d)
    else:                                        # arrows outside, pointing in
        sh.line(a - d * (ARROW + 3), b + d * (ARROW + 3))
        sh.arrow(a, d)
        sh.arrow(b, -d)
    if L >= tw + 2:
        mid = (a + b) * 0.5 + n * 1.0
    else:                                        # text beyond the end
        mid = b + d * (ARROW + 3 + tw / 2) + n * 1.0
    sh.text(label, mid.X, mid.Y, TXT, ha="center", va="bottom", angle=angle)


def dim_leader(sh: Sheet, pl: Placed, c3, size, ang, prefix, radius=False, length=8.0, inward=False):
    c = pl.P(c3)
    r = (size if radius else size / 2) * pl.k
    u = Vector(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    p = c + u * r
    if inward:                  # concave arc: leader comes from the centre side
        u = -u
    if length < 0:  # run out past the view's right/left dimension stack
        bx0, _, bx1, _ = pl.paper_bbox
        edge = bx1 - length if u.X >= 0 else bx0 + length
        length = max(8.0, (edge - p.X) / u.X)
    q = p + u * length
    side = 1 if u.X >= 0 else -1
    label = f"{prefix}{'R' if radius else '⌀'}{size:.3f}"
    tw = len(label) * TXT * CHAR_W
    s_end = q + Vector(side * (tw + 2), 0)
    sh.line(p, q)
    sh.line(q, s_end)
    sh.arrow(p, -u)
    sh.text(label, (q.X + s_end.X) / 2, q.Y + 1.0, TXT, ha="center")


def draw_dims(sh, placed: dict[str, Placed], dims):
    for dm in dims:
        kind, vname = dm[0], dm[1]
        if vname not in placed:
            continue
        pl = placed[vname]
        if kind in ("H", "V"):
            mode = dm[5] if len(dm) > 5 and isinstance(dm[5], str) else "bbox"
            label = dm[6] if len(dm) > 6 else None
            dim_linear(sh, pl, dm[2], dm[3], dm[4], kind == "H", mode, label=label)
        elif kind in ("D", "R", "Ri"):
            dim_leader(sh, pl, dm[2], dm[3], dm[4], dm[5], radius=kind != "D",
                       length=dm[6] if len(dm) > 6 else 8.0, inward=kind == "Ri")


# ==========================================================
# Layout
# ==========================================================

def margins(dims, vname):
    """(left, bottom, right, top) mm needed around a view for its dimensions."""
    m = [8.0, 8.0, 8.0, 8.0]
    for dm in dims:
        if dm[1] != vname:
            continue
        if dm[0] == "H" and not (len(dm) > 5 and dm[5] == "p"):
            i = 3 if dm[4] > 0 else 1
            m[i] = max(m[i], abs(dm[4]) + TXT + 3)
        elif dm[0] == "V" and not (len(dm) > 5 and dm[5] == "p"):
            i = 2 if dm[4] > 0 else 0
            m[i] = max(m[i], abs(dm[4]) + TXT + 3)
        elif dm[0] in ("D", "R", "Ri"):
            ang = dm[4] % 360
            i = 2 if ang < 90 or ang > 270 else 0
            ln = dm[6] if len(dm) > 6 else 8.0
            m[i] = max(m[i], 30.0, (-ln + 30.0) if ln < 0 else 0)
            j = 3 if 0 < ang < 180 else 1
            m[j] = max(m[j], 14.0)
    return m


def layout(boxes, dims, views, notes):
    """Pick paper + scale. A4 unless that forces 1:10 or smaller and A3 does better."""
    a4 = _layout(boxes, dims, views, notes, "A4")
    if a4 and a4[1][0] / a4[1][1] > 1 / 10:
        return a4
    a3 = _layout(boxes, dims, views, notes, "A3")
    if a3 and (not a4 or a3[1][0] / a3[1][1] > a4[1][0] / a4[1][1]):
        return a3
    if a4:
        return a4
    raise RuntimeError("part does not fit on A3")


def _layout(boxes, dims, views, notes, size):
    """Largest ISO scale that fits `size`; (size, scale, k, {view: (ox, oy)}) or None."""
    for size in (size,):
        W, H = PAPER[size]
        ax0, ax1 = M_LEFT + 4, W - M_OTHER - 4
        ay0, ay1 = M_OTHER + TB_H + notes_height(notes) + 4, H - M_OTHER - 4
        for sc in SCALES:
            k = IN * sc[0] / sc[1]
            mg = {v: margins(dims, v) for v in views}
            w = lambda v: (boxes[v][2] - boxes[v][0]) * k
            h = lambda v: (boxes[v][3] - boxes[v][1]) * k
            gap = 6.0
            col1 = max(mg[v][0] + w(v) + mg[v][2] for v in views if v in ("F", "T"))
            tot_w = col1 + (gap + mg["L"][0] + w("L") + mg["L"][2] if "L" in views else 0)
            row1 = max(mg[v][3] + h(v) + mg[v][1] for v in views if v in ("F", "L"))
            tot_h = row1 + (gap + mg["T"][3] + h("T") + mg["T"][1] if "T" in views else 0)
            if tot_w <= ax1 - ax0 and tot_h <= ay1 - ay0:
                x = ax0 + (ax1 - ax0 - tot_w) / 2
                ytop = ay1 - (ay1 - ay0 - tot_h) / 2
                fx = x + mg["F"][0]
                fy_top = ytop - max(mg[v][3] + (h(v) - h("F") if v == "L" else 0) for v in views if v in ("F", "L"))
                fy_top = ytop - mg["F"][3] if "L" not in views else ytop - max(mg["F"][3], mg["L"][3] + h("L") - h("F"))
                org = {"F": (fx - boxes["F"][0] * k, fy_top - h("F") - boxes["F"][1] * k)}
                fb = fy_top - h("F")
                if "T" in views:
                    ty_top = fb - max(mg["F"][1], mg["L"][1] if "L" in views else 0) - gap - mg["T"][3]
                    org["T"] = (fx - boxes["T"][0] * k, ty_top - h("T") - boxes["T"][1] * k)
                if "L" in views:
                    lx = x + col1 + gap + mg["L"][0]
                    org["L"] = (lx - boxes["L"][0] * k, fb - boxes["L"][1] * k)
                return size, sc, k, org
    return None


def scale_str(sc):
    return f"{sc[0]}:{sc[1]}"


# ==========================================================
# Sheets
# ==========================================================

def part_sheet(p: m.Params, part: m.Part, sheet_no, n_sheets, path, dxf_dir=None):
    shape = part.build(p)
    front = getattr(part, "front", "Z")
    vs = views_for(front)
    names = list(part.views)
    proj = {v: project(shape, vs[v]) for v in names}
    boxes = {v: uv_bbox(proj[v][0] + proj[v][1]) for v in names}
    dims = part.dims(p) if part.dims else []
    paper = getattr(part, "paper", None)
    if paper:
        size, sc, k, org = _layout(boxes, dims, names, part.notes, paper)
    else:
        size, sc, k, org = layout(boxes, dims, names, part.notes)
    sh = Sheet(size)
    border(sh)
    placed = {}
    for v in names:
        pl = Placed(vs[v], k, *org[v], boxes[v])
        placed[v] = pl
        vis, hid = proj[v]
        sh.layers["visible"] += to_paper(vis, pl)
        sh.layers["hidden"] += to_paper(hid, pl)
        center_lines(sh, shape, pl)
    draw_dims(sh, placed, dims)
    tbl = getattr(part, "table", None)
    if tbl:                                   # e.g. ordinates of a profile, bottom-left corner
        title, head, rows = tbl(p)
        n = len(head)
        cw = 17.0
        y = M_OTHER + 6 + (len(rows) + 1) * 4.8
        sh.text(title, M_LEFT + 6, y + 3, TXT_SMALL)
        _table(sh, M_LEFT + 6, y, [i * cw for i in range(n + 1)], rows, head=head, rowh=4.8)
    general_notes(sh, part.notes)
    title_block(sh, part.name, f"{_title()}, {p.label} brick", f"{_dwg()}-{p.label}-{part.item:02d}",
                sheet_no, n_sheets, scale_str(sc), part.stock, part.qty, "Detail drawing", key=part.key)
    sh.svg(path)
    if dxf_dir and part.flat:
        exp = ExportDXF(unit=Unit.IN)
        exp.add_layer("CUT")
        exp.add_shape(proj["F"][0], layer="CUT")
        exp.write(os.path.join(dxf_dir, f"{part.item:02d}_{part.key}.dxf"))
    return size, sc


def _asm_view(sh, comp, view, k, cx, ytop, hidden=True):
    """Project `comp`, centre it on x = cx with its top at ytop; return Placed."""
    vis, hid = project(comp, view)
    u0, v0, u1, v1 = uv_bbox(vis)
    ox = cx - (u0 + u1) / 2 * k
    oy = ytop - v1 * k
    pl = Placed(view, k, ox, oy, (u0, v0, u1, v1))
    sh.layers["visible"] += to_paper(vis, pl)
    if hidden:
        sh.layers["hidden"] += to_paper(hid, pl)
    return pl


def _view_label(sh, pl, text, below=6):
    x0, y0, x1, _ = pl.paper_bbox
    sh.text(text, (x0 + x1) / 2, y0 - below, TXT, ha="center", va="top")


def _parts_list(sh, p, plist, rowh=5.5):
    """ISO 7573 item list above the title block, reading upward."""
    x1 = sh.W - M_OTHER
    x0 = x1 - TB_W
    y = M_OTHER + TB_H
    cols = [0, 9, 17, 68, 128, 144, 180]

    def row(vals, y, bold=False):
        sh.line((x0, y + rowh), (x1, y + rowh), "border" if bold else "thin")
        for c in cols[1:-1]:
            sh.line((x0 + c, y), (x0 + c, y + rowh), "thin")
        for c, v in zip(cols, vals):
            sh.text(v, x0 + c + 1.2, y + max(0.8, (rowh - TXT_SMALL) / 2), TXT_SMALL)
    row(["Item", "Qty", "Title", "Stock", "lb ea", "Drawing no."], y, bold=True)
    y += rowh
    for pt in plist:
        row([str(pt.item), str(pt.qty), pt.name, pt.stock, f"{pt.weight(p):.1f}", f"{_dwg()}-{p.label}-{pt.item:02d}"], y)
        y += rowh
    sh.line((x0, M_OTHER + TB_H), (x0, y), "border")
    sh.line((x1, M_OTHER + TB_H), (x1, y), "border")
    sh.line((x0, y), (x1, y), "border")
    return y


def _balloons(sh, pl, inst, items):
    """One balloon per part, spread on an ellipse around the view, leaders to the
    vertex nearest the viewer (most likely visible)."""
    firsts = {}
    for key, _, s in inst:
        firsts.setdefault(key, s)
    bx0, by0, bx1, by1 = pl.paper_bbox
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    anchors = []
    for key, s in firsts.items():
        vtx = max(s.vertices(), key=lambda v: Vector(v).dot(pl.view.d))
        a = pl.P((Vector(vtx) * 0.6 + s.center() * 0.4))
        anchors.append((math.atan2(a.Y - cy, a.X - cx), key, a))
    anchors.sort()
    rx, ry = (bx1 - bx0) / 2 + 12, (by1 - by0) / 2 + 10
    n = len(anchors)
    for i, (_, key, a) in enumerate(anchors):
        ang = anchors[0][0] + 2 * math.pi * i / n
        b = Vector(cx + rx * math.cos(ang), cy + ry * math.sin(ang))
        u = (a - b).normalized()
        sh.line(b + u * 4, a)
        sh.circle((a.X, a.Y), 0.6, "visible")
        sh.circle((b.X, b.Y), 4, "thin")
        sh.text(str(items[key]), b.X, b.Y, TXT, ha="center", va="center")


def _design_notes(p):
    return [f"Brick {p.brick_l:g} x {p.brick_w:g} x {p.brick_h:g}; fill {p.fill:.2f} deep (ratio {p.fill / p.brick_h:.2f}).",
            f"Shown compressed and locked. Handle shown broken, full length {p.handle_len:g}.",
            "See sheet 4 for operation, loads and strength checks."]


def _mass(p, plist):
    return sum(pt.weight(p) * pt.qty for pt in plist)


def _mass_text(p, plist):
    """'about N lb', split into press and attachments when the model groups any part as one."""
    att = set(getattr(m, "ATTACHMENT_GROUPS", ()))
    if not att or not any(pt.group in att for pt in plist):
        return f"about {_mass(p, plist):.0f} lb"
    a = _mass(p, [pt for pt in plist if pt.group in att])
    return f"about {_mass(p, plist) - a:.0f} lb press + {a:.0f} lb {'/'.join(sorted(att)).lower()}"


def assembly_sheet(p: m.Params, plist, n_sheets, path):
    """Sheet 1: isometric view with balloons + parts list."""
    sh = Sheet("A3")
    border(sh)
    inst = m.assembly(p, "locked", handle_len=16.0)
    comp = Compound([s for _, _, s in inst])
    iv = View(Vector(1, -1, 0.8).normalized(), Vector(0, 0, 1))
    iv.up = (iv.up - iv.d * iv.up.dot(iv.d)).normalized()
    area_x0, area_x1 = M_LEFT, sh.W - M_OTHER - TB_W
    pl = _asm_view(sh, comp, iv, IN / 10, (area_x0 + area_x1) / 2, sh.H - M_OTHER - 30, hidden=False)
    _view_label(sh, pl, "ISOMETRIC VIEW", below=22)
    _balloons(sh, pl, inst, {pt.key: pt.item for pt in plist})
    notes = _design_notes(p) + [f"Steel weight {_mass_text(p, plist)}."]
    room = sh.H - M_OTHER - (4.0 * len(note_lines(notes, TB_W - 4)) + 6) - (M_OTHER + TB_H)
    y = _parts_list(sh, p, plist, rowh=min(5.5, room / (len(plist) + 1)))
    general_notes(sh, notes, y0=y)
    title_block(sh, _title(), f"General assembly, {p.label} brick", f"{_dwg()}-{p.label}-00",
                1, n_sheets, "1:10", "See parts list", 1, "Assembly drawing", key="assembly")
    sh.svg(path)


def assembly_views_sheet(p: m.Params, n_sheets, path):
    """Sheet 2: front + left views (first angle), compressed and locked."""
    sh = Sheet("A3")
    border(sh)
    inst = m.assembly(p, "locked", handle_len=16.0)
    comp = Compound([s for _, _, s in inst])
    fv = View(Vector(0, -1, 0), Vector(0, 0, 1))
    lv = View(-fv.right, fv.up)
    k = IN / 5
    rx0, rx1 = p.rail_x
    ytop = sh.H - M_OTHER - 18
    pf = _asm_view(sh, comp, fv, k, M_LEFT + 40 + (rx1 - rx0) * k / 2, ytop)
    vis, hid = project(comp, lv)
    u0, v0, u1, v1 = uv_bbox(vis)
    ox = pf.paper_bbox[2] + 40 - u0 * k
    pl = Placed(lv, k, ox, pf.oy, (u0, v0, u1, v1))
    sh.layers["visible"] += to_paper(vis, pl)
    sh.layers["hidden"] += to_paper(hid, pl)
    if hasattr(m, "asm_view_dims"):
        for view, a, b, off, horiz, label in m.asm_view_dims(p):
            dim_linear(sh, pf if view == "F" else pl, a, b, off, horiz, label=label)
    else:
        L, W = p.brick_l, p.brick_w
        ex, ez = p.eject_roller
        q = p.q_z(90.0)
        dim_linear(sh, pf, (rx0, 0, 0), (rx1, 0, 0), -10, True)
        dim_linear(sh, pf, (0, 0, p.zb), (L, 0, p.zb), -20, True, label=f"{L:.3f} MOLD")
        dim_linear(sh, pf, (p.xc, 0, 0), (ex, 0, ez), -30, True)
        dim_linear(sh, pf, (rx0, 0, 0), (-p.t_end, 0, p.zt), -10, False)
        dim_linear(sh, pf, (rx0, 0, 0), (p.xc, 0, q), -20, False)
        dim_linear(sh, pf, (rx1, 0, 0), (ex, 0, ez), 10, False)
        dim_linear(sh, pl, (0, -p.wall_y, p.zb), (0, p.wall_y, p.zb), -20, True, label=f"{W:.3f} MOLD")
        dim_linear(sh, pl, (0, -(p.rail_y + 1), 0), (0, p.rail_y + 1, 0), -10, True)
    general_notes(sh, _design_notes(p))
    title_block(sh, _title(), f"Assembly views, {p.label} brick", f"{_dwg()}-{p.label}-00",
                2, n_sheets, "1:5", "See parts list", 1, "Assembly drawing", key="assembly_views")
    sh.svg(path)


def positions_sheet(p: m.Params, n_sheets, path):
    """Sheet 3: the four operating positions, front view."""
    sh = Sheet("A3")
    border(sh)
    fv = View(Vector(0, -1, 0), Vector(0, 0, 1))
    order = [("fill", "1  FILL"), ("start", "2  START OF COMPRESSION"),
             ("locked", "3  COMPRESSED AND LOCKED"), ("eject", "4  EJECT")]
    ps = m.poses(p)
    projs = {}
    for key, _ in order:
        comp = Compound([s for _, _, s in m.assembly(p, key)])
        vis, _ = project(comp, fv)
        projs[key] = (vis, uv_bbox(vis))
    # slots: tall start view in its own column; fill + eject side by side; locked (wide) below them
    x0, x1, ytop = M_LEFT + 6, sh.W - M_OTHER - 6, sh.H - M_OTHER - 6
    xs = x0 + 90
    for sc in ((1, 10), (1, 20), (1, 50)):
        k = IN * sc[0] / sc[1]
        w = {key: (b[2] - b[0]) * k for key, (_, b) in projs.items()}
        h = {key: (b[3] - b[1]) * k for key, (_, b) in projs.items()}
        row1 = max(h["fill"], h["eject"]) + 16
        if (w["start"] <= 86 and h["start"] + 16 <= ytop - M_OTHER - 6 and w["fill"] + w["eject"] + 12 <= x1 - xs
                and w["locked"] <= x1 - xs and row1 + h["locked"] + 30 <= ytop - (M_OTHER + TB_H + 40)):
            break
    mid = xs + (x1 - xs) / 2
    slots = {"start": ((x0 + xs) / 2, ytop), "fill": (xs + (x1 - xs) / 4, ytop),
             "eject": (xs + 3 * (x1 - xs) / 4, ytop), "locked": (mid, ytop - row1 - 12)}
    for key, cap in order:
        vis, (u0, v0, u1, v1) = projs[key]
        cx, ctop = slots[key]
        pl = Placed(fv, k, cx - (u0 + u1) / 2 * k, ctop - 12 - v1 * k, (u0, v0, u1, v1))
        sh.layers["visible"] += to_paper(vis, pl)
        po = ps[key]
        sh.text(cap, cx, ctop, TXT, ha="center", va="top")
        piston = po.zp + p.pin_below_cap - p.zt
        sh.text(f"yoke {po.theta:.1f} deg, handle {po.psi:.1f} deg, piston {piston:+.3f}",
                cx, ctop - 6, TXT_SMALL, ha="center", va="top")
    notes = getattr(m, "POSITION_NOTES", [
        "Positions computed from the linkage; all four and the motions between them were checked for clearance.",
        "Yoke tilt from vertical toward the eject roller; handle angle from the yoke axis, positive away from "
        "the eject roller; piston = piston top relative to the mold top."])
    general_notes(sh, notes)
    title_block(sh, _title(), f"Operating positions, {p.label} brick", f"{_dwg()}-{p.label}-00",
                3, n_sheets, scale_str(sc), "-", 1, "Assembly drawing", key="positions")
    sh.svg(path)


def _table(sh, x, y, cols, rows, head=None, rowh=5.2, size=TXT_SMALL):
    """Rows drawn downward from y (top). cols = column x offsets incl. right edge."""
    w = cols[-1]
    allr = ([head] if head else []) + rows
    for i, r in enumerate(allr):
        yy = y - (i + 1) * rowh
        sh.line((x, yy), (x + w, yy), "border" if (head and i == 0) else "thin")
        for c, v in zip(cols, r):
            sh.text(str(v), x + c + 1.2, yy + 1.3, size)
    sh.line((x, y), (x + w, y), "border")
    for c in cols:
        sh.line((x + c, y), (x + c, y - len(allr) * rowh), "thin" if 0 < c < w else "border")
    return y - len(allr) * rowh


def design_sheet(p: m.Params, plist, n_sheets, path):
    """Sheet 4: operation, press data, stroke/force chart, strength checks."""
    sh = Sheet("A3")
    border(sh)
    ps = m.poses(p)
    xl, yt = M_LEFT + 6, sh.H - M_OTHER - 8
    sh.text("PRESS DATA", xl, yt, TXT)
    data = m.press_data(p, ps, _mass(p, plist)) if hasattr(m, "press_data") else [
        ("Brick (pressed)", f"{p.brick_l:g} x {p.brick_w:g} x {p.brick_h:g} in, {p.area:g} sq in face"),
        ("Loose fill depth", f"{p.fill:.3f} in (strike off level with mold top)"),
        ("Compression", f"{p.rise:.3f} in piston stroke, ratio {p.fill / p.brick_h:.2f}"),
        ("Working pressure", f"{p.p_work:g} psi = {p.f_work:,.0f} lbf on the piston"),
        ("Design (overfill) load", f"{p.p_design:g} psi = {p.f_design:,.0f} lbf, all parts checked"),
        ("Handle", f"{p.handle_len:g} in from pivot Q, swings {p.psi0:.0f} to {p.psi_stop:.0f} deg (over centre)"),
        ("Peak push on handle", f"{p.peak_hand(150):.0f} / {p.peak_hand(200):.0f} / {p.peak_hand(250):.0f} lbf "
                                f"at 150 / 200 / 250 psi"),
        ("Ejection", f"piston rises {p.brick_h + p.eject_over:.3f} in; yoke tilts "
                     f"{m.solve_theta(p, p.zp_comp)[1]:.0f} to {ps['eject'].theta:.0f} deg"),
        ("Steel weight", _mass_text(p, plist)),
    ]
    y = _table(sh, xl, yt - 3, [0, 48, 190], [list(r) for r in data])
    y -= 10
    sh.text("OPERATION", xl, y, TXT)
    steps = getattr(m, "OPERATION", None) or [
        "Latch claw shut on the catch bar (handle locked to the yoke), yoke tilted back onto the eject roller. Piston at bottom.",
        "Open the lid. Oil the mold walls. Fill loose soil mix to the top, press into the corners, strike off level.",
        "Close the lid. Swing handle and yoke upright together until the saddle roller sits on the lid track.",
        "Push the claw thumb bar down to flip the claw open onto its stop rod. Pull the handle over, away from the eject roller, past horizontal onto the "
        "handle stop; it goes slightly over centre and stays there. Use two or three firm pushes; it must reach the stop.",
        "Lift the handle back up over centre (it takes little force) to upright, drop the claw onto the catch bar, and tilt "
        "handle and yoke back onto the eject roller.",
        "Open the lid toward the eject roller. Push the handle down to raise the brick clear of the mold. "
        "Lift the brick straight off by its ends.",
        "Weigh or measure each fill: too little soil gives weak bricks; too much overloads the press.",
    ]
    import textwrap
    y -= 2
    for i, st in enumerate(steps, 1):
        for line in textwrap.wrap(f"{i}. {st}", 84, subsequent_indent="    "):
            y -= 4.2
            sh.text(line, xl, y, TXT_SMALL)
    y_ops = y
    # ---- chart ----
    cx0, cx1 = sh.W - M_OTHER - TB_W + 14, sh.W - M_OTHER - 16
    cy1 = sh.H - M_OTHER - 18
    cy0 = cy1 - 80
    sh.text("HAND FORCE AND PISTON RISE OVER THE STROKE", (cx0 + cx1) / 2 - 4, cy1 + 8, TXT_SMALL, ha="center")
    sh.poly([(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], "thin")
    a0 = p.psi0
    a1 = getattr(m, "CHART_END", 90.0)
    fmax = 50 * math.ceil(p.peak_hand(250) / 50)
    X = lambda a: cx0 + (a - a0) / (a1 - a0) * (cx1 - cx0)
    Yf = lambda f: cy0 + f / fmax * (cy1 - cy0)
    Yr = lambda r: cy0 + r / p.rise * (cy1 - cy0)
    for a in range(15 * math.ceil(a0 / 15), int(a1) + 1, 15):
        sh.line((X(a), cy0), (X(a), cy0 - 1.5))
        sh.text(f"{a}", X(a), cy0 - 2.5, TXT_SMALL, ha="center", va="top")
    for f in range(0, fmax + 1, 50):
        sh.line((cx0 - 1.5, Yf(f)), (cx0, Yf(f)))
        sh.text(f"{f}", cx0 - 2.5, Yf(f), TXT_SMALL, ha="right", va="center")
    for r in (0, 1, 2, p.rise):
        sh.line((cx1, Yr(r)), (cx1 + 1.5, Yr(r)))
        sh.text(f"{r:g}", cx1 + 2.5, Yr(r), TXT_SMALL, va="center")
    sh.text("handle angle (deg)", (cx0 + cx1) / 2, cy0 - 8, TXT_SMALL, ha="center", va="top")
    sh.text("hand force (lbf)", cx0 - 12, (cy0 + cy1) / 2, TXT_SMALL, ha="center", va="bottom", angle=90)
    sh.text("piston rise (in)", cx1 + 10, (cy0 + cy1) / 2, TXT_SMALL, ha="center", va="top", angle=90)
    others = [pr for pr in (150, 200, 250) if pr != p.p_work][:2]
    curves = [(p.p_work, "visible")] + list(zip(others, ("hidden", "center")))
    for pr, layer in curves:
        pts = [(X(r[0]), Yf(r[3])) for r in p.stroke_table(pr, step=1)]
        sh.poly(pts, layer, close=False)
    pts = [(X(r[0]), Yr(r[1])) for r in p.stroke_table(p.p_work, step=1)]
    sh.poly(pts, "thin", close=False)
    ly = cy0 - 16
    legend = [(layer, f"hand force, {pr:g} psi" + (" (working)" if layer == "visible" else ""))
              for pr, layer in curves] + [("thin", "piston rise")]
    for layer, lab in legend:
        sh.line((cx0, ly), (cx0 + 10, ly), layer)
        sh.text(lab, cx0 + 12, ly, TXT_SMALL, va="center")
        ly -= 4.5
    # ---- strength table ----
    rows = []
    for item, basis, sig, allow in m.checks(p):
        rows.append([item, f"{sig / 1000:.1f}", f"{allow / 1000:.1f}", f"{sig / allow:.2f}"])
    ty = y_ops - 10
    sh.text(f"STRENGTH CHECKS AT {p.f_design:,.0f} LBF (ksi)", xl, ty, TXT)
    _table(sh, xl, ty - 3, [0, 58, 136, 152, 168, 184], [[r[0], b, *r[1:]] for r, (_, b, _, _) in zip(rows, m.checks(p))],
           head=["Item", "Basis", "Stress", "Allow", "Ratio"], rowh=4.8)
    notes = getattr(m, "DESIGN_NOTES", [
        "First-order hand calculations; build one press and load-test before production.",
        "Allowables: A36 0.66 Fy bending, 0.5 Fu net tension; 4140 prehard 0.6 Fy; AR400 contact 0.3 p <= 0.5 Fy.",
        "Soil model: pressure rises as (e^5x - 1)/(e^5 - 1) over the stroke; lateral wall pressure 0.5 x vertical."])
    general_notes(sh, notes)
    title_block(sh, _title(), f"Operation and design data, {p.label} brick", f"{_dwg()}-{p.label}-00",
                4, n_sheets, "-", "-", 1, "Design data", key="design")
    sh.svg(path)


ASM_SHEETS = [("assembly", "General Assembly", "00a_assembly.svg", "1:10"),
              ("assembly_views", "Assembly Views", "00b_assembly_views.svg", "1:5"),
              ("positions", "Operating Positions", "00c_positions.svg", "1:20"),
              ("design", "Operation and Design Data", "00d_design.svg", "-")]


def build_all(p: m.Params, out, only=None):
    sheets_dir = os.path.join(out, "sheets")
    dxf_dir = os.path.join(out, "dxf")
    os.makedirs(sheets_dir, exist_ok=True)
    os.makedirs(dxf_dir, exist_ok=True)
    plist = m.parts(p)
    n0 = len(ASM_SHEETS)
    n = len(plist) + n0
    paths = []
    manifest = []
    makers = {"assembly": lambda path: assembly_sheet(p, plist, n, path),
              "assembly_views": lambda path: assembly_views_sheet(p, n, path),
              "positions": lambda path: positions_sheet(p, n, path),
              "design": lambda path: design_sheet(p, plist, n, path)}
    for i, (key, name, fname, scale) in enumerate(ASM_SHEETS, 1):
        if only and key not in only and "assembly" not in only:
            continue
        path = os.path.join(sheets_dir, fname)
        makers[key](path)
        paths.append(path)
        manifest.append(dict(key=key, item=0, name=name, sheet=i, file=fname, size="A3", scale=scale,
                             qty=1, stock="See parts list", group="Assembly", rev=sheet_rev(key)[0]))
        print(f"  {fname}")
    for pt in plist:
        if only and pt.key not in only:
            continue
        path = os.path.join(sheets_dir, f"{pt.item:02d}_{pt.key}.svg")
        size, sc = part_sheet(p, pt, pt.item + n0, n, path, dxf_dir)
        paths.append(path)
        manifest.append(dict(key=pt.key, item=pt.item, name=pt.name, sheet=pt.item + n0,
                             file=os.path.basename(path), size=size, scale=scale_str(sc), qty=pt.qty,
                             stock=pt.stock, color=pt.color, dxf=pt.flat, group=pt.group,
                             mass=round(pt.weight(p), 1), rev=sheet_rev(pt.key)[0]))
        print(f"  {pt.item:02d} {pt.name:28s} {size} {scale_str(sc)}")
    if not only:
        import json
        with open(os.path.join(out, "manifest.json"), "w") as f:
            json.dump(dict(brick=p.label, sheets=manifest), f, indent=1)
    return paths


def to_pdf(svgs, pdf_path):
    import cairosvg
    from pypdf import PdfWriter
    w = PdfWriter()
    tmp = []
    for s in svgs:
        t = s[:-4] + ".pdf"
        cairosvg.svg2pdf(url=s, write_to=t)
        w.append(t)
        tmp.append(t)
    w.write(pdf_path)
    for t in tmp:
        os.remove(t)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="14x7x4")
    ap.add_argument("--out", help="output dir (default drawings/<LxWxH>)")
    ap.add_argument("--only", help="comma list of part keys (and/or 'assembly')")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--model", choices=sorted(MODELS), default="full",
                    help="full = heavy-duty press (cinva_ram_b123d), simple = permies-style press (cinva_simple)")
    a = ap.parse_args()
    global m
    import importlib
    m = importlib.import_module(MODELS[a.model])
    p = m.Params(**m.parse_brick(a.brick))
    out = a.out or os.path.join("drawings", getattr(m, "OUT_PREFIX", "") + p.label)
    only = set(a.only.split(",")) if a.only else None
    print(f"{_title()} {p.label} -> {out}")
    paths = build_all(p, out, only)
    if not only:
        step = os.path.join(out, f"{getattr(m, 'FILE_PREFIX', 'CINVA-Ram')}_{p.label}.step")
        export_step(m.assembly_compound(p, "locked"), step, unit=Unit.IN)
        print(f"  {step}")
    if not a.no_pdf and paths:
        pdf = os.path.join(out, f"{getattr(m, 'FILE_PREFIX', 'CINVA-Ram')}_{p.label}.pdf")
        to_pdf(paths, pdf)
        print(f"  {pdf}")


if __name__ == "__main__":
    main()
