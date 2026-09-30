"""
CINVA-Ram type block press — parametric build123d model.

Mechanism (as in the original CINVA-Ram, see the VITA manual):
  * A mold box (two side walls + two end walls) sits on two base rails.
  * The piston (cap + two webs) slides in the box. A main pin P passes
    through the piston webs and through vertical slots in the side walls.
  * A yoke (two flat bars) hangs from pin P outside the box and rises above
    the lid, where two stub pins Q carry the handle head.
  * The handle head (two cheeks, bridges, handle tube) carries a saddle
    roller on an arm of length `arm` from Q. The roller rides on two ribs on
    the lid. Pulling the handle from vertical to horizontal lifts Q, the
    yoke pulls the piston up, and the brick is squeezed between piston and
    lid. The force loop closes through the brick; the frame only guides.
    With the roller under Q (handle horizontal) the linkage locks in the
    concave track on the lid ribs, slightly over centre against the handle stop.
  * Latched to the yoke, handle and yoke tilt back onto the eject roller.
    Lid open, pushing the handle down lifts pin P and ejects the brick.

The brick (L x W x H) and the compression rise set every size. Units:
inches. World frame: X along the mold (0..L), Y across (centred), Z up,
ground at Z = 0.

Usage:
    python3 cinva_ram_b123d.py --brick 14x7x4           # summary + checks
    python3 cinva_ram_b123d.py --brick 14x7x4 --step press.step

Needs LD_LIBRARY_PATH=$HOME/miniconda3/lib on this machine (conda's pyexpat
is otherwise linked against the older system libexpat).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from functools import cached_property

from build123d import (
    Align, Box, Color, Compound, Cylinder, Edge, Face, Location, Plane,
    Pos, Rot, Unit, Vector, Wire, export_step, extrude, make_hull,
)

STEEL = 0.2836  # lb / in^3


# ==========================================================
# Parameters
# ==========================================================

@dataclass(frozen=True)
class Params:
    brick_l: float = 14.0
    brick_w: float = 7.0
    brick_h: float = 4.0          # pressed brick thickness
    rise: float = 2.75            # compression stroke -> fill = brick_h + rise
    eject_over: float = 0.125     # piston rises this far above the mold top to eject

    # stock
    t_side: float = 0.75          # side walls (slotted)
    t_end: float = 0.625
    t_cover: float = 0.50
    t_rib: float = 1.00
    t_cap: float = 0.75           # piston cap
    t_web: float = 0.50
    t_bar: float = 0.75           # yoke bar thickness
    w_bar: float = 3.00           # yoke bar width
    t_cheek: float = 0.75
    clear: float = 0.125          # piston-to-mold clearance, total each axis
    d_pin: float = 1.75           # main pin P and roller axle
    d_qpin: float = 1.50          # stub pins Q
    d_roll: float = 3.00          # saddle roller
    track_h: float = 3.00         # rib height above the lid at the lock point (track bottom)
    track_r: float = 10.0         # concave roller track radius (continuous, no edges in the working range)
    stop_over: float = 3.0        # handle stop this far past centre: over-centre lock
    arm: float = 2.50             # Q -> roller centre
    handle_len: float = 72.0      # Q -> grip
    handle_od: float = 1.900      # 1-1/2" sch 80 pipe
    rail_h: float = 3.0           # 3 x 2 x 3/16 rectangular tube
    rail_w: float = 2.0
    rail_t: float = 0.1875
    eject_dx: float = 30.0        # eject roller: this far +X of mold centre
    eject_dz: float = 2.5         # ... and this far above the mold top
    d_eroll: float = 3.0
    # central latch claw (CINVA "lever latch"): one claw, pivoting on a tie between horns on the
    # yoke bars, hooks a catch bar between the handle cheeks
    catch_x: float = 1.0          # catch bar centre in cheek coords (across the handle) ...
    catch_z: float = 2.6          # ... and along the handle from Q
    catch_d: float = 1.50         # catch bar, 4140
    claw_k: float = 2.5           # claw pivot -> catch bar centre
    claw_t: float = 0.75          # each of the two claw plates
    claw_y0: float = 1.25         # inner face of the claw plates from the centreline
    tie_d: float = 1.75           # claw pivot tie between the yoke horns, 4140
    bridge_a: float = 5.75        # plain handle bridge, from Q along the handle (clear of the claw's swing)
    bridge_b: float = 8.5         # bored handle bridge
    eject_force: float = 2000.0   # lbf on the piston while ejecting (latch design load)
    eject_min_t: float = 10.0
    lid_open: float = 100.0       # lid opening angle, degrees     # handle must touch the eject roller at least this far from Q

    # loads
    p_work: float = 200.0         # psi, normal working pressure
    p_design: float = 306.0       # psi, structural design pressure (overfill)
    soil_k: float = 5.0           # stiffening exponent of the soil model

    @property
    def label(self) -> str:
        f = lambda v: f"{v:g}"
        return f"{f(self.brick_l)}x{f(self.brick_w)}x{f(self.brick_h)}"

    # ---- plan ----
    @property
    def xc(self):
        return self.brick_l / 2

    @property
    def wall_y(self):          # inner face of side walls
        return self.brick_w / 2

    @property
    def wall_out(self):
        return self.brick_w / 2 + self.t_side

    @property
    def bar_y(self):           # inner face of yoke bars
        return self.wall_out + 0.125

    @property
    def cheek_y(self):         # inner face of cheeks (1/16 from the yoke bars)
        return self.bar_y - 0.0625 - self.t_cheek

    @property
    def rib_y(self):           # rib centre line
        return self.brick_w / 2 - 1.0

    @property
    def web_y(self):           # outer face of piston webs = cap edge
        return self.brick_w / 2 - self.clear / 2

    @property
    def rail_y(self):          # rail centre line (under the side walls)
        return self.wall_y + self.t_side / 2

    # ---- heights ----
    @property
    def fill(self):
        return self.brick_h + self.rise

    @property
    def pin_below_cap(self):   # keeps the side slots below the loose fill
        return self.fill + self.eject_over + self.d_pin / 2 + 0.25

    @property
    def web_h(self):
        return self.pin_below_cap - self.t_cap + 1.5

    @property
    def piston_h(self):
        return self.t_cap + self.web_h

    @property
    def zb(self):              # box bottom = top of rails
        return self.rail_h

    @property
    def box_h(self):
        return self.fill + self.piston_h + 0.25

    @property
    def zt(self):              # mold top
        return self.zb + self.box_h

    @property
    def zp_fill(self):
        return self.zt - self.fill - self.pin_below_cap

    @property
    def zp_comp(self):
        return self.zt - self.brick_h - self.pin_below_cap

    @property
    def zp_eject(self):
        return self.zt + self.eject_over - self.pin_below_cap

    @property
    def slot(self):            # (bottom, top) Z of the side-wall slots
        return (self.zp_fill - self.d_pin / 2 - 0.125, self.zp_eject + self.d_pin / 2 + 0.125)

    @property
    def lock_z(self):          # roller centre at the lock point (bottom of the track arc)
        return self.zt + self.t_cover + self.track_h + self.d_roll / 2

    @property
    def track_arc(self):       # (centre z, radius) of the concave track surface, centred on the mold
        return self.zt + self.t_cover + self.track_h + self.track_r, self.track_r

    def roller_z(self, x):     # roller centre height riding on the track arc at x
        c = self.track_r - self.d_roll / 2
        u = x - self.xc
        return self.lock_z + c - math.sqrt(c * c - u * u)

    def q_z(self, psi):        # pivot Q height with the yoke upright and the handle at psi
        s = math.radians(psi)
        return self.roller_z(self.xc - self.arm * math.cos(s)) + self.arm * math.sin(s)

    @cached_property
    def psi0(self):            # handle start angle (deg, + toward -X): Q rises exactly `rise` to 90
        top = self.q_z(90.0)
        lo, hi = -80.0, 0.0
        for _ in range(80):
            m = (lo + hi) / 2
            if top - self.q_z(m) > self.rise:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2

    @property
    def psi_stop(self):
        return 90.0 + self.stop_over

    @property
    def yoke_len(self):        # P -> Q
        return self.q_z(90.0) - self.zp_comp

    @property
    def eject_roller(self):
        return self.xc + self.eject_dx, self.zt + self.eject_dz

    @property
    def rail_x(self):
        return -8.0, self.eject_roller[0] + 3.0

    @property
    def track(self):           # (x from, x to) of the flat roller track
        return self.xc - self.arm - 0.5, self.xc + 0.75

    # ---- loads ----
    @property
    def area(self):
        return self.brick_l * self.brick_w

    @property
    def f_work(self):
        return self.p_work * self.area

    @property
    def f_design(self):
        return self.p_design * self.area

    def soil(self, eps):
        k = self.soil_k
        return (math.exp(k * eps) - 1) / (math.exp(k) - 1)

    def _stroke_point(self, psi, F):
        q0 = self.q_z(self.psi0)
        rise = min(self.q_z(psi) - q0, self.rise)
        P = F * self.soil(max(rise, 0) / self.rise)
        dq = (self.q_z(psi + 0.01) - self.q_z(psi - 0.01)) / math.radians(0.02)
        return rise, P, max(P * dq / self.handle_len, 0.0)

    def stroke_table(self, pressure=None, step=5):
        """[(psi deg, piston rise, piston force, hand force)] over the compression stroke."""
        F = (pressure or self.p_work) * self.area
        angles = [self.psi0] + [a for a in range(0, 91, step) if a > self.psi0]
        return [(d, *self._stroke_point(d, F)) for d in angles]

    def peak_hand(self, pressure=None):
        F = (pressure or self.p_work) * self.area
        return max(self._stroke_point(i / 10, F)[2] for i in range(int(self.psi0 * 10) + 1, 900))


# ==========================================================
# Helpers (part-local: profile in XY, thickness +Z)
# ==========================================================

def plate(w, h, t):
    return Box(w, h, t, align=Align.MIN)


def hole(x, y, d, t):
    return Pos(x, y, -0.01) * Cylinder(d / 2, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))


def poly(pts, t):
    return extrude(Face(Wire.make_polygon([Vector(*q) for q in pts], close=True)), t)


def rod(d, length, axis="X"):
    c = Cylinder(d / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return {"X": Rot(0, 90, 0), "Y": Rot(-90, 0, 0), "Z": Location()}[axis] * c


def tube(od, idia, length, axis="X"):
    return rod(od, length, axis) - Pos(*(v * -0.01 for v in {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis])) * rod(idia, length + 0.02, axis)


def rect_tube(w, h, t, length):
    """Along X; w in Y, h in Z; min corner at origin."""
    return Box(length, w, h, align=Align.MIN) - Pos(-0.01, t, t) * Box(length + 0.02, w - 2 * t, h - 2 * t, align=Align.MIN)


def obround_slot(x, y0, y1, w, t):
    r = w / 2
    s = Pos(x - r, y0 + r, -0.01) * Box(w, y1 - y0 - w, t + 0.02, align=Align.MIN)
    for y in (y0 + r, y1 - r):
        s += Pos(x, y, -0.01) * Cylinder(r, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def hull_plate(circles, rects, t):
    """Convex hull of circles [(x, y, r)] and rectangles [(x0, y0, x1, y1)], extruded t."""
    es = [Edge.make_circle(r).moved(Location((x, y, 0))) for x, y, r in circles]
    for x0, y0, x1, y1 in rects:
        es += Wire.make_polygon([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], close=True).edges()
    return extrude(make_hull(es), t)


# ==========================================================
# Parts (local coordinates)
# ==========================================================

# ---- frame ----
def side_wall(p: Params):
    """x = along mold (0..L), y = up from box bottom."""
    s = plate(p.brick_l, p.box_h, p.t_side)
    s0, s1 = p.slot
    return s - obround_slot(p.xc, s0 - p.zb, s1 - p.zb, p.d_pin + 0.0625, p.t_side)


def end_wall(p: Params):
    return plate(p.brick_w + 2 * p.t_side, p.box_h, p.t_end)


def base_rail(p: Params):
    x0, x1 = p.rail_x
    r = rect_tube(p.rail_w, p.rail_h, p.rail_t, x1 - x0)
    for x in (1.0, x1 - x0 - 1.0):
        r -= Pos(x, p.rail_w / 2, -0.01) * Cylinder(0.28125, p.rail_h + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return r


def cross_tie(p: Params):
    """Between the rails; along Y."""
    n = 2 * (p.rail_y - p.rail_w / 2)
    return Rot(0, 0, 90) * rect_tube(2.0, p.rail_h, p.rail_t, n)


def roller_post(p: Params):
    ex, ez = p.eject_roller
    h = ez + 1.25 - p.rail_h
    post = Box(2.0, 2.0, h, align=Align.MIN) - Pos(0.25, 0.25, -0.01) * Box(1.5, 1.5, h + 0.02, align=Align.MIN)
    return post - Pos(1.0, -0.01, h - 1.25) * rod(1.0625, 2.02, "Y")


def eject_roller(p: Params):
    n = 2 * (p.rail_y - 1.0) - 0.25
    return tube(p.d_eroll, 1.0625, n, "Y")


def eject_axle(p: Params):
    return rod(1.0, 2 * (p.rail_y + 1.0) + 0.75, "Y")


def wall_lug(p: Params):
    """XZ profile: x = +X outward from the eject-end wall, y = Z up from mold top - 3."""
    s = hull_plate([(0.75, 2.25, 0.75)], [(0, 0, 1.5, 2.25)], 0.5)
    return s - hole(0.75, 2.25, 0.781, 0.5)


def cover_plate(p: Params):
    return plate(p.brick_l + 2 * p.t_end, p.brick_w + 2 * p.t_side, p.t_cover)


def track_h_at(p: Params, x):
    """Rib height above the lid on the concave track at x."""
    u = x - p.xc
    return p.track_h + p.track_r - math.sqrt(p.track_r ** 2 - u * u)


def rib_points(p: Params):
    L, te = p.brick_l, p.t_end
    t0, t1 = p.track
    kx, kh = rib_knee(p)
    return [(-te, 0), (L + te, 0), (L + te, RIB_END_EJECT), (kx, kh), (t1, track_h_at(p, t1)), (t0, track_h_at(p, t0)),
            (-te, 1.0)]


RIB_END_EJECT = 0.5   # rib height at the eject end (clears the catch bar as the yoke tips back)


def rib_knee(p: Params):
    """Knee on the eject-side slope: drops the rib away under the catch bar and tilting roller."""
    return p.track[1] + 1.0, p.track_h - 1.3


def cover_rib(p: Params):
    """x = world X, y = height above the lid plate; track is a concave arc between the two slopes."""
    r = poly(rib_points(p), p.t_rib)
    return r - hole(p.xc, p.track_h + p.track_r, 2 * p.track_r, p.t_rib)


def cover_lug(p: Params):
    """XZ profile: x from X = L - 1.5, y from Z = mold top - 1.5. Sits on the lid top and
    wraps down past the lid end to the hinge hole below the lid."""
    te = p.t_end
    s = Pos(0, 2.0, 0) * Box(1.5 + te, 0.5, 0.5, align=Align.MIN)          # on the lid top (weld)
    s += Pos(1.5 + te, 0.75, 0) * Box(1.5, 1.25, 0.5, align=Align.MIN)     # past the lid end, no higher than the lid
    px, pz = 2.25 + te, 0.75
    s += Pos(px, pz, 0) * Cylinder(0.75, 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # stop tail: touches the end wall face when the lid is open lid_open degrees
    tx, tz = lid_stop_tail(p)
    s += Pos(px, pz, 0) * hull_plate([(0, 0, 0.75), (tx, tz, 0.25)], [], 0.5)
    return s - hole(px, pz, 0.781, 0.5)


def lid_stop_tail(p: Params):
    """Tail lobe centre (relative to the hinge) whose R0.25 edge meets the end wall face at lid_open."""
    # opening by alpha turns the lobe from polar angle beta to beta - alpha; it touches the wall face
    # (0.75 left of the hinge) when its centre, 1.0 out, sits 0.5 left: angle 240 deg
    beta = math.pi + math.acos(0.5) + math.radians(p.lid_open)
    return math.cos(beta), math.sin(beta)


def hinge_axis(p: Params):
    """Lid hinge (x, z): outside the eject-end wall, below the lid, clear of the roller path."""
    return p.brick_l + p.t_end + 0.75, p.zt - 0.75


def hinge_pin(p: Params):
    return rod(0.75, 1.75, "Y")


def handle_stop(p: Params):
    h = handle_stop_h(p)
    return Box(2, 2, h, align=Align.MIN) - Pos(0.25, 0.25, -0.01) * Box(1.5, 1.5, h + 0.02, align=Align.MIN) \
        + Pos(0, 0, h) * Box(2, 2, 0.25, align=Align.MIN)


STOP_X = (-7.0, -5.0)   # stop post footprint, relative to the mold centre


def handle_low_point(p: Params, psi):
    """Lowest Z of the handle bridges over the stop post, handle at psi, yoke upright."""
    a = math.radians(-psi)
    q = p.q_z(psi)
    best = 1e9
    pts = [(-1.25 + 2.5 * i / 10, z0 + 0.75 * j / 10)
           for z0 in (p.bridge_a, p.bridge_b) for i in range(11) for j in range(11)]
    for xl, zl in pts:
        X = xl * math.cos(a) + zl * math.sin(a)
        Z = -xl * math.sin(a) + zl * math.cos(a)
        if STOP_X[0] <= X <= STOP_X[1]:
            best = min(best, q + Z)
    return best


def handle_stop_h(p: Params):
    """Post height (below its 1/4 cap) so the handle lands on it at psi_stop."""
    return handle_low_point(p, p.psi_stop) - (p.zt + p.t_cover) - 0.25


# ---- piston ----
def piston_cap(p: Params):
    return plate(p.brick_l - p.clear, p.brick_w - p.clear, p.t_cap)


def piston_web(p: Params):
    w = plate(p.brick_l - p.clear, p.web_h, p.t_web)
    return w - hole(p.xc - p.clear / 2, p.web_h - (p.pin_below_cap - p.t_cap), p.d_pin + 1 / 32, p.t_web)


def piston_diaphragm(p: Params):
    return plate(2 * (p.web_y - p.t_web), p.web_h, 0.5)


# ---- yoke ----
def yoke_bar(p: Params):
    """x across the bar (centred), y along the yoke from P (0) to Q (yoke_len). The horn beside Q
    carries the claw tie and the claw stop rod."""
    Ly, w, r = p.yoke_len, p.w_bar, p.w_bar / 2
    cl = claw_geom(p)
    (cx, cz), (sx, sz) = cl["C"], cl["stop"]
    b = Pos(-r, 0, 0) * Box(w, Ly, p.t_bar, align=Align.MIN)
    b += Cylinder(r, p.t_bar, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b += hull_plate([(0, Ly, r), (0, Ly - 3.0, r), (cx, Ly + cz, 1.3), (sx, Ly + sz, 0.75)], [], p.t_bar)
    b -= hole(0, 0, p.d_pin + 1 / 32, p.t_bar)
    b -= hole(0, Ly, p.d_qpin + 1 / 32, p.t_bar)
    b -= hole(cx, Ly + cz, p.tie_d + 1 / 32, p.t_bar)
    return b - hole(sx, Ly + sz, 0.781, p.t_bar)


def main_pin(p: Params):
    n = 2 * (p.bar_y + p.t_bar) + 1.25
    pin = rod(p.d_pin, n, "X")
    for x in (0.3125, n - 0.3125):
        pin -= Pos(x, 0, 0) * rod(0.28125, 2.0, "Z").moved(Location((0, 0, -1.0)))
    return pin


def q_pin(p: Params):
    n = p.t_cheek + 0.0625 + p.t_bar + 1.0
    pin = rod(p.d_qpin, n, "X")
    for x in (0.3125, n - 0.3125):
        pin -= Pos(x, 0, 0) * rod(0.28125, 2.0, "Z").moved(Location((0, 0, -1.0)))
    return pin


def _rot(v, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c)


def catch_yoke(p: Params):
    """Catch bar centre in the yoke frame (Q at origin) with the handle at psi0."""
    s = math.radians(p.psi0)
    x, z = p.catch_x, p.catch_z
    return (x * math.cos(s) - z * math.sin(s), x * math.sin(s) + z * math.cos(s))


CLAW_W = 0.75                 # arm half-width
CLAW_EAR = (-2.2, 0.6, 0.9)   # counterweight tail (x, y, r): puts the centre of mass where gravity shuts the claw


def claw_profile(p: Params, k):
    """One claw plate. Local: origin at the pivot, x along the arm to the catch bar, +y = notch mouth.
    Notch side walls are arcs about the pivot, so the catch bar slides straight out when the claw
    swings open and latch loads (along the arm) bear square on them."""
    rn = p.catch_d / 2 + 1 / 32
    t = p.claw_t
    cyl = lambda r, x=0.0, y=0.0: Pos(x, y, 0) * Cylinder(r, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s = cyl(1.3)
    s += Pos(0, -CLAW_W, 0) * Box(k - 0.8, 2 * CLAW_W, t, align=Align.MIN)
    s += Pos(k - 1.4, -1.45, 0) * Box(2.85, 2.35, t, align=Align.MIN)
    ex, ey, er = CLAW_EAR
    s += hull_plate([(0, 0, 1.3), (ex, ey, er)], [], t)
    ring = Pos(0, 0, -0.01) * (Cylinder(k + rn, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
                               - Cylinder(k - rn, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    s -= ring & (Pos(k - 2.0, 0, -0.02) * Box(4.0, 3.0, t + 0.04, align=Align.MIN))
    s -= hole(k, 0, 2 * rn, t)
    s -= hole(ex, ey, 0.875 + 1 / 32, t)                          # thumb bar
    return s - hole(0, 0, p.tie_d + 1 / 32, t)


def claw_geom(p: Params):
    """Central claw layout in the yoke frame (x' across, z' along the yoke), origin at Q.
    S: catch bar centre (handle at psi0).  The claw arm C->S lies along the catch bar's path about Q,
    so latch loads push along the arm and cannot rotate the claw.  C sits clockwise of the handle
    head, in space the head never sweeps.  The claw shuts by turning counter-clockwise (gravity)
    and opens clockwise onto a stop rod."""
    S = catch_yoke(p)
    R = math.hypot(*S)
    t = (-S[1] / R, S[0] / R)                                  # path of the catch bar (handle turning +psi)
    C = (S[0] - p.claw_k * t[0], S[1] - p.claw_k * t[1])
    arm = math.degrees(math.atan2(t[1], t[0]))
    cg = claw_weldment_cg(p)
    cg_ang = math.degrees(math.atan2(cg[1], cg[0])) + arm      # centre of mass direction, shut
    opening = cg_ang - 85.0                                    # clockwise swing to 5 deg past vertical
    stop = _rot((p.claw_k - 1.2, -(1.45 + 0.375 + 0.005)), arm - opening)   # under the flat face of the claw head
    return dict(S=S, R=R, C=C, k=p.claw_k, arm=arm, cg_ang=cg_ang, open=opening,
                stop=(C[0] + stop[0], C[1] + stop[1]))


def claw_weldment_cg(p: Params):
    plate_ = claw_profile(p, p.claw_k)
    c1, v1 = plate_.center(), plate_.volume
    v2 = math.pi * (0.875 / 2) ** 2 * 2 * p.claw_y0
    ex, ey, _ = CLAW_EAR
    return ((c1.X * v1 + ex * v2) / (v1 + v2), (c1.Y * v1 + ey * v2) / (v1 + v2))


def claw(p: Params):
    return claw_profile(p, p.claw_k)


def claw_thumb(p: Params):
    return rod(0.875, 2 * p.claw_y0 + 2 * p.claw_t, "Y")


def claw_tie(p: Params):
    return rod(p.tie_d, 2 * (p.bar_y + p.t_bar), "Y")


def tie_spacer(p: Params):
    return tube(2.5, p.tie_d + 1 / 16, p.bar_y - p.claw_y0 - p.claw_t - 0.0625, "Y")


def claw_stop(p: Params):
    return rod(0.75, 2 * (p.bar_y + p.t_bar), "Y")


def catch_bar(p: Params):
    return rod(p.catch_d, 2 * (p.cheek_y + p.t_cheek), "Y")


# ---- handle head ----
def cheek_points(p: Params):
    """Hole centres in cheek-local coords (x = -X at psi = 0, y = along handle)."""
    return dict(q=(0.0, 0.0), roll=(-p.arm, 0.0), catch=(p.catch_x, p.catch_z))


def cheek(p: Params):
    h = cheek_points(p)
    cx, cy = h["catch"]
    s = hull_plate([(0, 0, 1.5), (-p.arm, 0, 1.5), (cx, cy, 1.25)], [(-1.25, 2.5, 1.25, p.bridge_b + 0.75)], p.t_cheek)
    s -= hole(0, 0, p.d_qpin + 1 / 32, p.t_cheek)
    s -= hole(-p.arm, 0, p.d_pin + 1 / 32, p.t_cheek)
    return s - hole(cx, cy, p.catch_d + 1 / 32, p.t_cheek)


def saddle_roller(p: Params):
    return tube(p.d_roll, p.d_pin + 1 / 32, 2 * p.cheek_y - 0.125, "Y")


def roller_axle(p: Params):
    return rod(p.d_pin, 2 * (p.cheek_y + p.t_cheek), "Y")      # flush with the cheek outer faces


def bridge(p: Params, bored=False):
    b = plate(2.5, 2 * p.cheek_y, 0.75)
    return b - hole(1.25, p.cheek_y, p.handle_od + 1 / 16, 0.75) if bored else b


def handle_tube(p: Params):
    return tube(p.handle_od, p.handle_od - 0.4, p.handle_len - p.bridge_a - 0.75, "Z")


# ==========================================================
# Poses
# ==========================================================

@dataclass
class Pose:
    name: str
    theta: float      # yoke tilt from vertical toward +X (deg)
    psi: float        # handle angle relative to the yoke (deg, + toward -X)
    zp: float         # pin P height
    cover: float      # cover opening angle (deg)
    claw: float | None = None   # claw opening (deg); default: shut when the handle is at psi0, else open


def _handle_frame(p, th, psi, zp):
    return Pos(p.xc, 0, zp) * Rot(0, th, 0) * Pos(0, 0, p.yoke_len) * Rot(0, -psi, 0)


def _eject_contact(p: Params, th, zp):
    """Signed distance from the eject roller centre to the handle tube axis."""
    hf = _handle_frame(p, th, p.psi0, zp)
    o = (hf * Pos(0, 0, 0)).position
    d = (hf * Pos(0, 0, 1)).position - o
    ex, ez = p.eject_roller
    v = Vector(ex, 0, ez) - o
    t = v.dot(d)
    foot = o + d * t
    n = Vector(-d.Z, 0, d.X)             # left normal of the handle direction
    return (Vector(ex, 0, ez) - foot).dot(n), t


def solve_theta(p: Params, zp):
    """Yoke tilt at which the latched handle rests on the eject roller with pin P at zp."""
    r = p.d_eroll / 2 + p.handle_od / 2
    best = None
    for i in range(1, 890):
        th = i / 10
        d, t = _eject_contact(p, th, zp)
        err = abs(d + r)          # roller below the handle
        if t > p.eject_min_t and (best is None or err < best[0]):
            best = (err, th, t)
    return best


def poses(p: Params) -> dict:
    fill = solve_theta(p, p.zp_fill)
    ej = solve_theta(p, p.zp_eject)
    return {
        "fill": Pose("Fill (latched, tilted back, lid open)", fill[1], p.psi0, p.zp_fill, p.lid_open),
        "start": Pose("Start of compression (lid closed)", 0.0, p.psi0, p.zp_fill, 0),
        "locked": Pose("Compressed and locked (over centre, on the stop)", 0.0, p.psi_stop,
                       p.q_z(p.psi_stop) - p.yoke_len, 0),
        "eject": Pose("Ejected (latched, pushed down)", ej[1], p.psi0, p.zp_eject, p.lid_open),
    }


# ==========================================================
# Part registry
# ==========================================================

@dataclass
class Part:
    key: str
    name: str
    qty: int
    stock: str
    color: str
    build: callable
    views: tuple = ("F", "L")
    dims: callable = None
    notes: tuple = ()
    flat: bool = True
    front: str = "Z"
    group: str = ""
    item: int = 0

    def weight(self, p):
        return self.build(p).volume * STEEL


def _plate_dims(w, h, holes=(), t=None, lead=None):
    d = [("H", "F", (0, 0, 0), (w, 0, 0), -10), ("V", "F", (0, 0, 0), (0, h, 0), -10)]
    seen_x, seen_y = set(), set()
    for x, y, dia in holes:
        if round(x, 3) not in seen_x and 0.01 < x < w - 0.01:
            d.append(("H", "F", (0, h, 0), (x, y, 0), 8 + 8 * len(seen_x)))
            seen_x.add(round(x, 3))
        if round(y, 3) not in seen_y and 0.01 < y < h - 0.01:
            d.append(("V", "F", (w, 0, 0), (x, y, 0), 8 + 8 * len(seen_y)))
            seen_y.add(round(y, 3))
    by_d = {}
    for x, y, dia in holes:
        by_d.setdefault(dia, []).append((x, y))
    clear = -(8 + 8 * max(len(seen_y), 1) + 2)
    for dia, pts in by_d.items():
        n = len(pts)
        top = max(range(n), key=lambda j: pts[j][1])
        i, ang, ln = (lead or {}).get(dia, (top, 25, clear))
        d.append(("D", "F", (*pts[i], 0), dia, ang, f"{n}x " if n > 1 else "", ln))
    if t is not None:
        d.append(("H", "L", (0, 0, 0), (0, 0, t), -10))
    return d


def _pin_dims(d, n, cross=True):
    out = [("H", "F", (0, 0, 0), (n, 0, 0), -10), ("D", "L", (0, 0, 0), d, 45, "")]
    if cross:
        out.append(("H", "F", (0, 0, 0), (0.3125, 0, 0), 8))
    return out


def parts(p: Params) -> list[Part]:
    L, W = p.brick_l, p.brick_w
    s0, s1 = p.slot
    Ly = p.yoke_len
    ch = cheek_points(p)
    lx, ly = ch["catch"]
    cl = claw_geom(p)
    (cpx, cpz), (spx, spz) = cl["C"], cl["stop"]
    k = p.claw_k
    t0, t1 = p.track
    h0, h1 = track_h_at(p, t0), track_h_at(p, t1)
    ex, ez = p.eject_roller
    rx0, rx1 = p.rail_x
    post_h = ez + 1.25 - p.rail_h
    stop_h = handle_stop_h(p)
    pin_n = 2 * (p.bar_y + p.t_bar) + 1.25
    q_n = p.t_cheek + 0.0625 + p.t_bar + 1.0
    ax_n = 2 * (p.cheek_y + p.t_cheek) + 1.0
    web_hole_y = p.web_h - (p.pin_below_cap - p.t_cap)
    pl = lambda t: f'{t:.3f}" plate'

    ps = [
        # ---------------- frame ----------------
        Part("side", "Side Wall", 2, pl(p.t_side) + " A36", "gray", side_wall, group="Frame",
             dims=lambda p: _plate_dims(L, p.box_h, (), p.t_side) + [
                 ("H", "F", (0, p.box_h, 0), (p.xc - (p.d_pin + 0.0625) / 2, s1 - p.zb, 0), 8),
                 ("H", "F", (0, p.box_h, 0), (p.xc + (p.d_pin + 0.0625) / 2, s1 - p.zb, 0), 16),
                 ("V", "F", (L, 0, 0), (p.xc, s0 - p.zb, 0), 8),
                 ("V", "F", (L, 0, 0), (p.xc, s1 - p.zb, 0), 16),
                 ("R", "F", (p.xc, s1 - p.zb - (p.d_pin + 0.0625) / 2, 0), (p.d_pin + 0.0625) / 2, 60, "2x ", 14)],
             notes=("Slot guides main pin P; keep slot edges smooth and parallel.",
                    "Weld to end walls outside only; no weld or spatter inside the mold.")),
        Part("end", "End Wall", 2, pl(p.t_end) + " A36", "gray", end_wall, group="Frame",
             dims=lambda p: _plate_dims(W + 2 * p.t_side, p.box_h, (), p.t_end),
             notes=("Mold inside must be square: check diagonals before final welds.",)),
        Part("rail", "Base Rail", 2, '3 x 2 x 3/16 rect. tube', "green", base_rail, group="Frame",
             views=("F", "T", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (rx1 - rx0, 0, 0), -10), ("V", "F", (rx1 - rx0, 0, 0), (rx1 - rx0, 0, p.rail_h), 8),
                             ("H", "T", (0, p.rail_w, 0), (1.0, 1.0, 0), 8), ("H", "T", (rx1 - rx0, p.rail_w, 0), (rx1 - rx0 - 1.0, 1.0, 0), 16),
                             ("D", "T", (1.0, 1.0, 0), 0.5625, 300, "2x ", 10), ("H", "L", (0, 0, 0), (0, p.rail_w, 0), -8)],
             notes=("Mounting holes through both walls, for 1/2 anchor bolts or lags.",)),
        Part("tie", "Cross Tie", 2, '3 x 2 x 3/16 rect. tube', "green", cross_tie, group="Frame",
             views=("F", "T"), flat=False,
             dims=lambda p: [("V", "F", (0, 0, 0), (0, 2 * (p.rail_y - p.rail_w / 2), 0), -10),
                             ("H", "F", (-2.0, 0, 0), (0, 0, 0), -10)]),
        Part("post", "Eject Roller Post", 2, '2 x 2 x 1/4 sq. tube', "green", roller_post, group="Frame",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("V", "F", (2, 0, 0), (2, 0, post_h), 8), ("H", "F", (0, 0, 0), (2, 0, 0), -10),
                             ("V", "F", (0, 0, post_h), (1.0, 0, post_h - 1.25), -8),
                             ("D", "F", (1.0, 0, post_h - 1.25), 1.0625, 150, "", 10)]),
        Part("eroll", "Eject Roller", 1, '3" OD round, 1045', "green", eject_roller, group="Frame",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "L", (0, 0, 0), (0, 2 * (p.rail_y - 1.0) - 0.25, 0), -10),
                             ("D", "F", (0, 0, 0), p.d_eroll, 45, ""), ("D", "F", (0, 0, 0), 1.0625, 225, "")]),
        Part("eaxle", "Eject Roller Axle", 1, '1.000" round 1018', "purple", eject_axle, group="Frame",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), 1.0, 45, ""), ("H", "L", (0, 0, 0), (0, 2 * (p.rail_y + 1.0) + 0.75, 0), -10)]),
        Part("wlug", "Wall Hinge Lug", 2, pl(0.5) + " A36", "gray", wall_lug, group="Frame",
             dims=lambda p: _plate_dims(1.5, 3.0, [(0.75, 2.25, 0.781)], 0.5) + [("R", "F", (0.75, 2.25, 0), 0.75, 315, "", 12)],
             notes=("Weld to the outer face of the eject-end wall, top flush with the mold top, "
                    "outer face 0.250 in from the side-wall outer face.",)),

        # ---------------- lid ----------------
        Part("cover", "Lid Plate", 1, pl(p.t_cover) + " A36", "red", cover_plate, group="Lid",
             dims=lambda p: _plate_dims(L + 2 * p.t_end, W + 2 * p.t_side, (), p.t_cover),
             notes=("Underside must be flat and clean; it forms the top face of the brick.",)),
        Part("rib", "Lid Rib (Roller Track)", 2, pl(p.t_rib) + " AR400", "red", cover_rib, group="Lid",
             dims=lambda p: [("H", "F", (-p.t_end, 0, 0), (L + p.t_end, 0, 0), -10),
                             ("V", "F", (-p.t_end, 0, 0), (-p.t_end, 1.0, 0), -8),
                             ("V", "F", (L + p.t_end, 0, 0), (L + p.t_end, RIB_END_EJECT, 0), 8),
                             ("V", "F", (L + p.t_end, 0, 0), (t1, h1, 0), 16),
                             ("V", "F", (L + p.t_end, 0, 0), (p.xc, p.track_h, 0), 24),
                             ("V", "F", (L + p.t_end, 0, 0), (rib_knee(p)[0], rib_knee(p)[1], 0), 32),
                             ("H", "F", (-p.t_end, 0, 0), (rib_knee(p)[0], rib_knee(p)[1], 0), -42),
                             ("V", "F", (-p.t_end, 0, 0), (t0, h0, 0), -16),
                             ("H", "F", (-p.t_end, 0, 0), (t0, h0, 0), -18),
                             ("H", "F", (-p.t_end, 0, 0), (p.xc, p.track_h, 0), -26),
                             ("H", "F", (-p.t_end, 0, 0), (t1, h1, 0), -34),
                             ("Ri", "F", (p.xc, p.track_h + p.track_r, 0), p.track_r, 272, "TRACK ", 14),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_rib), -10)],
             notes=("AR400 wear plate: the roller bears on this edge at up to 15,000 lbf.",
                    f"Track is one concave arc R{p.track_r:.3f}, lowest point on the mold centreline, "
                    f"{p.track_h:.3f} above the lid; cut from the DXF, no flats or corners between the two slopes.",
                    "Grind the track smooth and square to the plate within 1/64.",
                    "Weld to lid plate both sides full length, low-hydrogen rod, preheat 300 F.")),
        Part("clug", "Lid Hinge Lug", 2, pl(0.5) + " A36", "red", cover_lug, group="Lid",
             dims=lambda p: [("H", "F", (0, 2.5, 0), (3.0 + p.t_end, 2.0, 0), 8), ("V", "F", (3.0 + p.t_end, 0, 0), (3.0 + p.t_end, 2.0, 0), 8),
                             ("H", "F", (0, 2.5, 0), (1.5 + p.t_end, 2.5, 0), 16), ("V", "F", (0, 2.0, 0), (0, 2.5, 0), -8),
                             ("H", "F", (0, 2.5, 0), (2.25 + p.t_end, 0.75, 0), 24), ("V", "F", (3.0 + p.t_end, 0, 0), (2.25 + p.t_end, 0.75, 0), 16),
                             ("D", "F", (2.25 + p.t_end, 0.75, 0), 0.781, 200, "", 10), ("R", "F", (2.25 + p.t_end, 0.75, 0), 0.75, 300, "", 8),
                             ("H", "L", (0, 0, 0), (0, 0, 0.5), -10)],
             notes=("Weld on the lid top at the eject end, inner edge against the lid end face, "
                    "outer face 0.750 in from the lid edge.",
                    "Hinge hole sits below the lid so the lug stays clear of the saddle roller.",
                    "The tail lobe rests on the end wall with the lid open just past vertical.")),
        Part("hpin", "Hinge Pin", 2, '0.750" round 1018', "white", hinge_pin, group="Lid",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), 0.75, 45, ""), ("H", "L", (0, 0, 0), (0, 1.75, 0), -10)],
             notes=("Retain with washer and 1/8 cotter pin each end.",)),
        Part("stop", "Handle Stop", 1, '2x2x1/4 sq. tube + cap', "red", handle_stop, group="Lid",
             views=("F", "T"), front="-Y", flat=False,
             dims=lambda p: [("V", "F", (2, 0, 0), (2, 0, stop_h + 0.25), 8), ("H", "F", (0, 0, 0), (2, 0, 0), -10)],
             notes=(f"Weld on the lid centreline, centre {p.xc + sum(STOP_X) / 2 + p.t_end:.3f} from the lid end "
                    f"away from the hinge.",
                    f"Height sets the lock: the handle must land on it {p.stop_over:g} deg past horizontal.")),

        # ---------------- piston ----------------
        Part("cap", "Piston Cap", 1, pl(p.t_cap) + " A36", "teal", piston_cap, group="Piston",
             dims=lambda p: _plate_dims(L - p.clear, W - p.clear, (), p.t_cap),
             notes=("Top face flat; break edges lightly. 1/16 clearance each side in the mold.",)),
        Part("web", "Piston Web", 2, pl(p.t_web) + " A36", "teal", piston_web, group="Piston",
             dims=lambda p: _plate_dims(L - p.clear, p.web_h, [(p.xc - p.clear / 2, web_hole_y, p.d_pin + 1 / 32)], p.t_web),
             notes=("Weld under the cap flush with its long edges; line-bore holes after welding if possible.",)),
        Part("diaph", "Piston Diaphragm", 2, pl(0.5) + " A36", "teal", piston_diaphragm, group="Piston",
             dims=lambda p: _plate_dims(2 * (p.web_y - p.t_web), p.web_h, (), 0.5),
             notes=("Weld between the webs at each end, under the cap.",)),

        # ---------------- yoke ----------------
        Part("bar", "Yoke Bar", 2, '0.750" plate A36 (profile)', "orange", yoke_bar, group="Yoke",
             dims=lambda p: [("V", "F", (1.5, 0, 0), (0, Ly, 0), 10), ("V", "F", (1.5, 0, 0), (cpx, Ly + cpz, 0), 18),
                             ("V", "F", (1.5, 0, 0), (spx, Ly + spz, 0), 26),
                             ("H", "F", (-1.5, 0, 0), (1.5, 0, 0), -10),
                             ("H", "F", (0, Ly + 1.5, 0), (cpx, Ly + cpz, 0), 8), ("H", "F", (0, Ly + 1.5, 0), (spx, Ly + spz, 0), 16),
                             ("D", "F", (0, 0, 0), p.d_pin + 1 / 32, 200, "P ", 12),
                             ("D", "F", (0, Ly, 0), p.d_qpin + 1 / 32, 160, "Q ", 12),
                             ("D", "F", (cpx, Ly + cpz, 0), p.tie_d + 1 / 32, 20, "TIE ", 12),
                             ("D", "F", (spx, Ly + spz, 0), 0.781, 330, "STOP ROD ", 12),
                             ("R", "F", (0, 0, 0), 1.5, 300, "", 8), ("H", "L", (0, 0, 0), (0, 0, p.t_bar), -10)],
             notes=("Drill both bars clamped together so hole spacing matches exactly.",
                    "Horn outline: tangent arcs R1.500 about Q and 3.000 below it, R1.300 about the tie hole, "
                    "R0.750 about the stop-rod hole (cut from the DXF).",
                    "Claw tie and stop rod are welded into both bars, which makes the yoke one rigid frame.")),
        Part("ppin", "Main Pin P", 1, f'{p.d_pin:.3f}" round 4140 prehard', "purple", main_pin, group="Yoke",
             views=("F", "L"), flat=False, dims=lambda p: _pin_dims(p.d_pin, pin_n),
             notes=("Cross holes 9/32 for 1/4 hitch or cotter pins.",)),
        Part("qpin", "Stub Pin Q", 2, f'{p.d_qpin:.3f}" round 4140 prehard', "purple", q_pin, group="Yoke",
             views=("F", "L"), flat=False, dims=lambda p: _pin_dims(p.d_qpin, q_n),
             notes=("Cross holes 9/32 for 1/4 hitch or cotter pins.",)),
        Part("claw", "Claw Plate", 2, pl(p.claw_t) + " A36", "pink", claw, group="Yoke",
             dims=lambda p: [("H", "F", (0, 0, 0), (k, 0, 0), -14),
                             ("H", "F", (-1.3, 0, 0), (k + 1.45, 0, 0), -22),
                             ("V", "F", (k + 1.45, -1.45, 0), (k + 1.45, 0.9, 0), 10),
                             ("V", "F", (k + 1.45, -1.45, 0), (k, 0, 0), 18),
                             ("H", "F", (0, 0, 0), (CLAW_EAR[0], CLAW_EAR[1], 0), 10),
                             ("V", "F", (-1.3, 0, 0), (CLAW_EAR[0], CLAW_EAR[1], 0), -8),
                             ("D", "F", (0, 0, 0), p.tie_d + 1 / 32, 225, "PIVOT ", 10),
                             ("D", "F", (CLAW_EAR[0], CLAW_EAR[1], 0), 0.906, 200, "THUMB BAR ", 14),
                             ("R", "F", (k, 0, 0), p.catch_d / 2 + 1 / 32, 300, "NOTCH ", 12),
                             ("H", "L", (0, 0, 0), (0, 0, p.claw_t), -10)],
             notes=("Two identical plates, welded to the thumb bar 2.500 apart (inside faces), make one claw.",
                    "Notch side walls are arcs centred on the pivot hole (cut from the DXF); break all edges.",
                    "The tail behind the pivot is a counterweight: it keeps the claw shut under its own weight.")),
        Part("cthumb", "Claw Thumb Bar", 1, '0.875" round 1018', "pink", claw_thumb, group="Yoke",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), 0.875, 45, ""),
                             ("H", "L", (0, 0, 0), (0, 2 * p.claw_y0 + 2 * p.claw_t, 0), -10)],
             notes=("Through both claw plates, flush with their outside faces; weld both ends.",
                    "Push it down to flip the claw open onto the stop rod; lift it to let the claw latch.")),
        Part("ctie", "Claw Tie", 1, f'{p.tie_d:.3f}" round 4140 prehard', "purple", claw_tie, group="Yoke",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), p.tie_d, 45, ""), ("H", "L", (0, 0, 0), (0, 2 * (p.bar_y + p.t_bar), 0), -10)],
             notes=("Through both yoke-bar horns, flush outside; weld both ends (small welds, slow cool).",
                    "Claw and tie spacers go on before the second end is welded.")),
        Part("tspacer", "Tie Spacer", 2, '2.5" OD round 1018', "purple", tie_spacer, group="Yoke",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), 2.5, 45, ""), ("D", "F", (0, 0, 0), p.tie_d + 1 / 16, 225, ""),
                             ("H", "L", (0, 0, 0), (0, p.bar_y - p.claw_y0 - p.claw_t - 0.0625, 0), -10)],
             notes=("Loose on the tie; centres the claw between the yoke bars.",)),
        Part("cstop", "Claw Stop Rod", 1, '0.750" round 1018', "purple", claw_stop, group="Yoke",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), 0.75, 45, ""), ("H", "L", (0, 0, 0), (0, 2 * (p.bar_y + p.t_bar), 0), -10)],
             notes=("Through both yoke-bar horns, flush outside; weld both ends. The open claw rests on it.",)),

        # ---------------- handle ----------------
        Part("cheek", "Handle Cheek", 2, pl(p.t_cheek) + " A36", "brown", cheek, group="Handle",
             dims=lambda p: [("H", "F", (-p.arm, 0, 0), (0, 0, 0), -12), ("H", "F", (0, p.bridge_b + 0.75, 0), (lx, ly, 0), 12),
                             ("V", "F", (1.25, 0, 0), (lx, ly, 0), 18), ("V", "F", (1.25, 0, 0), (1.25, p.bridge_b + 0.75, 0), 10),
                             ("H", "F", (-1.25, p.bridge_b + 0.75, 0), (1.25, p.bridge_b + 0.75, 0), 20),
                             ("D", "F", (0, 0, 0), p.d_qpin + 1 / 32, 250, "Q ", 14),
                             ("D", "F", (-p.arm, 0, 0), p.d_pin + 1 / 32, 220, "ROLLER ", 10),
                             ("D", "F", (lx, ly, 0), p.catch_d + 1 / 32, 345, "CATCH ", 18),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_cheek), -10)],
             notes=("Outline is tangent arcs R1.500 about Q and roller holes, R1.250 about the catch-bar hole.",
                    "Make as a mirrored pair; drill both clamped together.")),
        Part("sroll", "Saddle Roller", 1, '3" OD 4140, 40-45 HRC', "brown", saddle_roller, group="Handle",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "L", (0, 0, 0), (0, 2 * p.cheek_y - 0.125, 0), -10),
                             ("D", "F", (0, 0, 0), p.d_roll, 45, ""), ("D", "F", (0, 0, 0), p.d_pin + 1 / 32, 225, "")],
             notes=("Bore reamed for a running fit on the axle; grease.",)),
        Part("axle", "Roller Axle", 1, f'{p.d_pin:.3f}" round 4140 prehard', "purple", roller_axle, group="Handle",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), p.d_pin, 45, ""), ("H", "L", (0, 0, 0), (0, 2 * (p.cheek_y + p.t_cheek), 0), -10)],
             notes=("Weld axle ends to both cheeks after the roller is installed.",)),
        Part("catch", "Catch Bar", 1, f'{p.catch_d:.3f}" round 4140 prehard', "purple", catch_bar, group="Handle",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("D", "F", (0, 0, 0), p.catch_d, 45, ""),
                             ("H", "L", (0, 0, 0), (0, 2 * (p.cheek_y + p.t_cheek), 0), -10)],
             notes=("Through both cheeks, flush outside; weld to each cheek (small welds, slow cool).",
                    "The claw hooks it in the middle.")),
        Part("bridge", "Handle Bridge", 1, pl(0.75) + " A36", "brown", bridge, group="Handle",
             dims=lambda p: _plate_dims(2.5, 2 * p.cheek_y, (), 0.75),
             notes=(f"Weld between the cheeks, {p.bridge_a:.3f} from Q along the handle line.",)),
        Part("bridgeb", "Handle Bridge, Bored", 1, pl(0.75) + " A36", "brown", lambda p: bridge(p, True), group="Handle",
             dims=lambda p: _plate_dims(2.5, 2 * p.cheek_y, [(1.25, p.cheek_y, p.handle_od + 1 / 16)], 0.75),
             notes=(f"Weld between the cheeks, {p.bridge_b:.3f} from Q along the handle line.",)),
        Part("htube", "Handle Tube", 1, '1-1/2" sch 80 pipe', "brown", handle_tube, group="Handle",
             views=("F", "L"), flat=False,
             dims=lambda p: [("V", "T", (p.handle_od / 2, 0, 0), (p.handle_od / 2, 0, p.handle_len - p.bridge_a - 0.75), 10),
                             ("D", "F", (0, 0, 0), p.handle_od, 45, "")],
             notes=("Butt-weld to the plain bridge, fillet-weld through the bored bridge.",)),
    ]
    for i, part in enumerate(ps, 1):
        part.item = i
    return ps


# ==========================================================
# Assembly
# ==========================================================

COLORS = {
    "gray": (0.62, 0.62, 0.64), "red": (0.80, 0.15, 0.12), "teal": (0.10, 0.55, 0.55),
    "green": (0.20, 0.55, 0.20), "orange": (0.95, 0.55, 0.10), "brown": (0.50, 0.30, 0.15),
    "pink": (0.95, 0.55, 0.70), "white": (0.95, 0.95, 0.95), "purple": (0.50, 0.25, 0.65),
}

MIRROR_Y = Plane.XZ
UPRIGHT = Rot(90, 0, 0)                     # local x->X, y->Z, z->-Y
EDGE = Rot(0, 0, 90) * Rot(90, 0, 0)        # local x->Y, y->Z, z->X


def assembly(p: Params, pose: str = "locked", handle_len: float | None = None):
    """[(part_key, instance_name, solid), ...] in world coordinates."""
    ps = poses(p)[pose] if isinstance(pose, str) else pose
    L, W = p.brick_l, p.brick_w
    out = []

    def add(key, name, s, mirror=False):
        out.append((key, name, s))
        if mirror:
            out.append((key, name + " (mirror)", s.mirror(MIRROR_Y)))

    # frame (fixed)
    rx0, rx1 = p.rail_x
    add("rail", "Base Rail", Pos(rx0, p.rail_y - p.rail_w / 2, 0) * base_rail(p), mirror=True)
    for x in (rx0, rx1 - 2.0):
        add("tie", "Cross Tie", Pos(x + 2.0, -(p.rail_y - p.rail_w / 2), 0) * cross_tie(p))
    add("side", "Side Wall", Pos(0, p.wall_out, p.zb) * UPRIGHT * side_wall(p), mirror=True)
    for x in (-p.t_end, L):
        add("end", "End Wall", Pos(x, -p.wall_out, p.zb) * EDGE * end_wall(p))
    ex, ez = p.eject_roller
    add("post", "Eject Roller Post", Pos(ex - 1.0, p.rail_y - 1.0, p.rail_h) * roller_post(p), mirror=True)
    n_er = 2 * (p.rail_y - 1.0) - 0.25
    add("eroll", "Eject Roller", Pos(ex, -n_er / 2, ez) * eject_roller(p))
    n_ea = 2 * (p.rail_y + 1.0) + 0.75
    add("eaxle", "Eject Roller Axle", Pos(ex, -n_ea / 2, ez) * eject_axle(p))
    hx, hz = hinge_axis(p)
    add("wlug", "Wall Hinge Lug", Pos(L + p.t_end, p.wall_out - 0.25, p.zt - 3.0) * UPRIGHT * wall_lug(p), mirror=True)

    # lid: hinged below its eject-end edge, opens toward the eject roller
    lid = Pos(hx, 0, hz) * Rot(0, ps.cover, 0) * Pos(-hx, 0, -hz)
    add("cover", "Lid Plate", lid * Pos(-p.t_end, -p.wall_out, p.zt) * cover_plate(p))
    for y in (p.rib_y + p.t_rib / 2,):
        add("rib", "Lid Rib", lid * Pos(0, y, p.zt + p.t_cover) * UPRIGHT * cover_rib(p), mirror=True)
    ly = p.wall_out - 0.75
    add("clug", "Lid Hinge Lug", lid * Pos(L - 1.5, ly, p.zt - 1.5) * UPRIGHT * cover_lug(p), mirror=True)
    add("hpin", "Hinge Pin", Pos(hx, ly - 1.0, hz) * hinge_pin(p), mirror=True)
    add("stop", "Handle Stop", lid * Pos(p.xc + STOP_X[0], -1.0, p.zt + p.t_cover) * handle_stop(p))

    # piston
    zcap = ps.zp + p.pin_below_cap - p.t_cap
    add("cap", "Piston Cap", Pos(p.clear / 2, -(W - p.clear) / 2, zcap) * piston_cap(p))
    add("web", "Piston Web", Pos(p.clear / 2, p.web_y, zcap - p.web_h) * UPRIGHT * piston_web(p), mirror=True)
    for x in (p.clear / 2, L - p.clear / 2 - 0.5):
        add("diaph", "Piston Diaphragm", Pos(x, -(p.web_y - p.t_web), zcap - p.web_h) * EDGE * piston_diaphragm(p))

    # yoke
    yk = Pos(p.xc, 0, ps.zp) * Rot(0, ps.theta, 0)
    pin_n = 2 * (p.bar_y + p.t_bar) + 1.25
    add("ppin", "Main Pin P", Pos(p.xc, -pin_n / 2, ps.zp) * Rot(0, 0, 90) * main_pin(p))
    add("bar", "Yoke Bar", yk * Pos(0, p.bar_y + p.t_bar, 0) * UPRIGHT * yoke_bar(p), mirror=True)
    q_n = p.t_cheek + 0.0625 + p.t_bar + 1.0
    for s in (1, -1):
        y0 = p.cheek_y - 0.5 if s > 0 else -(p.cheek_y - 0.5) - q_n
        add("qpin", "Stub Pin Q", yk * Pos(0, y0, p.yoke_len) * Rot(0, 0, 90) * q_pin(p))

    # handle head
    hf = _handle_frame(p, ps.theta, ps.psi, ps.zp)
    add("cheek", "Handle Cheek", hf * Pos(0, p.cheek_y + p.t_cheek, 0) * UPRIGHT * cheek(p), mirror=True)
    n_r = 2 * p.cheek_y - 0.125
    add("sroll", "Saddle Roller", hf * Pos(-p.arm, -n_r / 2, 0) * saddle_roller(p))
    ax_n = 2 * (p.cheek_y + p.t_cheek)
    add("axle", "Roller Axle", hf * Pos(-p.arm, -ax_n / 2, 0) * roller_axle(p))
    add("bridge", "Handle Bridge", hf * Pos(-1.25, -p.cheek_y, p.bridge_a) * bridge(p))
    add("bridgeb", "Handle Bridge, Bored", hf * Pos(-1.25, -p.cheek_y, p.bridge_b) * bridge(p, True))
    hl = p.handle_len if handle_len is None else handle_len
    ht0 = p.bridge_a + 0.75
    add("htube", "Handle Tube", hf * Pos(0, 0, ht0) * tube(p.handle_od, p.handle_od - 0.4, hl - ht0, "Z"))
    # central latch: catch bar between the cheeks; one claw (two plates + thumb bar) on a tie
    # between the yoke horns
    cx, cy = cheek_points(p)["catch"]
    nb = 2 * (p.cheek_y + p.t_cheek)
    add("catch", "Catch Bar", hf * Pos(cx, -nb / 2, cy) * catch_bar(p))
    cl = claw_geom(p)
    gamma = ps.claw if ps.claw is not None else (0.0 if abs(ps.psi - p.psi0) < 1e-9 else cl["open"])
    Ly = p.yoke_len
    (tx, tz), (sx, sz) = cl["C"], cl["stop"]
    nt = 2 * (p.bar_y + p.t_bar)
    add("ctie", "Claw Tie", yk * Pos(tx, -nt / 2, Ly + tz) * claw_tie(p))
    add("cstop", "Claw Stop Rod", yk * Pos(sx, -nt / 2, Ly + sz) * claw_stop(p))
    add("tspacer", "Tie Spacer", yk * Pos(tx, p.claw_y0 + p.claw_t + 0.0625, Ly + tz) * tie_spacer(p), mirror=True)
    cf = yk * Pos(tx, 0, Ly + tz) * Rot(0, gamma, 0) * Rot(0, -cl["arm"], 0)
    add("claw", "Claw Plate", cf * Pos(0, p.claw_y0 + p.claw_t, 0) * UPRIGHT * claw(p), mirror=True)
    ex, ey, _ = CLAW_EAR
    add("cthumb", "Claw Thumb Bar", cf * Pos(ex, -(p.claw_y0 + p.claw_t), ey) * claw_thumb(p))
    return out


def assembly_compound(p: Params, pose="locked", **kw) -> Compound:
    colors = {pt.key: pt.color for pt in parts(p)}
    kids = []
    for key, name, s in assembly(p, pose, **kw):
        s.label = name
        s.color = Color(*COLORS[colors[key]])
        kids.append(s)
    return Compound(children=kids, label=f"CINVA-Ram {p.label} ({pose})")


def interference(p: Params, pose: str, tol=0.002):
    """Pairs of solids that overlap by more than `tol` cubic inches."""
    inst = assembly(p, pose)
    hits = []
    for i in range(len(inst)):
        bi = inst[i][2].bounding_box()
        for j in range(i + 1, len(inst)):
            bj = inst[j][2].bounding_box()
            if (bi.max.X < bj.min.X or bj.max.X < bi.min.X or bi.max.Y < bj.min.Y or bj.max.Y < bi.min.Y
                    or bi.max.Z < bj.min.Z or bj.max.Z < bi.min.Z):
                continue
            v = (inst[i][2] & inst[j][2]).volume
            if v > tol:
                hits.append((inst[i][1], inst[j][1], round(v, 4)))
    return hits


def sweep_poses(p: Params, n=8):
    """Intermediate positions of every motion, for clearance checks."""
    ps = poses(p)
    out = []
    for i in range(n + 1):                     # compression stroke, lid closed, on to the stop
        psi = p.psi0 + (p.psi_stop - p.psi0) * i / n
        out.append(Pose(f"compress {psi:.0f}", 0.0, psi, p.q_z(psi) - p.yoke_len, 0))
    th_c = solve_theta(p, p.zp_comp)[1]
    for zp, th1, tag in ((p.zp_fill, ps["fill"].theta, "tilt at fill"), (p.zp_comp, th_c, "tilt after pressing")):
        for i in range(1, n + 1):              # latched tilt back, lid closed
            out.append(Pose(f"{tag} {th1 * i / n:.0f}", th1 * i / n, p.psi0, zp, 0))
    th1, th_f = ps["eject"].theta, ps["fill"].theta
    for i in range(n + 1):                     # ejection stroke, lid open (from piston at bottom)
        th = th_f + (th1 - th_f) * i / n
        out.append(Pose(f"eject {th:.0f}", th, p.psi0, zp_for_theta(p, th), p.lid_open))
    return out


def zp_for_theta(p: Params, th):
    """Pin P height when the latched handle rests on the eject roller at yoke tilt th."""
    r = p.d_eroll / 2 + p.handle_od / 2
    lo, hi = p.zp_fill - 3, p.zp_eject + 3
    for _ in range(60):
        mid = (lo + hi) / 2
        d, _ = _eject_contact(p, th, mid)
        if (d + r) > 0:   # roller not yet reached: handle above it -> lower P... sign found by test
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ==========================================================
# Strength checks (first-order hand calcs at the design load)
# ==========================================================

FY_A36, FU_A36, FY_4140, FY_AR400 = 36000.0, 58000.0, 95000.0, 145000.0
E_STEEL = 30e6


def checks(p: Params):
    """[(item, basis, stress psi, allowable psi)] at the design force."""
    F = p.f_design
    rows = []
    sec = lambda d: math.pi * d ** 3 / 32
    # main pin P: bending between piston web and yoke bar
    e = (p.bar_y + p.t_bar / 2) - (p.web_y - p.t_web / 2)
    rows.append(("Main pin P, bending", f"M = F/2 x {e:.2f}, dia {p.d_pin:.3f} 4140",
                 F / 2 * e / sec(p.d_pin), 0.6 * FY_4140))
    rows.append(("Main pin P, shear", "F/2 per side", F / 2 / (math.pi * p.d_pin ** 2 / 4), 0.4 * FY_4140))
    e = (p.bar_y + p.t_bar / 2) - (p.cheek_y + p.t_cheek / 2)
    rows.append(("Stub pins Q, bending", f"M = F/2 x {e:.2f}, dia {p.d_qpin:.3f} 4140",
                 F / 2 * e / sec(p.d_qpin), 0.6 * FY_4140))
    e = (p.cheek_y + p.t_cheek / 2) - p.rib_y
    rows.append(("Roller axle, bending", f"M = F/2 x {e:.2f}, dia {p.d_pin:.3f} 4140",
                 F / 2 * e / sec(p.d_pin), 0.6 * FY_4140))
    an = (p.w_bar - p.d_pin - 1 / 32) * p.t_bar
    rows.append(("Yoke bar, net tension", f"F/2 on {an:.2f} sq in", F / 2 / an, 0.5 * FU_A36))
    rows.append(("Yoke bar, pin bearing", f"F/2 on {p.d_pin:.2f} x {p.t_bar:.2f}", F / 2 / (p.d_pin * p.t_bar), 0.9 * FY_A36))
    rows.append(("Cheek, Q pin bearing", f"F/2 on {p.d_qpin:.2f} x {p.t_cheek:.2f}", F / 2 / (p.d_qpin * p.t_cheek), 0.9 * FY_A36))
    # side wall: lateral soil pressure K0 = 0.5 on the brick band, strip above the slot, ends fixed
    pl = 0.5 * p.p_design
    hs = p.zt - p.slot[1]
    M = pl * p.brick_h * p.brick_l ** 2 / 12
    rows.append(("Side wall, bending", f"K0 0.5, strip {hs:.2f} x {p.t_side:.3f}, ends fixed",
                 M / (hs * p.t_side ** 2 / 6), 0.66 * FY_A36))
    M = pl * p.brick_h * (p.brick_w + 2 * p.t_side) ** 2 / 12
    rows.append(("End wall, bending", f"K0 0.5, band {p.brick_h:g} x {p.t_end:.3f}",
                 M / (p.brick_h * p.t_end ** 2 / 6), 0.66 * FY_A36))
    # lid: roller load at centre vs brick pressure spread over L -> M = F L / 8
    b, tp = p.brick_w + 2 * p.t_side, p.t_cover
    hr = p.track_h                                 # rib height at the lock point
    A1, y1 = b * tp, tp / 2
    A2, y2 = 2 * p.t_rib * hr, tp + hr / 2
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = b * tp ** 3 / 12 + A1 * (yb - y1) ** 2 + 2 * p.t_rib * hr ** 3 / 12 + A2 * (y2 - yb) ** 2
    c = max(yb, tp + hr - yb)
    rows.append(("Lid, bending at centre", f"M = F L / 8, I = {I:.1f} in^4", F * p.brick_l / 8 * c / I, 0.66 * FY_A36))
    # piston cap: one-way strip between webs
    sp = 2 * (p.web_y - p.t_web)
    rows.append(("Piston cap, bending", f"strip span {sp:.2f}, t {p.t_cap:.3f}",
                 p.p_design * sp ** 2 / 8 / (p.t_cap ** 2 / 6), 0.66 * FY_A36))
    # piston web: supported at the pin, uniform load -> M = F L / 16 per web, net section at the hole
    h, t, dh = p.web_h, p.t_web, p.d_pin + 1 / 32
    yh = p.web_h - (p.pin_below_cap - p.t_cap)
    A, yc = t * h - t * dh, (t * h * h / 2 - t * dh * yh) / (t * h - t * dh)
    I = t * h ** 3 / 12 + t * h * (h / 2 - yc) ** 2 - (t * dh ** 3 / 12 + t * dh * (yh - yc) ** 2)
    rows.append(("Piston web, bending", "M = F L / 16, net at pin hole",
                 F * p.brick_l / 16 * max(yc, h - yc) / I, 0.66 * FY_A36))
    # central claw at the ejection load: yoke moment about Q = F x (horizontal P-Q distance)
    th = poses(p)["eject"].theta
    cl = claw_geom(p)
    fl = p.eject_force * p.yoke_len * math.sin(math.radians(th)) / cl["R"]        # on the claw
    ym = p.claw_y0 + p.claw_t / 2                                                  # claw plate centre
    e = (p.bar_y + p.t_bar / 2) - ym
    rows.append(("Claw tie, bending (eject)", f"{fl:,.0f} lbf, {fl / 2:,.0f} per plate x {e:.2f}, dia {p.tie_d:.3f} 4140",
                 fl / 2 * e / sec(p.tie_d), 0.6 * FY_4140))
    e = (p.cheek_y + p.t_cheek / 2) - ym
    rows.append(("Catch bar, bending (eject)", f"{fl / 2:,.0f} lbf per plate x {e:.2f}, dia {p.catch_d:.3f} 4140",
                 fl / 2 * e / sec(p.catch_d), 0.6 * FY_4140))
    rows.append(("Claw notch, bearing (eject)", f"{fl / 2:,.0f} lbf on {p.catch_d:.2f} x {p.claw_t:.2f}",
                 fl / 2 / (p.catch_d * p.claw_t), 0.9 * FY_A36))
    rows.append(("Claw arm, tension (eject)", f"{fl / 2:,.0f} lbf on {2 * CLAW_W:.2f} x {p.claw_t:.2f}",
                 fl / 2 / (2 * CLAW_W * p.claw_t), 0.6 * FY_A36))
    rows.append(("Yoke horn, net at tie hole (eject)", f"{fl / 2:,.0f} lbf on (2.60 - {p.tie_d:.2f}) x {p.t_bar:.2f}",
                 fl / 2 / ((2.6 - p.tie_d - 1 / 32) * p.t_bar), 0.5 * FU_A36))
    # roller contact (Hertz line contact, steel on steel)
    Es = E_STEEL / (2 * (1 - 0.3 ** 2))
    q = F / 2 / p.t_rib
    Rr = p.d_roll / 2
    # allowable Hertz pressure: subsurface shear 0.3 p <= 0.5 Fy of the softer part (AR400 rib)
    pa = 0.5 * FY_AR400 / 0.3
    rows.append(("Roller on track at lock, contact", f"R {Rr:.3f} in concave R {p.track_r:g}, AR400 rib",
                 math.sqrt(q * Es * (1 / Rr - 1 / p.track_r) / math.pi), pa))
    return rows


# ==========================================================
# Verification: real track geometry, brick path, lid balance
# ==========================================================

def rib_top(p: Params, x):
    """Top of the rib (absolute Z) at world x, including the concave track."""
    pts = rib_points(p)
    base = p.zt + p.t_cover
    top = None
    for (x0, y0), (x1, y1) in zip(pts[2:], pts[3:] + pts[:1]):
        lo, hi = min(x0, x1), max(x0, x1)
        if lo - 1e-9 <= x <= hi + 1e-9 and hi > lo:
            top = max(top or -1e9, y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    if top is None:
        return None
    zc, rs = p.track_arc
    dx = x - p.xc
    if abs(dx) < rs:
        top = min(top + base, zc - math.sqrt(rs * rs - dx * dx)) - base
    return base + top


def roller_centre_z(p: Params, x, n=241):
    """Height of the saddle roller centre resting on the rib track with its centre at x."""
    r = p.d_roll / 2
    best = -1e9
    for i in range(n):
        s = x - r + 2 * r * i / (n - 1)
        t = rib_top(p, s)
        if t is not None:
            best = max(best, t + math.sqrt(max(r * r - (s - x) ** 2, 0)))
    return best


def stroke(p: Params, step=0.5):
    """Stroke on the real rib geometry: [(psi, roller x, piston top rel. mold top)], start to stop."""
    angles, psi = [], p.psi0
    while psi < p.psi_stop:
        angles.append(psi)
        psi += step
    angles = sorted(set(angles + [90.0, p.psi_stop]))
    out = []
    for psi in angles:
        s = math.radians(psi)
        rx = p.xc - p.arm * math.cos(s)
        qz = roller_centre_z(p, rx) + p.arm * math.sin(s)
        out.append((psi, rx, qz - p.yoke_len + p.pin_below_cap - p.zt))
    return out


def lid_moment(p: Params, psi, pressure=None):
    """Moment (lbf in) of the pressing loads about the lid hinge; > 0 presses the free end down.
    Brick pushes up at the mold centre, roller pushes down where it sits, and past centre the
    handle bears on the stop post (on the lid, far end)."""
    F = (pressure or p.p_work) * p.area
    q0 = p.q_z(p.psi0)
    P = F * p.soil(max(min(p.q_z(min(psi, 90)) - q0, p.rise), 0) / p.rise)
    hx, _ = hinge_axis(p)
    rx = p.xc - p.arm * math.cos(math.radians(psi))
    m = P * (hx - rx) - P * (hx - p.xc)
    if psi > 90:                                     # over centre: stop reaction on the lid
        xs = p.xc + sum(STOP_X) / 2
        fs = P * (rx - p.xc) / (p.xc - xs)
        m += fs * (hx - xs)
    return m


def brick_solid(p: Params, piston_top, h=None):
    return Pos(0.01, -p.brick_w / 2 + 0.01, piston_top) * Box(p.brick_l - 0.02, p.brick_w - 0.02, h or p.brick_h,
                                                             align=Align.MIN)


def _hits(inst, solid, skip=(), tol=1e-3):
    bb = solid.bounding_box()
    out = []
    for key, name, s in inst:
        if key in skip:
            continue
        b = s.bounding_box()
        if (b.max.X < bb.min.X or bb.max.X < b.min.X or b.max.Y < bb.min.Y or bb.max.Y < b.min.Y
                or b.max.Z < bb.min.Z or bb.max.Z < b.min.Z):
            continue
        v = (s & solid).volume
        if v > tol:
            out.append((name, round(v, 4)))
    return out


def verify(p: Params):
    """Run every functional check; returns [(check, ok, detail)]."""
    res = []
    st = stroke(p)
    by = {round(a, 3): t for a, _, t in st}
    brick = -by[90.0]
    res.append(("Brick thickness at lock", abs(brick - p.brick_h) < 0.002, f"{brick:.4f} in (target {p.brick_h:g})"))
    res.append(("Piston at start = fill depth", abs(-st[0][2] - p.fill) < 0.002, f"{-st[0][2]:.4f} in below mold top"))
    press = [t for a, _, t in st if a <= 90.0]
    rising = all(b > a - 1e-9 for a, b in zip(press, press[1:]))
    res.append(("Piston rises steadily all the way to lock", rising,
                f"{-press[0]:.3f} -> {-press[-1]:.3f} in below mold top over {p.psi0:.1f} .. 90 deg, no dips"))
    t0, t1 = p.track
    xs = [x for _, x, _ in st]
    res.append(("Roller stays on the continuous track arc", t0 <= min(xs) and max(xs) <= t1,
                f"roller x {min(xs):.3f} .. {max(xs):.3f}, arc {t0:.3f} .. {t1:.3f}"))
    drop = by[90.0] - by[round(p.psi_stop, 3)]
    res.append(("Over-centre lock holds the handle on the stop", 0 < drop < 0.01,
                f"piston backs off {drop:.4f} in from 90 to {p.psi_stop:g} deg, so brick pressure pushes the handle "
                f"onto the stop"))
    res.append(("Handle raises out of the lock", 0 < drop < 0.01,
                f"lifting the handle back over centre re-compresses only {drop:.4f} in"))
    low = handle_low_point(p, p.psi_stop)
    top = p.zt + p.t_cover + handle_stop_h(p) + 0.25
    early = handle_low_point(p, 90.0) - top
    res.append(("Handle lands on the stop just past centre", abs(low - top) < 1e-6 and early > 0,
                f"touches at {p.psi_stop:g} deg; {early:.3f} in clear at 90 deg"))
    m = [lid_moment(p, a / 2, 306) for a in range(int(2 * p.psi0) + 1, int(2 * p.psi_stop) + 1)]
    res.append(("Lid stays closed under load", min(m) >= -1e-6,
                f"hinge moment {min(m):,.0f} .. {max(m):,.0f} lbf in (free end pressed down)"))
    ps0 = poses(p)
    rest = ps0["eject"]
    wall = [x for x in assembly(p, rest) if x[0] == "end"]
    def lug_hits(ang):
        lugs = [x[2] for x in assembly(p, Pose("lid", rest.theta, rest.psi, rest.zp, ang)) if x[0] == "clug"]
        return sum((l & w[2]).volume for l in lugs for w in wall)
    res.append(("Lid rests open on its stop", lug_hits(p.lid_open - 1) < 1e-4 and lug_hits(p.lid_open + 2) > 1e-4,
                f"tail lobe meets the end wall at {p.lid_open:g} deg, just past vertical"))
    cl = claw_geom(p)
    Sx, Sz = cl["S"]
    path = (-Sz / cl["R"], Sx / cl["R"])                        # catch bar path at S when the handle turns
    arm = (math.cos(math.radians(cl["arm"])), math.sin(math.radians(cl["arm"])))
    ang = math.degrees(math.acos(max(-1, min(1, abs(path[0] * arm[0] + path[1] * arm[1])))))
    res.append(("Claw load runs along the claw (cannot pry it open)", ang < 0.01,
                f"{ang:.3f} deg between catch-bar path and claw arm"))
    tilts = max(ps0["fill"].theta, ps0["eject"].theta)
    def g_torque(th, a):                                        # CCW (+) about the tie, CG direction a (deg)
        return -math.cos(math.radians(th - a))
    shut = [g_torque(tilts * i / 20, cl["cg_ang"]) for i in range(21)]
    wt = (2 * claw(p).volume + math.pi * 0.4375 ** 2 * (2 * p.claw_y0 + 2 * p.claw_t)) * STEEL
    res.append(("Gravity holds the claw shut at every tilt", min(shut) > 0,
                f"centre of mass at {cl['cg_ang']:.0f} deg from the tie; shutting moment from 0 to {tilts:.0f} deg tilt; "
                f"claw {wt:.1f} lb"))
    res.append(("Flipped-open claw stays open on its stop", g_torque(0.0, cl["cg_ang"] - cl["open"]) < 0,
                f"opens {cl['open']:.0f} deg clockwise; centre of mass 5 deg past vertical rests it on the stop rod"))
    def claw_stop_overlap(g):
        inst = assembly(p, Pose("claw", 0.0, 60.0, p.q_z(60.0) - p.yoke_len, 0.0, g))
        cw = [x[2] for x in inst if x[0] == "claw"]
        st_ = [x[2] for x in inst if x[0] == "cstop"]
        return sum((a & b).volume for a in cw for b in st_)
    res.append(("Open claw rests on the stop rod", claw_stop_overlap(cl["open"] - 0.5) < 1e-4
                and claw_stop_overlap(cl["open"] + 2) > 1e-4, f"stop rod at {cl['stop'][0]:.3f}, {cl['stop'][1]:.3f} from Q"))
    s0, s1 = p.slot
    res.append(("Side slots never open to the soil", s1 < p.zt - p.fill,
                f"slot top {s1 - p.zt:+.3f}, loose fill bottom {-p.fill:+.3f} from mold top"))
    # mold cavity clear in the pressing positions
    ps = poses(p)
    for key in ("start", "locked"):
        inst = assembly(p, key)
        pt = ps[key].zp + p.pin_below_cap
        cav = brick_solid(p, pt + 0.001, p.zt - pt - 0.002)
        h = _hits(inst, cav)
        res.append((f"Mold cavity clear ({key})", not h, "; ".join(f"{a} {v}" for a, v in h) or "nothing inside the mold"))
    # brick path during ejection and lift-off
    worst = []
    for pose in sweep_poses(p, n=6):
        if not pose.name.startswith("eject"):
            continue
        inst = assembly(p, pose)
        pt = pose.zp + p.pin_below_cap
        if pt < p.zt - p.brick_h:
            continue
        h = _hits(inst, brick_solid(p, pt), skip=("cap",))
        worst += [f"{pose.name}: {a} {v}" for a, v in h]
    res.append(("Brick rises out of the mold unobstructed", not worst, "; ".join(worst) or "clear at every step"))
    pe = ps["eject"].zp + p.pin_below_cap
    res.append(("Brick fully above the mold at eject", pe >= p.zt, f"brick bottom {pe - p.zt:+.3f} from mold top"))
    inst = assembly(p, "eject")
    lift = brick_solid(p, pe + 0.01, p.brick_h + 18.0)
    h = _hits(inst, lift)
    res.append(("Brick lifts straight off (18 in)", not h, "; ".join(f"{a} {v}" for a, v in h) or "clear"))
    return res


def parse_brick(s: str):
    v = [float(x) for x in s.lower().replace('"', "").split("x")]
    if len(v) == 2:
        v.append(4.0)
    return dict(brick_l=v[0], brick_w=v[1], brick_h=v[2])


def summary(p: Params):
    ps = poses(p)
    lines = [
        f"CINVA-Ram {p.label}: face {p.area:g} sq in, fill {p.fill:.3f} (ratio {p.fill / p.brick_h:.2f}), "
        f"box {p.box_h:.3f} tall, mold top at {p.zt:.3f}",
        f"  arm {p.arm:.3f}, handle start {p.psi0:.1f} deg, yoke P-Q {p.yoke_len:.4f}",
        f"  piston force {p.f_work:,.0f} lbf at {p.p_work:g} psi -> peak hand force {p.peak_hand():.0f} lbf "
        f"({p.handle_len:g} in handle); design {p.f_design:,.0f} lbf at {p.p_design:g} psi",
        "  poses: " + ", ".join(f"{k} theta={v.theta:.1f}" for k, v in ps.items()),
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="14x7x4", help="L x W x H in inches")
    ap.add_argument("--step", help="write assembly STEP (locked pose) to this path")
    ap.add_argument("--check", action="store_true", help="run interference checks on every pose")
    a = ap.parse_args()
    p = Params(**parse_brick(a.brick))
    print(summary(p))
    tot = sum(pt.weight(p) * pt.qty for pt in parts(p))
    print(f"  {len(parts(p))} part types, steel weight about {tot:.0f} lb")
    for item, basis, sig, allow in checks(p):
        print(f"  {item:32s} {sig / 1000:6.1f} ksi / {allow / 1000:5.1f}  {'ok' if sig <= allow else 'OVER'}  ({basis})")
    if a.check:
        for name, ok, detail in verify(p):
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
        for pose in poses(p):
            hits = interference(p, pose)
            print(f"  {pose:7s}: " + ("clear" if not hits else "; ".join(f"{a} x {b} ({v})" for a, b, v in hits)))
    if a.step:
        export_step(assembly_compound(p), a.step, unit=Unit.IN)
        print(f"  wrote {a.step}")


if __name__ == "__main__":
    main()
