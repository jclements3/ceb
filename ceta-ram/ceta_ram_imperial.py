#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CETA-RAM Brick Making Machine — FreeCAD Parametric Model (IMPERIAL)

Based on: https://en.oho.wiki/wiki/Brick_Making_Machine_CETA-RAM_-_for_soil_bricks
Original design: CETA / OHO e.V. (CC-BY-SA 4.0)
Imperial conversion: standard US steel sizes

Run in FreeCAD: Macro → Execute Macro → select this file
Or from FreeCAD Python console: exec(open("ceta_ram_imperial.py").read())

All dimensions in mm internally (FreeCAD native), but derived from imperial sizes.
"""

import FreeCAD as App
import Part
import math

# ============================================================
# IMPERIAL TO MM CONVERSION
# ============================================================

def inch(x):
    """Convert inches to mm."""
    return x * 25.4

# ============================================================
# IMPERIAL STEEL SIZES (in inches, converted to mm at use)
# ============================================================

# Plate thicknesses
T_HALF  = 1/2       # 1/2" plate (replaces 13mm)
T_3_8   = 3/8       # 3/8" plate (replaces 10mm)
T_QTR   = 1/4       # 1/4" plate (replaces 6mm)

# Rod diameters
D_2_375 = 2 + 3/8   # 2-3/8" rod (replaces ∅60)
D_1_75  = 1 + 3/4   # 1-3/4" rod (replaces ∅44)
D_1_25  = 1 + 1/4   # 1-1/4" rod (replaces ∅32)
D_3_4   = 3/4       # 3/4" rod (replaces ∅20)
D_HALF  = 1/2       # 1/2" rod (replaces ∅12)

# Tube OD/ID pairs
T70_OD = 2 + 3/4;   T70_ID = D_2_375    # piston rod tube
T44_OD = D_1_75;    T44_ID = D_1_25     # piston rod 1
T50_OD = 2;          T50_ID = D_1_25     # support barrette bushing
T40_OD = 1 + 1/2;   T40_ID = D_3_4      # support structure tube
TCAP_OD = D_1_75;   TCAP_ID = D_1_25    # cap insurance

# Bolt holes
BOLT_CLEARANCE = 9/16   # clearance for 1/2" bolt
BOLT_TAP = 1/2          # tapped hole for 1/2" bolt

# C-channel C6x8.2
CHAN_WIDTH = 6
CHAN_DEPTH = 1 + 15/16   # ~1.92"
CHAN_WEB = 0.200
CHAN_FLANGE = 0.343

# ============================================================
# COLORS (R, G, B tuples)
# ============================================================

COL_STEEL = (0.7, 0.7, 0.75)
COL_ROD   = (0.6, 0.6, 0.65)
COL_WOOD  = (0.8, 0.6, 0.3)


def set_color(obj, rgb):
    """Set ViewObject color if GUI is available."""
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = rgb


def make_plate(name, length, width, thickness, parent=None):
    """Create a rectangular plate (box)."""
    box = Part.makeBox(inch(length), inch(width), inch(thickness))
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = box
    set_color(obj, COL_STEEL)
    return obj


def make_rod(name, diameter, length):
    """Create a solid cylindrical rod."""
    cyl = Part.makeCylinder(inch(diameter)/2, inch(length))
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = cyl
    set_color(obj, COL_ROD)
    return obj


def make_tube(name, od, id_, length):
    """Create a hollow tube."""
    outer = Part.makeCylinder(inch(od)/2, inch(length))
    inner = Part.makeCylinder(inch(id_)/2, inch(length))
    tube = outer.cut(inner)
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = tube
    set_color(obj, COL_ROD)
    return obj


def make_plate_with_holes(name, length, width, thickness, holes, color=COL_STEEL):
    """
    Create a plate with holes.
    holes: list of (x_inch, y_inch, diameter_inch) from plate origin
    """
    box = Part.makeBox(inch(length), inch(width), inch(thickness))
    for (hx, hy, hd) in holes:
        cyl = Part.makeCylinder(inch(hd)/2, inch(thickness) + 2)
        cyl.translate(App.Vector(inch(hx), inch(hy), -1))
        box = box.cut(cyl)
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = box
    set_color(obj, color)
    return obj


def make_c_channel(name, length):
    """Create a C6x8.2 channel section, length inches long."""
    L = inch(length)
    W = inch(CHAN_WIDTH)
    D = inch(CHAN_DEPTH)
    tw = inch(CHAN_WEB)
    tf = inch(CHAN_FLANGE)

    # Bottom flange
    flange = Part.makeBox(L, W, tf)
    # Left web
    web_l = Part.makeBox(L, tw, D)
    # Right web
    web_r = Part.makeBox(L, tw, D)
    web_r.translate(App.Vector(0, W - tw, 0))

    shape = flange.fuse(web_l).fuse(web_r)
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = shape
    set_color(obj, COL_STEEL)
    return obj


# ============================================================
# 1.0 STRUCTURE ASSEMBLY
# ============================================================

def make_structure():
    """Build Structure Assembly (1.0)."""
    parts = []

    # Dimensions
    side_length = 13 + 1/2   # 13-1/2"
    side_height = 8           # 8"
    base_width = 17           # 17"
    base_depth = 6            # 6"
    beam_length = 18          # 18"
    bars_length = 18          # 18"

    # 1.1 Side (x2) — 1/2" plate, 13-1/2" x 8"
    for i, y_off in enumerate([-(base_depth/2 + T_HALF/2), base_depth/2 - T_HALF/2]):
        side = make_plate(f"1.1_Side_{i+1}", T_HALF, side_length, side_height)
        x_off = -(base_width - side_length) / 2 - base_width/2
        side.Placement = App.Placement(
            App.Vector(inch(x_off), inch(y_off), inch(T_3_8)),
            App.Rotation(0, 0, 0))
        parts.append(side)

    # 1.2 Base structure — 3/8" plate, 17" x 6"
    base_holes = [
        (1+1/8, 1+1/4, BOLT_CLEARANCE),
        (1+1/8, base_depth - 1 - 1/4, BOLT_CLEARANCE),
        (base_width - 1 - 1/8, 1+1/4, BOLT_CLEARANCE),
        (base_width - 1 - 1/8, base_depth - 1 - 1/4, BOLT_CLEARANCE),
        (base_width - 3 - 1/8, base_depth/2, BOLT_TAP),
        (base_width - 5 - 1/2, base_depth/2, BOLT_TAP),
    ]
    base = make_plate_with_holes("1.2_Base_Structure", base_width, base_depth, T_3_8, base_holes)
    base.Placement = App.Placement(
        App.Vector(inch(-base_width/2), inch(-base_depth/2), 0),
        App.Rotation(0, 0, 0))
    parts.append(base)

    # 1.3 Beam 1 — C6x8.2, 18" long, with 3/4" hole
    beam1 = make_c_channel("1.3_Beam_1", beam_length)
    # Add hole at 7-1/8" from end, 1" up from bottom
    hole = Part.makeCylinder(inch(D_3_4)/2, inch(CHAN_WIDTH) + 2)
    hole.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90)
    hole.translate(App.Vector(inch(7+1/8), inch(CHAN_WIDTH) + 1, inch(1)))
    beam1.Shape = beam1.Shape.cut(hole)
    beam1.Placement = App.Placement(
        App.Vector(inch(-beam_length/2), inch(-base_depth/2), inch(T_3_8)),
        App.Rotation(0, 0, 0))
    parts.append(beam1)

    # 1.4 Beam 2 — C6x8.2, 18" long, no hole
    beam2 = make_c_channel("1.4_Beam_2", beam_length)
    beam2.Placement = App.Placement(
        App.Vector(inch(-beam_length/2), inch(-base_depth/2),
                   inch(T_3_8 + side_height - CHAN_DEPTH)),
        App.Rotation(0, 0, 0))
    parts.append(beam2)

    # 1.5 Cap insurance — 1-3/4" OD / 1-1/4" ID tube, 2-1/16" long
    cap_len = 2 + 1/16
    cap = make_tube("1.5_Cap_Insurance", TCAP_OD, TCAP_ID, cap_len)
    bars_top_z = T_3_8 + side_height + bars_length
    tube_top_z = bars_top_z + 1 + 7/16
    cap.Placement = App.Placement(
        App.Vector(0, 0, inch(tube_top_z)),
        App.Rotation(0, 0, 0))
    parts.append(cap)

    # 1.6 Cap insurance 1 — 1/4" plate, 2-1/16" x 1-9/16"
    cap1 = make_plate("1.6_Cap_Insurance_1", 2+1/16, 1+9/16, T_QTR)
    cap1.Placement = App.Placement(
        App.Vector(inch(-(2+1/16)/2), inch(-(1+9/16)/2),
                   inch(tube_top_z + cap_len)),
        App.Rotation(0, 0, 0))
    parts.append(cap1)

    # 1.7 Support structure (x2) — 1-1/2" OD / 3/4" ID tube, 1-7/16" long
    tube_len = 1 + 7/16
    side_offset = (base_width - side_length) / 2
    for i, x_pos in enumerate([
        -base_width/2 + side_offset + side_length/4,
        -base_width/2 + side_offset + 3*side_length/4
    ]):
        st = make_tube(f"1.7_Support_Structure_{i+1}", T40_OD, T40_ID, tube_len)
        st.Placement = App.Placement(
            App.Vector(inch(x_pos), 0, inch(bars_top_z)),
            App.Rotation(0, 0, 0))
        parts.append(st)

    # 1.8 Support structure 1 — 3/4" rod, 9-3/4" long
    rod_len = 9 + 3/4
    ss1 = make_rod("1.8_Support_Structure_1", D_3_4, rod_len)
    ss1.Placement = App.Placement(
        App.Vector(inch(rod_len/2), 0, inch(bars_top_z + tube_len/2)),
        App.Rotation(0, 90, 0))
    parts.append(ss1)

    # 1.9 Bars structure (x2) — 2-3/8" rod, 18" long
    for i, x_pos in enumerate([
        -base_width/2 + side_offset + side_length/4,
        -base_width/2 + side_offset + 3*side_length/4
    ]):
        bar = make_rod(f"1.9_Bars_Structure_{i+1}", D_2_375, bars_length)
        bar.Placement = App.Placement(
            App.Vector(inch(x_pos), 0, inch(T_3_8 + side_height)),
            App.Rotation(0, 0, 0))
        parts.append(bar)

    return parts


# ============================================================
# 2.0 TOP ASSEMBLY
# ============================================================

def make_top(z_offset=0):
    """Build Top Assembly (2.0)."""
    parts = []

    top_width = 16
    top_depth = 7
    top_support_length = 12
    top_support_width = 2
    bottom_top_len = 4 + 1/8
    bottom_top_1_len = 3 + 13/16
    bottom_top_1_w = 1
    hole_x = 1 + 1/8
    hole_y = 5 + 3/8

    # 2.1 Top — 3/8" plate, 16" x 7", 1-1/4" hole
    top = make_plate_with_holes("2.1_Top", top_width, top_depth, T_3_8,
                                [(hole_x, hole_y, D_1_25)])
    top.Placement = App.Placement(
        App.Vector(inch(-top_width/2), inch(-top_depth/2), inch(z_offset)),
        App.Rotation(0, 0, 0))
    parts.append(top)

    # 2.2 Top support (x2) — 1/2" plate, 12" x 2"
    # Simplified as rectangular bars (hook detail omitted for parametric clarity)
    for i, y_off in enumerate([
        -top_depth/2 + 3/4,
        top_depth/2 - 3/4 - top_support_width
    ]):
        ts = make_plate(f"2.2_Top_Support_{i+1}",
                        top_support_length, top_support_width, T_HALF)
        ts.Placement = App.Placement(
            App.Vector(inch(-top_support_length/2), inch(y_off),
                       inch(z_offset + T_3_8)),
            App.Rotation(0, 0, 0))
        parts.append(ts)

    # 2.3 Bottom top — 1-1/4" rod, 4-1/8" long
    bt = make_rod("2.3_Bottom_Top", D_1_25, bottom_top_len)
    bt.Placement = App.Placement(
        App.Vector(inch(-top_width/2 + hole_x), inch(-top_depth/2 + hole_y),
                   inch(z_offset - bottom_top_len)),
        App.Rotation(0, 0, 0))
    parts.append(bt)

    # 2.4 Bottom top 1 — 1/2" plate, 3-13/16" x 1"
    bt1 = make_plate("2.4_Bottom_Top_1", bottom_top_1_len, bottom_top_1_w, T_HALF)
    bt1.Placement = App.Placement(
        App.Vector(inch(-top_width/2 + hole_x - bottom_top_1_len/2),
                   inch(-top_depth/2 + hole_y - bottom_top_1_w/2),
                   inch(z_offset - bottom_top_len - T_HALF)),
        App.Rotation(0, 0, 0))
    parts.append(bt1)

    return parts


# ============================================================
# 3.0 PISTON ASSEMBLY
# ============================================================

def make_piston(z_offset=0):
    """Build Piston Assembly (3.0)."""
    parts = []

    pt_w = 12 + 5/8    # piston top width
    pt_d = 6            # piston top depth
    hole_sp = 3 + 1/16  # hole spacing
    hole_y = 3           # hole Y from edge
    rod_len = 10         # piston rod length
    rod1_len = 7 + 1/2   # piston rod 1 length
    caps_w = 8 + 1/2
    caps1_w = 12
    caps1_d = 1 + 1/2
    inner_h = 7 + 3/16

    # 3.1 Piston top — 3/8" plate, 12-5/8" x 6", 2x 2-3/4" holes
    pt_holes = [
        (pt_w/2 - hole_sp/2, hole_y, T70_OD),
        (pt_w/2 + hole_sp/2, hole_y, T70_OD),
    ]
    pt = make_plate_with_holes("3.1_Piston_Top", pt_w, pt_d, T_3_8, pt_holes)
    pt.Placement = App.Placement(
        App.Vector(inch(-pt_w/2), inch(-pt_d/2), inch(z_offset)),
        App.Rotation(0, 0, 0))
    parts.append(pt)

    # 3.4 Piston rod (x2) — 2-3/4" OD / 2-3/8" ID tube, 10" long
    for i, x_off in enumerate([-hole_sp/2, hole_sp/2]):
        pr = make_tube(f"3.4_Piston_Rod_{i+1}", T70_OD, T70_ID, rod_len)
        pr.Placement = App.Placement(
            App.Vector(inch(x_off), 0, inch(z_offset - rod_len)),
            App.Rotation(0, 0, 0))
        parts.append(pr)

    # 3.2 Piston caps (x2) — 3/8" plate, 8-1/2" x 6", 1-3/4" hole
    cap_holes = [(caps_w - D_1_75, hole_y, D_1_75)]
    for i, y_off in enumerate([-pt_d/2 - T_3_8, pt_d/2]):
        pc = make_plate_with_holes(f"3.2_Piston_Caps_{i+1}",
                                   caps_w, pt_d, T_3_8, cap_holes)
        # These are vertical plates — rotate 90° around X
        pc.Placement = App.Placement(
            App.Vector(inch(-pt_w/2), inch(y_off), inch(z_offset - inner_h)),
            App.Rotation(App.Vector(1, 0, 0), 90))
        parts.append(pc)

    # 3.3 Piston caps 1 (x2) — 3/8" plate, 12" x 1-1/2"
    for i, y_off in enumerate([-pt_d/2 - T_3_8, pt_d/2]):
        pc1 = make_plate(f"3.3_Piston_Caps_1_{i+1}", caps1_w, caps1_d, T_3_8)
        pc1.Placement = App.Placement(
            App.Vector(inch(-caps1_w/2), inch(y_off), inch(z_offset - T_3_8)),
            App.Rotation(0, 0, 0))
        parts.append(pc1)

    # 3.5 Piston rod 1 — 1-3/4" OD / 1-1/4" ID tube, 7-1/2" long
    pr1 = make_tube("3.5_Piston_Rod_1", T44_OD, T44_ID, rod1_len)
    pr1.Placement = App.Placement(
        App.Vector(0, 0, inch(z_offset - rod1_len)),
        App.Rotation(0, 0, 0))
    parts.append(pr1)

    return parts


# ============================================================
# 4.0 SUPPORT ASSEMBLY
# ============================================================

def make_support(z_offset=0):
    """Build Support Assembly (4.0)."""
    parts = []

    height = 25
    width = 2 + 1/2
    spacing = 10 + 1/2
    sp1_h = 8 + 3/16
    bot_hole = 1 + 1/2
    top_hole_from_top = 4 + 1/4
    bar_h = 2
    int_h = 5
    int_sp = 2 + 1/8
    top_section = 5 + 1/2
    axis_len = spacing

    # 4.1 Support piston (x2) — 1/2" plate, 25" x 2-1/2", 2x 1-1/4" holes
    sp_holes = [
        (width/2, bot_hole, D_1_25),
        (width/2, height - top_hole_from_top, D_1_25),
    ]
    for i, x_off in enumerate([-spacing/2 - T_HALF, spacing/2]):
        # These are tall vertical plates — make as width x height x thickness
        # then rotate
        sp = make_plate_with_holes(f"4.1_Support_Piston_{i+1}",
                                   T_HALF, width, height, [
                                       (T_HALF/2, width/2, D_1_25),  # won't work right
                                   ], COL_STEEL)
        # Simpler: make as box, cut holes manually
        box = Part.makeBox(inch(T_HALF), inch(width), inch(height))
        # Bottom hole
        h1 = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        h1.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
        h1.translate(App.Vector(-1, inch(width/2), inch(bot_hole)))
        # Top hole
        h2 = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        h2.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
        h2.translate(App.Vector(-1, inch(width/2), inch(height - top_hole_from_top)))
        shape = box.cut(h1).cut(h2)
        sp.Shape = shape
        sp.Placement = App.Placement(
            App.Vector(inch(x_off), inch(-width/2), inch(z_offset)),
            App.Rotation(0, 0, 0))
        parts.append(sp)

    # 4.2 Support piston 1 (x2) — 1/2" plate, 8-3/16" x 2-1/2"
    for i, x_off in enumerate([-spacing/2 - T_HALF, spacing/2]):
        sp1 = make_plate(f"4.2_Support_Piston_1_{i+1}", T_HALF, width, sp1_h)
        sp1.Placement = App.Placement(
            App.Vector(inch(x_off), inch(-width/2),
                       inch(z_offset + height - sp1_h)),
            App.Rotation(0, 0, 0))
        parts.append(sp1)

    # 4.3 Bar support (x2) — 1/2" plate, 2-1/2" x 2", 1-1/4" hole
    for i, x_off in enumerate([-spacing/2 - T_HALF - T_HALF, spacing/2 + T_HALF]):
        box = Part.makeBox(inch(T_HALF), inch(width), inch(bar_h))
        hole = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        hole.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
        hole.translate(App.Vector(-1, inch(width/2), inch(bar_h/2)))
        shape = box.cut(hole)
        bs = App.ActiveDocument.addObject("Part::Feature", f"4.3_Bar_Support_{i+1}")
        bs.Shape = shape
        set_color(bs, COL_STEEL)
        bs.Placement = App.Placement(
            App.Vector(inch(x_off), inch(-width/2), inch(z_offset)),
            App.Rotation(0, 0, 0))
        parts.append(bs)

    # 4.4 Axis support — 1-1/4" rod, 10-1/2" long
    ax = make_rod("4.4_Axis_Support", D_1_25, axis_len)
    ax.Placement = App.Placement(
        App.Vector(inch(axis_len/2), 0, inch(z_offset + bot_hole)),
        App.Rotation(0, 90, 0))
    parts.append(ax)

    # 4.5 Internal support (x2) — 1/2" plate, 5" x 2-1/2", 1-1/4" hole
    for i, x_off in enumerate([-int_sp/2 - T_HALF, int_sp/2]):
        box = Part.makeBox(inch(T_HALF), inch(width), inch(int_h))
        hole = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        hole.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
        hole.translate(App.Vector(-1, inch(width/2), inch(int_h - D_1_25)))
        shape = box.cut(hole)
        ins = App.ActiveDocument.addObject("Part::Feature", f"4.5_Internal_Support_{i+1}")
        ins.Shape = shape
        set_color(ins, COL_STEEL)
        ins.Placement = App.Placement(
            App.Vector(inch(x_off), inch(-width/2),
                       inch(z_offset + height - top_section)),
            App.Rotation(0, 0, 0))
        parts.append(ins)

    return parts


# ============================================================
# 5.0 LEVER ASSEMBLY
# ============================================================

def make_lever(z_offset=0, angle=45):
    """Build Lever Assembly (5.0)."""
    parts = []

    cb_len = 5 + 7/16
    cb_wid = 2 + 1/2
    bar_len = 17 + 3/4
    lever_arm = 14
    bar_length_5_2 = 9 + 7/16
    bar_length_5_3 = 6 + 11/16

    # 5.1 Cover bracket (x2) — 1/2" plate, 5-7/16" x 2-1/2", 2x 1-1/4" holes
    for i, z_off in enumerate([-T_HALF/2, T_HALF/2]):
        box = Part.makeBox(inch(cb_len), inch(cb_wid), inch(T_HALF))
        h1 = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        h1.translate(App.Vector(inch(D_1_25), inch(cb_wid/2), -1))
        h2 = Part.makeCylinder(inch(D_1_25)/2, inch(T_HALF) + 2)
        h2.translate(App.Vector(inch(cb_len - D_1_25), inch(cb_wid/2), -1))
        shape = box.cut(h1).cut(h2)
        cb = App.ActiveDocument.addObject("Part::Feature", f"5.1_Cover_Bracket_{i+1}")
        cb.Shape = shape
        set_color(cb, COL_STEEL)
        # Apply lever rotation
        cb.Placement = App.Placement(
            App.Vector(inch(-cb_len/2), inch(-cb_wid/2), inch(z_offset + z_off)),
            App.Rotation(App.Vector(0, 1, 0), -angle))
        parts.append(cb)

    # 5.8 Cover lever (x2) — 2"x2"x1/4" angle, 9-1/16" long
    cl_len = 9 + 1/16
    cl_leg = 2
    for i, y_off in enumerate([-cl_leg, cl_leg - T_QTR]):
        v_leg = Part.makeBox(inch(cl_len), inch(T_QTR), inch(cl_leg))
        h_leg = Part.makeBox(inch(cl_len), inch(cl_leg), inch(T_QTR))
        shape = v_leg.fuse(h_leg)
        cl = App.ActiveDocument.addObject("Part::Feature", f"5.8_Cover_Lever_{i+1}")
        cl.Shape = shape
        set_color(cl, COL_STEEL)
        cl.Placement = App.Placement(
            App.Vector(inch(-cl_len/2), inch(y_off), inch(z_offset + T_HALF/2)),
            App.Rotation(App.Vector(0, 1, 0), -angle))
        parts.append(cl)

    # 5.9 Bar lever — 1-3/4" rod, 17-3/4" long (handle)
    bl = make_rod("5.9_Bar_Lever", D_1_75, bar_len)
    # Position at top of lever arm, rotated
    rad = math.radians(angle)
    arm_x = -lever_arm * math.sin(rad)
    arm_z = lever_arm * math.cos(rad)
    bl.Placement = App.Placement(
        App.Vector(inch(arm_x), 0, inch(z_offset + arm_z)),
        App.Rotation(App.Vector(0, 1, 0), -angle))
    parts.append(bl)

    # 5.2 Barrette — 1-1/4" rod, 9-7/16" long (main pivot pin)
    bar52 = make_rod("5.2_Barrette", D_1_25, bar_length_5_2)
    bar52.Placement = App.Placement(
        App.Vector(0, 0, inch(z_offset - bar_length_5_2/2)),
        App.Rotation(0, 0, 0))
    # No rotation — pivot pin stays horizontal along Z (width axis)
    # Actually it should be along Y axis
    bar52.Placement = App.Placement(
        App.Vector(0, inch(-bar_length_5_2/2), inch(z_offset)),
        App.Rotation(App.Vector(1, 0, 0), 90))
    parts.append(bar52)

    # 5.3 Barrette 1 — 1-1/4" rod, 6-11/16" long
    bar53 = make_rod("5.3_Barrette_1", D_1_25, bar_length_5_3)
    bx = (cb_len/2 - D_1_25)
    bar53.Placement = App.Placement(
        App.Vector(inch(-bx * math.cos(rad)), inch(-bar_length_5_3/2),
                   inch(z_offset + bx * math.sin(rad))),
        App.Rotation(App.Vector(1, 0, 0), 90))
    parts.append(bar53)

    return parts


# ============================================================
# 6.0 PLATFORM ASSEMBLY
# ============================================================

def make_platform():
    """Build Platform Assembly (6.0)."""
    parts = []

    pl_len = 78 + 3/4
    pl_wid = 10 + 9/16
    pl_ht = 2 + 3/4
    pb_len = 15 + 3/4
    pb_wid = 6
    pb_ht = 2
    flat_len = 6
    flat_wid = 2 + 1/16

    offset_x = 8  # from left end

    # 6.2 Platform base (x3) — wood, 15-3/4" x 6" x 2"
    base_positions = [
        -offset_x,
        pl_len/2 - pb_len/2 - offset_x,
        pl_len - pb_len - offset_x,
    ]
    for i, xp in enumerate(base_positions):
        pb = make_plate(f"6.2_Platform_Base_{i+1}", pb_len, pb_wid, pb_ht)
        set_color(pb, COL_WOOD)
        pb.Placement = App.Placement(
            App.Vector(inch(xp), inch(-pb_wid/2), 0),
            App.Rotation(0, 0, 0))
        parts.append(pb)

    # 6.1 Platform — wood, 78-3/4" x 10-9/16" x 2-3/4"
    pl = make_plate("6.1_Platform", pl_len, pl_wid, pl_ht)
    set_color(pl, COL_WOOD)
    pl.Placement = App.Placement(
        App.Vector(inch(-offset_x), inch(-pl_wid/2), inch(pb_ht)),
        App.Rotation(0, 0, 0))
    parts.append(pl)

    # 6.3 Flat (x2) — 3/8" plate, 6" x 2-1/16", 2x 5/8" holes
    flat_holes = [
        (D_1_25, flat_wid/2, 5/8),
        (flat_len - D_1_25, flat_wid/2, 5/8),
    ]
    for i, x_extra in enumerate([4, 10]):
        fl = make_plate_with_holes(f"6.3_Flat_{i+1}",
                                   flat_len, flat_wid, T_3_8, flat_holes)
        fl.Placement = App.Placement(
            App.Vector(inch(pl_len/2 - pb_len/2 - offset_x + x_extra),
                       inch(-flat_wid/2),
                       inch(pb_ht + pl_ht)),
            App.Rotation(0, 0, 0))
        parts.append(fl)

    return parts


# ============================================================
# FULL ASSEMBLY
# ============================================================

def build_ceta_ram(lever_angle=45):
    """Build the complete CETA-RAM assembly."""

    # Create or reset document
    doc_name = "CETA_RAM_Imperial"
    if App.ActiveDocument and App.ActiveDocument.Name == doc_name:
        App.closeDocument(doc_name)
    doc = App.newDocument(doc_name)

    # Platform
    platform_parts = make_platform()

    # Vertical offsets
    platform_top = 2 + 2.75  # base_height + platform_height = 4.75"

    # Structure
    side_height = 8
    bars_length = 18
    tube_len = 1 + 7/16

    structure_x = (78 + 3/4) / 2 - 8  # center of platform - offset
    structure_z = platform_top

    # We need to offset all structure parts by structure_x along X and structure_z along Z
    # For simplicity, build at origin and note positions
    # The assembly functions place parts relative to their own origin
    # We'll add a global offset via group placement

    structure_parts = make_structure()
    for p in structure_parts:
        pl = p.Placement
        p.Placement = App.Placement(
            pl.Base + App.Vector(inch(structure_x), 0, inch(structure_z)),
            pl.Rotation)

    # Top assembly
    top_z = structure_z + T_3_8 + side_height + bars_length + tube_len
    top_parts = make_top(top_z)
    for p in top_parts:
        pl = p.Placement
        p.Placement = App.Placement(
            pl.Base + App.Vector(inch(structure_x), 0, 0),
            pl.Rotation)

    # Piston assembly
    piston_z = structure_z + T_3_8 + side_height - T_3_8
    piston_parts = make_piston(piston_z)
    for p in piston_parts:
        pl = p.Placement
        p.Placement = App.Placement(
            pl.Base + App.Vector(inch(structure_x), 0, 0),
            pl.Rotation)

    # Support assembly
    support_z = structure_z + T_3_8
    support_parts = make_support(support_z)
    for p in support_parts:
        pl = p.Placement
        p.Placement = App.Placement(
            pl.Base + App.Vector(inch(structure_x), 0, 0),
            pl.Rotation)

    # Lever assembly
    lever_pivot_z = support_z + 25 - (4 + 1/4)  # support_height - top_hole_from_top
    lever_parts = make_lever(lever_pivot_z, lever_angle)
    for p in lever_parts:
        pl = p.Placement
        p.Placement = App.Placement(
            pl.Base + App.Vector(inch(structure_x), 0, 0),
            pl.Rotation)

    doc.recompute()

    # Print summary
    print("\n" + "=" * 60)
    print("CETA-RAM Imperial Build Complete")
    print("=" * 60)
    print(f"Total parts: {len(doc.Objects)}")
    print(f"Lever angle: {lever_angle}°")
    print()
    print("IMPERIAL STEEL SIZES (order from supplier):")
    print("-" * 60)
    print(f"  1/2\" plate (ASTM A36):  sides, supports, brackets")
    print(f"  3/8\" plate (ASTM A36):  base, top, piston plates, flats")
    print(f"  1/4\" plate (ASTM A36):  cap plate, side levers")
    print(f"  C6x8.2 channel:         2 pcs @ 18\" long")
    print(f"  2-3/8\" round bar:       2 pcs @ 18\" long (main bars)")
    print(f"  1-3/4\" round bar:       1 pc @ 17-3/4\" (handle)")
    print(f"  1-1/4\" round bar:       pins/rods (multiple)")
    print(f"  3/4\" round bar:         1 pc @ 9-3/4\"")
    print(f"  1/2\" round bar:         1 pc @ 3-3/4\"")
    print(f"  2-3/4\" OD x 2-3/8\" ID tube: 2 pcs @ 10\"")
    print(f"  1-3/4\" OD x 1-1/4\" ID tube: 2 pcs (cap + piston rod 1)")
    print(f"  2\" OD x 1-1/4\" ID tube:     2 pcs @ 1-1/4\" (bushings)")
    print(f"  1-1/2\" OD x 3/4\" ID tube:   2 pcs @ 1-7/16\"")
    print(f"  2\"x2\"x1/4\" angle:      2 pcs @ 9-1/16\"")
    print(f"  1/2\"-13 bolts:          various lengths")
    print(f"  Kiln-dried wood:         78-3/4\" x 10-9/16\" x 2-3/4\"")
    print(f"                           3 pcs 15-3/4\" x 6\" x 2\" (bases)")
    print("=" * 60)

    return doc


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__" or App.ActiveDocument is not None:
    build_ceta_ram(lever_angle=45)
