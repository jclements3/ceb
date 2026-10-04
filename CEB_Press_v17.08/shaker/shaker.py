"""
OSE CEB soil shaker (hopper vibrator) of the OSE CEB Press 6 build, build123d model and ISO 128 drawing set.

Source: OSE "CEB a-z Build 1.0" manual, steps 3 (Shaker - Mount, pp. 15-17), 4 (Hammer and Shaft, pp. 18-19)
and 5 (Hydraulics), and the OSE 2015 weldment drawings 001-0042 (angle 21), 001-0043 (angle 8), 001-0044 /
001-0045 (hammer plates), 001-0046 (shaft), 001-0047 (brace rod), 001-0048 (Soil Shaker weldment) and 001-0077
(hammer weldment) in OSE/ceb_press_cnc_package/reference/weldment_drawings. Where the two disagree the
weldment drawing wins (it is the later, dimensioned one); the guard outline is from the manual (p. 15).

A hydraulic motor (Surplus Center 1-205-16-P-C class, 2-bolt SAE A flange) bolts through the 3-3/8 hole in
the 8 in angle; its shaft drives a 1 in shaft in a keyed coupler, and the 1 x 2 flat-bar hammer on the shaft
end knocks the hopper. The 21 in angle bolts to the hopper supports (3/4 bolts welded to them).

Units: inches. Mount frame: X along the 21 in angle, Y toward the hammer side, Z up.

Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/shaker/shaker.py [--no-pdf]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from build123d import Align, Box, Color, Compound, Pos, Rot, Unit, Vector, export_step  # noqa: E402

import cinva_drawings as D  # noqa: E402
from cinva_simple import COLORS, Part, _plate_dims, _rod_dims, hole, poly, rod  # noqa: E402

TITLE = "OSE CEB Soil Shaker"
DWG_PREFIX = "OSESH"
REVISIONS = {"A": ("2026-10-03", "Drawn from OSE CEB a-z Build 1.0 steps 3-4 and weldments 001-0042..0048, 0077")}
CURRENT_REV = "A"
ATTACHMENT_GROUPS = ()
OUT = os.path.join(HERE, "drawings")


class P:
    label = "shaker"


def angle(a, t, L, holes_v=(), holes_h=()):
    """a x a x t angle along X: horizontal leg in XY (y 0..a, z 0..t), vertical leg in XZ (y 0..t, z 0..a).
    holes_v: (x, z, d) through the vertical leg; holes_h: (x, y, d) through the horizontal leg."""
    s = Box(L, a, t, align=Align.MIN) + Box(L, t, a, align=Align.MIN)
    for x, z, d in holes_v:
        s -= Pos(x, -0.01, z) * Rot(-90, 0, 0) * rod(d, t + 0.02, "Z")
    for x, y, d in holes_h:
        s -= Pos(x, y, -0.01) * rod(d, t + 0.02, "Z")
    return s


# ---- 001-0042: 21 in L4x4x1/2, 4x 0.843 in the vertical leg (bolts to the hopper supports), 2x 0.562 in the
#      horizontal leg (to the 8 in angle) ----
A21_V = [(x, z, 0.843) for x in (1.25, 19.75) for z in (4.0 - 1.625, 4.0 - 3.125)]
A21_H = [(8.434, 3.0, 0.562), (12.567, 3.0, 0.562)]


def angle21(p):
    return angle(4.0, 0.5, 21.0, A21_V, A21_H)


# ---- 001-0043: 8 in L4x4x1/2: motor leg with the 3-3/8 pilot and 2x 0.562 flange bolts; the other leg 2x 0.437
#      to the 21 in angle ----
A8_V = [(4.0, 4.0 - 1.811, 3.375), (1.905, 4.0 - 1.811, 0.562), (6.095, 4.0 - 1.811, 0.562)]
A8_H = [(1.934, 3.5, 0.437), (6.067, 3.5, 0.437)]


def angle8(p):
    return angle(4.0, 0.5, 8.0, A8_V, A8_H)


def brace(p):                         # 001-0047: 1 in round x 7 (1 in rebar in the manual)
    return rod(1.0, 7.0, "X")


# ---- guard: 1/8 x 10 x 16 sheet, centred notch at the bottom over the hammer (manual p. 15) ----
GUARD = (16.0, 10.0, 0.125)
NOTCH = [(5.0, 0.0), (5.0, 0.75), (7.25, 3.0), (8.75, 3.0), (11.0, 0.75), (11.0, 0.0)]


def guard(p):
    w, h, t = GUARD
    pts = [(0.0, 0.0)] + NOTCH + [(w, 0.0), (w, h), (0.0, h)]
    return poly(pts, t)


def guard_side(p):                    # 1/4 x 2 x 2 angle x 10
    return angle(2.0, 0.25, 10.0)


def guard_top(p):                     # 1/4 x 2 x 2 angle x 16
    return angle(2.0, 0.25, 16.0)


# ---- hammer weldment 001-0077 ----
def hammer_arm(p):                    # 001-0044: 1 x 2 flat x 5, 1 in hole 1 in from the end
    return Box(5.0, 2.0, 1.0, align=Align.MIN) - hole(1.0, 1.0, 1.0, 1.0)


def hammer_head(p):                   # 001-0045: 1 x 2 flat x 6
    return Box(6.0, 2.0, 1.0, align=Align.MIN)


def shaft(p):                         # 001-0046: 1 in CRS x 7-1/4, 1/4 cross hole for the coupler bolt
    s = rod(1.0, 7.25, "X")
    return s - Pos(7.25 - 0.375, 0, -0.6) * rod(0.25, 1.2, "Z")


def parts(p):
    ps = [
        Part("a21", "Mount Angle 21", 1, 'L4 x 4 x 1/2 x 21', "gray", angle21, group="Mount",
             views=("F", "T", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (21.0, 0, 0), -10), ("V", "F", (21.0, 0, 0), (21.0, 0, 4.0), 10),
                             ("H", "F", (0, 0, 4.0), (1.25, 0, 2.375), 8), ("H", "F", (0, 0, 4.0), (19.75, 0, 2.375), 16),
                             ("V", "F", (0, 0, 4.0), (1.25, 0, 2.375), -10), ("V", "F", (0, 0, 4.0), (1.25, 0, 0.875), -18),
                             ("D", "F", (19.75, 0, 2.375), 0.843, 45, "4x ", 10),
                             ("H", "T", (0, 4.0, 0), (8.434, 3.0, 0), 8), ("H", "T", (0, 4.0, 0), (12.567, 3.0, 0), 16),
                             ("D", "T", (12.567, 3.0, 0), 0.562, 300, "2x ", 10)],
             notes=("OSE 001-0042. Bolts to the hopper supports on 3/4 bolts welded to them (a-z step 6).",
                    "Grind the top weld to the 8 in angle flush so the motor seats flat.")),
        Part("a8", "Motor Angle 8", 1, 'L4 x 4 x 1/2 x 8', "gray", angle8, group="Mount",
             views=("F", "T", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (8.0, 0, 0), -10), ("V", "F", (8.0, 0, 0), (8.0, 0, 4.0), 10),
                             ("H", "F", (0, 0, 4.0), (4.0, 0, 2.189), 8), ("H", "F", (0, 0, 4.0), (1.905, 0, 2.189), 16),
                             ("H", "F", (0, 0, 4.0), (6.095, 0, 2.189), 24), ("V", "F", (0, 0, 4.0), (4.0, 0, 2.189), -10),
                             ("D", "F", (4.0, 0, 2.189), 3.375, 60, "MOTOR PILOT ", 14),
                             ("D", "F", (6.095, 0, 2.189), 0.562, 300, "2x ", 10),
                             ("H", "T", (0, 4.0, 0), (1.934, 3.5, 0), 8), ("H", "T", (0, 4.0, 0), (6.067, 3.5, 0), 16),
                             ("D", "T", (6.067, 3.5, 0), 0.437, 300, "2x ", 10)],
             notes=("OSE 001-0043. Torch the pilot; the motor's raised centre must pass right through.",
                    "Manual p. 17 allows one shaped cutout for pilot and both bolts instead.")),
        Part("brace", "Brace Rod", 2, '1" round (or #8 rebar) x 7', "gray", brace, group="Mount",
             views=("F", "L"), front="-Y", flat=False, dims=lambda p: _rod_dims(1.0, 7.0),
             notes=("OSE 001-0047. Ends cut to fit; weld from the 8 in angle to the 21 in angle.",)),
        Part("guard", "Guard", 1, '1/8" sheet, 10 x 16', "orange", guard, group="Guard",
             dims=lambda p: [("H", "F", (0, 0, 0), (16.0, 0, 0), -10), ("V", "F", (16.0, 0, 0), (16.0, 10.0, 0), 10),
                             ("H", "F", (0, 10.0, 0), (5.0, 0, 0), 8), ("H", "F", (0, 10.0, 0), (7.25, 3.0, 0), 16),
                             ("H", "F", (0, 10.0, 0), (11.0, 0, 0), 24), ("V", "F", (0, 0, 0), (5.0, 0.75, 0), -10),
                             ("V", "F", (0, 0, 0), (7.25, 3.0, 0), -18), ("H", "L", (0, 0, 0), (0, 0, 0.125), -10)],
             notes=("Manual p. 15 (OSE 001-0074). Notch centred; it clears the hammer.",
                    "The guard catches the hammer if its weld fails: weld the frame angles all round.")),
        Part("gside", "Guard Side Angle", 2, 'L2 x 2 x 1/4 x 10', "orange", guard_side, group="Guard",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (10.0, 0, 0), -10), ("V", "F", (10.0, 0, 0), (10.0, 0, 2.0), 10)],
             notes=("OSE 001-0105.",)),
        Part("gtop", "Guard Top / Bottom Angle", 2, 'L2 x 2 x 1/4 x 16', "orange", guard_top, group="Guard",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: [("H", "F", (0, 0, 0), (16.0, 0, 0), -10), ("V", "F", (16.0, 0, 0), (16.0, 0, 2.0), 10)],
             notes=("OSE 001-0106. The bottom one welds to the 21 in angle.",)),
        Part("harm", "Hammer Arm", 1, '1 x 2 flat x 5', "red", hammer_arm, group="Hammer",
             dims=lambda p: _plate_dims(5.0, 2.0, [(1.0, 1.0, 1.0)], 1.0),
             notes=("OSE 001-0044. Weld to the hammer head 0.41 fillet both sides; it must not come off.",)),
        Part("hhead", "Hammer Head", 1, '1 x 2 flat x 6', "red", hammer_head, group="Hammer",
             dims=lambda p: _plate_dims(6.0, 2.0, (), 1.0), notes=("OSE 001-0045.",)),
        Part("shaft", "Shaft", 1, '1" CRS x 7-1/4', "red", shaft, group="Hammer",
             views=("F", "L"), front="-Y", flat=False,
             dims=lambda p: _rod_dims(1.0, 7.25) + [("H", "F", (7.25, 0, 0), (7.25 - 0.375, 0, 0), 10),
                                                    ("D", "F", (7.25 - 0.375, 0, 0), 0.25, 60, "THRU ", 10)],
             notes=("OSE 001-0046. Shaft end 1/4 short of the hammer arm's far face; 1/4 bolt hole drilled with the "
                    "coupler on, 3/8 from the coupler's edge (manual p. 19).",
                    "Coupler: 1 in keyed, cut to 2 long. Hammer 5/8 clear of the mount.")),
    ]
    for i, pt in enumerate(ps, 1):
        pt.item = i
    return ps


def assembly(p, pose=None, handle_len=None):
    """Arrangement per weldment 001-0048 sheet 2 (section): the two 4x4 angles welded flush in a Z, the 21 in
    angle's leg up (bolts to the hopper support), the 8 in angle's leg down and its pilot leg at the bottom;
    braces from the pilot leg to the 21 in angle; motor on the pilot leg, shaft down, hammer below; the guard
    on its 2x2 frame in front of the hammer. Motor and coupler not shown."""
    out = []
    add = lambda k, n, s: out.append((k, n, s))
    add("a21", "Mount Angle 21", angle21(p))
    x8 = 8.434 - 1.934                                   # 0.437 holes under the 21's 0.562 holes
    add("a8", "Motor Angle 8", Pos(x8, 0.5, -4.0) * Rot(90, 0, 0) * angle8(p))
    for x in (x8 + 1.0, x8 + 7.0):
        y0, z0, y1, z1 = -2.9, -3.5, 0.0, 2.9
        a = math.degrees(math.atan2(z1 - z0, y1 - y0))
        add("brace", "Brace Rod", Pos(x, y0, z0) * Rot(0, 0, 90) * Rot(0, -a, 0) * rod(1.0, 7.0, "X"))
    cx, cy = x8 + 4.0, 0.5 - (4.0 - 1.811)
    zt = -3.5 - 0.625                                    # shaft top: in the coupler under the pilot leg
    add("shaft", "Shaft", Pos(cx, cy, zt) * Rot(0, 90, 0) * shaft(p))
    zb = zt - 7.25 - 0.25
    add("harm", "Hammer Arm", Pos(cx - 1.0, cy - 1.0, zb) * hammer_arm(p))
    add("hhead", "Hammer Head", Pos(cx + 4.0, cy - 3.0, zb) * Rot(0, 0, 90) * Pos(0, -2.0, 0) * hammer_head(p))
    gy = cy - 7.5
    add("guard", "Guard", Pos(2.5, gy, -14.5) * Rot(90, 0, 0) * guard(p))
    add("gtop", "Guard Bottom Angle", Pos(2.5, gy, -14.5) * angle(2.0, 0.25, 16.0))
    add("gtop", "Guard Top Angle", Pos(2.5, gy, -4.5) * Rot(-90, 0, 0) * angle(2.0, 0.25, 16.0))
    add("gside", "Guard Side Angle", Pos(2.5, gy, -14.5) * Rot(0, -90, 0) * Rot(0, 0, 0) * angle(2.0, 0.25, 10.0).mirror(
        __import__("build123d").Plane.YZ).moved(__import__("build123d").Location((10.0, 0, 0))))
    add("gside", "Guard Side Angle", Pos(18.5, gy, -4.5) * Rot(0, 90, 0) * angle(2.0, 0.25, 10.0))
    return out


def asm_sheet(p, plist, n, path):
    sh = D.Sheet("A3")
    D.border(sh)
    inst = assembly(p)
    comp = Compound([s for _, _, s in inst])
    iv = D.View(Vector(1, -1, 0.8).normalized(), Vector(0, 0, 1))
    iv.up = (iv.up - iv.d * iv.up.dot(iv.d)).normalized()
    k = D.IN / 8
    area_x0, area_x1 = D.M_LEFT, sh.W - D.M_OTHER - D.TB_W
    pl = D._asm_view(sh, comp, iv, k, (area_x0 + area_x1) / 2, sh.H - D.M_OTHER - 40, hidden=False)
    D._view_label(sh, pl, "ISOMETRIC VIEW (ARRANGEMENT INDICATIVE)", below=20)
    D._balloons(sh, pl, inst, {pt.key: pt.item for pt in plist})
    notes = [f"Steel weight about {sum(pt.weight(p) * pt.qty for pt in plist):.0f} lb, less motor and coupler.",
             "Buy: hydraulic motor (2-bolt SAE A, 3-3/8 pilot), 1 in keyed coupler cut to 2 long, 1/4 x 2 bolt, "
             "1/2 NPT needle valve, tee, hoses per a-z step 5.",
             "Sources: OSE CEB a-z Build 1.0 pp. 15-20; OSE weldments 001-0042..0048, 001-0077."]
    room = sh.H - D.M_OTHER - (4.0 * len(D.note_lines(notes, D.TB_W - 4)) + 6) - (D.M_OTHER + D.TB_H)
    y = D._parts_list(sh, p, plist, rowh=min(5.5, room / (len(plist) + 1)))
    D.general_notes(sh, notes, y0=y)
    D.title_block(sh, TITLE, "Assembly", f"{DWG_PREFIX}-00", 1, n, "1:8", "See parts list", 1, "Assembly drawing",
                  key="assembly")
    sh.svg(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    D.m = sys.modules[__name__]
    p = P()
    plist = parts(p)
    sheets, dxf = os.path.join(OUT, "sheets"), os.path.join(OUT, "dxf")
    os.makedirs(sheets, exist_ok=True)
    os.makedirs(dxf, exist_ok=True)
    n = 1 + len(plist)
    paths = [os.path.join(sheets, "00_assembly.svg")]
    asm_sheet(p, plist, n, paths[0])
    man = [dict(key="assembly", sheet=1, file="00_assembly.svg")]
    for pt in plist:
        path = os.path.join(sheets, f"{pt.item:02d}_{pt.key}.svg")
        size, sc = D.part_sheet(p, pt, pt.item + 1, n, path, dxf)
        paths.append(path)
        man.append(dict(key=pt.key, item=pt.item, name=pt.name, sheet=pt.item + 1, file=os.path.basename(path),
                        size=size, scale=D.scale_str(sc), qty=pt.qty, stock=pt.stock, mass=round(pt.weight(p), 2)))
        print(f"  {pt.item:02d} {pt.name:26s} x{pt.qty} {pt.stock:30s} {size} {D.scale_str(sc)}")
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(dict(model=TITLE, sheets=man), f, indent=1)
    colors = {pt.key: pt.color for pt in plist}
    kids = []
    for key, name, s in assembly(p):
        s.label, s.color = name, Color(*COLORS[colors[key]])
        kids.append(s)
    export_step(Compound(children=kids, label=TITLE), os.path.join(OUT, "CEB_Shaker.step"), unit=Unit.IN)
    if not a.no_pdf:
        D.to_pdf(paths, os.path.join(OUT, "CEB_Shaker.pdf"))
        print(f"  {os.path.join(OUT, 'CEB_Shaker.pdf')}")


if __name__ == "__main__":
    main()
