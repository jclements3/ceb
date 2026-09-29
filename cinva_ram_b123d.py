"""
CINVA-Ram Block Press — parametric build123d model.

Port of cinva_ram.scad (part library + assembled press at the bottom of
that file). Every dimension that depends on the brick is derived from
BRICK_L x BRICK_W x BRICK_H; everything else (lever, toggle, clamp, ramp
peak/scoop geometry) is carried over unchanged.

Units: inches (1/4" plate unless noted). World frame matches the SCAD file:
    X = along the mold length, mold spans X0 .. X0 + BRICK_L
    Y = across the mold, centred on Y = 0
    Z = up, ground at Z = 0

Usage:
    python3 cinva_ram_b123d.py                      # 12 x 6 x 4 brick
    python3 cinva_ram_b123d.py --brick 14x7x4       # any L x W x H
    python3 cinva_ram_b123d.py --brick 14x7x4 --t 0.3 --step press.step

Needs LD_LIBRARY_PATH=$HOME/miniconda3/lib on this machine (conda's pyexpat
is otherwise linked against the older system libexpat).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from functools import cached_property

from build123d import (
    Align, Axis, Box, Color, Compound, Cylinder, Face, Location, Plane, Polygon,
    Pos, Rot, Solid, Unit, Vector, Wire, export_step, extrude,
)


# ==========================================================
# Parameters
# ==========================================================

@dataclass(frozen=True)
class Params:
    brick_l: float = 12.0     # mold length (X)
    brick_w: float = 6.0      # mold width (Y)
    brick_h: float = 4.0      # finished brick height
    t: float = 0.250          # plate thickness
    clear: float = 0.0625     # shelf-to-mold clearance (total, each axis)
    fill_ratio: float = 1.875  # loose-fill depth / pressed height -> end plate height
    frame_h: float = 15.0     # side plate height (Z)
    x0: float = 4.0           # mold start X (base brackets start here too)
    anim: float = 0.5         # 0 = roller on right slope, 0.5 = locked in scoop, 1 = left slope
    lever_angle: float = 87.0  # degrees, lever tilt about the load pin

    # --- fixed mechanism dimensions (not brick dependent) ---
    lever_len: float = 19.625
    lever_load_hole: float = 18.625   # along bar from grip end
    lever_roller_dist: float = 14.625  # load pin -> roller hole
    fulcrum_offset: float = 5.0        # fulcrum pin is this far -X of mold centre
    ramp_y_inner: float = 2.0          # ramps sit at |Y| = 2.000 .. 2.250
    roller_len: float = 6.0
    handle_len: float = 72.0
    base_len: float = 36.0

    @property
    def label(self) -> str:
        f = lambda v: f"{v:g}"
        return f"{f(self.brick_l)}x{f(self.brick_w)}x{f(self.brick_h)}"

    # --- derived: frame ---
    @property
    def xc(self):            # mold centre X (scoop, load pin, piston)
        return self.x0 + self.brick_l / 2

    @property
    def side_y(self):        # inner face of side plates
        return self.brick_w / 2

    @property
    def top_z(self):         # top edge of side plates
        return self.t + self.frame_h

    @property
    def ramp_base(self):     # underside of ramps (top of Top plate)
        return self.top_z + self.t

    @property
    def end_h(self):
        return self.fill_ratio * self.brick_h

    @property
    def lever_in(self):      # inner face of lever bars: clear the side plates by 1/2"
        return self.side_y + self.t + 0.5

    @property
    def cross_len(self):
        return 2 * (self.lever_in + self.t)

    @property
    def pin_len(self):       # fulcrum + load pins
        return self.cross_len + 0.5

    @property
    def fulcrum_x(self):
        return self.xc - self.fulcrum_offset

    @property
    def fulcrum_z(self):
        return self.t + self.frame_h / 2

    @property
    def ramp_peak(self):     # (left, right) ends of the flat peak, ramp-local X
        return self.brick_l / 2 - 0.625, self.brick_l / 2 + 1.625

    # --- derived: kinematics (same equations as cinva_ram.scad) ---
    @cached_property
    def kin(self) -> dict:
        L, xc, rb = self.brick_l, self.xc, self.ramp_base
        scoop_r, roller_r = 0.625, 0.500
        scoop_cz = rb + 3.0
        raw_x = (xc + 3.5) + self.anim * ((xc - 3.0) - (xc + 3.5))
        in_scoop = abs(raw_x - xc) <= scoop_r
        pl, pr = self.ramp_peak
        lx = raw_x - self.x0
        if lx > pr:
            surf = 1.0 + (L - lx) / (L - pr) * 2.0
        elif lx < pl:
            surf = 0.25 + lx / pl * 2.75
        else:
            surf = 3.0
        roller_x = xc if in_scoop else raw_x
        rest_z = scoop_cz - scoop_r + roller_r
        roller_z = rest_z if in_scoop else rb + surf + roller_r
        a = math.radians(self.lever_angle)
        load_z = roller_z - self.lever_roller_dist * math.sin(a)
        asm_dz = roller_z - rest_z
        axle_z = rb + 7.5 + asm_dz
        cf_z = load_z + self.lever_load_hole * math.sin(a) - math.cos(a)
        R = math.hypot(3.255, 0.155)
        phi = math.degrees(math.atan2(-0.155, 3.255))
        clamp = math.degrees(math.asin(max(-1, min(1, (cf_z - axle_z) / R)))) - phi
        return dict(
            roller_x=roller_x, roller_z=roller_z, dx=roller_x - xc, dz=asm_dz,
            load_z=load_z, shelf_z=load_z + 6.25, clamp_angle=clamp,
        )

    def pressure_ratio(self, ref: "Params") -> float:
        """Brick-face pressure relative to `ref` for the same lever force."""
        return (ref.brick_l * ref.brick_w) / (self.brick_l * self.brick_w)


# ==========================================================
# Primitive helpers (all local: profile in XY, thickness +Z)
# ==========================================================

def plate(w, h, t):
    return Box(w, h, t, align=Align.MIN)


def hole(x, y, d, t):
    return Pos(x, y, -0.01) * Cylinder(d / 2, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))


def extrude_poly(pts, t, fillets=()):
    """Extrude a closed polygon; `fillets` = [(radius, (x, y)), ...] 2D-fillets vertices."""
    f = Face(Wire.make_polygon([Vector(*p) for p in pts], close=True))
    for r, (vx, vy) in fillets:
        v = [x for x in f.vertices() if abs(x.X - vx) < 1e-6 and abs(x.Y - vy) < 1e-6]
        f = f.fillet_2d(r, v)
    return extrude(f, t)


def rod(d, length, axis="Y", centered=True):
    """Round bar along an axis, base at origin (or centred on it)."""
    c = Cylinder(d / 2, length, align=(Align.CENTER, Align.CENTER,
                                       Align.CENTER if centered else Align.MIN))
    return {"X": Rot(0, 90, 0), "Y": Rot(-90, 0, 0), "Z": Location()}[axis] * c


# ==========================================================
# Part library (local coordinates)
# ==========================================================

def side(p: Params):
    """Side plate: X = along mold (0..L), Y = height (0..frame_h)."""
    L, H, t = p.brick_l, p.frame_h, p.t
    s = plate(L, H, t)
    s -= hole(p.fulcrum_x - p.x0, H / 2, 1.000, t)            # fulcrum pin
    s -= hole(3.0, 1.0, 0.500, t) + hole(L - 3.0, 1.0, 0.500, t)  # base bolts
    s -= Pos(L / 2 - 0.5, 3.150, -0.01) * Box(1.0, 8.0, t + 0.02, align=Align.MIN)  # load-pin slot
    return s


def end_plate(p: Params):
    return plate(p.brick_w + 2 * p.t, p.end_h, p.t)


def top(p: Params):
    return plate(p.brick_l + 2 * p.t, p.brick_w + 2 * p.t, p.t)


def ramp_points(p: Params):
    L = p.brick_l
    pl, pr = p.ramp_peak
    return [(0, 0), (L, 0), (L, 1.0), (pr, 3.0), (pl, 3.0), (0, 0.25)]


def ramp(p: Params):
    pl, _ = p.ramp_peak
    r = extrude_poly(ramp_points(p), p.t)
    return r - Pos(pl + 0.625, 3.0, -0.01) * Cylinder(0.625, p.t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))


def shelf(p: Params):
    return plate(p.brick_l - p.clear, p.brick_w - p.clear, p.t)


def shelf_bracket(p: Params):
    return plate(p.brick_l - 1.0, 2.0, p.t)


def piston(p: Params):
    return plate(6.0, 7.25, p.t) - hole(3.0, 1.0, 1.000, p.t)


def base_bracket(p: Params):
    """2x2x1/4 angle: X = length, vertical leg in XZ at Y 0..t, horizontal leg in XY."""
    n, leg, t, L = p.base_len, 2.0, p.t, p.brick_l
    b = Box(n, t, leg, align=Align.MIN) + Box(n, leg, t, align=Align.MIN)
    for x in (3.0, n / 2, n - 3.0):
        b -= hole(x, leg / 2, 0.500, t)
    for x in (3.0, L - 3.0):  # match side-plate bolt holes (Z = t + 1)
        b -= Pos(x, -0.01, t + 1.0) * rod(0.500, t + 0.02, "Y", centered=False)
    return b


def lever_bar(p: Params):
    n, t = p.lever_len, p.t
    b = extrude_poly([(0, 0), (n, 0), (n, 2), (0, 2)], t, fillets=[(0.25, (n, 0)), (0.25, (n, 2))])
    return b - hole(p.lever_load_hole, 1.0, 1.000, t)


def lever_cross(p: Params):
    return plate(2.0, p.cross_len, p.t)


def lever_block(p: Params):
    """4 x 1.5 x 2 block, 1" roller hole along Y at x = 3."""
    b = Box(4.0, 1.5, 2.0, align=Align.MIN)
    return b - Pos(3.0, -0.01, 1.0) * rod(1.000, 1.52, "Y", centered=False)


def pivot(p: Params):
    b = Box(2, 2, 6, align=Align.MIN) + Pos(-1, 0, 5) * Box(1, 2, 1, align=Align.MIN)
    b -= Pos(1, 1, 2) * Cylinder(0.5, 4.01, align=(Align.CENTER, Align.CENTER, Align.MIN))  # handle socket
    b -= Pos(1, -0.01, 1) * rod(1.000, 2.02, "Y", centered=False)                           # spacer pin
    b -= Pos(-1 + 0.397, -0.01, 5.5) * rod(0.437, 2.02, "Y", centered=False)                # axle
    return b


def _toggle_link(h, holes, t):
    s = extrude_poly([(0, 0), (2, 0), (2, h), (0, h)], t, fillets=[(0.375, (0, 0)), (0.375, (2, 0))])
    for y in holes:
        s -= hole(1.0, y, 1.000, t)
    return s


def wing(p: Params):
    return _toggle_link(5.625, (1.250, 4.625), p.t)


def tail(p: Params):
    return _toggle_link(3.625, (1.250,), p.t)


CLAMP_PTS = [(0, 0), (2.929, 0), (3.048, 0.504), (3.652, 0.345), (3.571, 0),
             (3.880, 0), (4.147, 1.000), (0, 1.000)]


def clamp(p: Params):
    c = extrude_poly(CLAMP_PTS, p.t, fillets=[(0.25, (0, 0)), (0.25, (0, 1))])
    return c - hole(0.397, 0.500, 0.437, p.t)


def grabber(p: Params):
    return plate(2.75, 1.0, p.t)


def receiver(p: Params):
    return Cylinder(0.5, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) - \
        Cylinder(0.25, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def tab_reach(p: Params):
    """Ramp outer face to receiver centre (Y)."""
    return (p.side_y + p.t + 0.5) - (p.ramp_y_inner + p.t)


def tab(p: Params):
    d = tab_reach(p)
    s = Box(1.0, d, p.t, align=(Align.CENTER, Align.MIN, Align.MIN))
    s += Pos(0, d, 0) * Cylinder(0.5, p.t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s - hole(0, d, 0.500, p.t)


def hinge_pin(p: Params):
    return rod(0.440, 2.0 - 0.125 + 2 * p.t, "Z", centered=False)


# Round stock (drawn as simple turned parts)
def fulcrum_pin(p): return rod(0.950, p.pin_len, "X", centered=False)
def load_pin(p): return rod(0.950, p.pin_len, "X", centered=False)
def roller(p): return rod(1.000, p.roller_len, "X", centered=False)
def spacer_pin(p): return rod(1.000, 3.0, "X", centered=False)
def axle(p): return rod(0.437, 3.0, "X", centered=False)
def handle(p): return rod(0.950, p.handle_len, "X", centered=False)


# ==========================================================
# Part registry — one entry per drawing sheet / BOM line
# ==========================================================

@dataclass
class Part:
    key: str
    name: str
    qty: int
    stock: str
    color: str
    build: callable
    views: tuple = ("F", "L")   # F = front, T = top (below F), L = left view (right of F)
    dims: callable = None       # p -> list of dimension tuples (see cinva_drawings.py)
    notes: tuple = ()
    flat: bool = True           # emit a DXF flat pattern of the front view
    front: str = "Z"            # front view looks from +Z ("Z") or from -Y ("-Y")
    item: int = 0


def _plate_dims(w, h, holes=(), t=None, lead=None):
    """Overall size, hole locations (baseline from lower-left) and diameters."""
    d = [("H", "F", (0, 0, 0), (w, 0, 0), -12), ("V", "F", (0, 0, 0), (0, h, 0), -12)]
    seen_x, seen_y = set(), set()
    off_x, off_y = 10, 10
    for i, (x, y, dia) in enumerate(holes):
        if round(x, 3) not in seen_x and 0.01 < x < w - 0.01:
            d.append(("H", "F", (0, h, 0), (x, y, 0), off_x + 8 * len(seen_x)))
            seen_x.add(round(x, 3))
        if round(y, 3) not in seen_y and 0.01 < y < h - 0.01:
            d.append(("V", "F", (w, 0, 0), (x, y, 0), off_y + 8 * len(seen_y)))
            seen_y.add(round(y, 3))
    by_d = {}
    for x, y, dia in holes:
        by_d.setdefault(dia, []).append((x, y))
    clear = -(off_y + 8 * max(len(seen_y), 1) + 2)   # past the right-hand stack
    for dia, pts in by_d.items():
        n = len(pts)
        top = max(range(n), key=lambda j: pts[j][1])
        i, ang, ln = (lead or {}).get(dia, (top, 25, clear))
        d.append(("D", "F", (*pts[i], 0), dia, ang, f"{n}x " if n > 1 else "", ln))
    if t is not None:
        d.append(("H", "L", (0, 0, 0), (0, 0, t), -12))
    return d


def parts(p: Params) -> list[Part]:
    L, W, t = p.brick_l, p.brick_w, p.t
    pl, pr = p.ramp_peak
    fx = p.fulcrum_x - p.x0
    ps = [
        Part("side", "Side Plate", 2, f'{t:.3f}" plate', "gray", side,
             dims=lambda p: _plate_dims(L, p.frame_h, [(fx, p.frame_h / 2, 1.0), (3, 1, 0.5), (L - 3, 1, 0.5)], t,
                                         lead={0.5: (1, 110, 20.0)}) + [
                 ("H", "F", (L / 2 - 0.5, 11.15, 0), (L / 2 + 0.5, 11.15, 0), 6, "p"),
                 ("V", "F", (L / 2 + 0.5, 3.15, 0), (L / 2 + 0.5, 11.15, 0), 6, "p"),
                 ("V", "F", (L, 0, 0), (L / 2 + 0.5, 3.15, 0), 26),
                 ("H", "F", (0, p.frame_h, 0), (L / 2 - 0.5, 11.15, 0), 34)],
             notes=("Slot 1.000 wide guides the load pin.",)),
        Part("end", "End Plate", 2, f'{t:.3f}" plate', "gray", end_plate,
             dims=lambda p: _plate_dims(W + 2 * t, p.end_h, (), t)),
        Part("top", "Top Plate", 1, f'{t:.3f}" plate', "red", top,
             dims=lambda p: _plate_dims(L + 2 * t, W + 2 * t, (), t)),
        Part("ramp", "Ramp", 2, f'{t:.3f}" plate', "red", ramp,
             dims=lambda p: [
                 ("H", "F", (0, 0, 0), (L, 0, 0), -10),
                 ("V", "F", (0, 0, 0), (0, 0.25, 0), -8),
                 ("V", "F", (L, 0, 0), (L, 1.0, 0), 8),
                 ("V", "F", (L, 0, 0), (pr, 3.0, 0), 16),
                 ("H", "F", (0, 0.25, 0), (pl, 3.0, 0), 8),
                 ("H", "F", (0, 0.25, 0), (pl + 0.625, 3.0, 0), 16),
                 ("H", "F", (0, 0.25, 0), (pr, 3.0, 0), 24),
                 ("R", "F", (pl + 0.625, 3.0, 0), 0.625, 300, ""),
                 ("H", "L", (0, 0, 0), (0, 0, t), -12)],
             notes=("Scoop centre on mold centreline; roller locks here.",)),
        Part("shelf", "Shelf (Press Face)", 1, f'{t:.3f}" plate', "teal", shelf,
             dims=lambda p: _plate_dims(L - p.clear, W - p.clear, (), t),
             notes=(f"Mold is {L:g} x {W:g}; shelf is {p.clear:.4g} under each way.",)),
        Part("bracket", "Shelf Bracket", 2, f'{t:.3f}" plate', "teal", shelf_bracket,
             dims=lambda p: _plate_dims(L - 1, 2.0, (), t)),
        Part("piston", "Piston Plate", 4, f'{t:.3f}" plate', "teal", piston,
             dims=lambda p: _plate_dims(6.0, 7.25, [(3, 1, 1.0)], t),
             notes=("Weld in pairs (0.500 thick).",)),
        Part("base", "Base Bracket", 2, '2x2x1/4 angle', "green", base_bracket, views=("F", "T", "L"), front="-Y",
             dims=lambda p: [
                 ("H", "F", (0, 0, 0), (p.base_len, 0, 0), -10),
                 ("H", "F", (0, 0, 2), (3, 0, 1 + t), 8), ("H", "F", (0, 0, 2), (L - 3, 0, 1 + t), 16),
                 ("V", "F", (p.base_len, 0, 0), (p.base_len, 0, 2), 8),
                 ("V", "F", (0, 0, 0), (3, 0, 1 + t), -8),
                 ("D", "F", (L - 3, 0, 1 + t), 0.5, 30, "2x "),
                 ("H", "T", (0, 2, 0), (p.base_len / 2, 1, 0), -8),
                 ("V", "T", (0, 0, 0), (3, 1, 0), -8),
                 ("D", "T", (p.base_len - 3, 1, 0), 0.5, 300, "3x "),
                 ("H", "L", (0, 0, 0), (0, 2, 0), -8)],
             notes=("Vertical-leg holes match side plate bolt holes.",
                    "Horizontal holes at 3.000 from each end and centre."), flat=False),
        Part("lever", "Lever Bar", 2, f'{t:.3f}" x 2" flat bar', "orange", lever_bar,
             dims=lambda p: _plate_dims(p.lever_len, 2.0, [(p.lever_load_hole, 1.0, 1.0)], t) + [
                 ("R", "F", (p.lever_len - 0.25, 0.25, 0), 0.25, 315, "2x ", 10)]),
        Part("cross", "Lever Cross", 2, f'{t:.3f}" x 2" flat bar', "orange", lever_cross,
             dims=lambda p: _plate_dims(2.0, p.cross_len, (), t)),
        Part("block", "Lever Spacer Block", 1, "2 x 1-1/2 bar", "orange", lever_block, views=("F", "T", "L"),
             front="-Y",
             dims=lambda p: [("H", "F", (0, 0, 0), (4, 0, 0), -10), ("V", "F", (4, 0, 0), (4, 0, 2), 8),
                             ("H", "F", (0, 0, 2), (3, 0, 1), 8), ("V", "F", (0, 0, 0), (3, 0, 1), -8),
                             ("D", "F", (3, 0, 1), 1.0, 45, ""), ("H", "L", (0, 0, 0), (0, 1.5, 0), -10)],
             notes=("Roller hole 1.000 through.",), flat=False),
        Part("pivot", "Pivot Block", 1, "2 x 2 bar", "brown", pivot, views=("F", "T", "L"), front="-Y",
             dims=lambda p: [("H", "F", (-1, 0, 0), (2, 0, 0), -10), ("V", "F", (2, 0, 0), (2, 0, 6), 8),
                             ("H", "F", (-1, 0, 6), (0, 0, 5), 8), ("H", "F", (-1, 0, 6), (-0.603, 0, 5.5), 16),
                             ("H", "F", (-1, 0, 6), (1, 0, 1), 24),
                             ("V", "F", (-1, 0, 6), (-1, 0, 5), -8), ("V", "F", (-1, 0, 6), (-0.603, 0, 5.5), -16),
                             ("V", "F", (0, 0, 0), (1, 0, 1), -24), ("V", "F", (2, 0, 6), (2, 0, 2), 16),
                             ("D", "F", (1, 0, 1), 1.0, 300, ""), ("D", "F", (-0.603, 0, 5.5), 0.437, 225, "", 10),
                             ("D", "T", (1, 1, 6), 1.0, 45, ""), ("H", "L", (0, 0, 0), (0, 2, 0), -10)],
             notes=("Handle socket 1.000 dia x 4.000 deep from top.",
                    "Spacer-pin and axle holes through (Y)."), flat=False),
        Part("wing", "Wing (Long Toggle Link)", 2, f'{t:.3f}" plate', "brown", wing,
             dims=lambda p: _plate_dims(2.0, 5.625, [(1, 1.25, 1.0), (1, 4.625, 1.0)], t) + [
                 ("R", "F", (0.375, 0.375, 0), 0.375, 225, "2x ")]),
        Part("tail", "Tail (Short Toggle Link)", 2, f'{t:.3f}" plate', "brown", tail,
             dims=lambda p: _plate_dims(2.0, 3.625, [(1, 1.25, 1.0)], t) + [
                 ("R", "F", (0.375, 0.375, 0), 0.375, 225, "2x ")]),
        Part("clamp", "Clamp", 2, f'{t:.3f}" plate', "pink", clamp,
             dims=lambda p: [
                 ("H", "F", (0, 1, 0), (4.147, 1, 0), 8), ("H", "F", (0, 1, 0), (0.397, 0.5, 0), 16),
                 ("H", "F", (0, 0, 0), (2.929, 0, 0), -8), ("H", "F", (0, 0, 0), (3.048, 0.504, 0), -15),
                 ("H", "F", (0, 0, 0), (3.571, 0, 0), -22), ("H", "F", (0, 0, 0), (3.652, 0.345, 0), -29),
                 ("H", "F", (0, 0, 0), (3.880, 0, 0), -36),
                 ("V", "F", (4.147, 0, 0), (4.147, 1, 0), 8), ("V", "F", (4.147, 0, 0), (3.652, 0.345, 0), 16),
                 ("V", "F", (4.147, 0, 0), (3.048, 0.504, 0), 24), ("V", "F", (0, 0, 0), (0.397, 0.5, 0), -8),
                 ("D", "F", (0.397, 0.5, 0), 0.437, 20, "", 12), ("R", "F", (0.25, 0.25, 0), 0.25, 225, "2x "),
                 ("H", "L", (0, 0, 0), (0, 0, t), -12)]),
        Part("grabber", "Grabber", 1, f'{t:.3f}" plate', "pink", grabber,
             dims=lambda p: _plate_dims(2.75, 1.0, (), t)),
        Part("receiver", "Hinge Receiver", 1, '1" OD x 1/2" ID tube', "white", receiver, views=("F", "T"),
             dims=lambda p: [("V", "T", (0.5, 0, 0), (0.5, 0, 2), 8), ("D", "F", (0, 0, 0), 1.0, 45, ""),
                             ("D", "F", (0, 0, 0), 0.5, 225, "")], notes=("Weld to +Y side plate, top flush.",),
             flat=False),
        Part("tab", "Hinge Tab", 1, f'{t:.3f}" plate', "red", tab,
             dims=lambda p: [("H", "F", (-0.5, 0, 0), (0.5, 0, 0), -10),
                             ("V", "F", (0.5, 0, 0), (0.5, tab_reach(p), 0), 8),
                             ("D", "F", (0, tab_reach(p), 0), 0.5, 135, ""),
                             ("R", "F", (0, tab_reach(p), 0), 0.5, 45, ""),
                             ("H", "L", (0, 0, 0), (0, 0, t), -12)]),
        Part("hpin", "Hinge Pin", 1, '0.440" round', "white", hinge_pin, views=("F", "T"),
             dims=lambda p: [("V", "T", (0.22, 0, 0), (0.22, 0, 2 - 0.125 + 2 * t), 8),
                             ("D", "F", (0, 0, 0), 0.44, 45, "")], flat=False),
    ]
    for key, name, fn, d, n in [("fpin", "Fulcrum Pin", fulcrum_pin, 0.95, p.pin_len),
                                ("lpin", "Load Pin", load_pin, 0.95, p.pin_len),
                                ("roller", "Roller", roller, 1.0, p.roller_len),
                                ("spin", "Spacer Pin", spacer_pin, 1.0, 3.0),
                                ("axle", "Axle", axle, 0.437, 3.0),
                                ("handle", "Handle", handle, 0.95, p.handle_len)]:
        ps.append(Part(key, name, 1, f'{d:.3f}" round', "purple" if key != "handle" else "brown", fn,
                       views=("F", "L"), flat=False,
                       dims=lambda p, d=d, n=n: [("H", "F", (0, 0, 0), (n, 0, 0), -12),
                                                ("D", "L", (0, 0, 0), d, 45, "")]))
    ps[-1].notes = ("Cold-rolled; cut to length, chamfer ends.",)
    for i, part in enumerate(ps, 1):
        part.item = i
    return ps


# ==========================================================
# Assembly (world coordinates, same placement as cinva_ram.scad)
# ==========================================================

COLORS = {
    "gray": (0.62, 0.62, 0.64), "red": (0.80, 0.15, 0.12), "teal": (0.10, 0.55, 0.55),
    "green": (0.20, 0.55, 0.20), "orange": (0.95, 0.55, 0.10), "brown": (0.50, 0.30, 0.15),
    "pink": (0.95, 0.55, 0.70), "white": (0.95, 0.95, 0.95), "purple": (0.50, 0.25, 0.65),
}

MIRROR_Y = Plane.XZ  # mirror about Y = 0

EDGE_PLATE = Rot(0, 0, 90) * Rot(90, 0, 0)  # local x->Y, y->Z, z->X
UPRIGHT = Rot(90, 0, 0)                     # local x->X, y->Z, z->-Y


def assembly(p: Params, handle_len: float | None = None):
    """Return [(part_key, instance_name, solid_in_world), ...]."""
    k = p.kin
    L, W, t, xc, rb = p.brick_l, p.brick_w, p.t, p.xc, p.ramp_base
    sy = p.side_y
    out = []

    def add(key, name, solid, mirror=False):
        out.append((key, name, solid))
        if mirror:
            out.append((key, name + " (mirror)", solid.mirror(MIRROR_Y)))

    # Frame
    add("base", "Base Bracket", Pos(p.x0, sy + t, 0) * base_bracket(p), mirror=True)
    add("side", "Side Plate", Pos(p.x0, sy + t, t) * UPRIGHT * side(p), mirror=True)
    for x in (p.x0 - t, p.x0 + L):
        add("end", "End Plate", Pos(x, -(sy + t), p.top_z - p.end_h) * EDGE_PLATE * end_plate(p))

    # Lid: top + ramps + hinge
    add("top", "Top Plate", Pos(p.x0 - t, -(sy + t), p.top_z) * top(p))
    add("ramp", "Ramp", Pos(p.x0, p.ramp_y_inner + t, rb) * UPRIGHT * ramp(p), mirror=True)
    hx, hy = p.x0 + 0.25, sy + t + 0.5
    add("receiver", "Hinge Receiver", Pos(hx, hy, p.top_z - 2.0) * receiver(p))
    add("tab", "Hinge Tab", Pos(hx, p.ramp_y_inner + t, rb) * tab(p))
    add("hpin", "Hinge Pin", Pos(hx, hy, p.top_z - 2.0 + 0.125) * hinge_pin(p))

    # Shelf / piston
    sz = k["shelf_z"]
    add("shelf", "Shelf", Pos(p.x0 + p.clear / 2, -(W - p.clear) / 2, sz) * shelf(p))
    add("bracket", "Shelf Bracket", Pos(p.x0 + 0.5, sy - 0.75, sz - 2.0) * UPRIGHT * shelf_bracket(p), mirror=True)
    for y in (2.0, 1.75):
        add("piston", "Piston Plate", Pos(xc - 3.0, y, sz - 7.25) * UPRIGHT * piston(p), mirror=True)

    # Pins
    add("fpin", "Fulcrum Pin", Pos(p.fulcrum_x, -p.pin_len / 2, p.fulcrum_z) * Rot(0, 0, 90) * fulcrum_pin(p))
    add("lpin", "Load Pin", Pos(xc, -p.pin_len / 2, k["load_z"]) * Rot(0, 0, 90) * load_pin(p))
    add("roller", "Roller", Pos(k["roller_x"], -p.roller_len / 2, k["roller_z"]) * Rot(0, 0, 90) * roller(p))

    # Lever (pivots about the load pin)
    lev = Pos(xc, 0, k["load_z"]) * Rot(0, p.lever_angle, 0)
    bar = Pos(-p.lever_load_hole, p.lever_in + t, -1.0) * UPRIGHT * lever_bar(p)
    add("lever", "Lever Bar", lev * bar)
    add("lever", "Lever Bar (mirror)", lev * bar.mirror(MIRROR_Y))
    for z in (1.0, -1.0 - t):
        add("cross", "Lever Cross", lev * Pos(-p.lever_load_hole, -p.cross_len / 2, z) * lever_cross(p))
    add("block", "Lever Spacer Block", lev * Pos(-17.625, -0.75, -1.0) * lever_block(p))

    # Moving pivot assembly (translates with the roller)
    mv = Pos(k["dx"], 0, k["dz"])
    add("spin", "Spacer Pin", mv * Pos(xc - 3.375, -1.5, rb + 3.0) * Rot(0, 0, 90) * spacer_pin(p))
    add("pivot", "Pivot Block", mv * Pos(xc - 4.375, -1.0, rb + 2.0) * pivot(p))
    hl = p.handle_len if handle_len is None else handle_len
    add("handle", "Handle", mv * Pos(xc - 3.375, 0, rb + 4.0) * Rot(0, -90, 0) * rod(0.95, hl, "X", centered=False))
    ax = Vector(xc - 4.978, 0, rb + 7.5)
    add("axle", "Axle", mv * Pos(ax.X, -1.5, ax.Z) * Rot(0, 0, 90) * axle(p))
    cl = mv * Pos(ax) * Rot(0, -k["clamp_angle"], 0) * Pos(-ax)
    c = Pos(xc - 5.375, -1.125, rb + 7.0) * UPRIGHT * clamp(p)
    add("clamp", "Clamp", cl * c)
    add("clamp", "Clamp (mirror)", cl * c.mirror(MIRROR_Y))
    add("grabber", "Grabber", cl * Pos(xc - 1.495, -1.375, rb + 7.0)
        * Rot(0, math.degrees(math.atan(0.267)), 0) * EDGE_PLATE * grabber(p))
    link = lambda y: mv * Pos(xc + 1.25, y, rb + 4.0) * Rot(0, 0, 90) * Rot(0, 90, 0)
    add("wing", "Wing", link(-1.0 - t) * wing(p))
    add("wing", "Wing", link(1.0) * wing(p))
    add("tail", "Tail", link(-1.0) * tail(p))
    add("tail", "Tail", link(1.0 - t) * tail(p))
    return out


def assembly_compound(p: Params, **kw) -> Compound:
    colors = {pt.key: pt.color for pt in parts(p)}
    kids = []
    for key, name, s in assembly(p, **kw):
        s.label = name
        s.color = Color(*COLORS[colors[key]])
        kids.append(s)
    return Compound(children=kids, label=f"CINVA-Ram {p.label}")


def parse_brick(s: str):
    v = [float(x) for x in s.lower().replace('"', "").split("x")]
    if len(v) == 2:
        v.append(4.0)
    return dict(brick_l=v[0], brick_w=v[1], brick_h=v[2])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="12x6x4", help="L x W x H in inches (default 12x6x4)")
    ap.add_argument("--t", type=float, default=0.25, help="plate thickness")
    ap.add_argument("--anim", type=float, default=0.5, help="animation position 0..1")
    ap.add_argument("--step", help="write assembly STEP to this path")
    a = ap.parse_args()
    p = Params(**parse_brick(a.brick), t=a.t, anim=a.anim)
    ref = Params()
    print(f"CINVA-Ram {p.label}: mold {p.brick_l:g} x {p.brick_w:g}, face {p.brick_l * p.brick_w:g} in^2, "
          f"end plates {p.end_h:.3f} tall, pins {p.pin_len:.3f} long")
    print(f"  pressure vs 12x6 at same lever force: {p.pressure_ratio(ref):.0%}")
    asm = assembly_compound(p)
    print(f"  {len(asm.children)} solids, bbox {asm.bounding_box().size}")
    if a.step:
        export_step(asm, a.step, unit=Unit.IN)
        print(f"  wrote {a.step}")


if __name__ == "__main__":
    main()
