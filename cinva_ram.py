"""
CINVA-Ram Block Press — FreeCAD Solid Model Generator

All dimensions from engineering drawings (cinva1-7.jpg).
Material: 1/4" (0.250") steel plate throughout.

Usage: Run as a FreeCAD macro or paste into the FreeCAD Python console.
Parts are created at the origin; reposition as needed for assembly.
"""

import FreeCAD as App
import Part
from FreeCAD import Vector
import math

# --- Constants ---
IN = 25.4         # mm per inch
T = 0.250 * IN    # plate thickness (1/4")


# --- Document ---
doc = App.newDocument("CINVA_Ram")


def add(name, shape):
    """Add a solid shape to the document as a Part::Feature."""
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj


# ==============================================================
# SHEET 1 — Mold Box Walls (Part C)
#
# 2x side walls:  7.250 x 6.000  with 1.000" pivot hole
# 1x end wall:    6.000 x 11.500
# 1x end wall:    6.500 x 12.000
# ==============================================================

for i in range(2):
    box = Part.makeBox(7.250 * IN, 6.000 * IN, T)
    hole = Part.makeCylinder(
        0.500 * IN, T,
        Vector(6.250 * IN, 3.000 * IN, 0))
    add(f"C_SideWall_{i+1}", box.cut(hole))

add("C_EndWall_Short", Part.makeBox(6.000 * IN, 11.500 * IN, T))
add("C_EndWall_Tall", Part.makeBox(6.500 * IN, 12.000 * IN, T))


# ==============================================================
# SHEET 2 — Toggle Links
#
# 2x long:  2.000 x 3.625, hole 1.250" from bottom
# 2x short: 2.000 x 3.000, hole 0.750" from bottom
# All have R0.375" rounded bottom corners, 1.000" dia hole
# ==============================================================

def toggle_link(width, height, hole_y_from_bottom):
    """Flat link with rounded bottom corners and 1" pivot hole."""
    w = width * IN
    h = height * IN
    r = 0.375 * IN
    hr = 0.500 * IN  # 1" dia / 2

    edges = [
        Part.makeLine(Vector(0, h, 0), Vector(0, r, 0)),
        Part.makeCircle(r, Vector(r, r, 0), Vector(0, 0, 1), 180, 270),
        Part.makeLine(Vector(r, 0, 0), Vector(w - r, 0, 0)),
        Part.makeCircle(r, Vector(w - r, r, 0), Vector(0, 0, 1), 270, 360),
        Part.makeLine(Vector(w, r, 0), Vector(w, h, 0)),
        Part.makeLine(Vector(w, h, 0), Vector(0, h, 0)),
    ]
    wire = Part.Wire(edges)
    face = Part.Face(wire)
    solid = face.extrude(Vector(0, 0, T))

    hole = Part.makeCylinder(hr, T, Vector(w / 2, hole_y_from_bottom * IN, 0))
    return solid.cut(hole)


for i in range(2):
    add(f"ToggleLink_Long_{i+1}", toggle_link(2.000, 3.625, 1.250))

for i in range(2):
    add(f"ToggleLink_Short_{i+1}", toggle_link(2.000, 3.000, 0.750))


# ==============================================================
# SHEET 3 — Lever Latch (Part M)
#
# 2x L-shaped bracket: 4.147 x 1.035, step notch, 7/16" hole
# 1x spacer:           1.000 x 2.750
# ==============================================================

def latch_bracket():
    """L-shaped latch bracket: raised tab on left, main bar on right."""
    w = 4.147 * IN
    h = 1.035 * IN      # full height at tab
    bar_h = 0.518 * IN   # main bar height
    tab_w = 0.625 * IN   # tab width

    pts = [
        Vector(0, 0, 0),
        Vector(w, 0, 0),
        Vector(w, bar_h, 0),       # right side, bar height
        Vector(tab_w, bar_h, 0),   # step down to bar top
        Vector(tab_w, h, 0),       # up to full tab height
        Vector(0, h, 0),           # across tab top
    ]
    lines = [Part.makeLine(pts[i], pts[(i + 1) % len(pts)])
             for i in range(len(pts))]
    wire = Part.Wire(lines)
    face = Part.Face(wire)
    solid = face.extrude(Vector(0, 0, T))

    hole = Part.makeCylinder(
        0.437 / 2 * IN, T,
        Vector(w - 0.500 * IN, h - 0.397 * IN, 0))
    return solid.cut(hole)


for i in range(2):
    add(f"M_LatchBracket_{i+1}", latch_bracket())

add("M_LatchSpacer", Part.makeBox(1.000 * IN, 2.750 * IN, T))


# ==============================================================
# SHEET 4 — Handle (Part N) and Cross Bars
#
# 2x handle bar:     19.625 x 2.000, 1" hole at 1.000" from end
# 1x upper cross bar: 11.000 x 2.000
# 1x lower cross bar:  8.000 x 2.000
# ==============================================================

for i in range(2):
    box = Part.makeBox(19.625 * IN, 2.000 * IN, T)
    hole = Part.makeCylinder(
        0.500 * IN, T,
        Vector(1.000 * IN, 1.000 * IN, 0))
    add(f"N_HandleBar_{i+1}", box.cut(hole))

add("N_CrossBar_Upper", Part.makeBox(11.000 * IN, 2.000 * IN, T))
add("N_CrossBar_Lower", Part.makeBox(8.000 * IN, 2.000 * IN, T))


# ==============================================================
# SHEET 5 — Cover (Part A)
#
# Bent V-shape plate, 12.000" span
# Left leg 6.038", right leg 4.810"
# Flat edges: 0.250" (left), 1.000" (right)
# R0.625" semicircular notch at V bottom
# ==============================================================

def cover():
    """Bent V-shape cover. Two tilted plates fused, notch cut."""
    span = 12.000 * IN
    left_flat = 0.250 * IN
    right_flat = 1.000 * IN
    left_leg = 6.038 * IN
    right_leg = 4.810 * IN
    notch_r = 0.625 * IN
    depth_y = 6.500 * IN  # cover depth, approx from mold box end wall

    # Solve V geometry: both legs drop to same depth
    angled_span = span - left_flat - right_flat
    left_dx = (angled_span + (left_leg**2 - right_leg**2) / angled_span) / 2.0
    right_dx = angled_span - left_dx
    v_drop = math.sqrt(max(left_leg**2 - left_dx**2, 0))
    v_x = left_flat + left_dx  # X position of V bottom

    # Left plate: slopes from (0, z=v_drop) down to (v_x, z=0)
    left_hyp = math.sqrt(v_x**2 + v_drop**2)
    left_ang = math.degrees(math.atan2(v_drop, v_x))

    left_plate = Part.makeBox(left_hyp, depth_y, T)
    left_plate.rotate(Vector(0, 0, 0), Vector(0, 1, 0), -left_ang)
    left_plate.translate(Vector(0, 0, v_drop))

    # Right plate: slopes from (v_x, z=0) up to (span, z=v_drop)
    right_span_mm = span - v_x
    right_hyp = math.sqrt(right_span_mm**2 + v_drop**2)
    right_ang = math.degrees(math.atan2(v_drop, right_span_mm))

    right_plate = Part.makeBox(right_hyp, depth_y, T)
    right_plate.rotate(Vector(0, 0, 0), Vector(0, 1, 0), right_ang)
    right_plate.translate(Vector(v_x, 0, 0))

    shape = left_plate.fuse(right_plate)

    # Semicircular notch at V bottom
    notch = Part.makeCylinder(notch_r, depth_y,
                              Vector(v_x, 0, 0), Vector(0, 1, 0))
    return shape.cut(notch)


add("A_Cover", cover())


# ==============================================================
# SHEET 6 — Bearing Plates (Part B — Upper Saddle)
#
# 2x large: 3.000 x 2.000, R0.219" corners, centered 1" hole
# 2x small: 3.000 x 2.000, 1" hole at (1.000", 1.000")
# ==============================================================

def bearing_plate_large():
    """Rounded-corner plate with centered 1" hole."""
    w = 3.000 * IN
    h = 2.000 * IN
    r = 0.219 * IN
    hr = 0.500 * IN

    edges = [
        Part.makeCircle(r, Vector(r, r, 0), Vector(0, 0, 1), 180, 270),
        Part.makeLine(Vector(r, 0, 0), Vector(w - r, 0, 0)),
        Part.makeCircle(r, Vector(w - r, r, 0), Vector(0, 0, 1), 270, 360),
        Part.makeLine(Vector(w, r, 0), Vector(w, h - r, 0)),
        Part.makeCircle(r, Vector(w - r, h - r, 0), Vector(0, 0, 1), 0, 90),
        Part.makeLine(Vector(w - r, h, 0), Vector(r, h, 0)),
        Part.makeCircle(r, Vector(r, h - r, 0), Vector(0, 0, 1), 90, 180),
        Part.makeLine(Vector(0, h - r, 0), Vector(0, r, 0)),
    ]
    wire = Part.Wire(edges)
    face = Part.Face(wire)
    solid = face.extrude(Vector(0, 0, T))

    hole = Part.makeCylinder(hr, T, Vector(w / 2, h / 2, 0))
    return solid.cut(hole)


def bearing_plate_small():
    """Plain plate with 1" hole at (1", 1")."""
    w = 3.000 * IN
    h = 2.000 * IN
    box = Part.makeBox(w, h, T)
    hole = Part.makeCylinder(0.500 * IN, T,
                             Vector(1.000 * IN, 1.000 * IN, 0))
    return box.cut(hole)


for i in range(2):
    add(f"B_BearingPlate_Large_{i+1}", bearing_plate_large())

for i in range(2):
    add(f"B_BearingPlate_Small_{i+1}", bearing_plate_small())


# ==============================================================
# SHEET 7 — Baseboard (Part D) and Piston Cap (Part K)
#
# 1x baseboard:  15.000 x 12.000 with holes and slot
# 1x piston cap:  6.000 x 6.000
# ==============================================================

def baseboard():
    """Main baseboard plate with pivot hole, bolt holes, and piston slot."""
    w = 15.000 * IN
    h = 12.000 * IN

    box = Part.makeBox(w, h, T)

    # 1.000" dia toggle pivot hole — centered on width, 1" from top edge
    pivot = Part.makeCylinder(0.500 * IN, T,
                              Vector(w / 2, 11.000 * IN, 0))

    # 2x 0.500" dia mounting bolt holes — below slot, for bolting to feet
    bolt_left = Part.makeCylinder(0.250 * IN, T,
                                  Vector(1.000 * IN, 3.000 * IN, 0))
    bolt_right = Part.makeCylinder(0.250 * IN, T,
                                   Vector(1.000 * IN, 9.000 * IN, 0))

    # 8.000" x 1.000" rectangular piston slot — centered on rod
    slot = Part.makeBox(
        8.000 * IN, 1.000 * IN, T,
        Vector((w - 5.000 * IN - 8.000 * IN), 5.500 * IN, 0))

    shape = box.cut(pivot).cut(bolt_left).cut(bolt_right).cut(slot)
    return shape


add("D_Side", baseboard())
# Shelf — 6x12" flat plate the brick sits on, spans between slotted sides
add("K_Shelf", Part.makeBox(6.000 * IN, 12.000 * IN, T))

# Stabilizing bars — welded under shelf edges
add("K_Shelf_Left", Part.makeBox(6.000 * IN, 2.000 * IN, T))
add("K_Shelf_Right", Part.makeBox(6.000 * IN, 2.000 * IN, T))

# Piston plates — vertical, with 1" hole at 3" from bottom (same as side walls)
def piston_plate():
    box = Part.makeBox(2.000 * IN, 6.000 * IN, T)
    hole = Part.makeCylinder(0.500 * IN, T,
                             Vector(1.000 * IN, 3.000 * IN, 0))
    return box.cut(hole)

add("K_Piston_Left", piston_plate())
add("K_Piston_Right", piston_plate())


# ==============================================================
# Foot Brackets — L-shaped mounting feet
#
# 2x bracket: vertical leg 4.000 x 3.000, horizontal leg 4.000 x 3.000
# 0.500" bolt hole centered in horizontal leg
# ==============================================================

def foot_bracket():
    """L-shaped foot bracket for bolting press to base. 4' long, 2\" x 2\" L."""
    length = 48.000 * IN   # 4 feet
    leg = 2.000 * IN

    vert_leg = Part.makeBox(length, T, leg)
    horiz_leg = Part.makeBox(length, leg, T)
    shape = vert_leg.fuse(horiz_leg)

    # Horizontal leg bolt holes
    hole1 = Part.makeCylinder(0.250 * IN, T,
                              Vector(3.000 * IN, leg / 2, 0))
    hole2 = Part.makeCylinder(0.250 * IN, T,
                              Vector(length / 2, leg / 2, 0))
    hole3 = Part.makeCylinder(0.250 * IN, T,
                              Vector(length - 3.000 * IN, leg / 2, 0))

    # Vertical leg bolt holes — match baseboard mounting holes
    hole4 = Part.makeCylinder(0.250 * IN, T,
                              Vector(7.000 * IN, 0, 1.000 * IN),
                              Vector(0, 1, 0))
    hole5 = Part.makeCylinder(0.250 * IN, T,
                              Vector(13.000 * IN, 0, 1.000 * IN),
                              Vector(0, 1, 0))
    return shape.cut(hole1).cut(hole2).cut(hole3).cut(hole4).cut(hole5)


for i in range(2):
    add(f"Base_Bracket_{i+1}", foot_bracket())


# ==============================================================
# Done
# ==============================================================
doc.recompute()

print("=" * 50)
print("CINVA-Ram Block Press — 24 parts created")
print(f"Plate thickness: {T:.2f} mm (0.250\")")
print("Units: mm (converted from inches)")
print("=" * 50)
