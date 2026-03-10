/*
 * CINVA-Ram Block Press — OpenSCAD Solid Model
 *
 * All dimensions from engineering drawings (cinva1-7.jpg).
 * Material: 1/4" (0.250") steel plate throughout.
 * Units: inches.
 *
 * Usage: Open in OpenSCAD. Each part is a named module.
 * The layout at the bottom spreads all 22 parts for viewing.
 */

$fn = 64;

T = 0.250;  // plate thickness (1/4")


// ==========================================================
// Helper modules
// ==========================================================

module plate(w, h, t=T) {
    cube([w, h, t]);
}

module plate_with_hole(w, h, hole_d, hole_x, hole_y, t=T) {
    difference() {
        cube([w, h, t]);
        translate([hole_x, hole_y, -0.01])
            cylinder(d=hole_d, h=t+0.02);
    }
}

// Rectangle with radiused bottom corners, square top corners
module rounded_bottom_rect(w, h, r, t=T) {
    linear_extrude(height=t) {
        union() {
            // upper portion (above radius)
            translate([0, r])
                square([w, h - r]);
            // bottom-left radius
            translate([r, r])
                circle(r=r);
            // bottom center fill
            translate([r, 0])
                square([w - 2*r, r]);
            // bottom-right radius
            translate([w - r, r])
                circle(r=r);
        }
    }
}

// Rectangle with all four corners radiused
module rounded_rect(w, h, r, t=T) {
    linear_extrude(height=t)
        offset(r=r)
            offset(delta=-r)
                square([w, h]);
}


// ==========================================================
// SHEET 1 — Mold Box Walls (Part C)
//
// 2x side walls:  7.250 x 6.000  with 1.000" pivot hole
//    hole at 6.250" from left, 3.000" from top (= 3.000 from bottom)
// 1x end wall:    6.000 x 11.500
// 1x end wall:    6.500 x 12.000
// ==========================================================

module C_SideWall() {
    plate_with_hole(7.250, 6.000, 1.000, 6.250, 3.000);
}

module C_EndWall_Short() {
    plate(6.000, 11.500);
}

module C_EndWall_Tall() {
    plate(6.500, 12.000);
}


// ==========================================================
// SHEET 2 — Wing and Tail plates (from cinva2.jpg)
//
// Wing: 2.000 x 5.625 (3.625 + 2), 1" hole, R0.375" bottom corners
// Tail: 2.000 x 3.625, 1" hole at 1.250" from bottom, R0.375" bottom corners
// Welded in pairs (Wing+Tail) to make 0.5" thick assemblies
// ==========================================================

module toggle_link(width, height, hole_y) {
    difference() {
        rounded_bottom_rect(width, height, 0.375);
        translate([width / 2, hole_y, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}

module Wing_Left() {
    difference() {
        toggle_link(2.000, 5.625, 1.250);
        // Second hole aligns with Pivot Y-through hole
        translate([1.000, 4.625, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}

module Wing_Right() {
    difference() {
        toggle_link(2.000, 5.625, 1.250);
        // Second hole aligns with Pivot Y-through hole
        translate([1.000, 4.625, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}

module Tail_Left() {
    toggle_link(2.000, 3.625, 1.250);
}

module Tail_Right() {
    toggle_link(2.000, 3.625, 1.250);
}


// ==========================================================
// SHEET 3 — Lever Latch (Part M)
//
// 2x L-shaped bracket: 4.147 x 1.035
//    Main bar ~0.518" tall, raised tab on left 0.625" wide
//    up to 1.035" total. Corner notch 0.354" from bottom.
//    0.437" dia hole near right end (0.500" from edge, 0.397" from top)
//    1.000" dia hole in main bar, 2.929" from step
// 1x spacer: 1.000 x 2.750
// ==========================================================

module M_LatchBracket() {
    w     = 4.147;
    h     = 1.035;   // full height at tab
    bar_h = 0.518;   // main bar height
    tab_w = 0.625;   // tab width
    notch_h = 0.354; // notch height from bottom

    difference() {
        linear_extrude(height=T)
            polygon(points=[
                [0, 0],
                [w, 0],
                [w, bar_h],                   // right side, bar height
                [tab_w, bar_h],               // step down to bar top
                [tab_w, h],                   // up to full tab height
                [0, h],                       // across tab top
            ]);

        // 0.437" (7/16") dia hole — 0.500" from right edge, 0.397" from top
        translate([w - 0.500, h - 0.397, -0.01])
            cylinder(d=0.437, h=T+0.02);
    }
}

module M_LatchSpacer() {
    plate(1.000, 2.750);
}

// Clamp — latch bracket from cinva3.jpg
// Two horizontal lines (tab 0.309, bar 2.929) with angled notch between
// Notch: 0.354 and 0.518 walls (parallel, 13.3° from vert), 0.625 bottom
// Left face: 1.035 hypotenuse (vert 1.000, horiz 0.267)
module Clamp_Left() {
    difference() {
        linear_extrude(height=T)
            polygon(points=[
                [0, 0],             // bar bottom-left
                [2.929, 0],         // bar bottom-right (horiz 2.929)
                [3.048, 0.504],     // notch right (0.518 parallel wall)
                [3.652, 0.345],     // notch left (0.625 bottom)
                [3.571, 0],         // tab bottom-left (0.354 parallel wall)
                [3.880, 0],         // tab bottom-right (horiz 0.309)
                [4.147, 1.000],     // top of angled face
                [0, 1.000],         // bar top-left (vert 1.000)
            ]);                     // close: horiz back to (0,0)
        // 0.437" dia hole — 0.500" from left edge, 0.397" from bottom
        translate([0.500, 0.397, -0.01])
            cylinder(d=0.437, h=T+0.02);
    }
}

module Clamp_Right() {
    mirror([0, 0, 1])
        translate([0, 0, -T])
            Clamp_Left();
}

module Clamp_Spacer() {
    plate(1.000, 2.750);
}


// ==========================================================
// SHEET 4 — Handle (Part N) and Cross Bars
//
// 2x handle bar:      19.625 x 2.000, 1" hole 1.000" from end
// 1x upper cross bar: 11.000 x 2.000
// 1x lower cross bar:  8.000 x 2.000
// ==========================================================

module N_HandleBar() {
    plate_with_hole(19.625, 2.000, 1.000, 1.000, 1.000);
}

module Cross_Front() {
    plate(8.000, 2.000);
}

module Cross_Back() {
    plate(8.000, 2.000);
}


// ==========================================================
// SHEET 5 — Cover (Part A)
//
// Bent V-shape plate, 12.000" span across top
// Left flat 0.250", left leg 6.038"
// Right flat 1.000", right leg 4.810"
// R0.625" semicircular notch at V bottom
// Depth ~6.500" (matches mold box end wall)
// ==========================================================

module A_Cover() {
    span       = 12.000;
    left_flat  = 0.250;
    right_flat = 1.000;
    left_leg   = 6.038;
    right_leg  = 4.810;
    notch_r    = 0.625;
    depth_y    = 6.500;

    // Solve V geometry: both legs drop to same depth
    angled_span = span - left_flat - right_flat;
    left_dx  = (angled_span +
                (left_leg*left_leg - right_leg*right_leg) / angled_span) / 2;
    right_dx = angled_span - left_dx;
    v_drop   = sqrt(max(left_leg*left_leg - left_dx*left_dx, 0.001));
    v_x      = left_flat + left_dx;

    left_hyp  = sqrt(v_x * v_x + v_drop * v_drop);
    left_ang  = atan2(v_drop, v_x);

    right_span = span - v_x;
    right_hyp  = sqrt(right_span * right_span + v_drop * v_drop);
    right_ang  = atan2(v_drop, right_span);

    difference() {
        union() {
            // Left plate: high at x=0, slopes down to V bottom at x=v_x
            translate([0, 0, v_drop])
                rotate([0, -left_ang, 0])
                    cube([left_hyp, depth_y, T]);

            // Right plate: low at x=v_x, slopes up to x=span
            translate([v_x, 0, 0])
                rotate([0, right_ang, 0])
                    cube([right_hyp, depth_y, T]);
        }

        // Semicircular notch at V bottom, running along Y
        translate([v_x, -0.01, 0])
            rotate([-90, 0, 0])
                cylinder(r=notch_r, h=depth_y + 0.02);
    }
}


// ==========================================================
// SHEET 6 — Bearing / Guide Plates (Parts B, I, J)
//
// 2x large: 3.000 x 2.000, R0.219" corners, 1" hole centered
// 2x small: 3.000 x 2.000, 1" hole at (1.000, 1.000)
// ==========================================================

module B_BearingPlate_Large() {
    w = 3.000;
    h = 2.000;
    r = 0.219;

    difference() {
        rounded_rect(w, h, r);
        translate([w/2, h/2, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}

module B_BearingPlate_Small() {
    difference() {
        cube([3.000, 2.000, T]);
        translate([1.000, 1.000, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}


// ==========================================================
// SHEET 7 — Baseboard (Part D) and Piston Cap (Part K)
//
// 1x baseboard:  15.000 x 12.000
//    1.000" dia pivot hole, 2x 0.500" bolt holes
//    8.000 x 2.000 piston slot (5" from bottom, 5" from right)
// 1x piston cap:  6.000 x 6.000
// ==========================================================

module D_Side() {
    w = 15.000;
    h = 12.000;

    difference() {
        cube([w, h, T]);

        // 1.000" dia toggle pivot hole — centered on width, 1" from top edge
        translate([w/2, 11.000, -0.01])
            cylinder(d=1.000, h=T+0.02);

        // 0.500" dia mounting bolt holes — below slot, for bolting to feet
        translate([1.000, 3.000, -0.01])
            cylinder(d=0.500, h=T+0.02);
        translate([1.000, 9.000, -0.01])
            cylinder(d=0.500, h=T+0.02);

        // 8.000 x 1.000 rectangular piston slot — centered on rod
        translate([w - 5.000 - 8.000, 5.500, -0.01])
            cube([8.000, 1.000, T+0.02]);
    }
}

module D_Side_Left() {
    D_Side();
}

module D_Side_Right() {
    D_Side();
}

// --- Shelf: flat plate the brick sits on, spans between slotted sides ---
module K_Shelf() {
    plate(6.000, 12.000);
}

// --- Shelf brackets: 11x2x0.25, welded under shelf ~2" from each side ---
module Bracket_Left() {
    plate(11.000, 2.000);
}

module Bracket_Right() {
    plate(11.000, 2.000);
}

// --- Piston plates: 6x6x0.25, welded in pairs (0.5" thick) ---
// 1.000" dia hole at 0.500" from bottom, centered on width
module K_Piston_1() {
    plate_with_hole(6.000, 6.000, 1.000, 3.000, 0.500);
}

module K_Piston_2() {
    plate_with_hole(6.000, 6.000, 1.000, 3.000, 0.500);
}

module K_Piston_3() {
    plate_with_hole(6.000, 6.000, 1.000, 3.000, 0.500);
}

module K_Piston_4() {
    plate_with_hole(6.000, 6.000, 1.000, 3.000, 0.500);
}

// --- Front and Back plates: 7.5x6.5x0.25, welded to outside of shelf ---
module Front() {
    plate(7.500, 6.500);
}

module Back() {
    plate(7.500, 6.500);
}


// ==========================================================
// Pivot — solid block connecting handle to Load pin
//
// 2x2x6 block with:
//   1x4" rectangular slot (for handle bars to pass through)
//   1" dia hole (for Load pivot pin)
// Based on Blockpress003.jpg
// ==========================================================

module Pivot() {
    // 2x2 in X/Y, 6" tall in Z
    // Sunk slot faces up, 1" hole through Y for Spacer
    // 2x2x2 block at top toward front with 1" hole
    difference() {
        union() {
            cube([2, 2, 6]);
            // Front block at top — 0.794(X) x 2(Y) x 0.794(Z)
            translate([-0.794, 0, 6 - 0.794])
                cube([0.794, 2, 0.794]);
        }

        // 1" dia x 4" deep sunk hole from top — centered in X/Y
        translate([1, 1, 2])
            cylinder(d=1.000, h=4.01);

        // 1" dia hole through in Y — 1" from bottom, centered in X
        // Aligns with Spacer / ramp scoops
        translate([1, -0.01, 1])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2.02);

        // 0.437" dia hole through front block in Y — 0.397" from front end
        translate([-0.794 + 0.397, -0.01, 6 - 0.794/2])
            rotate([-90, 0, 0])
                cylinder(d=0.437, h=2.02);

    }
}


// ==========================================================
// Top plate — 12.5x6.5, sits on top of the side plates
// ==========================================================

module Top() {
    plate(12.500, 6.500);
}


// ==========================================================
// Ramps — V-shaped plates on top of the top plate
//
// Based on cinva5.jpg cover geometry:
//   12.000" span, left leg 6.038", right leg 4.810"
//   V drop ~0.72"
// Scaled to 12.500" span (matching top plate width)
// Depth 6.500" (matching top plate)
// ==========================================================

module Ramp(depth=6.500) {
    // Solid ramp from cinva5.jpg
    // Start simple: 12" bottom, 1" right edge, 0.25" left edge
    // 6 sides + R0.625" arc scoop at peak:
    //   12" bottom, 1" left up, 4.810" slope up-right,
    //   1" horizontal, R0.625" scoop, 6.038" slope down-right, 0.25" right down
    // Peak height ~3.0"
    // Gap = 1" horizontal + 1.25" arc = 2.25"

    peak_y = 3.0;
    left_peak_x = 4.374;     // 4.810" slope from (0,1)
    right_peak_x = 6.624;    // 6.038" slope to (12,0.25)

    linear_extrude(height=depth)
        difference() {
            polygon(points=[
                [0, 0],
                [12, 0],
                [12, 0.25],
                [right_peak_x, peak_y],
                [left_peak_x, peak_y],
                [0, 1],
            ]);
            // R0.625" scoop flush against 6.038 slope,
            // 1" horizontal flat after 4.810 slope
            translate([right_peak_x - 0.625, peak_y + 0.125])
                circle(r=0.625);
        }
}


// ==========================================================
// Foot Brackets — L-shaped mounting feet
//
// 2x foot bracket: weld vertical leg to baseboard bottom,
//    horizontal leg provides bolt-down surface
//    Vertical leg: 4.000 x 3.000
//    Horizontal leg: 4.000 x 3.000
//    0.500" dia bolt hole centered in horizontal leg
// ==========================================================

module Base_Bracket_Left() {
    Base_Bracket();
}

module Base_Bracket_Right() {
    Base_Bracket();
}

module Base_Bracket() {
    len  = 36.000;  // 3 feet long
    leg  = 2.000;   // 2" x 2" L profile

    difference() {
        union() {
            // Vertical leg (welds to baseboard)
            cube([len, T, leg]);
            // Horizontal leg (sits on ground/pallet)
            cube([len, leg, T]);
        }
        // 0.500" bolt holes in horizontal leg, spaced along length
        translate([3.000, leg / 2, -0.01])
            cylinder(d=0.500, h=T+0.02);
        translate([len / 2, leg / 2, -0.01])
            cylinder(d=0.500, h=T+0.02);
        translate([len - 3.000, leg / 2, -0.01])
            cylinder(d=0.500, h=T+0.02);

        // 0.500" bolt holes in vertical leg — match baseboard mounting holes
        // At X=7 and X=13 (baseboard at 1/3 point = X=16, holes 3" and 9" in)
        translate([7.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=0.500, h=T+0.02);
        translate([13.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=0.500, h=T+0.02);
    }
}


// ==========================================================
// Layout — all 24 parts spread out for viewing
//
// Parts are spaced so nothing overlaps.
// Comment out this section and call individual modules
// if you only need specific parts.
// 29 total pieces.
// ==========================================================

gap = 1.5;  // spacing between parts
ox = 56;    // X offset — clear of foot bracket at origin

// --- Base brackets: vertical legs on inside 7" apart, feet pointing outward ---
// Left bracket: shifted +2" in Y, foot extends -Y
color("green")
translate([0, 2.000, 0])
    mirror([0, 1, 0])
        Base_Bracket_Left();
// Right bracket: outside right side plate
color("green")
translate([0, 7.750 + 2*T, 0])
    Base_Bracket_Right();

// --- Baseboards (Part D) standing vertical at 1/3 point on feet ---
// Feet are 48" long; 1/3 = 16". Baseboard 15" wide along X, 12" tall in Z.
// Slot is vertical (baseboard rotated so the 8x2 slot runs up/down).
// One on each foot, against the inside face of each vertical leg.

// Left side — resting on left base, origin side (Y=1.5 to 1.75)
translate([16.000, 2.000 - T, T])
    rotate([0, 0, 0])
        rotate([90, 0, 0])
            rotate([0, 0, 90])
                D_Side_Left();

// Right side — inner face at shelf right edge (Y=7.750), between shelf and bracket
translate([16.000, 7.750 + T, T])
    rotate([0, 0, 0])
        rotate([90, 0, 0])
            rotate([0, 0, 90])
                D_Side_Right();

// --- Top plate (12.5x6.5) on top of side plates ---
// Z = side top = T + 15 = 15.25
// Y = left side outer face (1.5) to right side outer face (8.0) = 6.5"
// X = 12.5" centered over the assembly
color([0.50, 0.48, 0.45])
translate([4.000 - T, 1.500, T + 15.000])
    cube([12.500, 6.500, T]);

// --- Shelf (12x6x0.25) spanning between the two sides ---
// 12" in X (along feet), 6" in Y (between sides), T thick
// Left edge touching left side (Y=1.75), right edge at Y=7.75
shelf_z = 12.000;  // shelf top 3" from top of side
color([0.60, 0.58, 0.55])
translate([4.000, 1.750, shelf_z])
    cube([12.000, 6.000, T]);

// --- Shelf brackets (11x2x0.25) under shelf, 0.5" toward center from each side ---
// Vertical (standing on edge), 11" along X, 2" tall in Z, T thick in Y
// Left bracket: 0.5" in from shelf left edge
color([0.55, 0.50, 0.45])
translate([4.500, 1.750 + 0.500, shelf_z - 2.000])
    cube([11.000, T, 2.000]);

// Right bracket: 0.5" in from shelf right edge
color([0.55, 0.50, 0.45])
translate([4.500, 7.750 - 0.500 - T, shelf_z - 2.000])
    cube([11.000, T, 2.000]);

// --- Piston plates (4x 7.25x6x0.25, welded in pairs = 0.5" thick each) ---
// Touching inside face of each bracket
// Left bracket inner face at Y = 1.750 + 0.500 + T = 2.500
// Right bracket inner face at Y = 7.750 - 0.500 - T = 7.000
bracket_left_inner = 1.750 + 0.500 + T;   // Y=2.500
bracket_right_inner = 7.750 - 0.500 - T;  // Y=7.000

// Left piston pair: touching left bracket inner face
// 6" in X centered on 12" shelf: X = 4 + (12-6)/2 = 7
color([0.60, 0.58, 0.55])
translate([7.000, bracket_left_inner, shelf_z - 6.000])
    cube([6.000, 2*T, 6.000]);

// Right piston pair: touching right bracket inner face
color([0.60, 0.58, 0.55])
translate([7.000, bracket_right_inner - 2*T, shelf_z - 6.000])
    cube([6.000, 2*T, 6.000]);

// Load pin — through piston holes and pivot block, extends 1" past each side
color("purple")
translate([7.000 + 3.000, 0.500, shelf_z - 6.000 + 0.500])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);


// --- Ramp (solid V-shape) on top of the Top plate ---
// Top plate surface at Z = T + 15.000 + T = 15.500
// 12" cross-section in X, 6.5" depth in Y (matching top plate)
// Centered on 12.5" top plate: offset 0.25" from each X edge
ramp_z = T + 15.000 + T;

// Ramps — aligned with Wing/Tail plates outside the Pivot
// Left ramp at Wing_Left outer face, right ramp at Wing_Right outer face
ramp_y1 = 3.750 - 2*T - 0.500;      // 2.750 — left ramp, 0.5" further out
ramp_y2 = 5.750 + T + 0.500;        // 6.500 — right ramp, 0.5" further out

color("red")
translate([4.000, ramp_y1 + T, ramp_z])
    rotate([90, 0, 0])
        Ramp(depth=T);

color("red")
translate([4.000, ramp_y2 + T, ramp_z])
    rotate([90, 0, 0])
        Ramp(depth=T);

// Spacer — 1" dia bar, 3" long, resting in ramp scoops
// Centered at Y=4.75
spacer_length = 3.000;
color("purple")
translate([10.000, 4.750 - spacer_length/2, 18.500])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=spacer_length);

// Roller — 1" dia bar through Pivot/Wing holes, extends 1" past each ramp
// At X=6.625 (Pivot hole center), Z=18.5
// From Y = ramp_y1 - 1.0 to Y = ramp_y2 + T + 1.0
roller_y_start = ramp_y1 - 1.000;           // 1.750
roller_length = (ramp_y2 + T) - ramp_y1 + 2.000;  // 6.000
color("purple")
translate([6.625, roller_y_start, 18.500])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=roller_length);

// --- Lever (Part N) — Class 2: Fulcrum at front, Load at slot ---
// Fulcrum pin: X=5.0, Z=7.75 — bar rests ON TOP of pin
// Load pin: X=10.0, Z=6.5 (lever hole goes around)
// Bar: 19.625" long, hole 1" from end, centered on 2" width
// Fulcrum contact is 13.625" from bar grip end

lever_pin_x = 10.000;
lever_pin_z = shelf_z - 6.000 + 0.500;  // 6.5
fulcrum_x = 5.000;
fulcrum_z = 7.750;
pin_r = 0.475;                           // pin d=0.95
fulcrum_rest_z = fulcrum_z + pin_r;      // bar bottom rests on top of pin
lever_angle = 90;                         // degrees — hole aligns with Load pin
lever_fulcrum_along_bar = 13.625;         // grip end to fulcrum contact

// Fulcrum pin — through side plate holes
color("purple")
translate([fulcrum_x, 0.500, fulcrum_z])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);

// Left lever bar + round end (unioned) — at left end of crosses
color("orange")
translate([fulcrum_x, cross_center_y - 8.000/2, fulcrum_rest_z])
    rotate([0, lever_angle, 0])
        translate([-lever_fulcrum_along_bar, 0, 0])
            union() {
                cube([19.625, T, 2.000]);
                translate([19.625, 0, 1.000])
                    rotate([-90, 0, 0])
                        cylinder(r=1.000, h=T);
            }

// Right lever bar + round end (unioned) — at right end of crosses
color("orange")
translate([fulcrum_x, cross_center_y + 8.000/2 - T, fulcrum_rest_z])
    rotate([0, lever_angle, 0])
        translate([-lever_fulcrum_along_bar, 0, 0])
            union() {
                cube([19.625, T, 2.000]);
                translate([19.625, 0, 1.000])
                    rotate([-90, 0, 0])
                        cylinder(r=1.000, h=T);
            }

// Cross_Back (8x2) — at grip tip, levers welded here
cross_center_y = (1.500 + 8.000) / 2;  // 4.750
color("orange")
translate([fulcrum_x, cross_center_y - 8.000/2, fulcrum_rest_z])
    rotate([0, lever_angle, 0])
        translate([-lever_fulcrum_along_bar, 0, 0])
            cube([T, 8.000, 2.000]);

// Cross_Front (8x2) — 2" back from Cross_Back
color("orange")
translate([fulcrum_x, cross_center_y - 8.000/2, fulcrum_rest_z])
    rotate([0, lever_angle, 0])
        translate([-lever_fulcrum_along_bar + 2.000, 0, 0])
            cube([T, 8.000, 2.000]);

// Pivot block — standing above ramps
// Right face at X=7.625 (touching tail tips)
// Pivot: X=5.625..7.625, Y=3.75..5.75, Z=17.5..23.5
color("brown")
translate([5.625, 3.750, 17.500])
    Pivot();

// Axle — 7/16" dia, 3" long, through front block hole
// Center: X=5.228, Z=23.103, Y centered at 4.75
axle_x = 5.625 + (-0.794 + 0.397);      // 5.228
axle_z = 17.500 + (6 - 0.794/2);         // 23.103
color("purple")
translate([axle_x, 4.750 - 1.500, axle_z])
    rotate([-90, 0, 0])
        cylinder(d=0.437, h=3.000);

// Clamp — two latch brackets around Axle, welded to spacer plate
// Bracket hole at (3.647, 0.638) in module coords
// rotate([90,0,0]): (x,y,z)→(x,-z,y)  — module Y becomes world +Z
// Hole (0.500, 0.397, 0) → (0.500, 0, 0.397)
// For hole at Axle (5.228, Y, 23.103): translate_z = 23.103 - 0.397 = 22.706
// Bracket X range: 4.728 to 8.875 (hook at high X)
// Bracket Z range: 22.706 to 23.706
// Clamps 0.25" inside Cap ends, equal about Y=4.75
// After rotate, bracket Y = translate_y - T to translate_y
color("pink")
translate([4.728, 3.625, 22.706])
    rotate([90, 0, 0])
        Clamp_Left();

color("pink")
translate([4.728, 5.875 + T, 22.706])
    rotate([90, 0, 0])
        Clamp_Right();

// Cap (1x2.75) welded to angled end of Clamps (hook end)
// Angled face: (8.608, Z=22.706) to (8.875, Z=23.706), tilts 14.93° from vertical
// Cap tilted to match the Clamp end angle
color("pink")
translate([8.608, 4.750 - 2.750/2, 22.706])
    rotate([0, atan(0.267/1.000), 0])
        cube([T, 2.750, 1.000]);

// Wing and Tail plates — horizontal, holes surround Spacer (X=10, Z=18.5)
// After rotate([0,0,90]) rotate([0,90,0]):
//   plate X = -height..0, Y = 0..T, Z = 0..2
//   hole offset = (-1.250, 0, 1.0)
// translate([11.250, Y, 17.500]) puts hole at (10.0, Y, 18.5)
// Tail tip at X=7.625, Wing tip at X=5.625

// Wings — flat against Pivot Y faces (sides)
// Wing_Left: Y=3.50..3.75, touching Pivot left face at Y=3.75
color([0.65, 0.55, 0.45])
translate([11.250, 3.750 - T, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Wing_Left();

// Wing_Right: Y=5.75..6.00, touching Pivot right face at Y=5.75
color([0.65, 0.55, 0.45])
translate([11.250, 5.750, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Wing_Right();

// Tails — inside Pivot Y range, tips touching Pivot right face at X=7.625
// Tail_Left: Y=3.75..4.00
color([0.65, 0.55, 0.45])
translate([11.250, 3.750, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Tail_Left();

// Tail_Right: Y=5.50..5.75
color([0.65, 0.55, 0.45])
translate([11.250, 5.750 - T, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Tail_Right();

// --- Front and Back (7.5x6.5x0.25) — welded to outside of shelf ---
// 6.5" in Y (connecting sides), 7.5" in Z (hanging from top), T in X
// Top flush with side tops at Z=15.25
// Front: outside shelf front edge (X=4.0-T)
color("blue")
translate([4.000 - T, 1.500, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);

// Back: outside shelf back edge (X=16.0)
color("blue")
translate([4.000 + 12.000, 1.500, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);

/*  --- HIDDEN FOR NOW ---

// --- Side walls (Part C) ---
side_wall_z = 4.000;
side_wall_x1 = 7.000;
side_wall_x2 = side_wall_x1 + 6.000 + T;

color([0.55, 0.52, 0.50])
translate([side_wall_x1, 0, side_wall_z])
    cube([T, 7.250, 6.000]);

color([0.55, 0.52, 0.50])
translate([side_wall_x2, 0, side_wall_z])
    cube([T, 7.250, 6.000]);

// --- Piston assembly ---
piston_shelf_z = side_wall_z + 3.000;
mold_center_y = 7.250 / 2;

piston_cx = side_wall_x1 + T + 3.000;
piston_plate_z = piston_shelf_z - 6.000 + T;

color([0.60, 0.58, 0.55])
translate([piston_cx - T, mold_center_y - 1.000, piston_plate_z])
    cube([T, 2.000, 6.000]);

color([0.60, 0.58, 0.55])
translate([piston_cx, mold_center_y - 1.000, piston_plate_z])
    cube([T, 2.000, 6.000]);

color([0.60, 0.58, 0.55])
translate([side_wall_x1 + T, mold_center_y - 3.000, piston_shelf_z - 2.000])
    cube([T, 6.000, 2.000]);

color([0.60, 0.58, 0.55])
translate([side_wall_x2 - T, mold_center_y - 3.000, piston_shelf_z - 2.000])
    cube([T, 6.000, 2.000]);

color([0.70, 0.70, 0.70])
translate([side_wall_x1 - 0.25, mold_center_y, side_wall_z + 3.000])
    rotate([0, 90, 0])
        cylinder(d=0.95, h=6.500);

*/  // --- END HIDDEN ---

/*  --- PARTS LAYOUT HIDDEN FOR NOW ---

// --- Row 1: Mold box side walls (short, y up to 6.000) ---
row1_y = 0;
translate([ox, row1_y, 0])
    C_SideWall();
translate([ox + 7.250 + gap, row1_y, 0])
    C_SideWall();

// --- Row 2: Mold box end walls (tall, y up to 12.000) ---
translate([ox + 2*(7.250 + gap), row1_y, 0])
    C_EndWall_Short();
translate([ox + 2*(7.250 + gap) + 6.000 + gap, row1_y, 0])
    C_EndWall_Tall();

// --- Row 3: Toggle links ---
row3_y = 13.0;
translate([ox, row3_y, 0])
    ToggleLink_Long();
translate([ox + 2.000 + gap, row3_y, 0])
    ToggleLink_Long();
translate([ox + 2*(2.000 + gap), row3_y, 0])
    ToggleLink_Short();
translate([ox + 3*(2.000 + gap), row3_y, 0])
    ToggleLink_Short();

// --- Row 4: Latch parts ---
row4_y = row3_y + 3.625 + gap;
translate([ox, row4_y, 0])
    M_LatchBracket();
translate([ox + 4.147 + gap, row4_y, 0])
    M_LatchBracket();
translate([ox + 2*(4.147 + gap), row4_y, 0])
    M_LatchSpacer();

// --- Row 5: Handle bars ---
row5_y = row4_y + 2.750 + gap;
translate([ox, row5_y, 0])
    N_HandleBar();
translate([ox, row5_y + 2.000 + gap, 0])
    N_HandleBar();

translate([ox + 19.625 + gap, row5_y, 0])
    N_CrossBar_Upper();
translate([ox + 19.625 + gap, row5_y + 2.000 + gap, 0])
    N_CrossBar_Lower();

// --- Row 6: Cover ---
row6_y = row5_y + 2*(2.000 + gap) + gap;
translate([ox, row6_y, 0])
    A_Cover();

// --- Row 7: Bearing plates ---
row7_y = row6_y + 6.500 + gap;
translate([ox, row7_y, 0])
    B_BearingPlate_Large();
translate([ox + 3.000 + gap, row7_y, 0])
    B_BearingPlate_Large();
translate([ox + 2*(3.000 + gap), row7_y, 0])
    B_BearingPlate_Small();
translate([ox + 3*(3.000 + gap), row7_y, 0])
    B_BearingPlate_Small();

// --- Row 8: Sides ---
row8_y = row7_y + 2.000 + gap;
translate([ox, row8_y, 0])
    D_Side_Left();
translate([ox + 15.000 + gap, row8_y, 0])
    D_Side_Right();

// --- Row 9: Piston parts ---
row9_y = row8_y + 12.000 + gap;
translate([ox, row9_y, 0])
    K_Shelf();
translate([ox + 6.000 + gap, row9_y, 0])
    K_Shelf_Left();
translate([ox + 6.000 + gap + 6.000 + gap, row9_y, 0])
    K_Shelf_Right();
translate([ox + 3*(6.000 + gap), row9_y, 0])
    K_Piston_Left();
translate([ox + 3*(6.000 + gap) + 2.000 + gap, row9_y, 0])
    K_Piston_Right();

*/  // --- END PARTS LAYOUT ---

