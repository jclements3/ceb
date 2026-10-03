"""
Simple CINVA-Ram press — a faithful scale-up of the permies.com replica to a 14 x 7 x 4 brick.

Source: the builder's part drawings cinva1-7.jpg (permies.com thread 33406), his SketchUp model
and video of the finished press. Every part is his part scaled from his 11.5 x 6 x 3-5/8 brick:
lengths x 14/11.5, widths x 7/6, heights x 6.75/6.125 (his 6-1/8 fill depth to our 6-3/4).

How his press works (and this one):
  * Mold box: two tall side plates (slotted) and two short end plates at the top, standing on feet.
  * Piston: a cap on four webs; the main pin P runs through the webs, the side slots and the
    lower ends of the two yoke arms.
  * Lid: a plate with two V-shaped ramps. The top of each ramp has a half-round scoop right over
    the piston. The lid swings clear on two straps (his 11" bars) pivoting low on the side plates.
  * Yoke: two arms (his 19-5/8" bars) tied at the top by two cross bars (his 8" bars). Pin Q at the
    top of the arms carries the handle head.
  * Handle head (the "L-cam"): pin Q at the corner, the cam pin at the foot of the L, the handle
    socket along the other leg. To press, the cam pin sits in the scoop and the head pivots on it
    like a knee: pulling the handle over swings Q up and over the cam pin, the yoke lifts the piston,
    and the head locks 3 degrees over centre with the handle resting on the lid.
  * Latch: his two notched hook plates on the head drop over the upper cross bar and hold head and
    yoke together while the yoke is tilted.
  * Eject: with the lid swung clear, the latched yoke leans on the two fixed pins on the side
    plates; pushing the handle down levers the piston up.

Fixes to his drawings: side slot width (his 2" slot for a 1" pin; the supplier later changed it
to 1"), slot top kept below the loose soil, fixed-pin height set for the eject stroke, and heavier
stock where a 14 x 7 brick at CINVA pressure needs it
(listed on each part as `flag`).

Units: inches. World: X along the mold (0..L), Y across (centred), Z up, ground at Z = 0 (the top
of the stand the feet bolt to is at Z = base_h). -X end: fixed pins, the yoke tilts this way.
+X end: lid pivots; the handle is pulled toward it.

Usage:
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 cinva_simple.py [--check]
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from functools import cached_property

from build123d import (
    Align, Box, Color, Compound, Cylinder, Edge, Face, Location, Plane, Pos, Rot, Unit, Vector,
    Torus, Wire, export_step, extrude, make_hull,
)

STEEL = 0.2836  # lb / in^3

# Drawing revisions (cinva_drawings.py hooks). Letters in issue order: letter -> (date, change).
REVISIONS = {
    "A": ("2026-10-01", "Initial issue"),
    "B": ("2026-10-03", "ECP: cam pin 1-1/4 -> 1-3/8, side plates 1/2 -> 5/8 (sysml_trade.py). Geometry changed: "
                        "side, fpin, gpin, lid, ramp, xbar, ppin, cheek, campin, bridge, lpin, assembly sheets. "
                        "All sheets: note 3 now 'Material per title block' (was A36 / 1018 on 4140 and AR400 parts)."),
    "C": ("2026-10-03", "Feeder added (items 24-38): funnel on a sliding feed box with a knife-gate floor, rails, "
                        "stop post. Side plates: two 9/16 holes for the rail bracket / stop post. "
                        "All sheets: sheet count 27 -> 42."),
    "D": ("2026-10-03", "Working pressure 200 -> 150 psi and handle 72 -> 74 in, so the peak pull (119 lbf) is "
                        "under the CCOHS 120 lbf limit for pulling down above head height. Sheets: general "
                        "assembly, assembly views, operating positions, design data, handle."),
}
CURRENT_REV = "C"
SHEET_REV = {k: "D" for k in ("assembly", "assembly_views", "positions", "design", "htube")}
ATTACHMENT_GROUPS = ("Feeder",)   # drawings: steel weight split press / feeder       # every sheet; SHEET_REV = {key: letter} would hold any sheet left behind

# his press (inches), from cinva1-7.jpg
HIS = dict(
    brick_l=11.5, brick_w=6.0, fill=6.125,
    side=(12.0, 15.0), slot=(2.0, 10.0), fixed_pin=(1.0, 7.0), bolt=0.5,
    end=(6.0, 6.0), cap=(6.0, 11.5), lid=(6.5, 12.0), web=(7.25, 6.0), web_hole=1.0,
    ramp=dict(length=12.0, ends=(0.25, 1.0), legs=(6.038, 4.810), scoop=0.625, flat=1.0),
    arm=(19.625, 2.0), arm_hole=2.0, crossbar=(8.0, 2.0), strap=(11.0, 2.0),
    latch=(4.147, 1.0), latch_bar=(2.75, 1.0), pin=1.0, latch_pin=0.4375,
)


def his_ramp_peak():
    """Peak height H and leg run a of his V plate: legs 6.038 and 4.810, scoop 1.25 wide + 1.0 flat."""
    r = HIS["ramp"]
    L, (h0, h1), (l0, l1), s = r["length"], r["ends"], r["legs"], r["scoop"]
    lo, hi = 0.0, L
    for _ in range(80):
        a = (lo + hi) / 2
        H0 = h0 + math.sqrt(max(l0 * l0 - a * a, 0))
        b = L - a - 2 * s - r["flat"]
        H1 = h1 + math.sqrt(max(l1 * l1 - b * b, 0))
        if H0 > H1:
            lo = a
        else:
            hi = a
    return H0, a


# ==========================================================
# Parameters
# ==========================================================

@dataclass(frozen=True)
class Params:
    brick_l: float = 14.0
    brick_w: float = 7.0
    brick_h: float = 4.0          # pressed brick thickness
    rise: float = 2.75            # compression stroke -> fill 6.75 (his 2.5 on 6.125)
    eject_over: float = 0.125     # piston top rises this far above the mold top to eject
    base_h: float = 12.0          # the feet bolt to a stand this tall

    # stock (his 1/4 plate and 1" pins, heavier where flagged)
    t_side: float = 0.625         # ECP: side plate margin +7% -> +67%
    t_end: float = 0.50
    t_lid: float = 0.625
    t_ramp: float = 0.75          # AR400
    t_cap: float = 0.50
    t_web: float = 0.375
    t_arm: float = 0.50
    w_arm: float = 3.00           # his 2" bar; 3 wide for the net section at the pin holes
    t_bar: float = 0.375          # cross bars and lid straps
    t_cheek: float = 0.50
    t_latch: float = 0.375
    clear: float = 0.125
    d_pin: float = 1.75           # main pin P
    d_q: float = 1.25             # pin Q (two stubs)
    d_cam: float = 1.375          # cam pin (sits in the scoop); ECP: +6% -> +41%
    d_fpin: float = 1.25          # fixed (eject) pins
    d_gpin: float = 1.00          # lid strap pivots
    d_latch: float = 0.50         # latch pivot (his 7/16)
    handle_len: float = 74.0      # Q -> grip along the handle (rev D: 72 -> 74, 120 lbf at 150 psi)
    handle_od: float = 1.900      # 1-1/2" sch 80 pipe

    # mechanism
    psi0: float = -110.0          # head angle at the start (deg; cam->Q direction from vertical, + toward +X)
    psi_lock: float = 3.0         # over centre
    handle_off: float = 3.5       # handle axis from Q, measured past the cam pin
    theta_eject: float = 80.0     # yoke tilt at the end of the eject stroke (sets the fixed-pin height)

    # loads
    p_work: float = 150.0         # rev D: 200 -> 150 (CCOHS 120 lbf pull-down limit with a 74 in handle)
    p_design: float = 306.0
    soil_k: float = 5.0
    eject_force: float = 1000.0

    @property
    def label(self) -> str:
        f = lambda v: f"{v:g}"
        return f"{f(self.brick_l)}x{f(self.brick_w)}x{f(self.brick_h)}"

    # ---- scale factors from his press ----
    @property
    def sx(self):
        return self.brick_l / HIS["brick_l"]

    @property
    def sy(self):
        return self.brick_w / HIS["brick_w"]

    @property
    def sz(self):
        return self.fill / HIS["fill"]

    # ---- plan ----
    @property
    def xc(self):
        return self.brick_l / 2

    @property
    def wall_y(self):
        return self.brick_w / 2

    @property
    def wall_out(self):
        return self.brick_w / 2 + self.t_side

    @property
    def arm_y(self):           # inner face of the yoke arms
        return self.wall_out + 0.0625

    @property
    def cheek_y(self):         # inner face of the head cheeks (outer face = wall_out)
        return self.wall_out - self.t_cheek

    @property
    def ramp_y(self):          # outer face of the ramps, 1/16 inside the cheeks
        return self.cheek_y - 0.0625

    @property
    def lid_w(self):           # full width at the pull end (over the side plates, straps welded on)
        return 2 * (self.wall_out + 1 / 32)

    @property
    def lid_w_in(self):        # between the side plates elsewhere, so the head clears when it swings down
        return self.brick_w - 1 / 32

    @property
    def web_y(self):
        return self.brick_w / 2 - self.clear / 2

    @property
    def rail_y(self):          # drawing-sheet compatibility
        return self.wall_out

    # ---- heights ----
    @property
    def fill(self):
        return self.brick_h + self.rise

    @property
    def zb(self):              # bottom of the side plates (top of the stand)
        return self.base_h

    @property
    def side_h(self):          # his 15" side plate
        return HIS["side"][1] * self.sz

    @property
    def zt(self):              # mold top = side plate top
        return self.zb + self.side_h

    @property
    def zL(self):              # lid top
        return self.zt + self.t_lid

    @property
    def end_h(self):           # his 6" end plates, long enough to reach the piston at fill
        return max(HIS["end"][1] * self.sz, self.fill + self.t_cap + 0.25)

    @property
    def pin_below_cap(self):   # P to piston top; slot top stays below the loose fill (fix)
        return self.fill + self.eject_over + self.d_pin / 2 + 0.375

    @property
    def web_hole(self):        # his 1" from the web bottom
        return HIS["web_hole"] * self.sz

    @property
    def web_h(self):
        return self.pin_below_cap - self.t_cap + self.web_hole

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
    def slot(self):
        return (self.zp_fill - self.d_pin / 2 - 0.0625, self.zp_eject + self.d_pin / 2 + 0.0625)

    # ---- ramp (his V plate, scaled) and the cam pin ----
    @property
    def scoop_r(self):         # his R0.625 for a 1" pin: pin radius + 1/8
        return self.d_cam / 2 + 0.125

    @cached_property
    def ramp_profile(self):
        """Top edge of the ramp, [(x, h above the lid top)], his V plate scaled; plus the scoop centre."""
        r = HIS["ramp"]
        H, a = his_ramp_peak()
        k = (self.brick_l + 2 * self.t_end) / r["length"]            # his 12" lid -> ours
        x0 = -self.t_end
        h0, h1 = r["ends"][0] * self.sz, r["ends"][1] * self.sz
        Hs = H * self.sz
        xs = self.xc                                                  # scoop centre over the piston
        rs = self.scoop_r
        flat = r["flat"] * k
        x_end = self.brick_l + self.t_end
        pts = [(x0, h0), (xs - rs, Hs)]
        n = 24
        for i in range(1, n):                                         # half-round scoop
            t = math.pi - math.pi * i / n
            pts.append((xs + rs * math.cos(t), Hs - rs * math.sin(t)))
        pts += [(xs + rs, Hs), (xs + rs + flat, Hs), (x_end, h1)]
        return pts, (xs, Hs)

    @property
    def cam_c(self):           # cam pin centre seated in the scoop (x, z)
        _, (xs, Hs) = self.ramp_profile
        return xs, self.zL + Hs - self.scoop_r + self.d_cam / 2

    # ---- linkage: knee about the cam pin ----
    @cached_property
    def _knee(self):
        """(e, Ly): cam arm C->Q and yoke P->Q so that the stroke from psi0 to centre is `rise`."""
        cx, cz = self.cam_c
        zl = self.zp_comp                     # at centre (psi = 0) Q is right above C

        def zp_start(e):
            ly = cz + e - zl
            s, c = math.sin(math.radians(self.psi0)), math.cos(math.radians(self.psi0))
            return cz + e * c - math.sqrt(ly * ly - (e * s) ** 2)
        lo, hi = 0.3, 8.0
        for _ in range(80):
            e = (lo + hi) / 2
            if zp_start(e) > self.zp_fill:
                lo = e
            else:
                hi = e
        return e, cz + e - zl

    @property
    def e(self):
        return self._knee[0]

    @property
    def yoke_len(self):
        return self._knee[1]

    def knee(self, psi):
        """Pressing: (theta, zp, Q) with the cam pin in the scoop and the head at angle psi."""
        cx, cz = self.cam_c
        s, c = math.sin(math.radians(psi)), math.cos(math.radians(psi))
        qx, qz = cx + self.e * s, cz + self.e * c
        dx = qx - self.xc
        zp = qz - math.sqrt(self.yoke_len ** 2 - dx * dx)
        th = math.degrees(math.asin(-dx / self.yoke_len))          # + = tilted toward -X
        return th, zp, (qx, qz)

    def q_z(self, psi):        # drawing/chart compatibility
        return self.knee(psi)[1] + self.yoke_len

    @property
    def theta_start(self):
        return self.knee(self.psi0)[0]

    @property
    def rho0(self):            # head angle relative to the yoke axis when latched (start position)
        return self.psi0 + self.theta_start

    @property
    def zp_lock(self):
        return self.knee(self.psi_lock)[1]

    # names used by the drawing sheets and the animation
    @property
    def psi_stop(self):
        return self.psi_lock

    @property
    def beta0(self):
        return self.psi0

    @property
    def beta_lock(self):
        return self.psi_lock

    # ---- fixed (eject) pins ----
    @property
    def epin_d(self):          # yoke axis to fixed-pin centre when the arm rests on it
        return self.w_arm / 2 + self.d_fpin / 2

    @cached_property
    def epin(self):
        """Fixed pin centre: his 1" from the -X plate edge (scaled); height set so the eject stroke
        ends at theta_eject (close to his 7" x sz)."""
        x = -self.t_end + HIS["fixed_pin"][0] * self.sx
        D = self.xc - x
        th = math.radians(self.theta_eject)
        z = self.zp_eject + (D * math.cos(th) - self.epin_d) / math.sin(th)
        return x, z

    # ---- lid straps ----
    @property
    def strap_len(self):
        return HIS["strap"][0] * self.sz

    @property
    def gpin(self):            # lid pivot: 1" (scaled) in from the +X plate edge, a strap below the lid
        x = self.brick_l + self.t_end - HIS["fixed_pin"][0] * self.sx
        return x, self.zL - self.strap_len + 1.0 * self.sz

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
        z0 = self.zp_fill
        rise = min(self.knee(psi)[1] - z0, self.rise)
        P = F * self.soil(max(rise, 0) / self.rise)
        dz = (self.knee(psi + 0.05)[1] - self.knee(psi - 0.05)[1]) / math.radians(0.1)
        return rise, P, max(P * dz / self.handle_len, 0.0)

    def stroke_table(self, pressure=None, step=5):
        """[(psi deg, piston rise, piston force, hand force)] over the stroke."""
        F = (pressure or self.p_work) * self.area
        angles = [self.psi0] + [a for a in range(-180, 1, step) if a > self.psi0] + [0.0]
        return [(d, *self._stroke_point(d, F)) for d in sorted(set(angles))]

    def peak_hand(self, pressure=None):
        F = (pressure or self.p_work) * self.area
        n = int(-self.psi0 * 4)
        return max(self._stroke_point(self.psi0 + i / 4, F)[2] for i in range(1, n))


def _rot(v, deg):
    """Rotate (x, z) by deg, positive = counter-clockwise seen from -Y (x toward z)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return v[0] * c - v[1] * s, v[0] * s + v[1] * c


# ==========================================================
# Poses
# ==========================================================

@dataclass
class Pose:
    name: str
    theta: float      # yoke tilt from vertical toward -X (deg)
    psi: float        # head angle: cam->Q direction from vertical, + toward +X (deg, world)
    zp: float         # pin P height
    cover: float      # lid opening angle (deg)
    claw: float | None = None      # latch opening (deg); None: shut when latched, else open
    feed: float = 0.0  # feed box: 0 parked .. 1 over the mold (fill pose only)
    gate: float = 0.0  # knife gate: 0 shut .. 1 open


def eject_zp(p: Params, th):
    """Pin P height with the yoke arm resting on the fixed pins at tilt th."""
    fx, fz = p.epin
    D = p.xc - fx
    return fz - (D * math.cos(math.radians(th)) - p.epin_d) / math.sin(math.radians(th))


def solve_theta(p: Params, zp):
    """(err, tilt) at which the arm rests on the fixed pins with P at zp."""
    lo, hi = 1.0, 89.0
    for _ in range(60):
        m = (lo + hi) / 2
        if eject_zp(p, m) < zp:
            lo = m
        else:
            hi = m
    th = (lo + hi) / 2
    return abs(eject_zp(p, th) - zp), th


def zp_for_theta(p: Params, th):
    return eject_zp(p, th)


def latched(p: Params, name, th, zp, cover):
    return Pose(name, th, p.rho0 - th, zp, cover)


def poses(p: Params) -> dict:
    th_f = solve_theta(p, p.zp_fill)[1]
    th0, zp0, _ = p.knee(p.psi0)
    thl, zpl, _ = p.knee(p.psi_lock)
    return {
        "fill": latched(p, "Fill (latched, yoke on the fixed pins, lid swung clear)", th_f, p.zp_fill, p.lid_open),
        "start": Pose("Start of pressing (cam pin in the scoop)", th0, p.psi0, zp0, 0),
        "locked": Pose("Pressed and locked (3 deg over centre, handle on its rest)", thl, p.psi_lock, zpl, 0),
        "eject": latched(p, "Ejected (latched, handle pushed down)", p.theta_eject, p.zp_eject, p.lid_open),
    }


# ==========================================================
# Frames
# ==========================================================

def yoke_frame(p: Params, th, zp):
    """Origin P, local z along the yoke toward Q; tilt th toward -X."""
    return Pos(p.xc, 0, zp) * Rot(0, -th, 0)


def q_world(p: Params, th, zp):
    t = math.radians(th)
    return p.xc - p.yoke_len * math.sin(t), zp + p.yoke_len * math.cos(t)


def head_frame(p: Params, th, psi, zp):
    """Origin Q, local +z = cam->Q direction (world angle psi from vertical toward +X);
    local +x along the handle; cam pin at (0, 0, -e); handle axis at local z = -handle_off."""
    qx, qz = q_world(p, th, zp)
    return Pos(qx, 0, qz) * Rot(0, psi, 0)


def head_point(p: Params, th, psi, zp, local):
    """World (x, z) of head-local (x, z)."""
    qx, qz = q_world(p, th, zp)
    x, z = local
    c, s = math.cos(math.radians(psi)), math.sin(math.radians(psi))
    return qx + x * c + z * s, qz - x * s + z * c


def yoke_point(p: Params, th, zp, local):
    """World (x, z) of yoke-local (x, z) (origin P)."""
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    x, z = local
    return p.xc + x * c - z * s, zp + x * s + z * c


def lid_frame(p: Params, ang):
    gx, gz = p.gpin
    return Pos(gx, 0, gz) * Rot(0, ang, 0) * Pos(-gx, 0, -gz)


# ==========================================================
# Head, yoke-top and latch geometry
# ==========================================================

Q_BOSS = 1.25
CAM_BOSS = 1.25
LEG_HALF = 1.25          # half width of the handle leg of the L
LEG_LEN = 10.5           # handle leg length from Q along the handle (past the lid end at the lock)
BRIDGE_X = (8.0, 9.75)   # bridges (handle socket) along the handle from Q, clear of the ramps
BRIDGE_W = 2.0


def cheek_outline(p: Params):
    """(circles, rects) in head-local (x along the handle, z toward Q) for the L-shaped cheek."""
    a = p.handle_off
    return ([(0.0, 0.0, Q_BOSS), (0.0, -p.e, CAM_BOSS)],
            [(-LEG_HALF, -a - LEG_HALF, LEG_LEN, -a + LEG_HALF)])


LATCH_BOSS = 0.6


def cheek_lobe(p: Params):
    """Lobe on the handle leg carrying the latch pivot."""
    (lx, lz), _, _ = latch_geom(p)
    a = p.handle_off
    return [(lx, lz, LATCH_BOSS)], [(lx - LATCH_BOSS, -a, lx + LATCH_BOSS, lz)]


def _cheek_edge_z(p: Params, x_y):
    """Upper tangent of the Q/cam bosses (the part of the cheek that meets the cross bar) in yoke
    coordinates at the latched angle: returns z at yoke-local x (origin Q)."""
    r = p.rho0
    # cam boss centre relative to Q in yoke coordinates (x across, z along the yoke)
    cx, cz = -p.e * math.sin(math.radians(r)), -p.e * math.cos(math.radians(r))
    L = math.hypot(cx, cz)
    nx, nz = -cz / L, cx / L                     # left normal of Q->C
    if nz < 0:
        nx, nz = -nx, -nz
    ax, az = nx * Q_BOSS, nz * Q_BOSS             # tangent line through Q + n R
    t = (x_y - ax) / cx
    return az + t * cz


def crossbars(p: Params):
    """Cross bars (his 8" bars) between the arm tops, on edge, yoke-local (origin Q):
    [(x0, x1, z0, z1)]. The +X bar's lower corner is where the head rests at the start angle."""
    h = HIS["crossbar"][1] * p.sz
    x1 = XBAR_X1
    zb = _cheek_edge_z(p, x1) + 0.02
    return [(x1 - p.t_bar, x1, zb, zb + h), (-x1, -x1 + p.t_bar, zb, zb + h)]


XBAR_X1 = 0.875          # +X face of the pull-end cross bar from the yoke axis (inside the 3" arm)


def arm_top(p: Params):
    return crossbars(p)[0][3]


LATCH_K = HIS["latch"][0] - 0.397 - (HIS["latch"][0] - 2.929 - 0.625) - 0.3125   # his pivot -> notch


LATCH_ZL = -1.3          # latch pivot: head-local z (just above the handle tube, on a lobe of the cheek)


def latch_geom(p: Params):
    """Latch pivot L (head-local) and hook notch N (yoke-local, origin Q) at the latched angle.
    The notch drops over the top of the +X cross bar; the pivot sits on a lobe of the cheek so the
    hook hangs almost straight down onto the bar (gravity keeps it shut)."""
    x0, x1, z0, z1 = crossbars(p)[0]
    k = LATCH_K * p.sz
    nx, nz = (x0 + x1) / 2, z1
    r = math.radians(p.rho0)

    def to_yoke(hx, hz):          # head-local -> yoke-local (origin Q)
        return hx * math.cos(r) + hz * math.sin(r), -hx * math.sin(r) + hz * math.cos(r)
    lo, hi = 0.0, LEG_LEN + 3
    for _ in range(60):
        m = (lo + hi) / 2
        lx, lz = to_yoke(m, LATCH_ZL)
        if math.hypot(lx - nx, lz - nz) < k:
            lo = m
        else:
            hi = m
    return (lo, LATCH_ZL), (nx, nz), k


def handle_rest(p: Params):
    """Rest blocks on the lid edges under the cheeks' handle legs (x0, x1, height): the legs land on
    them at psi_lock."""
    th, zp, _ = p.knee(p.psi_lock)
    a = p.handle_off
    x0, x1 = p.brick_l + p.t_end - 2.5, p.brick_l + p.t_end - 0.5
    zs = []
    for x_along in [i * 0.1 for i in range(0, int(LEG_LEN * 10) + 1)]:
        wx, wz = head_point(p, th, p.psi_lock, zp, (x_along, -a - LEG_HALF))
        if x0 <= wx <= x1:
            zs.append(wz)
    return x0, x1, min(zs) - p.zL


def rest_y(p: Params):
    """Rest blocks sit under the cheeks, on the lid edge: cheek inner face to outer face."""
    return p.cheek_y, p.wall_out


# ==========================================================
# Feeder: funnel on a sliding feed box with a knife-gate floor (rev C)
# ==========================================================
# Everything moving above the mold stays within |y| <= 5.31 (pin Q stubs) over the whole cycle, the lid
# swings over the +X end and the yoke leans over the -X end, so the feeder parks on the +Y side and slides
# across in Y at fill only. Nothing fixed can bridge y 4.125..5.875 (yoke arms, Q stubs, lid straps sweep
# it), so the box has a knife-gate floor: closed while it crosses that gap, pulled open over the mold,
# pushed back in to shear the charge off at the mold top. The head cheek tips sit 0.9 to 2.7 above the
# mold top at x <= 1.39 at fill, so the box's -X end is a low lip and a 45 deg chute (steeper than the
# soil's angle of repose, so the end of the mold still fills). The funnel flares toward the operator only.
# Feeder frame: x as the press, y from the box centre, z from the mold top.

FB_T = 0.1345           # 10 ga sheet: box and funnel walls
FB_TG = 0.1875          # knife gate, 3/16 plate
FB_RELIEF = FB_TG + 1 / 32   # bottom of the end walls, funnel wall and tails: the gate runs under them
FB_LIP = 0.75           # -X lip height (under the head cheek tips)
FB_X1 = 1.75            # outer face of the -X wall's upright part
FB_H1 = 7.0             # upright box height
FB_H = 15.0             # funnel top
FB_FLARE = 30.0         # funnel flare toward +Y, deg from vertical
FB_TAIL = 4.25          # tails past the funnel wall, kept between the rails at full stroke
FB_TAIL_H = 1.5         # +X tail height (the -X tail is the lip)
GATE_EXT = 0.5          # gate past the funnel wall (handle)
GATE_STRIP = 0.1875     # stop strip on the gate's leading edge
LUG_X = (9.5, 11.0)     # stop lug on the strike wall
LUG_Z = (0.25, 0.75)
POST_X = (9.25, 11.25)  # side plate face the arms (x <= 8.62) and lid straps (x >= 11.83) never reach
POST_RELIEF = 0.25      # stop face this far outside the side plate: the head cheeks pass it with 1/4
FEED_Y0 = 5.875         # rails start: 0.56 past the Q stubs
FEED_STOP = 18.0        # park stop face (far tie)
RAIL_A, RAIL_T = 1.5, 0.1875   # 1-1/2 x 1-1/2 x 3/16 angle: rails, ties, legs
BRK_A, BRK_T, BRK_L = 3.0, 0.375, 2.0
BOLT_Z = 2.25           # bracket / post bolts, below the mold top
SOIL = 0.049            # lb / in^3, loose moist soil mix


def _fb_k():
    return math.tan(math.radians(FB_FLARE))


def _fb_c():
    """z - x along the inside of the 45 deg chute."""
    return FB_LIP + FB_T - FB_T * math.sqrt(2)


def fb_inner_x(z):
    """Inside of the -X end at height z (feeder frame)."""
    return max(0.0, min(z - _fb_c(), FB_X1 + FB_T))


def feed_park(p: Params):
    """Box centre y when parked against the far tie."""
    return FEED_STOP - (p.brick_w / 2 + FB_T + FB_TAIL)


def gate_travel(p: Params):
    return p.brick_w - GATE_STRIP


def feed_rail_x(p: Params):
    """Heels of the two rails (outside the box walls with 1/16 clearance)."""
    x0 = -FB_T - 1 / 16 - RAIL_T
    return x0, p.brick_l - x0


def _upright(pts_xz, y0, y1):
    """Polygon in (x, z) extruded over y0..y1."""
    return Pos(0, y1, 0) * UPRIGHT * poly(pts_xz, y1 - y0)


def _edge(pts_yz, x0, x1):
    """Polygon in (y, z) extruded over x0..x1."""
    return Pos(x0, 0, 0) * EDGE * poly(pts_yz, x1 - x0)


def fb_pin_end(p: Params):
    """-X end: lip, 45 deg chute, upright; flares with the funnel above FB_H1; lip runs on as a tail."""
    W2, k = p.brick_w / 2, _fb_k()
    c = _fb_c()
    zi0, zi1 = c, FB_X1 + FB_T + c
    xz = [(-FB_T, FB_RELIEF), (-FB_T, FB_LIP), (FB_X1, FB_LIP + FB_X1 + FB_T), (FB_X1, FB_H),
          (FB_X1 + FB_T, FB_H), (FB_X1 + FB_T, zi1), (0, zi0), (0, FB_RELIEF)]
    s = _upright(xz, -W2, W2 + FB_T)
    yo = FB_T / math.cos(math.radians(FB_FLARE))
    s += _edge([(W2 + FB_T, FB_H1), (W2 + yo, FB_H1), (W2 + (FB_H - FB_H1) * k + yo, FB_H), (W2 + FB_T, FB_H)],
               FB_X1, FB_X1 + FB_T)
    s += Pos(-FB_T, W2 + FB_T, FB_RELIEF) * Box(FB_T, FB_TAIL, FB_LIP - FB_RELIEF, align=Align.MIN)
    return s


def fb_lid_end(p: Params):
    """+X end, flat (profile y, z): runs on as a tail between the rails."""
    W2, k = p.brick_w / 2, _fb_k()
    yo = FB_T / math.cos(math.radians(FB_FLARE))
    return poly([(-W2, FB_RELIEF), (W2 + FB_T + FB_TAIL, FB_RELIEF), (W2 + FB_T + FB_TAIL, FB_TAIL_H),
                 (W2 + FB_T, FB_TAIL_H), (W2 + yo, FB_H1), (W2 + (FB_H - FB_H1) * k + yo, FB_H), (-W2, FB_H)], FB_T)


def fb_strike(p: Params):
    """-Y wall, flat (profile x, z): its bottom edge strikes the mold top; -X end follows the chute."""
    L = p.brick_l
    return poly([(-FB_T, 0), (L + FB_T, 0), (L + FB_T, FB_H), (FB_X1, FB_H), (FB_X1, FB_LIP + FB_X1 + FB_T),
                 (-FB_T, FB_LIP)], FB_T)


def fb_funnel(p: Params):
    """+Y wall: upright with the gate passing under it, then flared toward the operator."""
    L, W2, k = p.brick_l, p.brick_w / 2, _fb_k()
    c = _fb_c()
    s = _upright([(0, FB_RELIEF), (L, FB_RELIEF), (L, FB_H1), (FB_X1 + FB_T, FB_H1),
                  (FB_X1 + FB_T, FB_X1 + FB_T + c), (0, c)], W2, W2 + FB_T)
    yo = FB_T / math.cos(math.radians(FB_FLARE))
    s += _edge([(W2, FB_H1), (W2 + (FB_H - FB_H1) * k, FB_H), (W2 + (FB_H - FB_H1) * k + yo, FB_H), (W2 + yo, FB_H1)],
               FB_X1 + FB_T, L)
    return s


def knife_gate(p: Params):
    """Gate plate with the stop strip across its leading edge (feeder frame, closed)."""
    L, W2 = p.brick_l, p.brick_w / 2
    g = Pos(-FB_T, -W2, 0) * Box(L + 2 * FB_T, p.brick_w + FB_T + GATE_EXT, FB_TG, align=Align.MIN)
    g += Pos(1 / 16, -W2, FB_TG) * Box(L - 1 / 8, GATE_STRIP, GATE_STRIP, align=Align.MIN)
    return g


def gate_handle(p: Params):
    """U of 1/2 round on the gate's tail; its legs bear on the funnel wall when the gate is shut."""
    L, W2 = p.brick_l, p.brick_w / 2
    yc = W2 + FB_T + 0.25
    s = Pos(L / 2 - 2, yc, FB_TG + 4) * rod(0.5, 4.0, "X")
    for x in (L / 2 - 2, L / 2 + 2):
        s += Pos(x, yc, FB_TG) * rod(0.5, 4.0, "Z")
    return s


def box_handle(p: Params):
    """U of 1/2 round standing off the funnel's flared face, 11 in above the mold top."""
    L, W2, k = p.brick_l, p.brick_w / 2, _fb_k()
    z = 11.0
    y0 = W2 + (z - FB_H1) * k + FB_T / math.cos(math.radians(FB_FLARE)) - 0.25
    s = Pos(L / 2 - 3, y0 + 3.25, z) * rod(0.5, 6.0, "X")
    for x in (L / 2 - 3, L / 2 + 3):
        s += Pos(x, y0, z) * rod(0.5, 3.25, "Y")
    return s


def post_face(p: Params):
    return p.wall_out + POST_RELIEF


POST_T = 0.5            # 1/2 x 2 flat bar


def lug_len(p: Params):
    return post_face(p) - (p.brick_w / 2 + FB_T)


def stop_lug(p: Params):
    return plate(LUG_X[1] - LUG_X[0], lug_len(p), LUG_Z[1] - LUG_Z[0])


def feed_rail(p: Params):
    return angle_iron(RAIL_A, RAIL_T, FEED_STOP - FEED_Y0)


def tie_len(p: Params):
    x0, x1 = feed_rail_x(p)
    return x1 - x0


def near_tie(p: Params):
    return angle_iron(RAIL_A, RAIL_T, tie_len(p))


def far_tie(p: Params):
    return angle_iron(RAIL_A, RAIL_T, tie_len(p))


def leg_len(p: Params):
    return p.zt - 2 * RAIL_T


def feed_leg(p: Params):
    return angle_iron(RAIL_A, RAIL_T, leg_len(p))


def leg_tie_len(p: Params):
    x0, x1 = feed_rail_x(p)
    return (x1 - RAIL_T) - (x0 + RAIL_T)


def leg_tie(p: Params):
    return angle_iron(RAIL_A, RAIL_T, leg_tie_len(p))


def rail_bracket(p: Params):
    """3 x 3 x 3/8 angle, 2 long; two 9/16 holes in the leg bolted to the +Y side plate."""
    s = angle_iron(BRK_A, BRK_T, BRK_L)
    zh = BOLT_Z - 2 * RAIL_T
    for x in (0.5, 1.5):
        s -= Pos(x, -0.01, zh) * Rot(-90, 0, 0) * Cylinder(0.5625 / 2, BRK_T + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


POST_ZLO = 3.375        # post bottom below the mold top
POST_STEP = 0.5         # the stop face starts this far below the mold top


def stop_post(p: Params):
    """1/2 x 2 flat bar bolted to the -Y side plate, milled back POST_RELIEF above the step so the head
    cheeks pass it; the box's lug lands on that face."""
    w = POST_X[1] - POST_X[0]
    h0 = POST_ZLO - POST_STEP
    s = Box(w, POST_T, h0, align=Align.MIN) + Pos(0, 0, h0) * Box(w, POST_T - POST_RELIEF, POST_STEP + 1.0, align=Align.MIN)
    for x in (0.5, 1.5):
        s -= Pos(x, -0.01, POST_ZLO - BOLT_Z) * Rot(-90, 0, 0) * Cylinder(0.5625 / 2, 0.52, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def _angle_dims(n, a=RAIL_A):
    return [("H", "F", (0, 0, 0), (n, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 0, a), -8)]


def feeder_parts(p: Params):
    L, W2, k = p.brick_l, p.brick_w / 2, _fb_k()
    yo = FB_T / math.cos(math.radians(FB_FLARE))
    ytop = W2 + (FB_H - FB_H1) * k + yo
    ang = f'{RAIL_A:g} x {RAIL_A:g} x 3/16 angle'
    gyc = W2 + FB_T + 0.25
    bz = 11.0
    by0 = W2 + (bz - FB_H1) * k + yo - 0.25
    tl = feed_rail(p).bounding_box().size.X
    return [
        Part("fbpin", "Feed Box End (pin end)", 1, "10 ga sheet A36, bent", "yellow", fb_pin_end, group="Feeder",
             views=("F", "T", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (-FB_T, 0, FB_RELIEF), (FB_X1 + FB_T, 0, FB_RELIEF), -10),
                             ("V", "F", (-FB_T, 0, FB_RELIEF), (-FB_T, 0, FB_LIP), -10),
                             ("V", "F", (FB_X1 + FB_T, 0, FB_RELIEF), (FB_X1 + FB_T, 0, FB_H), 10)],
             notes=(f"Lip top {FB_LIP:g} above the gate's underside ({FB_LIP - FB_RELIEF:.3f} above this part's "
                    f"bottom edge), then 45 deg to the upright at {FB_X1:g} (outside). The head cheek tips pass over "
                    "this end at fill: do not raise the lip or flatten the chute.",
                    f"The lip runs on {FB_TAIL:g} past the funnel wall as a tail between the rails.",
                    "The upright part widens with the funnel flare above the box height.")),
        Part("fblid", "Feed Box End (lid end)", 1, "10 ga sheet A36", "yellow", fb_lid_end, group="Feeder",
             front="Z",
             dims=lambda p: [("H", "F", (-W2, FB_RELIEF, 0), (W2 + FB_T + FB_TAIL, FB_RELIEF, 0), -10),
                             ("V", "F", (-W2, FB_RELIEF, 0), (-W2, FB_H, 0), -10),
                             ("V", "F", (W2 + FB_T + FB_TAIL, FB_RELIEF, 0), (W2 + FB_T + FB_TAIL, FB_TAIL_H, 0), 10),
                             ("H", "F", (-W2, FB_H, 0), (ytop, FB_H, 0), 8)],
             notes=(f"Bottom edge sits {FB_RELIEF:.3f} above the gate's underside: the gate runs under it.",
                    f"The tail ({FB_TAIL:g} x {FB_TAIL_H:g}) stays between the rails at full stroke.")),
        Part("fbstrike", "Strike Wall", 1, "10 ga sheet A36", "yellow", fb_strike, group="Feeder", front="Z",
             dims=lambda p: [("H", "F", (-FB_T, 0, 0), (L + FB_T, 0, 0), -10),
                             ("V", "F", (L + FB_T, 0, 0), (L + FB_T, FB_H, 0), 10),
                             ("V", "F", (-FB_T, 0, 0), (-FB_T, FB_LIP, 0), -10),
                             ("H", "F", (-FB_T, FB_H, 0), (FB_X1, FB_H, 0), 8)],
             notes=("Bottom edge straight and square: it strikes the mold top when the box is pulled back.",
                    "Covers the ends of both end walls; weld outside only.")),
        Part("fbfunnel", "Funnel Wall", 1, "10 ga sheet A36, bent", "yellow", fb_funnel, group="Feeder",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, FB_RELIEF), (L, 0, FB_RELIEF), -10),
                             ("V", "F", (L, 0, FB_RELIEF), (L, 0, FB_H1), 10),
                             ("V", "F", (L, 0, FB_H1), (L, 0, FB_H), 18)],
             notes=(f"Upright to {FB_H1:g}, then bent {FB_FLARE:g} deg out toward the operator to {FB_H:g}.",
                    f"Bottom edge {FB_RELIEF:.3f} up: the gate passes under it.")),
        Part("gate", "Knife Gate", 1, "3/16 plate A36", "orange", knife_gate, group="Feeder",
             front="Z", flat=False,
             dims=lambda p: [("H", "F", (-FB_T, -W2, 0), (L + FB_T, -W2, 0), -10),
                             ("V", "F", (L + FB_T, -W2, 0), (L + FB_T, W2 + FB_T + GATE_EXT, 0), 10)],
             notes=("Bevel the leading edge on top, 30 deg, so the soil rides up over it when it is pushed shut.",
                    f"Stop strip across the leading edge, {GATE_STRIP:g} square: it stops the gate open at "
                    f"{gate_travel(p):.3f} travel.")),
        Part("ghandle", "Gate Handle", 1, '0.500" round 1018, bent', "orange", gate_handle, group="Feeder",
             front="-Y", flat=False,
             dims=lambda p: [("H", "F", (L / 2 - 2, gyc, FB_TG), (L / 2 + 2, gyc, FB_TG), -10),
                             ("V", "F", (L / 2 + 2, gyc, FB_TG), (L / 2 + 2, gyc, FB_TG + 4), 10)],
             notes=("Weld to the gate's tail. The legs bear on the funnel wall with the gate shut.",
                    "Push the box over the mold by this handle (the gate pushes the strike wall).")),
        Part("bhandle", "Box Handle", 1, '0.500" round 1018, bent', "yellow", box_handle, group="Feeder",
             front="Z", flat=False,
             dims=lambda p: [("H", "F", (L / 2 - 3, by0, bz), (L / 2 + 3, by0, bz), -10),
                             ("V", "F", (L / 2 + 3, by0, bz), (L / 2 + 3, by0 + 3.25, bz), 10)],
             notes=(f"Weld to the funnel's flared face, {bz:g} above the box bottom. Pull the box back by it, and hold "
                    "the box with it while you pull the gate open.",)),
        Part("lug", "Stop Lug", 1, "1/2 flat bar A36", "yellow", stop_lug, group="Feeder", front="Z",
             dims=lambda p: _plate_dims(LUG_X[1] - LUG_X[0], lug_len(p), (), LUG_Z[1] - LUG_Z[0]),
             notes=("Weld to the strike wall outside, its lower edge 1/4 above the wall's bottom edge.",
                    "Lands on the stop post: the box is then square over the mold.")),
        Part("rail", "Feed Rail", 2, ang, "green", feed_rail, group="Feeder", front="-Y", flat=False,
             views=("F", "L"), dims=lambda p: _angle_dims(tl),
             notes=("Top of the flat leg level with the mold top; upright leg outside, guiding the box tails.",
                    "Weld to the near tie and against the far tie's upright leg.")),
        Part("ntie", "Near Tie", 1, ang, "green", near_tie, group="Feeder", front="-Y", flat=False,
             views=("F", "L"), dims=lambda p: _angle_dims(tie_len(p)),
             notes=("Under both rails at their near end; bolt to the rail bracket.",)),
        Part("ftie", "Far Tie (park stop)", 1, ang, "green", far_tie, group="Feeder", front="-Y", flat=False,
             views=("F", "L"), dims=lambda p: _angle_dims(tie_len(p)),
             notes=("Upright leg up: the box tails stop against it in the park position.",)),
        Part("leg", "Feed Frame Leg", 2, ang, "green", feed_leg, group="Feeder", front="-Y", flat=False,
             views=("F", "L"), dims=lambda p: _angle_dims(leg_len(p)),
             notes=("To the ground beside the stand; lag or stake the foot. Cut to suit an uneven floor.",)),
        Part("ltie", "Leg Tie", 1, ang, "green", leg_tie, group="Feeder", front="-Y", flat=False,
             views=("F", "L"), dims=lambda p: _angle_dims(leg_tie_len(p)),
             notes=("Between the legs, 8 above the ground.",)),
        Part("bracket", "Rail Bracket", 1, f'{BRK_A:g} x {BRK_A:g} x 3/8 angle', "green", rail_bracket, group="Feeder",
             front="-Y", flat=False, views=("F", "L"),
             dims=lambda p: [("H", "F", (0, 0, 0), (BRK_L, 0, 0), -10), ("V", "F", (0, 0, 0), (0, 0, BRK_A), -10),
                             ("H", "F", (0, 0, BOLT_Z - 2 * RAIL_T), (0.5, 0, BOLT_Z - 2 * RAIL_T), 8),
                             ("D", "F", (0.5, 0, BOLT_Z - 2 * RAIL_T), 0.5625, 45, "2x ")],
             notes=("Bolt to the +Y side plate (two 1/2 bolts); the near tie bolts on its flat leg.",
                    "This 2 in of the side plate is the only part the yoke arms and lid straps never sweep.")),
        Part("spost", "Stop Post", 1, "1/2 x 2 flat bar A36", "green", stop_post, group="Feeder", front="-Y",
             flat=False, views=("F", "L"),
             dims=lambda p: [("H", "F", (0, 0, 0), (POST_X[1] - POST_X[0], 0, 0), -10),
                             ("V", "F", (POST_X[1] - POST_X[0], 0, 0), (POST_X[1] - POST_X[0], 0, POST_ZLO + 1.0), 10),
                             ("V", "F", (0, 0, POST_ZLO - POST_STEP), (0, 0, POST_ZLO + 1.0), -10),
                             ("D", "F", (0.5, 0, POST_ZLO - BOLT_Z), 0.5625, 45, "2x ")],
             notes=(f"Bolt to the -Y side plate through the same two holes as the bracket on the other plate.",
                    f"Mill the top {POST_STEP + 1.0:g} back {POST_RELIEF:g}: the head cheeks pass it there.")),
    ]


def feed_capacity(p: Params, n=400):
    """Soil the box and funnel hold above the gate (in^3)."""
    L, W, k = p.brick_l, p.brick_w, _fb_k()
    v, dz = 0.0, (FB_H1 - FB_TG) / n
    for i in range(n):
        z = FB_TG + (i + 0.5) * dz
        v += (L - fb_inner_x(z)) * W * dz
    dz = (FB_H - FB_H1) / n
    for i in range(n):
        z = FB_H1 + (i + 0.5) * dz
        v += (L - FB_X1 - FB_T) * (W + (z - FB_H1) * k) * dz
    return v


def charge_volume(p: Params):
    """One loose charge: the mold at fill."""
    return p.brick_l * p.brick_w * p.fill


def add_feeder(p: Params, ps, add):
    """Place the feeder: fixed frame plus the box at ps.feed (0 parked .. 1 over the mold), gate at ps.gate."""
    zt, L, W2 = p.zt, p.brick_l, p.brick_w / 2
    f = getattr(ps, "feed", 0.0)
    g = getattr(ps, "gate", 0.0)
    yc = feed_park(p) * (1 - f)
    fr = Pos(0, yc, zt)
    add("fbpin", "Feed Box End (pin end)", fr * fb_pin_end(p))
    add("fblid", "Feed Box End (lid end)", fr * Pos(L, 0, 0) * EDGE * fb_lid_end(p))
    add("fbstrike", "Strike Wall", fr * Pos(0, -W2, 0) * UPRIGHT * fb_strike(p))
    add("fbfunnel", "Funnel Wall", fr * fb_funnel(p))
    add("lug", "Stop Lug", fr * Pos(LUG_X[0], -post_face(p), LUG_Z[0]) * stop_lug(p))
    add("bhandle", "Box Handle", fr * box_handle(p))
    gt = fr * Pos(0, g * gate_travel(p), 0)
    add("gate", "Knife Gate", gt * knife_gate(p))
    add("ghandle", "Gate Handle", gt * gate_handle(p))
    # fixed frame
    x0, x1 = feed_rail_x(p)
    ztop = zt - RAIL_T
    add("rail", "Feed Rail", Pos(x0, FEED_STOP, ztop) * Rot(0, 0, -90) * feed_rail(p))
    add("rail", "Feed Rail", Pos(x1, FEED_Y0, ztop) * Rot(0, 0, 90) * feed_rail(p))
    add("ntie", "Near Tie", Pos(x0, FEED_Y0 + 0.0625 + RAIL_A, ztop) * Rot(180, 0, 0) * near_tie(p))
    add("ftie", "Far Tie (park stop)", Pos(x1, FEED_STOP + RAIL_T, ztop - RAIL_T) * Rot(0, 0, 180) * far_tie(p))
    ly = FEED_STOP + RAIL_T - RAIL_A
    leg = Pos(x0, ly, ztop - RAIL_T) * Rot(0, 90, 0) * feed_leg(p)
    add("leg", "Feed Frame Leg", leg)
    add("leg", "Feed Frame Leg", leg.mirror(Plane.YZ.offset(L / 2)))
    add("ltie", "Leg Tie", Pos(x0 + RAIL_T, ly + RAIL_T, 8.0) * leg_tie(p))
    add("bracket", "Rail Bracket", Pos(POST_X[1], p.wall_out, ztop - RAIL_T) * Rot(0, 180, 0) * rail_bracket(p))
    add("spost", "Stop Post", Pos(POST_X[0], -p.wall_out - POST_T, zt - POST_ZLO) * stop_post(p))


# ==========================================================
# Ramp contact while standing the yoke up (lid closed)
# ==========================================================

def _ramp_poly(p: Params):
    pts, _ = p.ramp_profile
    return pts


def ramp_h(p: Params, x):
    """Ramp top height above the lid at x (None beyond the ramp)."""
    pts = _ramp_poly(p)
    best = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        lo, hi = min(x0, x1), max(x0, x1)
        if hi - lo > 1e-9 and lo - 1e-9 <= x <= hi + 1e-9:
            v = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            best = v if best is None else max(best, v)
    return best


def cam_clear_z(p: Params, x, n=81):
    """Lowest cam-pin centre height at x that clears the ramp top (and the lid)."""
    r = p.d_cam / 2
    best = p.zL + r
    for i in range(n):
        s = x - r + 2 * r * i / (n - 1)
        h = ramp_h(p, s)
        if h is not None:
            best = max(best, p.zL + h + math.sqrt(max(r * r - (s - x) ** 2, 0)))
    return best


def standup_zp(p: Params, th):
    """P height while the latched yoke is stood up / tilted back with the lid closed: the piston sits
    on the slot bottom unless the cam pin rides on the ramp."""
    cx, cz = head_point(p, th, p.rho0 - th, 0.0, (0.0, -p.e))      # zp = 0 reference
    return max(p.zp_fill, cam_clear_z(p, cx) - cz)


STAND_OUT = 12.0         # the stand (bench) reaches this far past the pull end; the open lid lies on it


def _lid_points(p: Params):
    """Outline points of lid + ramps + straps in the XZ plane (closed position)."""
    pts = [(-p.t_end, p.zt), (p.brick_l + p.t_end, p.zt)]
    pts += [(x, p.zL + h) for x, h in _ramp_poly(p)]
    gx, gz = p.gpin
    pts += [(gx - 1.1, gz - 1.1), (gx + 1.1, gz - 1.1)]
    tip = -p.t_end - HS_LEG - HS_R - HS_ROD / 2                   # horseshoe handle
    pts += [(tip, p.zt + p.t_lid / 2 + d) for d in (-HS_ROD / 2, HS_ROD / 2)]
    return pts


def _lid_open_angle(p: Params):
    """The lid swings over toward +X until it rests on the stand top or the ground."""
    gx, gz = p.gpin
    pts = _lid_points(p)
    x_stand = p.brick_l + p.t_end + STAND_OUT
    a = 0.0
    while a < 200:
        a += 0.25
        for x, z in pts:
            dx, dz = _rot((x - gx, z - gz), -a)
            wx, wz = gx + dx, gz + dz
            floor = p.base_h if wx <= x_stand else 0.0
            if wz <= floor:
                return a - 0.25
    return a


Params.lid_open = cached_property(_lid_open_angle)
Params.lid_open.__set_name__(Params, "lid_open")


# ==========================================================
# Part builders (local coordinates: profile in XY, thickness +Z)
# ==========================================================

def plate(w, h, t):
    return Box(w, h, t, align=Align.MIN)


def hole(x, y, d, t):
    return Pos(x, y, -0.01) * Cylinder(d / 2, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))


def poly(pts, t):
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:                       # clockwise outline: its face would extrude toward -Z
        pts = pts[::-1]
    return extrude(Face(Wire.make_polygon([Vector(*q) for q in pts], close=True)), t)


def rod(d, length, axis="X"):
    c = Cylinder(d / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return {"X": Rot(0, 90, 0), "Y": Rot(-90, 0, 0), "Z": Location()}[axis] * c


def tube(od, idia, length, axis="X"):
    return rod(od, length, axis) - Pos(*(v * -0.01 for v in {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis])) * rod(idia, length + 0.02, axis)


def angle_iron(a, t, length):
    """a x a x t angle along X; legs along +Y and +Z from the heel at the origin."""
    return Box(length, a, t, align=Align.MIN) + Box(length, t, a, align=Align.MIN)


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




# ---- frame ----
LOC_D = 0.25


def foot_x(p: Params):
    """World x of the foot clips' -X ends: his corners at the fixed-pin end; at the pull end moved in
    so the lid straps swing past."""
    return [-p.t_end, p.brick_l + p.t_end - FOOT[2] - 3.0]


def bolt_holes(p: Params):
    """His 1/2" bolt holes near the bottom of the side plates (local plate coords), one per clip."""
    ex, ez = HIS["bolt"] * p.sx, HIS["bolt"] * p.sz
    return [(x + p.t_end + ex, ez) for x in foot_x(p)]


def side_plate(p: Params):
    """Local x = world X + t_end, local y = world Z - zb."""
    te, zb = p.t_end, p.zb
    w = p.brick_l + 2 * te
    s = plate(w, p.side_h, p.t_side)
    s0, s1 = p.slot
    s -= obround_slot(p.xc + te, s0 - zb, s1 - zb, p.d_pin + 0.0625, p.t_side)
    fx, fz = p.epin
    s -= hole(fx + te, fz - zb, p.d_fpin, p.t_side)
    gx, gz = p.gpin
    s -= hole(gx + te, gz - zb, p.d_gpin + 1 / 32, p.t_side)
    for x, z in bolt_holes(p) + feeder_holes(p):
        s -= hole(x, z, 0.5625, p.t_side)
    return s


def feeder_holes(p: Params):
    """Two 9/16 holes for the feeder's rail bracket (+Y plate) and stop post (-Y plate), local plate coords."""
    return [(x + p.t_end, p.zt - BOLT_Z - p.zb) for x in (POST_X[0] + 0.5, POST_X[0] + 1.5)]


def end_plate(p: Params):
    return plate(p.brick_w, p.end_h, p.t_end)


FOOT = (2.0, 0.25, 3.0)       # 2 x 2 x 1/4 angle clip, 3 long


def foot(p: Params):
    a, t, n = FOOT
    s = angle_iron(a, t, n)
    ex, ez = HIS["bolt"] * p.sx, HIS["bolt"] * p.sz
    s -= Pos(ex, -0.01, ez) * Rot(-90, 0, 0) * Cylinder(0.28125, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s -= Pos(n / 2, a / 2 + t / 2, -0.01) * Cylinder(0.28125, t + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def fpin_len(p: Params):
    return p.t_side + 0.0625 + p.t_arm + 0.375


def fixed_pin(p: Params):
    return rod(p.d_fpin, fpin_len(p), "Z")


def gpin_len(p: Params):
    return p.t_side + 1 / 32 + p.t_bar + 0.5


def lid_pivot(p: Params):
    return rod(p.d_gpin, gpin_len(p), "Z")


# ---- lid ----
LID_WIDE_X = 11.5         # world x where the lid widens to cover the side plates (pull end)


def lid_outline(p: Params):
    """Lid plate outline, local x = world X + t_end, local y from the -Y edge of the wide part."""
    L = p.brick_l + 2 * p.t_end
    w, wi = p.lid_w, p.lid_w_in
    d = (w - wi) / 2
    xw = LID_WIDE_X + p.t_end
    return [(0, d), (xw, d), (xw, 0), (L, 0), (L, w), (xw, w), (xw, w - d), (0, w - d)]


def lid_plate(p: Params):
    return poly(lid_outline(p), p.t_lid)


def ramp(p: Params):
    """His V plate, scaled. Local x = world X, local y = height above the lid top."""
    pts = _ramp_poly(p)
    return poly(pts + [(pts[-1][0], 0.0), (pts[0][0], 0.0)], p.t_ramp)


STRAP_W = HIS["strap"][1] * 1.1


def strap(p: Params):
    """His 11" bar, scaled: pivot hole near the bottom, top end welded to the lid edge."""
    gx, gz = p.gpin
    n = p.zL - (gz - STRAP_W / 2)
    s = plate(STRAP_W, n, p.t_bar)
    return s - hole(STRAP_W / 2, STRAP_W / 2, p.d_gpin + 1 / 32, p.t_bar)


HS_ROD = 0.5              # horseshoe lid handle: 1/2 round bent into a U
HS_R = 2.0                # U radius (legs 4 apart)
HS_LEG = 1.0              # straight legs before the bend


def horseshoe(p: Params):
    """U handle: legs along +x from the weld face (x = 0), bend centred at (HS_LEG, 0); the bend is the
    rod section revolved 180 deg (meshes cleanly)."""
    from build123d import Axis, Circle, revolve
    section = Plane.XZ.offset(0) * Pos(HS_R, 0) * Circle(HS_ROD / 2)
    bend = Rot(0, 0, -90) * revolve(section, Axis.Z, 180)
    legs = [Pos(0, y, 0) * rod(HS_ROD, HS_LEG, "X") for y in (-HS_R, HS_R)]
    return legs[0] + legs[1] + Pos(HS_LEG, 0, 0) * bend


def rest_block(p: Params):
    x0, x1, h = handle_rest(p)
    return plate(x1 - x0, rest_y(p)[1] - rest_y(p)[0], h)


# ---- piston ----
WEB_W = HIS["web"][1]


def piston_cap(p: Params):
    return plate(p.brick_l - p.clear, p.brick_w - p.clear, p.t_cap)


def web_w(p: Params):
    return WEB_W * p.sx


def piston_web(p: Params):
    w = web_w(p)
    s = plate(w, p.web_h, p.t_web)
    return s - hole(w / 2, p.web_hole, p.d_pin + 1 / 32, p.t_web)


def web_faces(p: Params):
    """Outer faces (+Y side) of the four webs: two pairs near the walls, mirrored."""
    return [p.web_y, p.web_y - p.t_web - 0.5]


# ---- yoke ----
def arm_bottom(p: Params):
    """Round end centred on P (his hole sits 2 in from a 1 in radius end; centred here so the tilted
    arm clears the stand)."""
    return p.w_arm / 2


def arm(p: Params):
    """Yoke-local: x across, y along the yoke from P."""
    r = p.w_arm / 2
    top = p.yoke_len + arm_top(p)
    s = hull_plate([(0, 0, r)], [(-r, 0, r, top)], p.t_arm)
    s -= hole(0, 0, p.d_pin + 1 / 32, p.t_arm)
    s -= hole(0, p.yoke_len, p.d_q + 1 / 32, p.t_arm)
    return s


def crossbar(p: Params):
    x0, x1, z0, z1 = crossbars(p)[0]
    return plate(2 * p.arm_y, z1 - z0, p.t_bar)


def pin_len_p(p: Params):
    return 2 * (p.arm_y + p.t_arm) + 1.25


def main_pin(p: Params):
    return rod(p.d_pin, pin_len_p(p), "Z")


# ---- handle head ----
def cheek(p: Params):
    """Head-local: x along the handle, y toward Q (Q at the origin, cam pin at (0, -e))."""
    c, r = cheek_outline(p)
    lc, lr = cheek_lobe(p)
    x0, z0, x1, z1 = r[0]
    s = hull_plate(c, [], p.t_cheek) + Pos(x0, z0, 0) * plate(x1 - x0, z1 - z0, p.t_cheek)
    s += hull_plate(lc, lr, p.t_cheek)
    s -= hole(0, 0, p.d_q, p.t_cheek)
    s -= hole(0, -p.e, p.d_cam + 1 / 64, p.t_cheek)
    (lx, lz), _, _ = latch_geom(p)
    s -= hole(lx, lz, p.d_latch + 1 / 32, p.t_cheek)
    return s


def q_len(p: Params):
    return (p.arm_y + p.t_arm + 0.625) - p.cheek_y


def q_pin(p: Params):
    return rod(p.d_q, q_len(p), "Z")


def cam_pin(p: Params):
    return rod(p.d_cam, 2 * p.wall_out, "Z")


def bridge(p: Params):
    s = plate(BRIDGE_W, 2 * p.cheek_y, 0.375)
    return s - hole(BRIDGE_W / 2, p.cheek_y, p.handle_od + 1 / 16, 0.375)


def tube_len(p: Params):
    return p.handle_len - BRIDGE_X[0]


def handle_tube(p: Params, length=None):
    return tube(p.handle_od, p.handle_od - 0.4, length or tube_len(p), "X")


# ---- latch (his notched hook plates, notch moved to the tip) ----
LATCH_W = HIS["latch"][1] * 1.1
LATCH_Y = 1.9                 # latch plates' outer faces from the centreline


def latch_fork_tilt(p: Params):
    """Angle (deg) between the latch line and the bar's height direction (yoke -z), for cutting the fork square."""
    (lx, lz), (nx, nz), k = latch_geom(p)
    r = math.radians(p.rho0)
    ly_x, ly_z = lx * math.cos(r) + lz * math.sin(r), -lx * math.sin(r) + lz * math.cos(r)   # L in yoke-local
    dx, dz = nx - ly_x, nz - ly_z
    return math.degrees(math.atan2(dx, -dz))


def latch_plate(p: Params):
    """Latch-local: pivot at the origin, +x toward the notch; the fork at the tip drops over the
    cross bar (bar top edge at x = k), cut square to the bar."""
    _, _, k = latch_geom(p)
    r = LATCH_W / 2
    s = hull_plate([(0, 0, r)], [(0, -r, k + 0.5, r)], p.t_latch)
    wn = p.t_bar + 0.125
    fork = Pos(-0.3, -wn / 2, -0.01) * Box(1.2, wn, p.t_latch + 0.02, align=Align.MIN)
    s -= Pos(k, 0, 0) * Rot(0, 0, -latch_fork_tilt(p)) * fork          # plate y maps to -head z
    return s - hole(0, 0, p.d_latch + 1 / 32, p.t_latch)


def latch_pin_len(p: Params):
    return 2 * p.cheek_y + 2 * p.t_cheek


def latch_pin(p: Params):
    return rod(p.d_latch, latch_pin_len(p), "Z")


def latch_bar(p: Params):
    return plate(HIS["latch_bar"][0] * 0 + 2 * LATCH_Y, HIS["latch_bar"][1] * 1.1, 0.375)


def latch_angle(p: Params):
    """Head-local angle (deg) of the latch pivot->notch line when shut."""
    (lx, lz), (nx, nz), k = latch_geom(p)
    r = math.radians(p.rho0)
    hx = nx * math.cos(r) - nz * math.sin(r)       # yoke-local -> head-local (inverse of to_yoke)
    hz = nx * math.sin(r) + nz * math.cos(r)
    return math.degrees(math.atan2(-(hz - lz), hx - lx))


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
    his: str = ""         # his part it comes from (cinva1-7.jpg)
    flag: str = ""        # why it is heavier / different from his
    paper: str = ""
    table: callable = None

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


def _rod_dims(d, n):
    return [("D", "F", (0, 0, 0), d, 45, ""), ("H", "L", (0, 0, 0), (0, n, 0), -10)]




def _rod_dims(d, n):
    return [("D", "F", (0, 0, 0), d, 45, ""), ("H", "L", (0, 0, 0), (0, n, 0), -10)]


def ramp_table(p: Params):
    """Ramp top ordinates: X from the lid's -X edge, H above the ramp bottom."""
    te = p.t_end
    xs = [i * 0.5 for i in range(int((p.brick_l + 2 * te) / 0.5) + 1)]
    pts = [(x, ramp_h(p, x - te)) for x in xs]
    pts = [q for q in pts if q[1] is not None]
    ncol = 5
    nrow = math.ceil(len(pts) / ncol)
    rows = []
    for r in range(nrow):
        row = []
        for c in range(ncol):
            i = c * nrow + r
            row += [f"{pts[i][0]:.3f}", f"{pts[i][1]:.3f}"] if i < len(pts) else ["", ""]
        rows.append(row)
    return ("RAMP TOP ORDINATES (X FROM LID -X EDGE, H ABOVE RAMP BOTTOM); SCOOP PER DETAIL", ["X", "H"] * ncol, rows)


def parts(p: Params) -> list[Part]:
    L, W, te, zb = p.brick_l, p.brick_w, p.t_end, p.zb
    s0, s1 = p.slot
    fx, fz = p.epin
    gx, gz = p.gpin
    Ly = p.yoke_len
    pl = lambda t: f'{t:.3f}" plate'
    sw = L + 2 * te
    (lx, lz), _, k = latch_geom(p)
    xb = crossbars(p)[0]
    rx0, rx1, rh = handle_rest(p)
    ramp_pts = _ramp_poly(p)
    xs, Hs = p.ramp_profile[1]
    ww = web_w(p)
    bh = bolt_holes(p)

    ps = [
        # ---------------- frame ----------------
        Part("side", "Side Plate", 2, pl(p.t_side) + " A36", "gray", side_plate, group="Frame",
             his="12 x 15 side plate, 1/4 (sheet 7)",
             flag="1/4 in his; 1/2 holds the soil pressure of the 14 in brick (the lid sits on top and does not brace the plate tops)",
             dims=lambda p: [
                 ("H", "F", (0, 0, 0), (sw, 0, 0), -10), ("V", "F", (sw, 0, 0), (sw, p.side_h, 0), 10),
                 ("H", "F", (0, 0, 0), (p.xc + te - (p.d_pin + 0.0625) / 2, s0 - zb, 0), -18),
                 ("H", "F", (0, 0, 0), (p.xc + te + (p.d_pin + 0.0625) / 2, s0 - zb, 0), -26),
                 ("V", "F", (sw, 0, 0), (p.xc + te, s0 - zb, 0), 18),
                 ("V", "F", (sw, 0, 0), (p.xc + te, s1 - zb, 0), 26),
                 ("R", "F", (p.xc + te, s1 - zb - (p.d_pin + 0.0625) / 2, 0), (p.d_pin + 0.0625) / 2, 60, "SLOT 2x ", 14),
                 ("H", "F", (0, p.side_h, 0), (fx + te, fz - zb, 0), 8),
                 ("V", "F", (0, 0, 0), (fx + te, fz - zb, 0), -10),
                 ("D", "F", (fx + te, fz - zb, 0), p.d_fpin, 120, "FIXED PIN ", 12),
                 ("H", "F", (0, p.side_h, 0), (gx + te, gz - zb, 0), 16),
                 ("V", "F", (sw, 0, 0), (gx + te, gz - zb, 0), 34),
                 ("D", "F", (gx + te, gz - zb, 0), p.d_gpin + 1 / 32, 300, "LID PIVOT ", 16),
                 ("H", "F", (0, 0, 0), (bh[0][0], bh[0][1], 0), -34), ("V", "F", (0, 0, 0), (bh[0][0], bh[0][1], 0), -18),
                 ("D", "F", (bh[0][0], bh[0][1], 0), 0.5625, 225, "2x ", 10),
                 ("H", "L", (0, 0, 0), (0, 0, p.t_side), -10)],
             notes=("Slot width is his error fixed: his drawing shows 2.000 for a 1 in pin; cut it pin + 1/16.",
                    "The slot is centred on the plate length and stops below the loose soil at fill.",
                    "Weld the end plates between the side plates, outside only; no weld or spatter inside the mold.")),
        Part("end", "End Plate", 2, pl(p.t_end) + " A36", "gray", end_plate, group="Frame",
             his="6 x 6 end plate (sheet 7)",
             flag="1/4 in his; 1/2 spans the 7 in mold width; 7.75 tall so it reaches the piston at fill",
             dims=lambda p: _plate_dims(W, p.end_h, (), p.t_end),
             notes=("Between the side plates, top flush with them. Mold inside must be square: check diagonals.",)),
        Part("foot", "Foot Clip", 4, '2 x 2 x 1/4 angle', "green", foot, group="Frame",
             views=("F", "T", "L"), front="-Y", flat=False, his="his L-shaped feet",
             dims=lambda p: [("H", "F", (0, 0, 0), (FOOT[2], 0, 0), -10),
                             ("V", "L", (0, 0, 0), (0, FOOT[0], 0), -8)],
             notes=("Bolt through the side plate's bottom-corner holes (1/2 bolts), and lag or bolt to the stand.",
                    f"The stand top is {p.base_h:g} in above the ground; any solid bench or timber frame will do.")),
        Part("fpin", "Fixed Pin", 2, f'{p.d_fpin:.3f}" round 1018', "purple", fixed_pin, group="Frame",
             views=("F", "L"), front="-Y", flat=False, his="1 in fixed pin (his 1 in hole, sheet 7)",
             flag="1 in in his; 1-1/4 for the eject load",
             dims=lambda p: _rod_dims(p.d_fpin, fpin_len(p)),
             notes=("Through the side plate hole, inner end flush with the inside face; weld outside.",
                    f"The yoke arm lies on it to eject and to fill. Height set so the eject ends at "
                    f"{p.theta_eject:g} deg (his 7 in x {p.sz:.3f} = {HIS['fixed_pin'][1] * p.sz:.2f}).")),
        Part("gpin", "Lid Pivot Pin", 2, f'{p.d_gpin:.3f}" round 1018', "white", lid_pivot, group="Frame",
             views=("F", "L"), flat=False, his="(pivot of his lid straps)",
             dims=lambda p: _pin_dims(p.d_gpin, gpin_len(p)),
             notes=("Weld in the side plate, inner end flush inside; strap on the outside, washer and 1/8 cotter.",)),

        # ---------------- lid ----------------
        Part("lid", "Lid Plate", 1, pl(p.t_lid) + " A36", "red", lid_plate, group="Lid",
             his="6.5 x 12 top plate (sheet 1)",
             flag="1/4 in his; 5/8. Fits between the side plates (on the end plates) except at the pull end, so the head clears it",
             dims=lambda p: [("H", "F", (0, 0, 0), (sw, 0, 0), -10), ("V", "F", (sw, 0, 0), (sw, p.lid_w, 0), 10),
                             ("V", "F", (0, (p.lid_w - p.lid_w_in) / 2, 0), (0, p.lid_w - (p.lid_w - p.lid_w_in) / 2, 0), -10),
                             ("H", "F", (0, p.lid_w, 0), (LID_WIDE_X + te, p.lid_w, 0), 8),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_lid), -10)],
             notes=("Rests on the end plates. The narrow part stays 1/64 inside the side plates' inner faces "
                    "(the head swings down past it); the wide part at the pull end also sits on the side plates.",
                    "Underside flat and clean: it is the brick's top face.")),
        Part("ramp", "V Ramp", 2, pl(p.t_ramp) + " AR400", "red", ramp, group="Lid", paper="A3",
             his="12 in V plate with R0.625 scoop (sheet 5)",
             flag="1/4 in his; 3/4 AR400: the cam pin carries the whole press force in the scoop",
             table=ramp_table,
             dims=lambda p: [("H", "F", (-te, 0, 0), (L + te, 0, 0), -10),
                             ("V", "F", (-te, 0, 0), (-te, ramp_pts[0][1], 0), -8),
                             ("V", "F", (L + te, 0, 0), (L + te, ramp_pts[-1][1], 0), 8),
                             ("V", "F", (L + te, 0, 0), (xs + p.scoop_r, Hs, 0), 18),
                             ("H", "F", (-te, 0, 0), (xs, Hs, 0), -20, "bbox", f"{xs + te:.3f} SCOOP"),
                             ("H", "F", (-te, Hs, 0), (xs + p.scoop_r + HIS['ramp']['flat'] * sw / 12, Hs, 0), 8),
                             ("R", "F", (xs, Hs, 0), p.scoop_r, 300, "SCOOP ", 12),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_ramp), -10)],
             notes=("His V plate scaled: long leg to the -X end (fixed-pin end), half-round scoop centred on "
                    "the mold, flat, short leg to the +X end.",
                    f"Scoop R{p.scoop_r:.3f} (cam pin + 1/8, as his R0.625 for a 1 in pin); dress it smooth.",
                    "Weld to the lid top along both sides; AR400: low-hydrogen rod, preheat 300 F.")),
        Part("strap", "Lid Strap", 2, pl(p.t_bar) + " A36", "red", strap, group="Lid",
             his="11 x 2 bar (sheet 4)",
             dims=lambda p: _plate_dims(STRAP_W, p.zL - (gz - STRAP_W / 2), [(STRAP_W / 2, STRAP_W / 2, p.d_gpin + 1 / 32)], p.t_bar),
             notes=("Outside the side plate on the lid pivot pin; top end welded to the lid plate edge.",
                    "The lid swings over on these and rests upside down beside the press.")),
        Part("hrest", "Handle Rest", 2, f'{handle_rest(p)[2]:.3f} x 1/2 flat bar', "red", rest_block, group="Lid",
             dims=lambda p: _plate_dims(rx1 - rx0, rest_y(p)[1] - rest_y(p)[0], (), rh),
             notes=("Weld on the lid top along each long edge at the pull end, under the head cheeks. The "
                    "cheeks land on them 3 deg past centre: that is the over-centre lock.",
                    "Fit on assembly: shim or grind so the handle stops 3 deg below horizontal with the lid closed.")),

        # ---------------- piston ----------------
        Part("cap", "Piston Cap", 1, pl(p.t_cap) + " A36", "teal", piston_cap, group="Piston",
             his="6 x 11.5 plate (sheet 1)", flag="1/4 in his; 1/2 so the cap does not dish",
             dims=lambda p: _plate_dims(L - p.clear, W - p.clear, (), p.t_cap),
             notes=("Top face flat; 1/16 clearance each side in the mold.",)),
        Part("web", "Piston Web", 4, pl(p.t_web) + " A36", "teal", piston_web, group="Piston",
             his="7.25 x 6 plate, 1 in hole (sheet 1)", flag="1/4 in his; 3/8",
             dims=lambda p: _plate_dims(ww, p.web_h, [(ww / 2, p.web_hole, p.d_pin + 1 / 32)], p.t_web),
             notes=("Two pairs under the cap: outer faces flush with the cap edges, the others 1/2 inboard of them. "
                    "Line-bore the pin holes after welding.",)),

        # ---------------- yoke ----------------
        Part("arm", "Yoke Arm", 2, pl(p.t_arm) + " A36", "blue", arm, group="Yoke",
             his="19.625 x 2 bar, 1 in hole (sheet 4)",
             flag="2 x 1/4 bar in his; 3 x 1/2 for the pin loads; 2.3 in longer so the cross bars clear the head",
             dims=lambda p: [("V", "F", (1.2, 0, 0), (0, Ly, 0), 10),
                             ("V", "F", (1.2, -arm_bottom(p), 0), (1.2, Ly + arm_top(p), 0), 20),
                             ("V", "F", (1.2, -arm_bottom(p), 0), (0, 0, 0), -10),
                             ("H", "F", (-p.w_arm / 2, 0, 0), (p.w_arm / 2, 0, 0), -10),
                             ("D", "F", (0, 0, 0), p.d_pin + 1 / 32, 200, "P ", 12),
                             ("D", "F", (0, Ly, 0), p.d_q + 1 / 32, 160, "Q ", 12),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_arm), -10)],
             notes=("Drill both arms clamped together.",)),
        Part("xbar", "Cross Bar", 2, pl(p.t_bar) + " A36", "blue", crossbar, group="Yoke",
             his="8 x 2 bar (sheet 4)",
             dims=lambda p: _plate_dims(2 * p.arm_y, xb[3] - xb[2], (), p.t_bar),
             notes=("On edge between the arm tops, one flush with each arm edge (a box).",
                    "The head rests on the lower edge of the pull-end bar at the start, and the latch hooks its "
                    "top edge.")),
        Part("ppin", "Main Pin P", 1, f'{p.d_pin:.3f}" round 4140 prehard', "purple", main_pin, group="Yoke",
             flag="1 in mild steel in his; 1-3/4 4140 (four webs put the load inboard of the arms)", views=("F", "L"), flat=False,
             dims=lambda p: _pin_dims(p.d_pin, pin_len_p(p)),
             notes=("Through arm, slot, four webs, slot, arm; 1/4 hitch pins outside the arms.",)),

        # ---------------- handle head ----------------
        Part("cheek", "Head Cheek", 2, pl(p.t_cheek) + " A36", "orange", cheek, group="Handle",
             his="head (his links and 3 x 2 plates, sheets 2 and 6)",
             dims=lambda p: [("V", "F", (1.5, 0, 0), (0, -p.e, 0), 12),
                             ("V", "F", (1.5, 0, 0), (0, -p.handle_off, 0), 20),
                             ("H", "F", (0, 1.5, 0), (lx, lz, 0), 10),
                             ("V", "F", (-1.5, 0, 0), (lx, lz, 0), -10),
                             ("H", "F", (-LEG_HALF, -p.handle_off - LEG_HALF, 0), (LEG_LEN, -p.handle_off - LEG_HALF, 0), -10),
                             ("D", "F", (0, 0, 0), p.d_q, 135, "Q ", 12),
                             ("D", "F", (0, -p.e, 0), p.d_cam + 1 / 64, 225, "CAM PIN ", 12),
                             ("D", "F", (lx, lz, 0), p.d_latch + 1 / 32, 60, "LATCH ", 10),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_cheek), -10)],
             notes=(f"The L-cam: cam pin {p.e:.3f} below Q (hold +/-0.010), handle leg along the other side.",
                    "His head is built from his link plates and 3 x 2 plates; this one-piece cheek does the same "
                    "job with one part per side.")),
        Part("qpin", "Pin Q (stub)", 2, f'{p.d_q:.3f}" round 4140 prehard', "purple", q_pin, group="Handle",
             flag="1 in in his; 1-1/4 4140", views=("F", "L"), flat=False,
             dims=lambda p: _pin_dims(p.d_q, q_len(p)),
             notes=("Weld into the cheek, inner end flush inside; turns in the arm. Washer and hitch pin outside.",)),
        Part("campin", "Cam Pin", 1, f'{p.d_cam:.3f}" round 4140 prehard', "purple", cam_pin, group="Handle",
             flag="1 in in his; 1-1/4 4140", views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: _rod_dims(p.d_cam, 2 * p.wall_out),
             notes=("Through both cheeks, flush outside; weld the ends. It seats in the ramp scoops.",)),
        Part("bridge", "Handle Bridge", 2, pl(0.375) + " A36", "orange", bridge, group="Handle",
             dims=lambda p: _plate_dims(BRIDGE_W, 2 * p.cheek_y, [(BRIDGE_W / 2, p.cheek_y, p.handle_od + 1 / 16)], 0.375),
             notes=(f"Between the cheeks on the handle leg, square to it, {BRIDGE_X[0]:g} and {BRIDGE_X[1]:g} from Q.",)),
        Part("htube", "Handle", 1, '1-1/2" sch 80 pipe', "orange", handle_tube, group="Handle",
             views=("F", "L"), flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (tube_len(p), 0, 0), -10), ("D", "L", (0, 0, 0), p.handle_od, 45, "")],
             notes=("Through both bridges, end flush with the inner bridge; weld all round.",)),
        Part("latch", "Latch Hook", 2, pl(p.t_latch) + " A36", "pink", latch_plate, group="Handle",
             his="4.147 x 1 notched plate (sheet 3)",
             flag="his notch is on the side; here it is at the tip so the hook drops straight onto the cross bar",
             dims=lambda p: [("H", "F", (0, 0, 0), (k, 0, 0), -12), ("H", "F", (-LATCH_W / 2, 0, 0), (k + 0.5, 0, 0), -20),
                             ("V", "F", (k + 0.5, -LATCH_W / 2, 0), (k + 0.5, LATCH_W / 2, 0), 10),
                             ("D", "F", (0, 0, 0), p.d_latch + 1 / 32, 135, "", 10),
                             ("H", "L", (0, 0, 0), (0, 0, p.t_latch), -10)],
             notes=(f"Fork at the tip {p.t_bar + 0.125:.3f} wide, 0.600 deep, fits over the cross bar.",)),
        Part("lbar", "Latch Bar", 1, '3/8 x 1-1/8 flat bar', "pink", latch_bar, group="Handle",
             his="1 x 2.75 bar (sheet 3)",
             dims=lambda p: _plate_dims(2 * LATCH_Y, LATCH_W, (), 0.375),
             notes=("Welded across the two hooks; lift it to open the latch.",)),
        Part("lpin", "Latch Pivot", 1, f'{p.d_latch:.3f}" round 1018', "purple", latch_pin, group="Handle",
             his="7/16 pin (sheet 3)", views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: _rod_dims(p.d_latch, latch_pin_len(p)),
             notes=("Through both cheeks and hooks; cotter each end.",)),
        Part("lhandle", "Lid Handle", 1, '0.500" round 1018, bent', "red", horseshoe, group="Lid",
             views=("T", "F"), front="Z", flat=False,
             dims=lambda p: [("V", "T", (HS_LEG + HS_R, -HS_R - HS_ROD / 2, 0), (HS_LEG + HS_R, HS_R + HS_ROD / 2, 0), 10),
                             ("H", "T", (0, HS_R + HS_ROD / 2, 0), (HS_LEG + HS_R + HS_ROD / 2, HS_R + HS_ROD / 2, 0), 10),
                             ("R", "T", (HS_LEG, 0, 0), HS_R, 45, "CL ", 10),
                             ("D", "F", (0, HS_R, 0), HS_ROD, 135, "", 8)],
             notes=(f"Bend 1/2 round into a U, {2 * HS_R:g} between leg centres; weld the leg ends to the lid's "
                    "fixed-pin end face, centred, level with the lid.",
                    "Lift here to swing the lid over onto the stand, and to swing it back.")),
    ] + feeder_parts(p)
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
    "blue": (0.15, 0.25, 0.85), "yellow": (0.95, 0.85, 0.10),
}

MIRROR_Y = Plane.XZ
UPRIGHT = Rot(90, 0, 0)                     # local x->X, y->Z, z->-Y
EDGE = Rot(0, 0, 90) * Rot(90, 0, 0)        # local x->Y, y->Z, z->X
ALONG_Y = Rot(90, 0, 0)                     # rod built along Z -> along -Y
LATCH_OPEN = 180.0                          # latch flipped over onto the handle leg


def is_latched(p: Params, pose: Pose):
    return abs((pose.psi + pose.theta) - p.rho0) < 1e-6


def assembly(p: Params, pose: str = "locked", handle_len: float | None = None):
    """[(part_key, instance_name, solid), ...] in world coordinates."""
    ps = poses(p)[pose] if isinstance(pose, str) else pose
    L, W, te, zb = p.brick_l, p.brick_w, p.t_end, p.zb
    out = []

    def add(key, name, s, mirror=False):
        out.append((key, name, s))
        if mirror:
            out.append((key, name + " (mirror)", s.mirror(MIRROR_Y)))

    # frame
    add("side", "Side Plate", Pos(-te, p.wall_out, zb) * UPRIGHT * side_plate(p), mirror=True)
    for x in (-te, L):
        add("end", "End Plate", Pos(x, -W / 2, p.zt - p.end_h) * EDGE * end_plate(p))
    for x in foot_x(p):
        add("foot", "Foot Clip", Pos(x, p.wall_out, zb) * foot(p), mirror=True)
    fx, fz = p.epin
    add("fpin", "Fixed Pin", Pos(fx, p.wall_out - p.t_side + fpin_len(p), fz) * ALONG_Y * fixed_pin(p), mirror=True)
    gx, gz = p.gpin
    add("gpin", "Lid Pivot Pin", Pos(gx, p.wall_out - p.t_side + gpin_len(p), gz) * ALONG_Y * lid_pivot(p), mirror=True)

    # lid
    lf = lid_frame(p, ps.cover)
    add("lid", "Lid Plate", lf * Pos(-te, -p.lid_w / 2, p.zt) * lid_plate(p))
    add("ramp", "V Ramp", lf * Pos(0, p.ramp_y, p.zL) * UPRIGHT * ramp(p), mirror=True)
    add("strap", "Lid Strap", lf * Pos(gx - STRAP_W / 2, p.wall_out + 1 / 32 + p.t_bar, gz - STRAP_W / 2)
        * UPRIGHT * strap(p), mirror=True)
    rx0, rx1, _ = handle_rest(p)
    add("hrest", "Handle Rest", lf * Pos(rx0, rest_y(p)[0], p.zL) * rest_block(p), mirror=True)
    add("lhandle", "Lid Handle", lf * Pos(-te, 0, p.zt + p.t_lid / 2) * Rot(0, 0, 180) * horseshoe(p))

    # piston
    zcap = ps.zp + p.pin_below_cap - p.t_cap
    add("cap", "Piston Cap", Pos(p.clear / 2, -(W - p.clear) / 2, zcap) * piston_cap(p))
    ww = web_w(p)
    for f in web_faces(p):
        add("web", "Piston Web", Pos(p.xc - ww / 2, f, zcap - p.web_h) * UPRIGHT * piston_web(p), mirror=True)
    add("ppin", "Main Pin P", Pos(p.xc, pin_len_p(p) / 2, ps.zp) * ALONG_Y * main_pin(p))

    # yoke
    yk = yoke_frame(p, ps.theta, ps.zp)
    add("arm", "Yoke Arm", yk * Pos(0, p.arm_y + p.t_arm, 0) * UPRIGHT * arm(p), mirror=True)
    for x0, x1, z0, z1 in crossbars(p):
        add("xbar", "Cross Bar", yk * Pos(x0, -p.arm_y, p.yoke_len + z0) * Box(x1 - x0, 2 * p.arm_y, z1 - z0, align=Align.MIN))

    # handle head
    hf = head_frame(p, ps.theta, ps.psi, ps.zp)
    a = p.handle_off
    add("cheek", "Head Cheek", hf * Pos(0, p.wall_out, 0) * UPRIGHT * cheek(p), mirror=True)
    add("qpin", "Pin Q", hf * Pos(0, p.cheek_y + q_len(p), 0) * ALONG_Y * q_pin(p), mirror=True)
    add("campin", "Cam Pin", hf * Pos(0, p.wall_out, -p.e) * ALONG_Y * cam_pin(p))
    for xb in BRIDGE_X:
        add("bridge", "Handle Bridge", hf * Pos(xb + 0.375, -p.cheek_y, -a - BRIDGE_W / 2) * Rot(0, -90, 0) * bridge(p))
    hl = p.handle_len if handle_len is None else handle_len
    add("htube", "Handle", hf * Pos(BRIDGE_X[0], 0, -a) * handle_tube(p, hl - BRIDGE_X[0]))
    # latch
    (lx, lz), _, k = latch_geom(p)
    open_ = ps.claw if ps.claw is not None else (0.0 if is_latched(p, ps) else LATCH_OPEN)
    lt = hf * Pos(lx, 0, lz) * Rot(0, latch_angle(p) + open_, 0)
    add("latch", "Latch Hook", lt * Pos(0, LATCH_Y, 0) * UPRIGHT * latch_plate(p), mirror=True)
    add("lbar", "Latch Bar", lt * Pos(0.45 * k - 0.55, -LATCH_Y, -LATCH_W / 2 - 0.375) * Box(1.1, 2 * LATCH_Y, 0.375, align=Align.MIN))
    add("lpin", "Latch Pivot", hf * Pos(lx, p.wall_out, lz) * ALONG_Y * latch_pin(p))
    add_feeder(p, ps, add)
    return out


def assembly_compound(p: Params, pose="locked", **kw) -> Compound:
    colors = {pt.key: pt.color for pt in parts(p)}
    kids = []
    for key, name, s in assembly(p, pose, **kw):
        s.label = name
        s.color = Color(*COLORS[colors[key]])
        kids.append(s)
    return Compound(children=kids, label=f"Simple CINVA-Ram {p.label} ({pose})")


# parts that touch by design (welded, pinned or bearing)
TOUCH = {frozenset(x) for x in [
    ("side", "end"), ("side", "foot"), ("side", "fpin"), ("side", "gpin"), ("strap", "gpin"),
    ("lid", "ramp"), ("lid", "strap"), ("lid", "hrest"), ("lid", "side"), ("lid", "end"),
    ("cap", "web"), ("web", "ppin"), ("arm", "ppin"), ("side", "ppin"), ("arm", "xbar"),
    ("arm", "qpin"), ("cheek", "qpin"), ("cheek", "campin"), ("cheek", "bridge"), ("bridge", "htube"),
    ("latch", "lbar"), ("latch", "lpin"), ("cheek", "lpin"), ("lid", "lhandle"),
    # feeder weldments and seats
    ("fbfunnel", "bhandle"), ("gate", "ghandle"), ("fbstrike", "lug"),
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
    """Every motion of the cycle, for clearance checks."""
    ps = poses(p)
    th_f, th_e = ps["fill"].theta, ps["eject"].theta
    th0 = p.theta_start
    out = []
    for i in range(n + 1):                   # pressing (and lifting the handle back): cam pin in the scoop
        psi = p.psi0 + (p.psi_lock - p.psi0) * i / n
        th, zp, _ = p.knee(psi)
        out.append(Pose(f"press {psi:.0f}", th, psi, zp, 0, LATCH_OPEN))
    for i in range(n + 1):                   # latched, standing up / tilting back with the lid closed
        th = th_f + (th0 - th_f) * i / n
        out.append(latched(p, f"stand up {th:.0f}", th, standup_zp(p, th), 0))
    for i in range(1, n + 1):                # lid swinging open / closed at fill
        out.append(latched(p, f"lid {p.lid_open * i / n:.0f}", th_f, p.zp_fill, p.lid_open * i / n))
    for i in range(n + 1):                   # eject and back, lid open
        th = th_f + (th_e - th_f) * i / n
        out.append(latched(p, f"eject {th:.0f}", th, eject_zp(p, th), p.lid_open))
    return out


# ==========================================================
# Strength checks
# ==========================================================

FY_A36, FU_A36, FY_4140, FY_1018, FY_AR400 = 36000.0, 58000.0, 95000.0, 50000.0, 145000.0
E_STEEL = 30e6


def eject_hand(p: Params, th, F=None):
    """Hand force (lbf, perpendicular to the handle, at the grip) to eject at tilt th."""
    F = p.eject_force if F is None else F
    d = 0.05

    def grip(t):
        zp = eject_zp(p, t)
        return head_point(p, t, p.rho0 - t, zp, (p.handle_len, -p.handle_off))
    g0, g1 = grip(th - d), grip(th + d)
    ds = math.hypot(g1[0] - g0[0], g1[1] - g0[1])
    dz = eject_zp(p, th + d) - eject_zp(p, th - d)
    return F * dz / ds


def max_eject_hand(p: Params):
    """Largest hand force over the part of the eject stroke where the piston pushes the brick."""
    th_c = solve_theta(p, p.zp_comp)[1]
    return max(eject_hand(p, th_c + (p.theta_eject - th_c) * i / 20) for i in range(21))


def checks(p: Params):
    """[(item, basis, stress psi, allowable psi)] at the design force."""
    F = p.f_design
    rows = []
    sec = lambda d: math.pi * d ** 3 / 32
    # pin P: four webs (two per side) to the arm outside the side plate
    ya = p.arm_y + p.t_arm / 2
    yw = [f - p.t_web / 2 for f in web_faces(p)]
    M = F / 2 * ya - F / 4 * sum(yw)
    rows.append(("Main pin P, bending", f"M = {M:,.0f} lbf in, 4 webs, dia {p.d_pin:.3f} 4140",
                 M / sec(p.d_pin), 0.6 * FY_4140))
    rows.append(("Main pin P, shear", "F/2 per side", F / 2 / (math.pi * p.d_pin ** 2 / 4), 0.4 * FY_4140))
    e = (p.arm_y + p.t_arm / 2) - (p.cheek_y + p.t_cheek / 2)
    rows.append(("Pin Q, bending", f"M = F/2 x {e:.2f}, dia {p.d_q:.3f} 4140", F / 2 * e / sec(p.d_q), 0.6 * FY_4140))
    e = (p.cheek_y + p.t_cheek / 2) - (p.ramp_y - p.t_ramp / 2)
    rows.append(("Cam pin, bending", f"M = F/2 x {e:.2f}, dia {p.d_cam:.3f} 4140", F / 2 * e / sec(p.d_cam), 0.6 * FY_4140))
    an = (p.w_arm - p.d_pin - 1 / 32) * p.t_arm
    rows.append(("Yoke arm, net tension at P", f"F/2 on {an:.2f} sq in", F / 2 / an, 0.5 * FU_A36))
    rows.append(("Yoke arm, pin bearing", f"F/2 on {p.d_pin:.2f} x {p.t_arm:.2f}", F / 2 / (p.d_pin * p.t_arm), 0.9 * FY_A36))
    rows.append(("Cheek, Q pin bearing", f"F/2 on {p.d_q:.2f} x {p.t_cheek:.2f}", F / 2 / (p.d_q * p.t_cheek), 0.9 * FY_A36))
    rows.append(("Piston web, pin bearing", f"F/4 on {p.d_pin:.2f} x {p.t_web:.3f}", F / 4 / (p.d_pin * p.t_web), 0.9 * FY_A36))
    # side plate: soil pressure on the 4 in band at the top; shared between the vertical cantilever from
    # below the band and the horizontal span between the end plates, by stiffness
    q = 0.5 * p.p_design
    h, Lh = p.brick_h, p.brick_l
    kv, kh = 8 / h ** 4, 384 / Lh ** 4
    M = max(kv / (kv + kh) * q * h * h / 2, kh / (kv + kh) * q * Lh * Lh / 12)
    rows.append(("Side plate, bending", f"K0 0.5, band {h:g} in, span {Lh:g}, t {p.t_side:.3f}",
                 M / (p.t_side ** 2 / 6), 0.66 * FY_A36))
    M = q * p.brick_w ** 2 / 12
    rows.append(("End plate, bending", f"K0 0.5, span {p.brick_w:g} fixed ends, t {p.t_end:.3f}",
                 M / (p.t_end ** 2 / 6), 0.66 * FY_A36))
    # lid + ramps as a beam: cam pin load at the centre against the brick pressure over L
    b, tp = p.lid_w_in, p.t_lid
    hr = p.ramp_profile[1][1] - p.scoop_r
    A1, y1 = b * tp, tp / 2
    A2, y2 = 2 * p.t_ramp * hr, tp + hr / 2
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = b * tp ** 3 / 12 + A1 * (yb - y1) ** 2 + 2 * p.t_ramp * hr ** 3 / 12 + A2 * (y2 - yb) ** 2
    c = max(yb, tp + hr - yb)
    rows.append(("Lid and ramps, bending", f"M = F L / 8 at the scoop, I = {I:.1f} in^4", F * p.brick_l / 8 * c / I,
                 0.66 * FY_A36))
    span = 2 * (p.ramp_y - p.t_ramp)
    rows.append(("Lid plate between ramps", f"strip span {span:.2f}, t {p.t_lid:.3f}",
                 p.p_design * span ** 2 / 8 / (p.t_lid ** 2 / 6), 0.66 * FY_A36))
    # piston cap over four webs (largest span between web centres)
    ys = sorted([-(f - p.t_web / 2) for f in web_faces(p)] + [f - p.t_web / 2 for f in web_faces(p)])
    sp = max(b2 - a2 for a2, b2 in zip(ys, ys[1:]))
    rows.append(("Piston cap, bending", f"strip span {sp:.2f}, t {p.t_cap:.3f}",
                 p.p_design * sp ** 2 / 8 / (p.t_cap ** 2 / 6), 0.66 * FY_A36))
    h, t = p.web_h, p.t_web
    M = F / 4 * web_w(p) / 8
    rows.append(("Piston web, bending", f"F/4 over {web_w(p):.2f}, supported at the pin", M / (t * h * h / 6), 0.66 * FY_A36))
    # cam pin in the scoop (conformal contact, R pin in R scoop)
    Es = E_STEEL / (2 * (1 - 0.3 ** 2))
    qn = F / 2 / p.t_ramp
    Re = 1 / (2 / p.d_cam - 1 / p.scoop_r)
    rows.append(("Cam pin in scoop, contact", f"R {p.d_cam / 2:.3f} in R {p.scoop_r:.3f}, AR400",
                 math.sqrt(qn * Es / Re / math.pi), 0.5 * FY_AR400 / 0.3))
    # eject: fixed pin and latch
    ps = poses(p)
    th_e = ps["eject"].theta
    fe = max_eject_hand(p)
    rf = p.eject_force * 3
    rows.append(("Fixed pin, bending (eject)", f"{rf / 2:,.0f} lbf per side x {fpin_len(p) - p.t_side / 2:.2f}",
                 rf / 2 * (fpin_len(p) - p.t_side / 2) / sec(p.d_fpin), 0.66 * FY_1018))
    fl = fe * p.handle_len / 3.0
    rows.append(("Latch hooks, bearing (tilting)", f"{fl:,.0f} lbf on 2 x {p.t_latch:.3f} x {p.t_bar:.3f}",
                 fl / 2 / (p.t_latch * p.t_bar), 0.9 * FY_A36))
    # feeder: full box parked, as a point load mid-span on each rail between the ties
    wb = feed_capacity(p) * SOIL + sum(pt.weight(p) * pt.qty for pt in parts(p)
                                       if pt.key in ("fbpin", "fblid", "fbstrike", "fbfunnel", "gate", "ghandle", "bhandle", "lug"))
    span = (FEED_STOP + RAIL_T - RAIL_A / 2) - (FEED_Y0 + 0.0625 + RAIL_A / 2)
    rows.append(("Feed rail, bending", f"{wb / 2:.0f} lb mid-span {span:.1f}, {RAIL_A:g} angle",
                 wb / 2 * span / 4 / angle_s(RAIL_A, RAIL_T), 0.66 * FY_A36))
    return rows


def angle_s(a, t):
    """Elastic section modulus of an equal-leg angle about the axis parallel to a leg (smaller fibre)."""
    A1, y1 = a * t, t / 2
    A2, y2 = (a - t) * t, t + (a - t) / 2
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = a * t ** 3 / 12 + A1 * (yb - y1) ** 2 + t * (a - t) ** 3 / 12 + A2 * (y2 - yb) ** 2
    return I / max(yb, a - yb)


# ==========================================================
# Verification
# ==========================================================

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


def verify(p: Params, sweep=True):
    """Every functional check; [(check, ok, detail)]."""
    res = []
    ps = poses(p)
    brick = p.zt - (p.zp_comp + p.pin_below_cap)
    res.append(("Brick thickness at centre", abs(brick - p.brick_h) < 1e-6, f"{brick:.4f} in (target {p.brick_h:g})"))
    zs = [p.knee(p.psi0 + i * 0.5)[1] for i in range(int(-p.psi0 * 2) + 1)]
    res.append(("Piston rises steadily over the stroke", all(b > a - 1e-9 for a, b in zip(zs, zs[1:])),
                f"{zs[0] - p.zt + p.pin_below_cap:+.3f} -> {zs[-1] - p.zt + p.pin_below_cap:+.3f} in from the mold top"))
    back = p.knee(0.0)[1] - p.zp_lock
    res.append(("Locks over centre on the handle rest", 0 < back < 0.02,
                f"at {p.psi_lock:g} deg the piston is {back:.4f} in below its top point, so the brick pushes "
                f"the handle onto its rest"))
    s0, s1 = p.slot
    res.append(("Side slots never open to the soil", s1 < p.zt - p.fill,
                f"slot top {s1 - p.zt:+.3f}, loose fill bottom {-p.fill:+.3f} from mold top"))
    th_f, th_e = ps["fill"].theta, ps["eject"].theta
    res.append(("Yoke rests on the fixed pins to fill and eject", 5 < th_f < th_e < 85,
                f"fill {th_f:.1f} deg, eject {th_e:.1f} deg"))
    g = lambda th, zp: head_point(p, th, p.rho0 - th, zp, (p.handle_len, -p.handle_off))[1]
    gs = [g(th_f, p.zp_fill), g(th_e, p.zp_eject)]
    res.append(("Eject grip stays above the ground", min(gs) > 6, f"grip {gs[0]:.0f} in -> {gs[1]:.0f} in above the ground"))
    fe = max_eject_hand(p)
    res.append(("Eject hand force", fe < 175, f"{fe:.0f} lbf at {p.eject_force:,.0f} lbf to break the brick loose "
                                               f"(the piston travels {p.rise:g} in free before it reaches the brick)"))
    lift = max(standup_zp(p, p.theta_start + i * 0.25) for i in range(int((th_f - p.theta_start) * 4) + 1)) - p.zp_fill
    res.append(("Cam pin rides over the ramp into the scoop when the yoke stands up", lift < 1.5,
                f"piston lifts {lift:.3f} in as the pin climbs out of / into the scoop"))
    if not sweep:
        return res
    for key in ("start", "locked"):
        inst = assembly(p, key)
        pt = ps[key].zp + p.pin_below_cap
        cav = brick_solid(p, pt + 0.001, p.zt - pt - 0.002)
        h = _hits(inst, cav)
        res.append((f"Mold cavity clear ({key})", not h, "; ".join(f"{a} {v}" for a, v in h) or "nothing inside the mold"))
    bad = []
    for pose in list(ps.values()) + sweep_poses(p, n=6):
        bad += [f"{pose.name}: {a} x {b} ({v})" for a, b, v in interference(p, pose)]
    res.append(("All positions and motions clear", not bad, "; ".join(bad[:10]) or "clear"))
    worst = []
    for pose in sweep_poses(p, n=6):
        if not pose.name.startswith("eject"):
            continue
        inst = assembly(p, pose)
        pt = pose.zp + p.pin_below_cap
        if pt < p.zt - p.brick_h:
            continue
        worst += [f"{pose.name}: {a} {v}" for a, v in _hits(inst, brick_solid(p, pt), skip=("cap",))]
    res.append(("Brick rises out of the mold unobstructed", not worst, "; ".join(worst) or "clear at every step"))
    pe = ps["eject"].zp + p.pin_below_cap
    res.append(("Brick fully above the mold at eject", pe >= p.zt - 1e-6, f"brick bottom {pe - p.zt:+.3f} from mold top"))
    h = _hits(assembly(p, "eject"), brick_solid(p, pe + 0.01, p.brick_h + 18.0))
    res.append(("Brick lifts straight off (18 in)", not h, "; ".join(f"{a} {v}" for a, v in h) or "clear"))
    res += verify_feeder(p, ps)
    return res


FEED_MOVING = ("fbpin", "fblid", "fbstrike", "fbfunnel", "gate", "ghandle", "bhandle", "lug")
FEED_CLEAR = 0.25       # minimum running clearance, feeder to the head and yoke


def feed_slide_poses(p: Params, ps=None, n=8):
    import dataclasses
    f0 = (ps or poses(p))["fill"]
    out = [dataclasses.replace(f0, name=f"feed {i / n:.2f}", feed=i / n) for i in range(n + 1)]
    out += [dataclasses.replace(f0, name=f"gate {i / 4:.2f}", feed=1.0, gate=i / 4) for i in range(1, 5)]
    return out


def verify_feeder(p: Params, ps):
    """Feeder checks: capacity, stop, slide and gate travel clear of the head at fill, running clearances."""
    res = []
    cap, ch = feed_capacity(p), charge_volume(p)
    res.append(("Feed box holds a full charge", cap >= ch,
                f"{cap:,.0f} cu in above the gate = {cap / ch:.2f} loose charges of {ch:,.0f}"))
    lug_face = -(p.brick_w / 2 + FB_T + lug_len(p))
    eng = p.brick_w / 2 + FB_T + FB_TAIL - FEED_Y0
    res.append(("Feed box stops square over the mold", abs(lug_face + post_face(p)) < 1e-9 and eng >= 1.5,
                f"lug lands on the post at y {lug_face:.3f}; box inside {0:g}..{p.brick_l:g} = the mold; "
                f"tails {eng:.2f} in between the rails at full stroke"))
    open_edge = p.brick_w / 2 - GATE_STRIP
    res.append(("Knife gate opens the mold", p.brick_w / 2 - open_edge <= 0.25,
                f"open, the gate edge is {p.brick_w / 2 - open_edge:.3f} in short of the mold's far wall"))
    bad, dmin = [], {}
    press = {"cheek", "arm", "qpin", "campin", "xbar", "latch", "lbar", "lpin", "bridge", "htube"}
    for pose in feed_slide_poses(p, ps):
        bad += [f"{pose.name}: {a} x {b} ({v})" for a, b, v in interference(p, pose)]
        inst = assembly(p, pose)
        mv = [(k, s) for k, n, s in inst if k in FEED_MOVING]
        pr = [(k, s) for k, n, s in inst if k in press]
        for ka, sa in mv:
            bb = sa.bounding_box()
            for kb, sb in pr:
                b2 = sb.bounding_box()
                if (bb.max.X + 2 < b2.min.X or b2.max.X + 2 < bb.min.X or bb.max.Y + 2 < b2.min.Y
                        or b2.max.Y + 2 < bb.min.Y or bb.max.Z + 2 < b2.min.Z or b2.max.Z + 2 < bb.min.Z):
                    continue
                d = sa.distance_to(sb)
                if kb not in dmin or d < dmin[kb][0]:
                    dmin[kb] = (d, ka, pose.name)
    res.append(("Feed box slides and opens clear (fill)", not bad, "; ".join(bad[:6]) or "clear at every step"))
    worst = min(dmin.items(), key=lambda kv: kv[1][0]) if dmin else None
    res.append(("Feed box running clearance to the head and yoke", worst is None or worst[1][0] >= FEED_CLEAR,
                f"min {worst[1][0]:.3f} in, {worst[1][1]} to {worst[0]} at {worst[1][2]} (need {FEED_CLEAR:g})"
                if worst else "nothing within reach"))
    return res


def parse_brick(s: str):
    v = [float(x) for x in s.lower().replace('"', "").split("x")]
    if len(v) == 2:
        v.append(4.0)
    return dict(brick_l=v[0], brick_w=v[1], brick_h=v[2])


def summary(p: Params):
    ps = poses(p)
    return "\n".join([
        f"Simple CINVA-Ram {p.label} (his press x {p.sx:.3f} long, x {p.sy:.3f} wide, x {p.sz:.3f} tall): "
        f"fill {p.fill:.3f}, mold top {p.zt - p.zb:.3f} above the stand ({p.zt:.2f} above the ground)",
        f"  cam arm e {p.e:.4f}, yoke P-Q {p.yoke_len:.4f}, head {p.psi0:g} -> {p.psi_lock:g} deg, "
        f"fixed pins at {p.epin[1] - p.zb:.3f} up (his {HIS['fixed_pin'][1] * p.sz:.3f})",
        f"  piston force {p.f_work:,.0f} lbf at {p.p_work:g} psi -> peak hand force {p.peak_hand():.0f} lbf "
        f"({p.handle_len:g} in handle); design {p.f_design:,.0f} lbf at {p.p_design:g} psi",
        "  poses: " + ", ".join(f"{k} theta={v.theta:.1f}" for k, v in ps.items()),
    ])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="14x7x4")
    ap.add_argument("--step")
    ap.add_argument("--check", action="store_true", help="also run the collision sweeps")
    a = ap.parse_args()
    p = Params(**parse_brick(a.brick))
    print(summary(p))
    tot = sum(pt.weight(p) * pt.qty for pt in parts(p))
    print(f"  {len(parts(p))} part types, steel weight about {tot:.0f} lb")
    for item, basis, sig, allow in checks(p):
        print(f"  {item:34s} {sig / 1000:6.1f} ksi / {allow / 1000:5.1f}  {'ok' if sig <= allow else 'OVER'}  ({basis})")
    for name, ok, detail in verify(p, sweep=a.check):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if a.step:
        export_step(assembly_compound(p), a.step, unit=Unit.IN)


if __name__ == "__main__":
    main()


# ==========================================================
# Hooks for the drawing sheets (cinva_drawings.py --model simple) and the animation
# ==========================================================

TITLE = "Simple CINVA-Ram Press"
CHART_END = 0.0          # the stroke ends with the knee straight (head angle 0)
DWG_PREFIX = "SCR"
FILE_PREFIX = "Simple-CINVA-Ram"
OUT_PREFIX = "simple-"

POSITION_NOTES = [
    "Positions computed from the linkage; all four and the motions between them were checked for clearance.",
    "Yoke tilt from vertical toward the fixed pins; head angle = direction cam pin -> Q from vertical, positive "
    "toward the pull end; piston = piston top relative to the mold top.",
]

OPERATION = [
    "Start: latch shut, yoke leaning on the fixed pins, piston at the bottom, lid swung over onto the stand.",
    "Oil the mold. Shovel soil mix into the funnel (it holds about two charges). Push the feed box over the mold "
    "by the gate handle until its lug lands on the stop post. Hold the box handle and pull the gate open; tap the "
    "box. Push the gate shut (it shears the charge off level with the mold top) and pull the box back to park by "
    "its handle. Swing the lid back on by its horseshoe handle.",
    "Lift the handle and yoke upright together: the cam pin rides up the long leg of the ramps and drops into "
    "the scoops.",
    "Lift the latch bar to free the head. Pull the handle over toward the lid pivots until the head cheeks land "
    "on the rests, 3 deg past centre: the brick is pressed and the handle stays down.",
    "Raise the handle back past upright (the piston drops away from the brick), drop the latch over the cross "
    "bar, and tilt handle and yoke back onto the fixed pins.",
    "Lift the lid by its horseshoe handle and swing it over onto the stand. Push the handle down: the piston "
    "lifts the brick clear. Lift it off by its ends.",
    "Let the handle rise: the piston drops back to the bottom for the next fill.",
]

DESIGN_NOTES = [
    "First-order hand calculations; build one press and load-test before production.",
    "Allowables: A36 0.66 Fy bending, 0.5 Fu net tension; 4140 prehard 0.6 Fy; AR400 contact 0.3 p <= 0.5 Fy.",
    "Soil model: pressure rises as (e^5x - 1)/(e^5 - 1) over the stroke; lateral wall pressure 0.5 x vertical.",
    "Eject hand force assumes 1,000 lbf to break the brick loose; grease the scoops, pins and fixed pins.",
]


def press_data(p: Params, ps, mass):
    th_c = solve_theta(p, p.zp_comp)[1]
    return [
        ("Brick (pressed)", f"{p.brick_l:g} x {p.brick_w:g} x {p.brick_h:g} in, {p.area:g} sq in face"),
        ("Scale from his press", f"x {p.sx:.3f} long, x {p.sy:.3f} wide, x {p.sz:.3f} tall"),
        ("Loose fill depth", f"{p.fill:.3f} in (his 6-1/8); mold top {p.zt:.1f} in above the ground on a "
                             f"{p.base_h:g} in stand"),
        ("Working pressure", f"{p.p_work:g} psi = {p.f_work:,.0f} lbf on the piston"),
        ("Design (overfill) load", f"{p.p_design:g} psi = {p.f_design:,.0f} lbf, all parts checked"),
        ("Knee", f"cam arm {p.e:.3f}, head {p.psi0:g} to +{p.psi_lock:g} deg, yoke P-Q {p.yoke_len:.3f}"),
        ("Peak push on handle", f"{p.peak_hand(150):.0f} / {p.peak_hand(200):.0f} / {p.peak_hand(250):.0f} lbf "
                                f"at 150 / 200 / 250 psi ({p.handle_len:g} in handle)"),
        ("Ejection", f"piston rises {p.fill + p.eject_over:.3f} in; yoke tilts {ps['fill'].theta:.0f} to "
                     f"{ps['eject'].theta:.0f} deg; about {max_eject_hand(p):.0f} lbf on the handle"),
        ("Steel weight", "press about {:.0f} lb, feeder about {:.0f} lb".format(
            *(sum(pt.weight(p) * pt.qty for pt in parts(p) if (pt.group == "Feeder") == f) for f in (False, True)))),
        ("Feeder", f"{feed_capacity(p):,.0f} cu in = {feed_capacity(p) / charge_volume(p):.1f} loose charges; "
                   f"stroke {feed_park(p):.2f} in; gate travel {gate_travel(p):.3f} in"),
    ]


def _rail_x(self):
    return -self.t_end - 22.0, self.brick_l + self.t_end + 24.0


Params.rail_x = property(_rail_x)


def asm_view_dims(p: Params):
    L, W, te = p.brick_l, p.brick_w, p.t_end
    fx, fz = p.epin
    gx, gz = p.gpin
    return [
        ("F", (-te, 0, p.zb), (L + te, 0, p.zb), -10, True, None),
        ("F", (0, 0, p.zb), (L, 0, p.zb), -20, True, f"{L:.3f} MOLD"),
        ("F", (-te, 0, p.zb), (-te, 0, p.zt), -10, False, None),
        ("F", (-te, 0, p.zb), (fx, 0, fz), -20, False, None),
        ("F", (L + te, 0, p.zb), (gx, 0, gz), 10, False, None),
        ("F", (-te, 0, 0), (-te, 0, p.zb), -30, False, f"{p.zb:g} STAND"),
        ("L", (0, -W / 2, p.zt), (0, W / 2, p.zt), 20, True, f"{W:.3f} MOLD"),
    ]


GROUP_OF = {
    "side": "frame", "end": "frame", "foot": "frame", "fpin": "frame", "gpin": "frame",
    "lid": "lid", "ramp": "lid", "strap": "lid", "hrest": "lid", "lhandle": "lid",
    "cap": "piston", "web": "piston", "ppin": "piston",
    "arm": "yoke", "xbar": "yoke",
    "cheek": "handle", "qpin": "handle", "campin": "handle", "bridge": "handle", "htube": "handle",
    "lpin": "handle", "latch": "claw", "lbar": "claw",
    **{k: "frame" for k in ("fbpin", "fblid", "fbstrike", "fbfunnel", "gate", "ghandle", "bhandle", "lug",
                            "rail", "ntie", "ftie", "leg", "ltie", "bracket", "spost")},
}


def extra_meshes(p: Params):
    """(group, solid, rgb) not in the parts list: the stand the press bolts to."""
    x0 = -p.t_end - 2.0
    x1 = p.brick_l + p.t_end + STAND_OUT
    w = p.wall_out + 4.0
    return [("frame", Pos(x0, -w, 0) * Box(x1 - x0, 2 * w, p.zb, align=Align.MIN), (0.55, 0.42, 0.28))]


def anim_ref(p: Params):
    return Pose("reference", 0.0, p.psi0, p.zp_fill, 0.0, 0.0)


def anim_meta(p: Params):
    ref = anim_ref(p)
    (lx, lz), _, _ = latch_geom(p)
    cx, cz = head_point(p, ref.theta, ref.psi, ref.zp, (lx, lz))
    return dict(hinge=list(p.gpin), psi_ref=-(ref.psi + ref.theta), zp_ref=ref.zp,
                claw_pivot=[cx, cz], claw_open=LATCH_OPEN, claw_on="handle", title=TITLE)


def ease(s):
    return s * s * (3 - 2 * s)


def timeline(p: Params):
    """Phases (name, seconds, f(s) -> state) in the viewer's conventions (theta = -tilt, psi = -(head angle
    relative to the yoke)), and the phase roles."""
    ps = poses(p)
    th_f, th_e, th0 = ps["fill"].theta, ps["eject"].theta, p.theta_start
    ptop = lambda zp: zp + p.pin_below_cap
    brick_bot = p.zt - p.brick_h
    F = p.f_work
    lo = p.lid_open

    def st(th, psi, zp, cover, latch, bb, bt, force=0.0):
        return dict(theta=-th, psi=-(psi + th), zp=zp, cover=cover, latch=latch, bb=bb, bt=bt, force=force,
                    theta_show=th, psi_show=psi)

    def lat(th, zp, cover, latch, bb, bt):
        return st(th, p.rho0 - th, zp, cover, latch, bb, bt)

    def press(psi, bb=None, force=True):
        th, zp, _ = p.knee(psi)
        b = ptop(zp) if bb is None else bb
        return st(th, psi, zp, 0.0, LATCH_OPEN, b, p.zt, p._stroke_point(psi, F)[2] if force else 0.0)

    phases = [
        ("Fill the mold with loose soil mix", 2.5,
         lambda s: lat(th_f, p.zp_fill, lo, 0, ptop(p.zp_fill), ptop(p.zp_fill) + p.fill * ease(s))),
        ("Swing the lid back on by its handle", 1.5,
         lambda s: lat(th_f, p.zp_fill, lo * (1 - ease(s)), 0, ptop(p.zp_fill), p.zt)),
        ("Stand the yoke up: cam pin drops into the scoops", 1.8,
         lambda s: (lambda th: lat(th, standup_zp(p, th), 0, 0, ptop(standup_zp(p, th)), p.zt))(th_f + (th0 - th_f) * ease(s))),
        ("Lift the latch", 0.8,
         lambda s: lat(th0, p.zp_fill, 0, LATCH_OPEN * ease(s), ptop(p.zp_fill), p.zt)),
        ("Pull the handle over (pressing)", 4.0,
         lambda s: press(p.psi0 + (p.psi_lock - p.psi0) * ease(s))),
        ("Locked over centre: brick pressed to 4 in", 1.0,
         lambda s: press(p.psi_lock, force=False)),
        ("Raise the handle: piston drops away from the brick", 1.8,
         lambda s: press(p.psi_lock + (p.psi0 - p.psi_lock) * ease(s), bb=brick_bot, force=False)),
        ("Drop the latch over the cross bar", 0.8,
         lambda s: lat(th0, p.zp_fill, 0, LATCH_OPEN * (1 - ease(s)), brick_bot, p.zt)),
        ("Tilt handle and yoke back onto the fixed pins", 1.5,
         lambda s: (lambda th: lat(th, standup_zp(p, th), 0, 0, brick_bot, p.zt))(th0 + (th_f - th0) * ease(s))),
        ("Lift the lid by its handle and swing it over onto the stand", 1.5,
         lambda s: lat(th_f, p.zp_fill, lo * ease(s), 0, brick_bot, p.zt)),
        ("Push the handle down to eject the brick", 3.0,
         lambda s: (lambda th: (lambda zp: lat(th, zp, lo, 0, max(brick_bot, ptop(zp)),
                                               max(brick_bot, ptop(zp)) + p.brick_h))(eject_zp(p, th)))(th_f + (th_e - th_f) * ease(s))),
        ("Lift the brick off and stack it", 2.2,
         lambda s: lat(th_e, p.zp_eject, lo, 0, ptop(p.zp_eject), ptop(p.zp_eject) + p.brick_h)),
        ("Let the handle rise: piston drops for the next fill", 1.5,
         lambda s: (lambda th: lat(th, eject_zp(p, th), lo, 0, 0.0, 0.0))(th_e + (th_f - th_e) * ease(s))),
    ]
    return phases, dict(phase_press=4, phase_pressed=5, phase_lift=11)


def hinge_axis(p: Params):
    """Lid pivot (x, z), for the animation."""
    return p.gpin
