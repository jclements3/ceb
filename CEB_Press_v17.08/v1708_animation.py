"""
Animation of the OSE CEB Press v17.08 with the a-z soil shaker, for the three.js viewer in animation/.

Geometry: OSE's FreeCAD assembly via v1708_drawings.load() (inches, world) and shaker/shaker.py assembly().
Motion (derived from the geometry, printed when run):
  * drawer (whole Drawer sub-assembly incl. its 34 in rods and rod holders, plus the secondary cylinder's rod
    and rod-end clevis) slides along Y; Y offset 0 = OSE's CAD pose;
  * ram (main cylinder rod, the stacked 4-1/4 .. 4-3/4 plates, the 5 x 10 plate and the 6 x 12 press foot)
    slides along Z; offset 0 = CAD pose (foot 0.3 below the table);
  * shaker hammer + shaft spin about the shaft; the shaker mount is fixed to the back right hopper support.
The two cylinders are single merged solids in OSE's file; they are split at the rod/barrel shoulder found by
sectioning (main cylinder z 15.85, secondary cylinder y 13.3). A plain rod is added behind each split so the
rod stays continuous inside the barrel when it extends.

Cycle (OSE v17.08 controller order): ram down to load (soil drops from the hopper through the drawer's open
cavity, shaker running), drawer to the compress position (its closed block over the chamber), ram up
(compress), drawer to the eject position (open-bottomed end over the chamber), ram up flush (eject), drawer
back to fill (the block's wall pushes the brick out onto the -Y table), brick lifted off.

Writes animation/press.json. Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/v1708_animation.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "shaker"))

FPS = 30
OUT = os.path.join(HERE, "animation", "press.json")

# ---- derived geometry (inches, world; checked by derive() below) ----
CHAMBER = (14.2, 26.1, -12.5, -6.5)       # x0, x1, y0, y1: frame liners / end walls
TABLE_Z = 28.1                             # top of the frame table plates the drawer slides on
DRAWER_BOTTOM = 28.2                       # underside of the drawer block (the brick's top face when pressing)
FOOT_CAD = 27.8                            # press-foot top in OSE's CAD pose
MAIN_SPLIT = 15.85                         # main cylinder: barrel below, 2.75 rod above
SEC_SPLIT = 13.3                           # secondary cylinder: 1-1/8 rod + clevis at -Y, barrel at +Y
# drawer offsets (Y) for each station, from the drawer's own walls in the CAD pose:
#   open cavity (between walls at y -11.8..-11.3 and -5.3..-4.8) -> y -11.3..-5.3
#   closed block (bottom plate y -17.7..-11.7, top plate above)   -> centre -14.7
#   open-bottomed end under the long top plate                    -> y < -18.3
D_FILL = CHAMBER[2] - (-11.3)              # cavity over the chamber: -1.2
D_PRESS = (CHAMBER[2] + CHAMBER[3]) / 2 - (-17.7 + -11.7) / 2     # block centred: +5.2
D_EJECT = CHAMBER[3] - (-18.3)             # block's -Y wall just past the chamber's +Y wall: +11.8
PUSH_WALL = -18.3                          # block's -Y wall face (pushes the brick out toward -Y)
# ram: foot top heights
FOOT_LOAD = 21.1                           # 7.0 in of loose fill to the table
BRICK_H = 4.0                              # pressed block: 6 x 12 x 4
FOOT_PRESS = DRAWER_BOTTOM - BRICK_H       # 24.2
FOOT_EJECT = round(TABLE_Z + 0.05, 3)               # brick bottom just above the table: it slides off
# shaker: mount bolted to the -X face of the back right hopper support (x 32.9..34.9, y 12.7..14.7);
# its first 0.843 bolt hole on the support's centre line
SHAKER_POS = (32.9, 13.7 - 1.25, 46.5)
SHAKER_ROT_Z = 90.0                        # local X -> world +Y, local Y -> world -X
SHAFT_LOCAL = (6.5 + 4.0, 0.5 - (4.0 - 1.811))


def shaker_world(lx, ly, lz=0.0):
    x0, y0, z0 = SHAKER_POS
    return x0 - ly, y0 + lx, z0 + lz


GROUP_COLORS = {}


def _load():
    import v1708_drawings as V
    return V.load()


def build_group(name):
    """[(solid, rgb)] for one viewer group, in world coordinates (CAD pose)."""
    from build123d import Box, Pos, Align, Rot
    import v1708_drawings as V
    from cinva_simple import COLORS, rod
    subs = {n: (rgb, sols) for n, rgb, sols in V.load()}
    out = []
    big = lambda: Box(200, 200, 200, align=Align.CENTER)
    if name == "frame":
        for n in ("Frame", "Arms", "Hopper Seat"):
            rgb, sols = subs[n]
            out += [(s, rgb) for s in sols]
        rgb, sols = subs["Main Cylinder"]
        barrel = max(sols, key=lambda s: s.volume)
        out.append((barrel & (Pos(0, 0, MAIN_SPLIT - 100) * big()), rgb))
        out += [(s, rgb) for s in sols if s.bounding_box().max.Z < 1.0]           # clevis, pin, bushings
        rgb, sols = subs["Secondary Cylinder"]
        cyl = max(sols, key=lambda s: s.volume)
        out.append((cyl & (Pos(0, SEC_SPLIT + 100, 0) * big()), rgb))
        out += [(s, rgb) for s in sols if s is not cyl]                          # far-end pin
    elif name == "hopper":
        for n in ("Hopper", "Grate"):
            rgb, sols = subs[n]
            out += [(s, rgb) for s in sols]
    elif name == "drawer":
        rgb, sols = subs["Drawer"]
        out += [(s, rgb) for s in sols]
        rgb, sols = subs["Secondary Cylinder"]
        cyl = max(sols, key=lambda s: s.volume)
        out.append((cyl & (Pos(0, SEC_SPLIT - 100, 0) * big()), rgb))
        b = cyl.bounding_box()
        cx, cz = (b.min.X + b.max.X) / 2, (b.min.Z + b.max.Z) / 2
        out.append((Pos(cx, SEC_SPLIT - 0.05, cz) * Rot(-90, 0, 0) * rod(1.125, 13.0, "Z"), rgb))
    elif name == "ram":
        rgb, sols = subs["Main Cylinder"]
        barrel = max(sols, key=lambda s: s.volume)
        out.append((barrel & (Pos(0, 0, MAIN_SPLIT + 100) * big()), rgb))
        out += [(s, rgb) for s in sols if s.bounding_box().min.Z > 24.0]
        b = barrel.bounding_box()
        cx, cy = (b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2
        out.append((Pos(cx, cy, MAIN_SPLIT - 8.0 + 0.05) * rod(2.75, 8.0, "Z"), rgb))
    elif name in ("shaker", "hammer"):
        import shaker as SH
        cols = {pt.key: COLORS[pt.color] for pt in SH.parts(SH.P())}
        moving = {"shaft", "harm", "hhead"}
        x0, y0, z0 = SHAKER_POS
        for key, _, s in SH.assembly(SH.P()):
            if (key in moving) == (name == "hammer"):
                out.append((Pos(x0, y0, z0) * Rot(0, 0, SHAKER_ROT_Z) * s, cols[key]))
    return out


def mesh_group(name):
    verts_all, idx_all, col_all = [], [], []
    for s, rgb in build_group(name):
        if s is None or s.volume < 1e-6:
            continue
        verts, tris = s.tessellate(0.01, 0.15)
        base = len(verts_all) // 3
        for v in verts:
            verts_all += [round(v.X, 3), round(v.Y, 3), round(v.Z, 3)]
            col_all += [round(c, 3) for c in rgb]
        for t in tris:
            idx_all += [base + i for i in t]
    return dict(name=name, positions=verts_all, indices=idx_all, colors=col_all)


def derive():
    """Re-check the derived stations against the solids and print them."""
    from build123d import Box, Pos, Align, Compound
    import v1708_drawings as V
    subs = {n: sols for n, _, sols in V.load()}
    fr = Compound(subs["Frame"]).bounding_box()
    print(f"frame x {fr.min.X:.2f}..{fr.max.X:.2f}  top z {fr.max.Z:.2f}")
    print(f"chamber x {CHAMBER[0]}..{CHAMBER[1]}  y {CHAMBER[2]}..{CHAMBER[3]}  table z {TABLE_Z}  "
          f"drawer underside z {DRAWER_BOTTOM}")
    print(f"drawer stations (Y offset from CAD): fill {D_FILL:+.2f}  press {D_PRESS:+.2f}  eject {D_EJECT:+.2f}  "
          f"(stroke {D_EJECT - D_FILL:.2f}; secondary rod visible {SEC_SPLIT - (-0.7):.1f} in in CAD)")
    print(f"ram foot top: load {FOOT_LOAD}  pressed {FOOT_PRESS}  eject {FOOT_EJECT}  CAD {FOOT_CAD}  "
          f"(stroke {FOOT_EJECT - FOOT_LOAD:.2f}; rod visible {25.2 - MAIN_SPLIT:.2f} in CAD)")
    print(f"loose fill {TABLE_Z - FOOT_LOAD:.2f} -> brick {BRICK_H} (ratio {(TABLE_Z - FOOT_LOAD) / BRICK_H:.2f})")
    # collision checks at the stations
    def inter(a, b):
        hits = []
        for i, (sa, _) in enumerate(a):
            ba = sa.bounding_box()
            for sb, _ in b:
                bb = sb.bounding_box()
                if (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y
                        or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z):
                    continue
                r = sa & sb
                v = r.volume if r is not None else 0.0
                if v > 0.01:
                    hits.append(round(v, 3))
        return hits
    frame = build_group("frame") + build_group("hopper")
    drawer = build_group("drawer")
    for d in (D_FILL, D_PRESS, D_EJECT):
        moved = [(Pos(0, d, 0) * s, c) for s, c in drawer]
        h = inter(moved, frame)
        print(f"  drawer at {d:+.2f}: {len(h)} overlaps with frame/hopper, total {sum(h):.3f} cu in")
    ram = build_group("ram")
    for f in (FOOT_LOAD, FOOT_EJECT):
        moved = [(Pos(0, 0, f - FOOT_CAD) * s, c) for s, c in ram]
        h = inter(moved, frame)
        print(f"  ram foot at {f}: {len(h)} overlaps with frame, total {sum(h):.3f} cu in")
    sk = build_group("shaker") + build_group("hammer")
    h = inter(sk, frame + build_group("drawer"))
    print(f"  shaker: {len(h)} overlaps with the press, total {sum(h):.3f} cu in")


def ease(s):
    return s * s * (3 - 2 * s)


def timeline():
    """Phases: (name, seconds, f(s) -> state). State: drawer, ram (offsets from CAD), spin (deg/frame flag),
    soil boxes [(x0,x1,y0,y1,z0,z1,kind)], kind 0 loose, 1 pressed."""
    x0, x1, y0, y1 = CHAMBER
    cav = lambda d: (x0, x1, -11.3 + d, -5.3 + d)          # drawer's open cavity at offset d
    loose, pressed = 0, 1

    def st(d, foot, shaker, boxes, note=""):
        return dict(drawer=d, ram=foot - FOOT_CAD, foot=foot, shaker=shaker, boxes=boxes)

    throat = (x0, x1, y0, y1, 34.2, 40.1, loose)            # soil standing in the hopper throat

    def cavity(d):
        a, b, c, e = cav(d)
        return (a, b, c, e, DRAWER_BOTTOM + 0.5, 34.1, loose)

    brick_out = lambda yb: (x0, x1, yb - 6.0, yb, TABLE_Z, TABLE_Z + BRICK_H, pressed)
    phases = [
        ("Ram drops to load: soil falls from the hopper through the drawer (shaker on)", 3.0,
         lambda s: (lambda f: st(D_FILL, f, 1, [throat, cavity(D_FILL), (x0, x1, y0, y1, f, TABLE_Z, loose)]))(
             FOOT_EJECT + (FOOT_LOAD - FOOT_EJECT) * ease(s))),
        ("Drawer slides over: its closed block covers the chamber", 2.0,
         lambda s: (lambda d: st(d, FOOT_LOAD, 0, [throat, cavity(d), (x0, x1, y0, y1, FOOT_LOAD, TABLE_Z, loose)]))(
             D_FILL + (D_PRESS - D_FILL) * ease(s))),
        (f"Main cylinder compresses the block to {BRICK_H:g} in", 3.0,
         lambda s: (lambda f: st(D_PRESS, f, 0, [throat, cavity(D_PRESS),
                                                 (x0, x1, y0, y1, f, DRAWER_BOTTOM, loose if s < 1 else pressed)]))(
             FOOT_LOAD + (FOOT_PRESS - FOOT_LOAD) * ease(s))),
        ("Drawer moves on: its open end over the chamber", 1.8,
         lambda s: (lambda d: st(d, FOOT_PRESS, 0, [throat, cavity(d), (x0, x1, y0, y1, FOOT_PRESS, DRAWER_BOTTOM, pressed)]))(
             D_PRESS + (D_EJECT - D_PRESS) * ease(s))),
        ("Main cylinder raises the brick flush with the table", 2.0,
         lambda s: (lambda f: st(D_EJECT, f, 0, [throat, cavity(D_EJECT), (x0, x1, y0, y1, f, f + BRICK_H, pressed)]))(
             FOOT_PRESS + (FOOT_EJECT - FOOT_PRESS) * ease(s))),
        ("Drawer returns to fill: its block pushes the brick out onto the table", 2.6,
         lambda s: (lambda d: st(d, FOOT_EJECT, 0, [throat, cavity(d),
                                                    brick_out(min(y1, PUSH_WALL + d))]))(
             D_EJECT + (D_FILL - D_EJECT) * ease(s))),
        ("Lift the brick off and stack it", 2.0,
         lambda s: st(D_FILL, FOOT_EJECT, 0, [throat, cavity(D_FILL), brick_out(PUSH_WALL + D_FILL)])),
    ]
    return phases


def main():
    if "--no-derive" not in sys.argv:
        derive()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    names = ["frame", "hopper", "drawer", "ram", "shaker", "hammer"]
    with mp.get_context("spawn").Pool(4) as pool:
        groups = pool.map(mesh_group, names)
    phases = timeline()
    frames = []
    spin = 0.0
    for i, (nm, dur, fn) in enumerate(phases):
        n = max(2, round(dur * FPS))
        for k in range(n):
            s = k / (n - 1)
            d = fn(s)
            if d["shaker"]:
                spin = (spin + 360.0 * 1500 / 60 / FPS / 25) % 360.0     # ~1500 rpm shown 25x slowed
            boxes = [[round(v, 3) for v in b] for b in d["boxes"]]
            frames.append([i, round(s, 4), round(d["drawer"], 4), round(d["ram"], 4), round(spin, 2),
                           round(d["foot"], 3), boxes])
    sx, sy, sz = shaker_world(*SHAFT_LOCAL)
    meta = dict(
        title="OSE CEB Press v17.08 with soil shaker", label="6 × 12 × 4", fps=FPS,
        motions={"drawer": dict(type="translate", axis=[0, 1, 0], col="drawer"),
                 "ram": dict(type="translate", axis=[0, 0, 1], col="ram"),
                 "hammer": dict(type="rotate", axis=[0, 0, 1], origin=[sx, sy, sz], col="spin")},
        stations=dict(drawer_fill=D_FILL, drawer_press=D_PRESS, drawer_eject=D_EJECT,
                      foot_load=FOOT_LOAD, foot_press=FOOT_PRESS, foot_eject=FOOT_EJECT, table=TABLE_Z),
        brick=[CHAMBER[1] - CHAMBER[0], CHAMBER[3] - CHAMBER[2], BRICK_H],
        view_target=[22.0, 0.0, 38.0], views=dict(iso=[-82.0, -140.0, 112.0], front=[20.0, -150.0, 40.0],
                                                   side=[-120.0, -6.0, 40.0], top=[20.0, -5.0, 190.0], back=[105.0, 120.0, 95.0]),
        notes=["Geometry: OSE CEB_17.08_CAD_Assembly.fcstd. Cylinders split at the rod shoulder; a plain rod "
               "continues each rod inside its barrel.",
               "Drawer stations and ram strokes derived from the drawer walls, chamber liners and table plates; "
               f"loose fill {TABLE_Z - FOOT_LOAD:.1f} in to a {BRICK_H:g} in block is indicative.",
               "Shaker (OSE a-z Build 1.0) placed indicatively on the back right hopper support; the spinning "
               "hammer is an eccentric that shakes the hopper through the support."])
    data = dict(meta=meta, phases=[p[0] for p in phases],
                columns=["phase", "s", "drawer", "ram", "spin", "foot", "boxes"], frames=frames, groups=groups)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    nv = sum(len(g["positions"]) // 3 for g in groups)
    print(f"wrote {OUT}: {len(frames)} frames ({len(frames) / FPS:.1f} s), {nv:,} vertices, "
          f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
