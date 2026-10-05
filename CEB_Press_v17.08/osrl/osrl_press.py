"""
OSRL "Resilient Living" CEB press, rev 1.1: a clone of the Open Source Resilient Living drawings.

Source: OSRL CEB Press Drawings 1-1 (11 sheets, Dec 2011, design team Damien Gendron and Butte Metz,
CC BY-SA 3.0, www.osrliving.org) and the OSRL "Manual CEB Press" wiki pages. Every part and dimension
below is theirs (sheet numbers in the part notes). Where the drawings leave a placement open, the choice
is noted where it is made; where their part does not work as drawn, the change is flagged in the part's
notes and in DEVIATIONS.

The machine (CINVA type, 12 x 6 x 4 block with two 2-3/8 cores):
  * Body: front and rear C6x13 channels (webs are the mold ends, flanges point out) standing on a 1/4
    base plate, two 1/4 x 8 side plates across the top 8 in, two 2 in pipe guide rods standing on the base
    plate. The rods pass up through the mold and core the block. C3x6 outrigger mounts at the four bottom
    corners; two C3x6 outriggers bolt to the front pair.
  * Piston: 1/4 top plate with a 1/2 lower insert, on two 2-1/2 pipe guides that slide on the guide rods,
    two tapered side plates and a 1 in pipe pivot tube; the 1 in piston pin carries the yoke arms.
  * Yoke: two 3/8 x 2-1/2 arms; the yoke head (head bodies, head sides, pivot mounts) bolts to them in
    1 in steps. Hole 4 gives the 4 in block.
  * Toggle: square-tube toggle body (the 1-1/4 pipe lever slides in) on a 1 in toggle axle in the pivot
    mounts; two lower toggle plates carry the 2 in followers 2.875 from the toggle axle.
  * Lid: 3/16 plate with two 1/4 rails; each rail climbs from the hinge end to a 2 in scoop over the mold
    centre. Hinged on the front channel end and counterweighted so it opens and closes on its own.
  * Latch: hooks the toggle to the yoke head so lever and yoke swing as one onto the two eject rollers on
    the front channel; pushing the lever down then ejects the block.

Mechanism: with the lever latched along the yoke, standing the yoke up rolls the followers up the rail
slopes until they drop into the scoops (the manual's "letting the lower rollers fall into place"); that
happens with the piston still on the bottom. Release the latch and pull the lever over to horizontal: the
toggle turns about the seated followers, the toggle axle swings up over them, and the yoke lifts the
piston. At horizontal the axle is straight above the followers and the piston pin (dead centre).

Units: inches. World: X along the mold (0..12), front (hinge, eject rollers, outriggers) at -X; Y across,
centred; Z up, ground at Z = 0 (bottom of the outriggers and mounts).

Usage:
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 osrl_press.py [--check] [--step out.step]
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace
from functools import cached_property, lru_cache

import os
import sys

import numpy as np
from build123d import (
    Align, Axis, Box, Circle, Color, Compound, Cone, Cylinder, Plane, Pos, Rot, Unit, export_step, revolve,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cinva_simple import (
    ALONG_Y, COLORS, EDGE, MIRROR_Y, STEEL, UPRIGHT, Part, _pin_dims, _plate_dims, _rod_dims, hole, hull_plate,
    plate, poly, rod, tube,
)

# ==========================================================
# Their stock
# ==========================================================

C6 = dict(d=6.0, bf=2.157, tw=0.437, tf=0.343)       # C6x13
C3 = dict(d=3.0, bf=1.596, tw=0.356, tf=0.273)       # C3x6
PIPE = {"1": (1.315, 1.049), "1-1/4": (1.660, 1.380), "2": (2.375, 2.067), "2-1/2": (2.875, 2.469)}  # sch 40 OD, ID

T_ARM = 0.375            # yoke arms, head bodies, head sides, pivot mounts, lower toggles: 3/8 x 2-1/2
W_ARM = 2.5
ARM_LEN = 26.75
HB_LEN = 7.5             # head body
HS_H = 4.0               # head side
PM_LEN = 5.25            # pivot mount, hole 4.00 from the end
TB = (2.0, 0.1875, 9.0)  # toggle body: 2 sq tube, 3/16 wall, 9 long, axle 1-1/4 from the bottom
TB_AXLE = 1.25
LEVER_IN = 1.0           # lever bottom this far above the toggle axle (slid into the toggle body)
LT_LEN = 5.375           # lower toggle
LATCH = dict(len=5.25, h=1.5, t=0.125, hook=(2.0625, 2.75), pivot=(1.0, 4.75), rear=0.5)
LATCH_OPEN = 15.0        # latch lifted this far (deg) to release
CW = dict(d=3.5, t=1.375, pin=(0.5, 2.0), arm_t=0.125, arm_len=9.5)
HINGE_PIN = (0.375, 0.625)   # theirs 1-3/8 long; see DEVIATIONS


@dataclass(frozen=True)
class Params:
    brick_l: float = 12.0
    brick_w: float = 6.0
    brick_nom: float = 4.0
    hole_n: int = 4                  # yoke-arm hole (1..5 from the top) for the head's upper bolt
    eject_hole: int = 7              # eject axle hole: 7, 8 or 9 in up the front channel
    e: float = 2.875                 # toggle axle -> follower axle
    d_follow: float = 2.0
    lever_len: float = 48.0
    t_lid: float = 0.1875
    rail_y: float = 1.875            # rail centre lines from the lid centre line (sheet 9)
    t_rail: float = 0.25
    over: float = 0.0625             # block bottom this far above the mold top at the end of eject
    p_work: float = 200.0
    p_design: float = 300.0
    soil_k: float = 5.0
    eject_force: float = 600.0
    clear: float = 0.0

    @property
    def label(self):
        return f"{self.brick_l:g}x{self.brick_w:g}x{self.brick_nom:g}"

    @property
    def xc(self):
        return self.brick_l / 2

    zb = 3.0                         # top of the base plate (outrigger mounts are 3 deep)
    chan_len = 18.0

    @property
    def zt(self):                    # mold top = channel and side-plate tops
        return self.zb + self.chan_len

    @property
    def zL(self):                    # lid top
        return self.zt + self.t_lid

    @property
    def wall_y(self):
        return self.brick_w / 2

    @property
    def wall_out(self):
        return self.wall_y + 0.25

    # piston (sheet 8): pin 8-1/4 below the side tops, 1/4 top plate, 1/2 lower insert, sides 9-5/8 tall
    pin_below_cap = 9.0

    @property
    def zp_bot(self):                # piston sides on the base plate
        return self.zb + (9.625 - 8.25)

    @property
    def fill(self):
        return self.zt - (self.zp_bot + self.pin_below_cap)

    @property
    def pin_y(self):                 # outer faces of the piston sides / pivot tube ends
        return 5.875 / 2

    @property
    def arm_y(self):                 # inner faces of the arms: spacers 0.813 outside the pivot tube
        return self.pin_y + 0.8125

    # ---- lid rail (sheet 10), x from the rail's low (hinge) end, height above the lid top ----
    @cached_property
    def rail_profile(self):
        cx, cz, r = 6.0, 2.8, 1.0                   # 2 in scoop, 5.0 from the high end
        a1 = math.asin(2.5 - cz)                     # meets the 2-1/2 flat
        pts = [(0.0, 0.0), (0.0, 0.125), (4.75, 2.8), (5.0, 2.8)]
        n = 30
        for i in range(1, n + 1):
            a = math.pi + (math.pi + a1 - math.pi) * 0 + (2 * math.pi + a1 - math.pi) * i / n
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
        pts += [(9.5, 2.5), (11.0, 1.0), (11.0, 0.0)]
        return pts

    rail_x0 = 0.0                    # rail's low end: 1/2 in from the lid's hinge edge (lid -0.5 .. 12.5)

    @cached_property
    def seat(self):
        return self.xc, self.zL + 2.8

    @cached_property
    def _env(self):
        """Follower-centre envelope over the lid and rails: (xs, heights above the lid top)."""
        r = self.d_follow / 2
        segs = [((-0.5, 0.0), (12.5, 0.0))]
        prof = [(self.rail_x0 + x, h) for x, h in self.rail_profile]
        segs += list(zip(prof, prof[1:]))
        pts = []
        for (x0, h0), (x1, h1) in segs:
            n = max(2, int(math.hypot(x1 - x0, h1 - h0) / 0.005))
            t = np.linspace(0, 1, n)
            pts.append(np.stack([x0 + (x1 - x0) * t, h0 + (h1 - h0) * t], 1))
        pts = np.concatenate(pts)
        xs = np.arange(-14.0, 16.0, 0.005)
        out = np.full(xs.shape, -1e9)
        for px, ph in pts:
            m = np.abs(xs - px) < r
            if m.any():
                out[m] = np.maximum(out[m], ph + np.sqrt(r * r - (xs[m] - px) ** 2))
        return xs, out

    def env(self, x):
        xs, hs = self._env
        return float(np.interp(x, xs, hs))

    # ---- yoke and head (sheet 5): arm-frame (x toward +X when upright, z up the arm from P) ----
    @property
    def head_top(self):              # head sides' top: their upper hole on arm hole n (1 in from the arm top)
        return ARM_LEN - 1.25 - (self.hole_n - 1)

    @property
    def A_loc(self):
        """Toggle axle: 4.0 behind the front end of the pivot mounts (2-3/4 behind the arm centre line), the
        mounts' top edges on the head bodies' bottom edges. (Sheet 1 scales to 1/2 lower; that gives a 3.6 block at
        hole 4 and seats the followers with the piston 1/2 off the bottom, so the touching layout is taken.)"""
        return (2.75, self.head_top - 2.5 - 1.25)

    @property
    def D(self):                     # P -> toggle axle
        return math.hypot(*self.A_loc)

    @property
    def delta(self):                 # angle of P->A from the arm axis (deg, toward +X)
        return math.degrees(math.atan2(*self.A_loc))

    @property
    def F_loc(self):                 # follower axle with the lever along the arms (latched)
        return (self.A_loc[0] + self.e, self.A_loc[1])

    @property
    def yoke_len(self):
        return self.D

    # ---- latched stand-up: followers ride the rails ----
    def F_world(self, tau, zp):
        return arm_pt(self, tau, zp, self.F_loc)

    def standup_zp(self, tau):
        fx, fz = arm_pt(self, tau, 0.0, self.F_loc)
        return max(self.zp_bot, self.zL + self.env(fx) - fz)

    @cached_property
    def tau_seat(self):              # followers in the scoops, lever latched
        lx, lz = self.F_loc
        return -math.degrees(math.atan2(lx, lz))

    @cached_property
    def zp_seat(self):
        return self.seat[1] - math.hypot(*self.F_loc)

    # ---- pressing: toggle turns about the seated followers; psi = lever angle from vertical toward +X ----
    def press(self, psi):
        """(tau, phi, zp) at lever angle psi (deg, world)."""
        sx, sz = self.seat
        s = math.radians(psi)
        ax, az = sx - self.e * math.cos(s), sz + self.e * math.sin(s)
        zp = az - math.sqrt(self.D ** 2 - (ax - self.xc) ** 2)
        tau = math.degrees(math.atan2(ax - self.xc, az - zp)) - self.delta
        return tau, psi - tau, zp

    def q_z(self, psi):              # pin height at lever angle psi (drawing-sheet hook name)
        return self.press(psi)[2]

    @property
    def psi0(self):
        return self.tau_seat

    psi_stop = 90.0

    @cached_property
    def zp_lock(self):
        return self.press(90.0)[2]

    @property
    def zp_comp(self):
        return self.zp_lock

    @property
    def brick_h(self):
        return self.zt - (self.zp_lock + self.pin_below_cap)

    @property
    def rise(self):
        return round(self.zp_lock - self.zp_seat, 4)

    @property
    def zp_eject(self):
        return self.zt + self.over - self.pin_below_cap

    eject_over = property(lambda self: self.over)

    # ---- eject rollers (sheet 3: 3/4 axle holes 7, 8, 9 up the front channel, 1-5/16 from the web) ----
    @property
    def eroll(self):
        return -1.3125, self.zb + self.eject_hole

    eroll_d = W_ARM / 2 + 1.0       # arm axis -> roller centre when the arm rests on it

    # ---- lid hinge (sheet 2 detail A, sheet 3): hole 2-1/4 up a 3 in tab, tab top 1-7/8 above the plates ----
    @property
    def hinge(self):
        return -0.5, self.zt + 1.875 - 0.75

    # ---- loads ----
    @property
    def area(self):
        return self.brick_l * self.brick_w - 2 * math.pi * (PIPE["2"][0] / 2) ** 2

    def soil(self, eps):
        k = self.soil_k
        return (math.exp(k * eps) - 1) / (math.exp(k) - 1)

    handle_len = property(lambda self: self.lever_len)

    @property
    def grip(self):                  # toggle axle -> lever end
        return LEVER_IN + self.lever_len

    def grip_pt(self, psi):
        sx, sz = self.seat
        s = math.radians(psi)
        ax, az = sx - self.e * math.cos(s), sz + self.e * math.sin(s)
        return ax + self.grip * math.sin(s), az + self.grip * math.cos(s)

    def _stroke_point(self, psi, F):
        """(rise, piston force, hand force) at lever angle psi; hand force square to the lever."""
        zp = self.press(psi)[2]
        rise = zp - self.zp_seat
        P = F * self.soil(min(max(rise / self.rise, 0.0), 1.0))
        d = 0.05
        dz = self.press(min(psi + d, 90.0))[2] - self.press(psi - d)[2]
        g0, g1 = self.grip_pt(psi - d), self.grip_pt(min(psi + d, 90.0))
        return rise, P, max(P * dz / math.hypot(g1[0] - g0[0], g1[1] - g0[1]), 0.0)

    def hand(self, psi, pressure):
        return self._stroke_point(psi, pressure * self.area)[2]

    def peak_hand(self, pressure=None):
        pr = pressure or self.p_work
        a0 = self.psi0
        return max(self.hand(a0 + (90.0 - a0) * i / 400, pr) for i in range(1, 400))

    def pressure_for(self, force):
        lo, hi = 1.0, 3000.0
        for _ in range(40):
            m = (lo + hi) / 2
            lo, hi = (lo, m) if self.peak_hand(m) > force else (m, hi)
        return lo

    def stroke_table(self, pressure=None, step=5):
        pr = pressure or self.p_work
        out = []
        for a in range(math.ceil(self.psi0), 91, step):
            r, P, h = self._stroke_point(a, pr * self.area)
            out.append((a, r, P, h))
        return out

    @property
    def f_work(self):
        return self.p_work * self.area

    @property
    def f_design(self):
        return self.p_design * self.area

    @property
    def rail_x(self):                # assembly-views sheet: front view extents
        return -20.5, 26.0


def arm_pt(p: Params, tau, zp, local):
    """World (x, z) of arm-frame (x, z); tau = arm tilt from vertical, + toward +X."""
    c, s = math.cos(math.radians(tau)), math.sin(math.radians(tau))
    x, z = local
    return p.xc + x * c + z * s, zp - x * s + z * c


# ==========================================================
# Poses
# ==========================================================

@dataclass
class Pose:
    name: str
    tau: float        # yoke arm tilt from vertical, + toward the rear (+X)
    phi: float        # lever angle from the arms, + toward the rear
    zp: float         # piston pin height
    cover: float      # lid angle (deg, negative = open)
    claw: float = 0.0  # latch lift (deg)

    @property
    def theta(self):  # drawing sheets: yoke tilt
        return self.tau

    @property
    def psi(self):    # drawing sheets: lever angle (world)
        return self.tau + self.phi


def eject_zp(p: Params, tau):
    """Pin height with the arms resting on the eject rollers at tilt tau (< 0, toward the front)."""
    rx, rz = p.eroll
    c, s = math.cos(math.radians(tau)), math.sin(math.radians(tau))
    return rz - (p.eroll_d + (rx - p.xc) * c) / s


def solve_tau(p: Params, zp):
    lo, hi = -89.9, -1.0              # eject_zp falls as tau goes from -90 toward 0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if eject_zp(p, m) > zp else (lo, m)
    return (lo + hi) / 2


LID_KEYS = ("lid", "rail", "cwarm", "cw", "cwpin", "hpin", "uinsert")


@lru_cache(maxsize=None)
def lid_open(p: Params):
    """Lid opening angle: the lid swings open on its counterweights until a lid part first touches the frame
    (body, eject rollers); it rests there. Clashes with the yoke are left to the collision sweep."""
    t_f = solve_tau(p, p.zp_bot)
    prev = 0.0
    for i in range(1, 90):
        a = -2.0 * i
        inst = assembly(p, Pose("lid", t_f, 0.0, p.zp_bot, a))
        lids = [x for x in inst if x[0] in LID_KEYS]
        rest = [x for x in inst if GROUP_OF[x[0]] == "frame"]
        for ka, _, sa in lids:
            ba = sa.bounding_box()
            for kb, _, sb in rest:
                if frozenset((ka, kb)) in TOUCH:
                    continue
                bb = sb.bounding_box()
                if (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y
                        or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z):
                    continue
                if (sa & sb).volume > 1e-4:
                    return prev
        prev = a
    return prev


def poses(p: Params) -> dict:
    lo = lid_open(p)
    t_f, t_e = solve_tau(p, p.zp_bot), solve_tau(p, p.zp_eject)
    tl, phl, zl = p.press(90.0)
    return {
        "fill": Pose("Fill (latched, yoke on the eject rollers, lid open)", t_f, 0.0, p.zp_bot, lo),
        "start": Pose("Start of pressing (followers in the scoops)", p.tau_seat, 0.0, p.zp_seat, 0.0, LATCH_OPEN),
        "locked": Pose("Pressed (lever horizontal, dead centre)", tl, phl, zl, 0.0, LATCH_OPEN),
        "eject": Pose("Ejected (latched, lever pushed down)", t_e, 0.0, p.zp_eject, lo),
    }


# ==========================================================
# Part builders (part-local frames; flat parts in XY, thickness +Z)
# ==========================================================

def channel(c, length, holes=()):
    """C section along Z: web x 0..tw (back face x = 0), flanges y +-(d/2 - tf .. d/2) out to x = bf.
    holes: (x, z, dia) through Y."""
    d, bf, tw, tf = c["d"], c["bf"], c["tw"], c["tf"]
    s = Pos(0, -d / 2, 0) * Box(tw, d, length, align=Align.MIN)
    for y in (-d / 2, d / 2 - tf):
        s += Pos(0, y, 0) * Box(bf, tf, length, align=Align.MIN)
    for x, z, dia in holes:
        s -= Pos(x, d / 2 + 0.01, z) * ALONG_Y * rod(dia, d + 0.02, "Z")
    return s


def front_channel(p):
    return channel(C6, p.chan_len, [(1.3125, z, 0.75) for z in (7.0, 8.0, 9.0)])


def rear_channel(p):
    return channel(C6, p.chan_len, [(1.4375, z, 0.3125) for z in (2.0, 4.0, 14.0, 16.0)])


def side_plate(p):
    return plate(13.0, 8.0, 0.25)


BASE_HOLES = [(3.0 + 2.1875, 3.0, 0.5625), (9.0 + 2.1875, 3.0, 0.5625)]


def base_plate(p):
    s = plate(16.375, 6.0, 0.25)
    for x, y, d in BASE_HOLES:
        s -= hole(x, y, d, 0.25)
    return s


def c3_flat(length, holes=()):
    """C3x6 lying web-vertical: length along X, web in the XZ plane (y 0..tw), flanges out to +Y."""
    d, bf, tw, tf = C3["d"], C3["bf"], C3["tw"], C3["tf"]
    s = Box(length, tw, d, align=Align.MIN)
    for z in (0.0, d - tf):
        s += Pos(0, 0, z) * Box(length, bf, tf, align=Align.MIN)
    for x, dia in holes:
        s -= Pos(x, tw + 0.01, d / 2) * ALONG_Y * rod(dia, tw + 0.02, "Z")
    return s


def outrigger_mount(p):
    return c3_flat(4.5, [(0.75, 0.5), (3.75, 0.5)])


def outrigger(p):
    return c3_flat(18.0)


def mounting_tab(p):
    s = plate(6.0, 2.0, 0.3125)
    for x in (0.75, 4.5):
        s -= hole(x, 1.0, 0.5625, 0.3125)
    return s


def hinge_tab(p):
    pts = [(0.75, 0.0), (1.5, 0.0), (1.5, 2.25)]
    pts += [(0.75 + 0.75 * math.cos(math.radians(a)), 2.25 + 0.75 * math.sin(math.radians(a))) for a in range(0, 181, 10)]
    pts += [(0.0, 2.25)]
    return poly(pts, 0.125) - hole(0.75, 2.25, 0.375 + 1 / 32, 0.125)


def guide_rod(p):
    return tube(*PIPE["2"], p.chan_len, "Z")


def rod_top(p):
    return rod(2.0625, 0.25, "Z")


def rod_bottom(p):
    return rod(2.0625, 0.375, "Z") - Pos(0, 0, -0.01) * rod(0.4375, 0.4, "Z")


def eject_axle(p):
    return rod(0.75, 10.0, "Z")


def eject_roller(p):
    return tube(2.0, 0.75, 1.75, "Z")


# ---- piston (sheets 7, 8) ----
PT = (11.9375, 5.9375)
PISTON_HOLES = [(3.0 - 0.03125, PT[1] / 2, 2.375), (9.0 - 0.03125, PT[1] / 2, 2.375)]


def piston_top(p):
    s = plate(*PT, 0.25)
    for x, y, d in PISTON_HOLES:
        s -= hole(x, y, d, 0.25)
    return s


def stiffener(p):
    return plate(10.0, 1.0, 0.25)


def piston_guide(p):
    return tube(*PIPE["2-1/2"], 6.0, "Z")


SIDE_PTS = [(0.0, 9.625), (0.0, 5.375), (1.875, 0.0), (4.125, 0.0), (6.0, 5.375), (6.0, 9.625)]


def piston_side(p):
    return poly(SIDE_PTS, 0.25) - hole(3.0, 9.625 - 8.25, 1.3125, 0.25)


def pivot_tube(p):
    return tube(*PIPE["1"], 5.875, "Z")


def piston_pin(p):
    s = rod(1.0, 9.25, "Z")
    for z in (0.25, 9.0):
        s -= Pos(0, 0.6, z) * ALONG_Y * rod(0.15625, 1.2, "Z")
    return s


def pin_spacer(p):
    return tube(1.375, 1.0, 0.8125, "Z")


def _insert(d0, d1, h, hole_d):
    """Ring/countersink cone: d0 at z = h, d1 at z = 0."""
    return Cone(d1 / 2, d0 / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) - Pos(0, 0, -0.01) * rod(hole_d, h + 0.02, "Z")


def lower_insert(p):
    s = plate(*PT, 0.5)
    for x, y, d in PISTON_HOLES:
        s -= Pos(x, y, 0) * Cone(2.875 / 2 - 0.5, 3.875 / 2 + 0.001, 0.5 + 0.001,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        s -= hole(x, y, d, 0.5)
    return s


def upper_insert(p):
    return _insert(3.875, 2.875, 0.5, 2.375)


# ---- yoke (sheets 5, 6) ----
def yoke_arm(p):
    s = plate(W_ARM, ARM_LEN, T_ARM) - hole(W_ARM / 2, 1.25, 1.0, T_ARM)
    for k in range(1, 8):
        s -= hole(W_ARM / 2, ARM_LEN - k, 0.5, T_ARM)
    return s


def head_body(p):
    return plate(HB_LEN, W_ARM, T_ARM)


def head_side(p):
    return plate(W_ARM, HS_H, T_ARM) - hole(W_ARM / 2, 3.0, 0.4219, T_ARM) - hole(W_ARM / 2, 1.0, 0.4219, T_ARM)


def pivot_mount(p):
    s = hull_plate([(4.0, 1.25, 1.25)], [(0.0, 0.0, 4.0, 2.5)], T_ARM)
    return s - hole(4.0, 1.25, 1.0, T_ARM)


def toggle_body(p):
    w, t, L = TB
    s = Box(w, w, L, align=(Align.CENTER, Align.CENTER, Align.MIN)) - \
        Pos(0, 0, -0.01) * Box(w - 2 * t, w - 2 * t, L + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s - Pos(0, w / 2 + 0.01, TB_AXLE) * ALONG_Y * rod(1.0, w + 0.02, "Z")


def lower_toggle(p):
    s = hull_plate([(1.25, 1.25, 1.25), (1.25 + p.e, 1.25, 1.25)], [], T_ARM)
    return s - hole(1.25, 1.25, 1.0, T_ARM) - hole(1.25 + p.e, 1.25, 1.0, T_ARM)


def toggle_axle(p):
    return rod(1.0, 3.5, "Z")


def follower_axle(p):
    return rod(1.0, 6.0, "Z")


def follower(p):
    return tube(2.0, 1.0, 1.25, "Z")


def lever(p):
    return tube(*PIPE["1-1/4"], p.lever_len, "Z")


def latch_body(p):
    L, h, t = LATCH["len"], LATCH["h"], LATCH["t"]
    pts = [(0.0, h), (L, h), (L, 0.0), (h, 0.0)]          # 45 deg front end
    px = L - LATCH["rear"]
    return poly(pts, t) - hole(px, h / 2, 0.25 + 1 / 64, t)


def latch_hook(p):
    w, L = LATCH["hook"]
    return plate(L, w, LATCH["t"])


def latch_pivot(p):
    return rod(0.25, 2.5, "Z")


U_R = 0.975              # latch handle: 1/4 rod, 1.95 wide, 3-1/8 tall


def latch_handle(p):
    section = Plane.XZ * Pos(U_R, 0) * Circle(0.125)
    bend = Rot(0, 0, -90) * revolve(section, Axis.Z, 180)
    leg = 3.125 - U_R - 0.125
    s = Pos(0, -U_R, 0) * rod(0.25, leg, "X") + Pos(0, U_R, 0) * rod(0.25, leg, "X") + Pos(leg, 0, 0) * bend
    return Rot(0, -90, 0) * s                                # legs up +Z, U in the YZ plane


# ---- lid (sheets 9, 10) ----
def lid_plate(p):
    return plate(13.0, 6.5, p.t_lid)


def lid_rail(p):
    pts = p.rail_profile[1:-1] + [(11.0, 0.0), (0.0, 0.0)]
    return poly(pts, p.t_rail)


CWA_PTS = ([(0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (9.5, 2.25), (9.5, 2.5), (0.75, 2.5)]
           + [(0.75 + 0.75 * math.cos(math.radians(a)), 1.75 + 0.75 * math.sin(math.radians(a))) for a in range(100, 180, 10)]
           + [(0.0, 1.75)])


CWA_HOLE = (1.5, 0.9375)    # hinge hole in the block: sheet 9 puts the pin at the lid's hinge edge, at lid level


def cw_arm(p):
    """Counterweight arm (sheet 10), u from the block's rear end toward the tip, v up from the lid."""
    return poly(CWA_PTS, CW["arm_t"]) - hole(*CWA_HOLE, 0.375 + 1 / 32, CW["arm_t"])


CWA_REAR = 1.0           # block rear end on the lid (world x): hinge hole over the side plates' front edge
CW_PIN_UV = (9.25, 2.25)


def counterweight(p):
    return tube(CW["d"], 0.5, CW["t"], "Z")


def cw_pin(p):
    return rod(*CW["pin"], "Z")


def hinge_pin(p):
    return rod(*HINGE_PIN, "Z")


def cw_centre(p: Params, cover=0.0):
    return CWA_REAR - CW_PIN_UV[0], p.zL + CW_PIN_UV[1]


# ==========================================================
# Assembly
# ==========================================================

def arm_frame(p: Params, tau, zp):
    return Pos(p.xc, 0, zp) * Rot(0, tau, 0)


def toggle_frame(p: Params, tau, phi, zp):
    ax, az = p.A_loc
    return arm_frame(p, tau, zp) * Pos(ax, 0, az) * Rot(0, phi, 0)


def lid_frame(p: Params, cover):
    hx, hz = p.hinge
    return Pos(hx, 0, hz) * Rot(0, cover, 0) * Pos(-hx, 0, -hz)


def latch_frame(p: Params, claw):
    px, pz = LATCH["pivot"]
    return Pos(px, 0, pz) * Rot(0, claw, 0) * Pos(-px, 0, -pz)


def assembly(p: Params, pose: str = "locked", handle_len: float | None = None):
    """[(part_key, instance_name, solid), ...] in world coordinates."""
    ps = poses(p)[pose] if isinstance(pose, str) else pose
    out = []

    def add(key, name, s, mirror=False):
        out.append((key, name, s))
        if mirror:
            out.append((key, name + " (mirror)", s.mirror(MIRROR_Y)))

    zb, zt, L = p.zb, p.zt, p.brick_l
    # ---- body ----
    add("fchan", "Front Channel", Pos(0, 0, zb) * Rot(0, 0, 180) * front_channel(p))
    add("rchan", "Rear Channel", Pos(L, 0, zb) * rear_channel(p))
    add("side", "Side Plate", Pos(-0.5, p.wall_out, zt - 8.0) * UPRIGHT * side_plate(p), mirror=True)
    add("base", "Base Plate", Pos(p.xc - 16.375 / 2, -3.0, zb - 0.25) * base_plate(p))
    for x0 in (p.xc - 16.375 / 2, p.xc + 16.375 / 2 - 4.5):
        add("omount", "Outrigger Mount", Pos(x0, 3.0, 0) * outrigger_mount(p) if x0 < 0 else
            Pos(x0 + 4.5, 3.0, 0) * outrigger_mount(p).mirror(Plane.YZ), mirror=True)
    hx, hz = p.hinge
    add("hinge", "Lid Hinge", Pos(hx - 0.75, p.wall_out + 0.125, hz - 2.25) * UPRIGHT * hinge_tab(p), mirror=True)
    for x in (3.0, 9.0):
        add("grod", "Guide Rod", Pos(x, 0, zb) * guide_rod(p))
        add("rtop", "Rod Top", Pos(x, 0, zt - 0.25) * rod_top(p))
        add("rbot", "Rod Bottom", Pos(x, 0, zb) * rod_bottom(p))
    ex, ez = p.eroll
    add("eaxle", "Eject Axle", Pos(ex, 5.0, ez) * ALONG_Y * eject_axle(p))
    add("eroll", "Eject Roller", Pos(ex, 3.0 + 1.75, ez) * ALONG_Y * eject_roller(p), mirror=True)
    # ---- outriggers (front pair) ----
    x_end = p.xc - 16.375 / 2
    add("outr", "Outrigger", Pos(x_end - 18.0, 3.0, 0) * outrigger(p), mirror=True)
    add("otab", "Mounting Tab", Pos(x_end + 1.5, 3.0 + C3["tw"] + 0.3125, 0.5) * UPRIGHT * Rot(0, 0, 180)
        * Pos(-6.0, -2.0, 0) * mounting_tab(p), mirror=True)

    # ---- lid ----
    lf = lid_frame(p, ps.cover)
    add("lid", "Lid", lf * Pos(-0.5, -3.25, zt) * lid_plate(p))
    add("rail", "Lid Rail", lf * Pos(p.rail_x0, p.rail_y + p.t_rail / 2, p.zL) * UPRIGHT * lid_rail(p), mirror=True)
    add("cwarm", "Counterweight Arm", lf * Pos(CWA_REAR, 3.25, p.zL) * UPRIGHT
        * cw_arm(p).mirror(Plane.YZ), mirror=True)
    cx, cz = cw_centre(p)
    add("cwpin", "Counterweight Pin", lf * Pos(cx, 3.25, cz) * ALONG_Y * cw_pin(p), mirror=True)
    add("cw", "Counterweight", lf * Pos(cx, 3.25 - 0.625, cz) * ALONG_Y * counterweight(p), mirror=True)
    add("hpin", "Hinge Pin", lf * Pos(hx, 3.0 + HINGE_PIN[1], hz) * ALONG_Y * hinge_pin(p), mirror=True)
    for x in (3.0, 9.0):
        add("uinsert", "Upper Insert", lf * Pos(x, 0, zt - 0.5) * upper_insert(p))

    # ---- piston ----
    zp = ps.zp
    add("linsert", "Lower Insert", Pos(0.03125, -PT[1] / 2, zp + 8.5) * lower_insert(p))
    add("ptop", "Piston Top Plate", Pos(0.03125, -PT[1] / 2, zp + 8.25) * piston_top(p))
    for y in (2.0, -2.0):
        add("stiff", "Plate Stiffener", Pos(1.0, y + 0.125, zp + 7.25) * UPRIGHT * stiffener(p))
    for x in (3.0, 9.0):
        add("pguide", "Piston Guide", Pos(x, 0, zp + 2.25) * piston_guide(p))
    add("pside", "Piston Side", Pos(3.0, p.pin_y, zp - 1.375) * UPRIGHT * piston_side(p), mirror=True)
    add("ptube", "Pivot Tube", Pos(p.xc, p.pin_y, zp) * ALONG_Y * pivot_tube(p))
    add("ppin", "Piston Pin", Pos(p.xc, 4.625, zp) * ALONG_Y * piston_pin(p))
    add("spacer", "Pin Spacer", Pos(p.xc, p.arm_y, zp) * ALONG_Y * pin_spacer(p), mirror=True)

    # ---- yoke ----
    yk = arm_frame(p, ps.tau, zp)
    ht = p.head_top
    ay = p.arm_y
    add("arm", "Yoke Arm", yk * Pos(-W_ARM / 2, ay + T_ARM, -1.25) * UPRIGHT * yoke_arm(p), mirror=True)
    for xf in (-W_ARM / 2 - T_ARM, W_ARM / 2):
        add("hbody", "Head Body", yk * Pos(xf, -HB_LEN / 2, ht - W_ARM) * EDGE * head_body(p))
    add("hside", "Head Side", yk * Pos(-W_ARM / 2, ay, ht - HS_H) * UPRIGHT * head_side(p), mirror=True)
    ax, az = p.A_loc
    add("pmount", "Pivot Mount", yk * Pos(ax - 4.0, 1.0 + T_ARM, az - 1.25) * UPRIGHT * pivot_mount(p), mirror=True)

    # ---- toggle (lever group) ----
    tf = toggle_frame(p, ps.tau, ps.phi, zp)
    add("tbody", "Toggle Body", tf * Pos(0, 0, -TB_AXLE) * toggle_body(p))
    add("ltoggle", "Lower Toggle", tf * Pos(-1.25, 1.75, -1.25) * UPRIGHT * lower_toggle(p), mirror=True)
    add("taxle", "Toggle Axle", tf * Pos(0, 1.75, 0) * ALONG_Y * toggle_axle(p))
    add("faxle", "Follower Axle", tf * Pos(p.e, 3.0, 0) * ALONG_Y * follower_axle(p))
    add("follow", "Toggle Follower", tf * Pos(p.e, 3.0, 0) * ALONG_Y * follower(p), mirror=True)
    hl = p.lever_len if handle_len is None else handle_len
    add("lever", "Lever", tf * Pos(0, 0, LEVER_IN) * tube(*PIPE["1-1/4"], hl, "Z"))
    px, pz = LATCH["pivot"]
    add("lpivot", "Latch Pivot", tf * Pos(px, 1.25, pz) * ALONG_Y * latch_pivot(p))
    lt = tf * latch_frame(p, ps.claw)
    L, h, t = LATCH["len"], LATCH["h"], LATCH["t"]
    x0 = px + LATCH["rear"] - L                                    # latch front end
    add("lbody", "Latch Body", lt * Pos(x0, TB[0] / 2 + t, pz - h / 2) * UPRIGHT * latch_body(p), mirror=True)
    w, hl_ = LATCH["hook"]
    add("lhook", "Latch Hook", lt * Pos(x0, 0, pz + h / 2) * Rot(0, 45, 0)
        * Pos(0, -w / 2, -t) * latch_hook(p))
    add("lhandle", "Latch Handle", lt * Pos(px + 0.35, 0, pz - h / 2) * latch_handle(p))
    return out


def assembly_compound(p: Params, pose="locked", **kw) -> Compound:
    colors = {pt.key: pt.color for pt in parts(p)}
    kids = []
    for key, name, s in assembly(p, pose, **kw):
        s.label = name
        s.color = Color(*COLORS[colors[key]])
        kids.append(s)
    return Compound(children=kids, label=f"OSRL CEB press {p.label} ({pose})")


# parts that touch by design (welded, bolted, pinned, bearing)
TOUCH = {frozenset(x) for x in [
    ("fchan", "side"), ("rchan", "side"), ("fchan", "base"), ("rchan", "base"), ("base", "omount"),
    ("side", "hinge"), ("fchan", "eaxle"), ("eaxle", "eroll"), ("fchan", "eroll"),
    ("grod", "rtop"), ("grod", "rbot"), ("grod", "base"), ("rbot", "base"), ("omount", "otab"), ("outr", "otab"),
    ("omount", "outr"), ("fchan", "omount"), ("rchan", "omount"),
    ("lid", "rail"), ("lid", "cwarm"), ("cwarm", "cwpin"), ("cw", "cwpin"), ("cwarm", "hpin"), ("hinge", "hpin"),
    ("lid", "uinsert"), ("lid", "side"), ("lid", "fchan"), ("lid", "rchan"), ("lid", "rtop"), ("uinsert", "grod"),
    ("uinsert", "rtop"), ("lid", "grod"), ("cwarm", "hinge"),
    ("linsert", "ptop"), ("ptop", "stiff"), ("ptop", "pguide"), ("ptop", "pside"), ("pside", "ptube"),
    ("ptube", "ppin"), ("ppin", "spacer"), ("pside", "spacer"), ("ptube", "spacer"), ("ppin", "arm"),
    ("spacer", "arm"), ("ptop", "grod"), ("linsert", "grod"), ("pguide", "grod"), ("stiff", "pguide"),
    ("pside", "base"),
    ("arm", "hside"), ("arm", "hbody"), ("hbody", "hside"), ("hbody", "pmount"), ("pmount", "taxle"),
    ("pmount", "tbody"), ("pmount", "ltoggle"),
    ("tbody", "taxle"), ("tbody", "ltoggle"), ("ltoggle", "taxle"), ("ltoggle", "faxle"), ("faxle", "follow"),
    ("ltoggle", "follow"), ("tbody", "lever"), ("tbody", "lpivot"), ("lbody", "lpivot"), ("lbody", "lhook"),
    ("lbody", "lhandle"), ("tbody", "lbody"), ("follow", "rail"), ("ltoggle", "rail"), ("lhook", "hbody"),
    ("arm", "eroll"),
]}


def interference(p: Params, pose, tol=0.002, inst=None):
    inst = inst or assembly(p, pose)
    hits = []
    for i in range(len(inst)):
        bi = inst[i][2].bounding_box()
        for j in range(i + 1, len(inst)):
            if frozenset((inst[i][0], inst[j][0])) in TOUCH or inst[i][0] == inst[j][0]:
                continue
            bj = inst[j][2].bounding_box()
            if (bi.max.X < bj.min.X or bj.max.X < bi.min.X or bi.max.Y < bj.min.Y or bj.max.Y < bi.min.Y
                    or bi.max.Z < bj.min.Z or bj.max.Z < bi.min.Z):
                continue
            v = (inst[i][2] & inst[j][2]).volume
            if v > tol:
                hits.append((inst[i][1], inst[j][1], round(v, 4)))
    return hits


def sweep_poses(p: Params, n=8):
    ps = poses(p)
    t_f, t_e, t_s = ps["fill"].tau, ps["eject"].tau, p.tau_seat
    lo = ps["fill"].cover
    out = []
    for i in range(n + 1):                               # standing up / tilting back, latched, lid closed
        t = t_f + (t_s - t_f) * i / n
        out.append(Pose(f"stand up {t:.0f}", t, 0.0, p.standup_zp(t), 0.0))
    for i in range(1, n + 1):                            # latch lift at the seat
        out.append(Pose(f"latch {LATCH_OPEN * i / n:.0f}", t_s, 0.0, p.zp_seat, 0.0, LATCH_OPEN * i / n))
    for i in range(n + 1):                               # pressing
        psi = p.psi0 + (90.0 - p.psi0) * i / n
        t, ph, z = p.press(psi)
        out.append(Pose(f"press {psi:.0f}", t, ph, z, 0.0, LATCH_OPEN))
    for i in range(1, n + 1):                            # lid swinging, yoke on the rollers
        out.append(Pose(f"lid {lo * i / n:.0f}", t_f, 0.0, p.zp_bot, lo * i / n))
    for i in range(n + 1):                               # eject
        t = t_f + (t_e - t_f) * i / n
        out.append(Pose(f"eject {t:.0f}", t, 0.0, eject_zp(p, t), lo))
    return out


# ==========================================================
# Strength checks
# ==========================================================

FY_A36, FU_A36, FY_CRS, FY_A53 = 36000.0, 58000.0, 50000.0, 35000.0
E_STEEL = 30e6


def eject_hand(p: Params, tau, F=None):
    """Hand force (lbf, at the lever end, square to it) to eject at tilt tau."""
    F = p.eject_force if F is None else F
    d = 0.05
    gl = (p.A_loc[0], p.A_loc[1] + p.grip)

    def grip(t):
        return arm_pt(p, t, eject_zp(p, t), gl)
    g0, g1 = grip(tau + d), grip(tau - d)
    dz = eject_zp(p, tau - d) - eject_zp(p, tau + d)
    return F * dz / math.hypot(g1[0] - g0[0], g1[1] - g0[1])


def max_eject_hand(p: Params):
    t_c = solve_tau(p, p.zp_lock)
    t_e = solve_tau(p, p.zp_eject)
    return max(eject_hand(p, t_c + (t_e - t_c) * i / 20) for i in range(21))


def lid_balance(p: Params):
    """(lid moment, counterweight moment) about the hinge, lb in (positive = closes the lid)."""
    hx, _ = p.hinge
    mo = {"lid": 0.0, "cw": 0.0}
    for key, name, s in assembly(p, "start"):
        if key in ("lid", "rail", "cwarm", "cwpin", "hpin"):
            mo["lid"] += s.volume * STEEL * (s.center().X - hx)
        elif key == "cw":
            mo["cw"] += s.volume * STEEL * (s.center().X - hx)
    return mo["lid"], mo["cw"]


def checks(p: Params):
    """[(item, basis, stress psi, allowable psi)] at the design force."""
    F = p.f_design
    rows = []
    sec = lambda d: math.pi * d ** 3 / 32
    # piston pin: side plate (pivot tube end) to arm, across the spacer
    e = (p.arm_y + T_ARM / 2) - (p.pin_y - 0.125)
    rows.append(("Piston pin, bending", f"F/2 x {e:.3f}, 1 CRS", F / 2 * e / sec(1.0), 0.66 * FY_CRS))
    rows.append(("Piston pin, shear", "F/2 per side", F / 2 / (math.pi / 4), 0.4 * FY_CRS))
    an = (W_ARM - 1.0 - 1 / 16) * T_ARM
    rows.append(("Yoke arm, net tension at P", f"F/2 on {an:.3f} sq in", F / 2 / an, 0.5 * FU_A36))
    rows.append(("Yoke arm, pin bearing", "F/2 on 1.0 x 3/8", F / 2 / (1.0 * T_ARM), 0.9 * FY_A36))
    rows.append(("Head bolts, shear", "F/2 on two 1/2 bolts per side", F / 2 / (2 * math.pi / 4 * 0.5 ** 2), 0.4 * 92000))
    rows.append(("Yoke arm, bolt bearing", "F/2 on two 1/2 x 3/8", F / 2 / (2 * 0.5 * T_ARM), 0.9 * FY_A36))
    e = (1.375 + T_ARM / 2) - (1.0 + T_ARM / 2)
    rows.append(("Toggle axle, bending", f"F/2 x {e:.3f}, 1 CRS", F / 2 * e / sec(1.0), 0.66 * FY_CRS))
    rows.append(("Pivot mount, axle bearing", "F/2 on 1.0 x 3/8", F / 2 / (1.0 * T_ARM), 0.9 * FY_A36))
    e = p.rail_y - (1.375 + T_ARM / 2)
    rows.append(("Follower axle, bending", f"F/2 x {e:.3f}, 1 CRS", F / 2 * e / sec(1.0), 0.66 * FY_CRS))
    rows.append(("Rail scoop, bearing", "F/2 on 2.0 x 1/4 (follower seated)", F / 2 / (2.0 * p.t_rail), 0.9 * FY_A36))
    # lid + rails as a beam at the scoop bottom (1.8 high): follower load at the centre, soil spread over L
    b, tp = 6.5, p.t_lid
    hr = 1.8
    A1, y1 = b * tp, tp / 2
    A2, y2 = 2 * p.t_rail * hr, tp + hr / 2
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = b * tp ** 3 / 12 + A1 * (yb - y1) ** 2 + 2 * p.t_rail * hr ** 3 / 12 + A2 * (y2 - yb) ** 2
    c = max(yb, tp + hr - yb)
    rows.append(("Lid and rails, bending", f"F L / 8, I = {I:.2f} in^4", F * p.brick_l / 8 * c / I, 0.66 * FY_A36))
    span = 2 * (p.rail_y - p.t_rail / 2)
    rows.append(("Lid plate between rails", f"strip span {span:.2f}, 3/16", p.p_design * span ** 2 / 8 / (tp ** 2 / 6), 0.66 * FY_A36))
    over = 3.25 - (p.rail_y + p.t_rail / 2)
    rows.append(("Lid plate outside rails", f"cantilever {over:.3f}, 3/16", p.p_design * over ** 2 / 2 / (tp ** 2 / 6), 0.66 * FY_A36))
    # side plate: welded to the channel flanges at its ends only, free top and bottom; soil at 0.5 p
    q = 0.5 * p.p_design
    rows.append(("Side plate, bending", "K0 0.5, span 12, 1/4, ends fixed",
                 q * p.brick_l ** 2 / 12 / (0.25 ** 2 / 6), 0.66 * FY_A36))
    rows.append(("Channel web (mold end)", "K0 0.5, span 6, 0.437",
                 q * p.brick_w ** 2 / 12 / (C6["tw"] ** 2 / 6), 0.66 * FY_A36))
    sq = TB[0]
    s_tb = (sq ** 4 - (sq - 2 * TB[1]) ** 4) / (6 * sq)
    od, idd = PIPE["1-1/4"]
    s_lv = math.pi * (od ** 4 - idd ** 4) / (32 * od)
    fh = p.peak_hand(p.p_design)
    rows.append(("Lever, bending at socket", f"{fh:.0f} lbf x {p.grip - TB[2] + TB_AXLE:.1f}, 1-1/4 sch 40",
                 fh * (p.grip - TB[2] + TB_AXLE) / s_lv, 0.66 * FY_A53))
    rows.append(("Toggle body, bending", f"{fh:.0f} lbf x {p.grip:.1f}, 2 x 3/16 sq", fh * p.grip / s_tb, 0.66 * 46000))
    # eject
    fe = max_eject_hand(p)
    R = p.eject_force + fe
    e = 3.0 + 1.75 / 2 - 2.9 - 0.0
    arm = (3.0 + 0.875) - (3.0 - C6["tf"] / 2)
    rows.append(("Eject axle, bending", f"{R / 2:,.0f} lbf per roller x {arm:.2f}, 3/4 CRS", R / 2 * arm / sec(0.75), 0.66 * FY_CRS))
    t_c = solve_tau(p, p.zp_lock)
    zc = eject_zp(p, t_c)
    rx, rz = p.eroll
    dist = math.hypot(rx - p.xc, rz - zc)
    M = p.eject_force * abs(rx - p.xc) / 2
    rows.append(("Yoke arm, bending (eject)", f"{p.eject_force:,.0f} lbf at P x {abs(rx - p.xc):.1f}, 2 arms",
                 M / (T_ARM * W_ARM ** 2 / 6), 0.66 * FY_A36))
    return rows


# ==========================================================
# Verification
# ==========================================================

def brick_solid(p: Params, piston_top, h=None):
    s = Pos(0.01, -p.brick_w / 2 + 0.01, piston_top) * Box(p.brick_l - 0.02, p.brick_w - 0.02, h or p.brick_h,
                                                            align=Align.MIN)
    for x in (3.0, 9.0):
        s -= Pos(x, 0, piston_top - 0.01) * rod(PIPE["2"][0] + 0.02, (h or p.brick_h) + 0.02, "Z")
    return s


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


def verify(p: Params, sweep=True):
    """Every functional check; [(check, ok, detail)]."""
    res = []
    ps = poses(p)
    res.append(("Block thickness at hole " + str(p.hole_n), abs(p.brick_h - p.brick_nom) < 0.25,
                f"{p.brick_h:.3f} in (nominal {p.brick_nom:g}); holes 1..5 give "
                + ", ".join(f"{replace(p, hole_n=n).brick_h:.2f}" for n in range(1, 6))))
    res.append(("Compression ratio", 1.5 < p.fill / p.brick_h < 2.2,
                f"loose fill {p.fill:.3f} -> {p.brick_h:.3f} = {p.fill / p.brick_h:.2f}"))
    lift = p.zp_seat - p.zp_bot
    worst = max(p.standup_zp(p.tau_seat + (ps["fill"].tau - p.tau_seat) * i / 200) for i in range(201)) - p.zp_bot
    res.append(("Followers drop into the scoops as the yoke stands up", -1e-6 <= lift < 0.25 and worst < 1.5,
                f"seated at yoke tilt {p.tau_seat:.1f} deg with the piston {lift:.3f} in off the bottom; "
                f"riding over the rail lifts it at most {worst:.3f} in"))
    zs = [p.press(p.psi0 + (90 - p.psi0) * i / 100)[2] for i in range(101)]
    res.append(("Piston rises steadily as the lever goes over", all(b > a - 1e-9 for a, b in zip(zs, zs[1:])),
                f"lever {p.psi0:.1f} -> 90 deg, piston +{p.rise:.3f} in"))
    t1, ph1, _ = p.press(90.0)
    res.append(("Dead centre at lever horizontal", abs(p.press(90.0)[0] + p.delta) < 1e-6,
                f"toggle axle straight over the followers and the pin; yoke tilt {t1:.1f} deg. No positive stop "
                f"past centre in their drawings: the operator holds the lever down, then raises it"))
    t_f, t_e = ps["fill"].tau, ps["eject"].tau
    res.append(("Yoke rests on the eject rollers to fill and eject", -89 < t_e < t_f < -5,
                f"fill {t_f:.1f} deg, eject {t_e:.1f} deg (roller in hole {p.eject_hole})"))
    gl = (p.A_loc[0], p.A_loc[1] + p.grip)
    gs = [arm_pt(p, t_f, p.zp_bot, gl)[1], arm_pt(p, t_e, p.zp_eject, gl)[1]]
    res.append(("Eject: lever end stays above the ground", min(gs) > 6, f"lever end {gs[0]:.0f} in -> {gs[1]:.0f} in"))
    fe = max_eject_hand(p)
    res.append(("Eject hand force", fe < 120, f"{fe:.0f} lbf at {p.eject_force:,.0f} lbf to break the block loose"))
    ml, mc = lid_balance(p)
    res.append(("Lid counterweight balance", 0.6 < -mc / ml < 1.4,
                f"lid {ml:.0f} lb in, counterweights {mc:.0f} lb in about the hinge ({-mc / ml:.2f}); opens to "
                f"{-ps['fill'].cover:.0f} deg, resting on the front channel"))
    ph = p.peak_hand()
    res.append(("Lever force (their 80 lbf)", True,
                f"peak {ph:.0f} lbf at {p.p_work:g} psi; 80 lbf presses to {p.pressure_for(80):.0f} psi"))
    if not sweep:
        return res
    for key in ("start", "locked"):
        inst = assembly(p, key)
        pt = ps[key].zp + p.pin_below_cap
        cav = brick_solid(p, pt + 0.001, p.zt - pt - 0.002)
        h = _hits(inst, cav, skip=("grod", "rtop", "uinsert"))
        res.append((f"Mold cavity clear ({key})", not h, "; ".join(f"{a} {v}" for a, v in h) or "nothing inside the mold"))
    bad = []
    for pose in list(ps.values()) + sweep_poses(p, n=6):
        bad += [f"{pose.name}: {a} x {b} ({v})" for a, b, v in interference(p, pose)]
    res.append(("All positions and motions clear", not bad, "; ".join(bad[:12]) or "clear"))
    worst = []
    for pose in sweep_poses(p, n=6):
        if not pose.name.startswith("eject"):
            continue
        inst = assembly(p, pose)
        pt = pose.zp + p.pin_below_cap
        if pt < p.zt - p.brick_h:
            continue
        worst += [f"{pose.name}: {a} {v}" for a, v in _hits(inst, brick_solid(p, pt), skip=("linsert", "grod", "rtop", "uinsert"))]
    res.append(("Block rises out of the mold unobstructed", not worst, "; ".join(worst) or "clear at every step"))
    pe = ps["eject"].zp + p.pin_below_cap
    res.append(("Block fully above the mold at eject", pe >= p.zt - 1e-6, f"block bottom {pe - p.zt:+.3f} from mold top"))
    h = _hits(assembly(p, "eject"), brick_solid(p, pe + 0.01, p.brick_h + 18.0))
    res.append(("Block lifts straight off (18 in)", not h, "; ".join(f"{a} {v}" for a, v in h) or "clear"))
    return res


def parse_brick(s: str):
    v = [float(x) for x in s.lower().replace('"', "").split("x")]
    out = dict(brick_l=v[0], brick_w=v[1])
    if len(v) > 2:
        out["brick_nom"] = v[2]
    if (v[0], v[1]) != (12.0, 6.0):
        raise SystemExit("the OSRL press is a 12 x 6 machine; the thickness is set by the yoke hole (hole_n)")
    return out


def summary(p: Params):
    ps = poses(p)
    return "\n".join([
        f"OSRL CEB press {p.label}: fill {p.fill:.3f} -> block {p.brick_h:.3f} (yoke hole {p.hole_n}), "
        f"mold top {p.zt:.2f} above the ground",
        f"  toggle e {p.e:g}, P->axle {p.D:.3f}, lever {p.psi0:.1f} -> 90 deg, piston +{p.rise:.3f}",
        f"  piston force {p.f_work:,.0f} lbf at {p.p_work:g} psi -> peak hand force {p.peak_hand():.0f} lbf "
        f"({p.lever_len:g} in lever); design {p.f_design:,.0f} lbf at {p.p_design:g} psi",
        "  poses: " + ", ".join(f"{k} tau={v.tau:.1f}" for k, v in ps.items()),
    ])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="12x6x4")
    ap.add_argument("--hole", type=int, default=4)
    ap.add_argument("--step")
    ap.add_argument("--check", action="store_true", help="also run the collision sweeps")
    a = ap.parse_args()
    p = Params(**parse_brick(a.brick), hole_n=a.hole)
    print(summary(p))
    tot = sum(pt.weight(p) * pt.qty for pt in parts(p))
    print(f"  {len(parts(p))} part types, weight about {tot:.0f} lb (their 205 lb)")
    for item, basis, sig, allow in checks(p):
        print(f"  {item:38s} {sig / 1000:6.1f} ksi / {allow / 1000:5.1f}  {'ok' if sig <= allow else 'OVER'}  ({basis})")
    for name, ok, detail in verify(p, sweep=a.check):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if a.step:
        export_step(assembly_compound(p), a.step, unit=Unit.IN)


# ==========================================================
# Part registry
# ==========================================================

@dataclass
class Insert(Part):
    density: float = 0.035          # UHMW / hardwood, lb/in^3

    def weight(self, p):
        return self.build(p).volume * self.density


def parts(p: Params) -> list[Part]:
    pl = lambda t: f"{t} plate"
    ps = [
        # ---------------- body (sheets 2, 3, 4) ----------------
        Part("fchan", "Front Channel", 1, "C6x13 x 18", "gray", front_channel, group="Body",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("V", "F", (0, 0, 0), (0, 0, p.chan_len), -10), ("H", "F", (0, 0, 0), (C6["bf"], 0, 0), -10),
                             ("V", "F", (0, 0, 0), (1.3125, 0, 7.0), 10), ("V", "F", (0, 0, 0), (1.3125, 0, 8.0), 18),
                             ("V", "F", (0, 0, 0), (1.3125, 0, 9.0), 26), ("H", "F", (0, 0, p.chan_len), (1.3125, 0, 9.0), 8),
                             ("D", "F", (1.3125, 0, 9.0), 0.75, 60, "6x THRU ", 14)],
             notes=("Sheet 3. Eject axle in the 7 in hole (sheet 2); 8 and 9 tilt the yoke less at eject.",
                    "Web back face is the mold end. Grind 1/32 off each flange face if the block comes out over 6.")),
        Part("rchan", "Rear Channel", 1, "C6x13 x 18", "gray", rear_channel, group="Body",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("V", "F", (0, 0, 0), (0, 0, p.chan_len), -10), ("H", "F", (0, 0, 0), (C6["bf"], 0, 0), -10)]
             + [("V", "F", (0, 0, 0), (1.4375, 0, z), 10 + 8 * i) for i, z in enumerate((2.0, 4.0, 14.0, 16.0))]
             + [("H", "F", (0, 0, p.chan_len), (1.4375, 0, 16.0), 8), ("D", "F", (1.4375, 0, 16.0), 0.3125, 60, "3/8 UNC 8x ", 14)],
             notes=("Sheet 3. The tapped holes take a hopper or bench bracket (not in the drawings).",)),
        Part("side", "Side Plate", 2, pl("1/4 x 8") + " x 13", "gray", side_plate, group="Body",
             dims=lambda p: _plate_dims(13.0, 8.0, (), 0.25),
             notes=("Sheet 3. Weld to the outside of both channels' flanges, top flush, 1/2 past each web.",
                    "The 1/4 plate spans 12 in between the flanges with nothing across it; see the design sheet.")),
        Part("base", "Base Plate", 1, pl("1/4 x 6") + " x 16-3/8", "gray", base_plate, group="Body",
             dims=lambda p: _plate_dims(16.375, 6.0, BASE_HOLES, 0.25),
             notes=("Sheet 3. 9/16 holes take the guide rods' 1/2 UNC bolts from below.",)),
        Part("omount", "Outrigger Mount", 4, "C3x6 x 4-1/2", "gray", outrigger_mount, group="Body",
             views=("F", "T", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (4.5, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 0, 3.0), -10),
                             ("H", "F", (0, 0, 3.0), (0.75, 0, 1.5), 8), ("H", "F", (0, 0, 3.0), (3.75, 0, 1.5), 16),
                             ("D", "F", (3.75, 0, 1.5), 0.5, 60, "1/2 UNC 2x ", 12)],
             notes=("Sheet 3. Web flush with the base plate edge, flanges out; weld to the base plate and channel.",)),
        Part("hinge", "Lid Hinge", 2, pl("1/8 x 1-1/2"), "gray", hinge_tab, group="Body",
             dims=lambda p: [("H", "F", (0, 0, 0), (1.5, 0, 0), -10), ("V", "F", (1.5, 0, 0), (1.5, 3.0, 0), 10),
                             ("V", "F", (1.5, 0, 0), (0.75, 2.25, 0), 18), ("H", "F", (0.75, 0, 0), (1.5, 0, 0), -18),
                             ("D", "F", (0.75, 2.25, 0), 0.40625, 135, "", 10)],
             notes=("Sheets 2, 3. Hole 1-1/8 above the side plate top, over its front edge (detail A).",)),
        Part("grod", "Guide Rod", 2, '2" sch 40 pipe x 18', "gray", guide_rod, group="Body",
             views=("F", "T"), front="-Y", flat=False, dims=lambda p: _rod_dims(PIPE["2"][0], 18.0),
             notes=("Sheet 4. Plumb on the base plate, 6.00 apart, centred in the mold. Forms the block's cores.",)),
        Part("rtop", "Rod Top", 2, pl("1/4") + " dia 2-1/16", "gray", rod_top, group="Body",
             views=("T", "F"), front="-Y", dims=lambda p: _rod_dims(2.0625, 0.25),
             notes=("Sheet 4. Weld flush in the rod's top end; grind smooth.",)),
        Part("rbot", "Rod Bottom", 2, pl("3/8") + " dia 2-1/16", "gray", rod_bottom, group="Body",
             views=("T", "F"), front="-Y", dims=lambda p: _rod_dims(2.0625, 0.375),
             notes=("Sheet 4. Weld in the rod's bottom end; tap 1/2 UNC.",)),
        Part("eaxle", "Eject Axle", 1, '3/4" CRS x 10', "purple", eject_axle, group="Body",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(0.75, 10.0),
             notes=("Sheet 4. Through both front-channel flanges; washers and cotters outside the rollers.",)),
        Part("eroll", "Eject Roller", 2, '2" CRS x 1-3/4', "white", eject_roller, group="Body",
             views=("T", "F"), front="-Y", flat=False, dims=lambda p: _rod_dims(2.0, 1.75),
             notes=("Sheet 4. 3/4 bore. The yoke arms rest on these to fill and to eject.",)),
        # ---------------- outriggers (sheets 2, 4) ----------------
        Part("outr", "Outrigger", 2, "C3x6 x 18", "red", outrigger, group="Outrigger",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (18.0, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 0, 3.0), -10)],
             notes=("Sheet 4. In line with the front mounts, toward the eject side.",)),
        Part("otab", "Mounting Tab", 2, pl("5/16 x 2") + " x 6", "red", mounting_tab, group="Outrigger",
             dims=lambda p: _plate_dims(6.0, 2.0, [(0.75, 1.0, 0.5625), (4.5, 1.0, 0.5625)], 0.3125),
             notes=("Sheet 4. Weld in the outrigger, 1-1/2 protruding; bolt to the mount (1/2 UNC).",)),
        # ---------------- piston (sheets 7, 8) ----------------
        Part("ptop", "Piston Top Plate", 1, pl("1/4"), "teal", piston_top, group="Piston",
             dims=lambda p: _plate_dims(*PT, PISTON_HOLES, 0.25),
             notes=("Sheet 8. 11-15/16 x 5-15/16: 1/32 running clearance in the mold.",)),
        Part("stiff", "Plate Stiffener", 2, pl("1/4 x 1") + " x 10", "teal", stiffener, group="Piston",
             dims=lambda p: _plate_dims(10.0, 1.0, (), 0.25),
             notes=("Sheet 8. On edge under the top plate, 2 in each side of the centre line.",)),
        Part("pguide", "Piston Guide", 2, '2-1/2" sch 40 pipe x 6', "teal", piston_guide, group="Piston",
             views=("F", "T"), front="-Y", flat=False, dims=lambda p: _rod_dims(PIPE["2-1/2"][0], 6.0),
             notes=("Sheet 8. Under the top plate holes; slides on the guide rods.",)),
        Part("pside", "Piston Side", 2, pl("1/4 x 6"), "teal", piston_side, group="Piston",
             dims=lambda p: [("H", "F", (0, 0, 0), (6.0, 9.625, 0), 10), ("V", "F", (6.0, 0, 0), (6.0, 9.625, 0), 10),
                             ("V", "F", (6.0, 9.625, 0), (6.0, 5.375, 0), 18), ("H", "F", (0, 0, 0), (1.875, 0, 0), -10),
                             ("H", "F", (0, 0, 0), (4.125, 0, 0), -18), ("V", "F", (0, 0, 0), (3.0, 1.375, 0), -10),
                             ("D", "F", (3.0, 1.375, 0), 1.3125, 45, "", 10)],
             notes=("Sheet 8. The piston rests on the base plate on these (pin 1-3/8 up).",)),
        Part("ptube", "Pivot Tube", 1, '1" sch 40 pipe x 5-7/8', "teal", pivot_tube, group="Piston",
             views=("F", "T"), front="-Y", flat=False, dims=lambda p: _rod_dims(PIPE["1"][0], 5.875),
             notes=("Sheet 8. Through both piston sides, ends flush outside.",)),
        Part("ppin", "Piston Pin", 1, '1" CRS x 9-1/4', "purple", piston_pin, group="Piston",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _pin_dims(1.0, 9.25),
             notes=("Sheet 8. 5/32 cross holes 1/4 from the ends for cotter pins.",)),
        Part("spacer", "Pin Spacer", 2, '1-3/8" OD x 1" bore', "purple", pin_spacer, group="Piston",
             views=("T", "F"), front="-Y", flat=False, dims=lambda p: _rod_dims(1.375, 0.8125),
             notes=("Sheet 8. Between the pivot tube ends and the yoke arms.",)),
        Insert("linsert", "Lower Insert", 1, '1/2" aluminium, plastic or wood', "yellow", lower_insert, group="Piston",
               dims=lambda p: _plate_dims(*PT, PISTON_HOLES, 0.5),
               notes=("Sheet 8. 45 deg countersinks 3-7/8 at the face chamfer the cores.",)),
        # ---------------- yoke (sheets 5, 6) ----------------
        Part("arm", "Yoke Arm", 2, pl("3/8 x 2-1/2") + " x 26-3/4", "brown", yoke_arm, group="Yoke",
             dims=lambda p: _plate_dims(W_ARM, ARM_LEN, [(W_ARM / 2, 1.25, 1.0)] + [(W_ARM / 2, ARM_LEN - k, 0.5) for k in range(1, 8)], T_ARM),
             notes=("Sheet 6. Drill both arms stacked. Head bolts in holes n and n+2; hole 4 gives the 4 in block.",)),
        Part("hbody", "Head Body", 2, pl("3/8 x 2-1/2") + " x 7-1/2", "brown", head_body, group="Yoke",
             dims=lambda p: _plate_dims(HB_LEN, W_ARM, (), T_ARM),
             notes=("Sheet 6. Across the arms at their front and rear edges, between the head sides.",)),
        Part("hside", "Head Side", 2, pl("3/8 x 2-1/2") + " x 4", "brown", head_side, group="Yoke",
             dims=lambda p: _plate_dims(W_ARM, HS_H, [(W_ARM / 2, 3.0, 0.4219), (W_ARM / 2, 1.0, 0.4219)], T_ARM),
             notes=("Sheet 6. Tap 1/2 UNF; bolts from outside through the arm.",)),
        Part("pmount", "Pivot Mount", 2, pl("3/8 x 2-1/2") + " x 5-1/4", "brown", pivot_mount, group="Yoke",
             dims=lambda p: [("H", "F", (0, 0, 0), (5.25, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 2.5, 0), -10),
                             ("H", "F", (0, 2.5, 0), (4.0, 1.25, 0), 8), ("D", "F", (4.0, 1.25, 0), 1.0, 45, "", 10),
                             ("H", "L", (0, 0, 0), (0, 0, T_ARM), -10)],
             notes=("Sheet 6. 2.0 apart either side of the toggle body, under the head bodies; the toggle axle "
                    "sits 2-3/4 behind the arm centre line, so the lever swings over clear of the head.",)),
        Part("tbody", "Toggle Body", 1, '2" sq x 3/16 tube x 9', "orange", toggle_body, group="Toggle",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("V", "F", (0, 0, 0), (0, 0, TB[2]), -10), ("H", "F", (-1, 0, 0), (1, 0, 0), -10),
                             ("V", "F", (0, 0, 0), (0, 0, TB_AXLE), 10)],
             notes=("Sheet 6. 1 in hole 1-1/4 from the bottom; weld the toggle axle in it and the lower toggles to it.",)),
        Part("ltoggle", "Lower Toggle", 2, pl("3/8 x 2-1/2") + " x 5-3/8", "orange", lower_toggle, group="Toggle",
             dims=lambda p: [("H", "F", (0, 0, 0), (LT_LEN, 0, 0), -10), ("H", "F", (1.25, 2.5, 0), (1.25 + p.e, 2.5, 0), 8),
                             ("D", "F", (1.25, 1.25, 0), 1.0, 135, "2x ", 10), ("H", "L", (0, 0, 0), (0, 0, T_ARM), -10)],
             notes=("Sheet 6. Square to the toggle body: follower axle behind the toggle axle with the lever upright.",)),
        Part("taxle", "Toggle Axle", 1, '1" CRS x 3-1/2', "purple", toggle_axle, group="Toggle",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(1.0, 3.5),
             notes=("Sheet 6. Turns in the pivot mounts.",)),
        Part("faxle", "Follower Axle", 1, '1" CRS x 6', "purple", follower_axle, group="Toggle",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(1.0, 6.0),
             notes=("Sheet 6.",)),
        Part("follow", "Toggle Follower", 2, '2" CRS x 1-1/4', "white", follower, group="Toggle",
             views=("T", "F"), front="-Y", flat=False, dims=lambda p: _rod_dims(2.0, 1.25),
             notes=("Sheet 6. 1 in bore. Rides the lid rails and seats in the scoops.",)),
        Part("lever", "Lever", 1, '1-1/4" sch 40 pipe x 48', "orange", lever, group="Toggle",
             views=("F", "T"), front="-Y", flat=False, dims=lambda p: _rod_dims(PIPE["1-1/4"][0], p.lever_len),
             notes=("Sheet 6. Grind flats to slide into the toggle body; do not weld (it comes out for carrying).",)),
        Part("lbody", "Latch Body", 2, pl("1/8 x 1-1/2") + " x 5-1/4", "pink", latch_body, group="Toggle",
             dims=lambda p: [("H", "F", (0, 0, 0), (LATCH["len"], 0, 0), -10), ("V", "F", (LATCH["len"], 0, 0), (LATCH["len"], LATCH["h"], 0), 10),
                             ("H", "F", (0, LATCH["h"], 0), (LATCH["len"] - LATCH["rear"], LATCH["h"] / 2, 0), 8),
                             ("D", "F", (LATCH["len"] - LATCH["rear"], LATCH["h"] / 2, 0), 0.265, 45, "", 10)],
             notes=("Sheet 6. 45 deg front end carries the hook.",)),
        Part("lhook", "Latch Hook", 1, pl("1/8") + " 2-1/16 x 2-3/4", "pink", latch_hook, group="Toggle",
             dims=lambda p: _plate_dims(LATCH["hook"][1], LATCH["hook"][0], (), LATCH["t"]),
             notes=("Sheet 6. Drops in front of the rear head body and holds the lever along the yoke.",)),
        Part("lpivot", "Latch Pivot", 1, '1/4" CRS x 2-1/2', "purple", latch_pivot, group="Toggle",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(0.25, 2.5),
             notes=("Sheet 6. Weld across the back of the toggle body.",)),
        Part("lhandle", "Latch Handle", 1, '1/4" CRS, bent U', "pink", latch_handle, group="Toggle",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("V", "L", (0, -U_R, 0), (0, -U_R, 3.125), -10), ("H", "L", (0, -U_R, 0), (0, U_R, 0), -10)],
             notes=("Sheet 6. Press down to lift the hook and free the lever.",)),
        # ---------------- lid (sheets 9, 10) ----------------
        Part("lid", "Lid", 1, pl("3/16") + " 6-1/2 x 13", "green", lid_plate, group="Lid",
             dims=lambda p: _plate_dims(13.0, 6.5, (), p.t_lid), notes=("Sheet 10.",)),
        Part("rail", "Lid Rail", 2, pl("1/4"), "green", lid_rail, group="Lid",
             dims=lambda p: [("H", "F", (0, 0, 0), (11.0, 0, 0), -10), ("V", "F", (11.0, 0, 0), (11.0, 1.0, 0), 10),
                             ("V", "F", (11.0, 0, 0), (9.5, 2.5, 0), 18), ("V", "F", (0, 0, 0), (4.75, 2.8, 0), -10),
                             ("H", "F", (6.0, 2.8, 0), (11.0, 2.8, 0), 18), ("H", "F", (4.75, 2.8, 0), (11.0, 2.8, 0), 26),
                             ("H", "F", (9.5, 2.5, 0), (11.0, 2.5, 0), 10), ("R", "F", (6.0, 2.8, 0), 1.0, 225, "", 12)],
             notes=("Sheet 10. Scoop 0.70 below the 2-1/2 flat; centre 5.0 from the high end, over the mold centre.",
                    "On edge 1-7/8 each side of the lid centre line, low end 1/2 from the hinge edge.")),
        Part("cwarm", "Counterweight Arm", 2, pl("1/8"), "green", cw_arm, group="Lid",
             dims=lambda p: [("H", "F", (0, 0, 0), (9.5, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 2.5, 0), -10),
                             ("H", "F", (0, 0, 0), (2.0, 0, 0), -18), ("V", "F", (9.5, 0, 0), (9.5, 2.25, 0), 10),
                             ("H", "F", (0, 2.5, 0), (*CWA_HOLE, 0), 8), ("V", "F", (0, 0, 0), (*CWA_HOLE, 0), -18),
                             ("D", "F", (*CWA_HOLE, 0), 0.40625, 60, "", 10)],
             notes=("Sheet 10. Block on the lid edge, tip forward. The hinge hole is not dimensioned: 1-1/2 from the "
                    "block's rear end, 15/16 up, puts the pin at the lid's hinge edge as on sheet 9.",)),
        Part("cw", "Counterweight", 2, '3-1/2" round x 1-3/8', "green", counterweight, group="Lid",
             views=("T", "F"), front="-Y", flat=False, dims=lambda p: _rod_dims(3.5, 1.375),
             notes=("Sheet 10. 1/2 hole. 1-3/4 min between the pair.",)),
        Part("cwpin", "Counterweight Pin", 2, '1/2" round x 2', "green", cw_pin, group="Lid",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(0.5, 2.0),
             notes=("Sheet 10. Weld securely all round to the arm tip.",)),
        Part("hpin", "Hinge Pin", 2, '3/8" round x 5/8', "purple", hinge_pin, group="Lid",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(0.375, HINGE_PIN[1]),
             notes=("Sheet 10 gives 1-3/8; cut to 5/8 (see design sheet: longer, it fouls the followers inside "
                    "or the yoke arms outside as the yoke stands up).",)),
        Insert("uinsert", "Upper Insert", 2, '1/2" aluminium, plastic or wood', "yellow", upper_insert, group="Lid",
               views=("T", "F"), front="-Y", flat=False, dims=lambda p: _rod_dims(3.875, 0.5),
               notes=("Sheet 10. Two-faced tape under the lid, 3-1/2 from its ends, over the rod tops.",)),
    ]
    for i, pt in enumerate(ps, 1):
        pt.item = i
    return ps



# ==========================================================
# Hooks for the drawing sheets (cinva_drawings.py --model osrl) and the animation
# ==========================================================

TITLE = "OSRL CEB Press"
CHART_END = 90.0
DWG_PREFIX = "OSRL"
FILE_PREFIX = "OSRL-CEB-Press"
OUT_PREFIX = "osrl-"
REVISIONS = {"A": ("2026-10-03", "Initial issue: clone of OSRL CEB press drawings rev 1.1 (Dec 2011, CC BY-SA 3.0)")}
CURRENT_REV = "A"
ATTACHMENT_GROUPS = ()

DEVIATIONS = [
    "Hinge pin 5/8 long, not 1-3/8: longer, it fouls the followers (inside) or the yoke arms (outside).",
]

POSITION_NOTES = [
    "Positions computed from the linkage; all four and the motions between them were checked for clearance.",
    "Yoke tilt = arm tilt from vertical, + toward the rear channel; lever = lever angle from vertical, + toward the "
    "rear; piston = piston face (lower insert) relative to the mold top.",
]

OPERATION = [
    "Start: lever latched along the yoke, yoke resting on the eject rollers, piston on the bottom, lid open "
    "(it rests on its counterweights against the front channel).",
    "Oil the mold. Fill with loose mix to the top, press it into the corners, strike off level. Close the lid.",
    "Lift the lever (and yoke with it) toward upright: the followers roll up the rail slopes and drop into the "
    "scoops with the piston still on the bottom.",
    "Press the latch handle down to lift the hook. Pull the lever over to horizontal toward the rear channel "
    "(two or three firm pushes). It must reach horizontal, or the block comes out thick.",
    "Raise the lever back to upright (the piston drops away from the block); let the latch drop over the head.",
    "Tilt lever and yoke forward onto the eject rollers. Open the lid. Push the lever down steadily to raise the "
    "block clear; lift it off by its ends.",
    "Let the lever rise: the piston drops back to the bottom for the next fill.",
]

DESIGN_NOTES = [
    "Their drawings rev 1.1 as drawn, except: " + " ".join(DEVIATIONS),
    "First-order hand calculations; build one press and load-test before production.",
    "Allowables: A36 0.66 Fy bending, 0.5 Fu net tension; CRS 1018 Fy 50 ksi; A53 pipe Fy 35 ksi.",
    "Soil model: pressure rises as (e^5x - 1)/(e^5 - 1) over the stroke; lateral wall pressure 0.5 x vertical.",
]


def press_data(p: Params, ps, mass):
    return [
        ("Block (pressed)", f"{p.brick_l:g} x {p.brick_w:g} x {p.brick_h:.2f} in, two 2-3/8 cores, {p.area:.1f} sq in"),
        ("Yoke hole", f"{p.hole_n}: block " + ", ".join(f"{replace(p, hole_n=n).brick_h:.2f}" for n in range(1, 6))
         + " in for holes 1..5"),
        ("Loose fill depth", f"{p.fill:.3f} in, ratio {p.fill / p.brick_h:.2f}; mold top {p.zt:g} in above the ground"),
        ("Working pressure", f"{p.p_work:g} psi = {p.f_work:,.0f} lbf on the piston"),
        ("Design (overfill) load", f"{p.p_design:g} psi = {p.f_design:,.0f} lbf, all parts checked"),
        ("Toggle", f"follower {p.e:g} from the axle; lever {p.psi0:.1f} to 90 deg; piston +{p.rise:.3f} in"),
        ("Peak push on lever", f"{p.peak_hand(150):.0f} / {p.peak_hand(200):.0f} / {p.peak_hand(250):.0f} lbf at "
                               f"150 / 200 / 250 psi ({p.lever_len:g} in lever); their 80 lbf = {p.pressure_for(80):.0f} psi"),
        ("Ejection", f"piston rises {p.fill + p.over:.3f} in; yoke tilts {-ps['fill'].tau:.0f} to {-ps['eject'].tau:.0f} deg "
                     f"forward; about {max_eject_hand(p):.0f} lbf on the lever"),
        ("Weight", f"about {mass:.0f} lb (their 205 lb)"),
    ]


def asm_view_dims(p: Params):
    L, W = p.brick_l, p.brick_w
    return [
        ("F", (0, 0, p.zb), (L, 0, p.zb), -20, True, f"{L:g} MOLD"),
        ("F", (p.xc - 16.375 / 2, 0, 0), (p.xc - 16.375 / 2 - 18.0, 0, 0), -10, True, None),
        ("F", (p.xc + 16.375 / 2, 0, 0), (p.xc + 16.375 / 2, 0, p.zt), 10, False, None),
        ("F", (p.xc + 16.375 / 2, 0, 0), (p.eroll[0], 0, p.eroll[1]), 20, False, None),
        ("L", (0, -W / 2, p.zt), (0, W / 2, p.zt), 20, True, f"{W:g} MOLD"),
    ]


GROUP_OF = {
    **{k: "frame" for k in ("fchan", "rchan", "side", "base", "omount", "hinge", "grod", "rtop", "rbot", "eaxle",
                            "eroll", "outr", "otab")},
    **{k: "lid" for k in ("lid", "rail", "cwarm", "cw", "cwpin", "hpin", "uinsert")},
    **{k: "piston" for k in ("linsert", "ptop", "stiff", "pguide", "pside", "ptube", "ppin", "spacer")},
    **{k: "yoke" for k in ("arm", "hbody", "hside", "pmount")},
    **{k: "handle" for k in ("tbody", "ltoggle", "taxle", "faxle", "follow", "lever", "lpivot")},
    **{k: "claw" for k in ("lbody", "lhook", "lhandle")},
}


def extra_meshes(p: Params):
    return []


def anim_ref(p: Params):
    return Pose("reference", 0.0, 0.0, p.zp_bot, 0.0, 0.0)


def hinge_axis(p: Params):
    return p.hinge


VIEW_TARGET = [2.0, 0.0, 17.0]
VIEW_ISO = [-50.0, -84.0, 58.0]


def anim_meta(p: Params):
    ref = anim_ref(p)
    tf = arm_pt(p, ref.tau, ref.zp, p.A_loc)
    px, pz = LATCH["pivot"]
    return dict(hinge=list(p.hinge), psi_ref=0.0, zp_ref=ref.zp, head=list(p.A_loc),
                claw_pivot=[tf[0] + px, tf[1] + pz], claw_open=LATCH_OPEN, claw_on="handle", title=TITLE,
                view_target=VIEW_TARGET, views=dict(iso=VIEW_ISO), psi_stop=90.0)


def ease(s):
    return s * s * (3 - 2 * s)


def timeline(p: Params):
    """Phases (name, seconds, f(s) -> state) in the viewer's conventions (theta = arm tilt, psi = -lever angle
    from the arms), and the phase roles."""
    ps = poses(p)
    t_f, t_e, t_s = ps["fill"].tau, ps["eject"].tau, p.tau_seat
    lo = ps["fill"].cover
    ptop = lambda zp: zp + p.pin_below_cap
    bb0 = ptop(p.zp_bot)
    brick_bot = p.zt - p.brick_h
    F = p.f_work

    def st(tau, phi, zp, cover, claw, bb, bt, force=0.0):
        return dict(theta=tau, psi=-phi, zp=zp, cover=cover, latch=claw, bb=bb, bt=bt, force=force,
                    theta_show=tau, psi_show=tau + phi)

    def press(psi, bb=None, force=True):
        tau, phi, zp = p.press(psi)
        return st(tau, phi, zp, 0.0, LATCH_OPEN, ptop(zp) if bb is None else bb, p.zt,
                  p._stroke_point(min(psi, 89.95), F)[2] if force else 0.0)

    def stand(t, cover, bb):
        z = p.standup_zp(t)
        return st(t, 0.0, z, cover, 0.0, max(bb, ptop(z)) if bb is None else bb, p.zt)

    phases = [
        ("Fill the mold with loose soil mix", 2.5,
         lambda s: st(t_f, 0.0, p.zp_bot, lo, 0.0, bb0, bb0 + p.fill * ease(s))),
        ("Close the lid (counterweighted)", 1.5,
         lambda s: st(t_f, 0.0, p.zp_bot, lo * (1 - ease(s)), 0.0, bb0, p.zt)),
        ("Stand the yoke up: followers roll up the rails into the scoops", 2.0,
         lambda s: (lambda t: st(t, 0.0, p.standup_zp(t), 0.0, 0.0, ptop(p.standup_zp(t)), p.zt))(t_f + (t_s - t_f) * ease(s))),
        ("Press the latch handle to free the lever", 0.8,
         lambda s: st(t_s, 0.0, p.zp_seat, 0.0, LATCH_OPEN * ease(s), ptop(p.zp_seat), p.zt)),
        ("Pull the lever over to horizontal (pressing)", 4.0,
         lambda s: press(p.psi0 + (90.0 - p.psi0) * ease(s))),
        (f"Pressed: block {p.brick_h:.2f} in", 1.0,
         lambda s: press(90.0, force=False)),
        ("Raise the lever: piston drops away from the block", 1.8,
         lambda s: press(90.0 + (p.psi0 - 90.0) * ease(s), bb=brick_bot, force=False)),
        ("Let the latch drop over the head", 0.8,
         lambda s: st(t_s, 0.0, p.zp_seat, 0.0, LATCH_OPEN * (1 - ease(s)), brick_bot, p.zt)),
        ("Tilt lever and yoke onto the eject rollers", 1.8,
         lambda s: (lambda t: st(t, 0.0, p.standup_zp(t), 0.0, 0.0, brick_bot, p.zt))(t_s + (t_f - t_s) * ease(s))),
        ("Open the lid: it swings onto its counterweights", 1.5,
         lambda s: st(t_f, 0.0, p.zp_bot, lo * ease(s), 0.0, brick_bot, p.zt)),
        ("Push the lever down to eject the block", 3.0,
         lambda s: (lambda t: (lambda zp: st(t, 0.0, zp, lo, 0.0, max(brick_bot, ptop(zp)),
                                             max(brick_bot, ptop(zp)) + p.brick_h))(eject_zp(p, t)))(t_f + (t_e - t_f) * ease(s))),
        ("Lift the block off and stack it", 2.2,
         lambda s: st(t_e, 0.0, p.zp_eject, lo, 0.0, ptop(p.zp_eject), ptop(p.zp_eject) + p.brick_h)),
        ("Let the lever rise: piston drops for the next fill", 1.5,
         lambda s: (lambda t: st(t, 0.0, eject_zp(p, t), lo, 0.0, 0.0, 0.0))(t_e + (t_f - t_e) * ease(s))),
    ]
    return phases, dict(phase_press=4, phase_pressed=5, phase_lift=11)


if __name__ == "__main__":
    main()
