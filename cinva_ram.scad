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
            polygon(points=concat(
                // bottom-left R0.250 round (center 0.250, 0.250)
                [for (a = [180:10:270]) [0.250 + 0.250*cos(a), 0.250 + 0.250*sin(a)]],
                [[2.929, 0],         // bar bottom-right (horiz 2.929)
                [3.048, 0.504],     // notch right (0.518 parallel wall)
                [3.652, 0.345],     // notch left (0.625 bottom)
                [3.571, 0],         // tab bottom-left (0.354 parallel wall)
                [3.880, 0],         // tab bottom-right (horiz 0.309)
                [4.147, 1.000]],    // top of angled face
                // top-left R0.250 round (center 0.250, 0.750)
                [for (a = [90:10:180]) [0.250 + 0.250*cos(a), 0.750 + 0.250*sin(a)]]
            ));
        // 0.437" dia hole — 0.397" from left end, centered in 1" height
        translate([0.397, 0.500, -0.01])
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

        // 8.000 x 1.000 rectangular piston slot — bottom barely touches Load bar
        translate([3.150, 5.500, -0.01])
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
            // Front block at top — 1.000(X) x 2(Y) x 1.000(Z)
            translate([-1.000, 0, 6 - 1.000])
                cube([1.000, 2, 1.000]);
        }

        // 1" dia x 4" deep sunk hole from top — centered in X/Y
        translate([1, 1, 2])
            cylinder(d=1.000, h=4.01);

        // 1" dia hole through in Y — 1" from bottom, centered in X
        // Aligns with Spacer / ramp scoops
        translate([1, -0.01, 1])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2.02);

        // 0.437" dia hole through front block in Y — 0.397" from front edge, centered vertically
        translate([-1.000 + 0.397, -0.01, 6 - 0.500])
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
                [12, 1],
                [12 - left_peak_x, peak_y],
                [12 - right_peak_x, peak_y],
                [0, 0.25],
            ]);
            // R0.625" scoop flush against slope
            translate([12 - right_peak_x + 0.625, peak_y + 0.125])
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

        // 0.500" bolt holes in vertical leg — match side plate mounting holes
        // Side holes at world X=7 and X=13; bracket starts at X=4, so local X=3 and X=9
        translate([3.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=0.500, h=T+0.02);
        translate([9.000, -0.01, 1.000])
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
translate([4.000, 2.000, 0])
    mirror([0, 1, 0])
        Base_Bracket_Left();
// Right bracket: outside right side plate, vertical leg touching side
color("green")
translate([4.000, 7.750 + T, 0])
    Base_Bracket_Right();

// --- Animation ---
// Enable: View > Animate, set FPS=10, Steps=100
// $t goes 0 to 1: handle pull from rest to fulcrum
pull_angle = $t * 50;  // brown assembly rotates 0-50° around Spacer pin
spacer_x = 6.625;
spacer_z = 18.500;

// --- Lever (Part N) — Class 2: Fulcrum at front, Load at slot ---
// Fulcrum pin: X=5.0, Z=7.75 — bar rests ON TOP of pin
// Load pin: X=10.0, Z=6.5 (lever hole goes around)
// Bar: 19.625" long, hole 1" from end, centered on 2" width
// Fulcrum contact is 13.625" from bar grip end

lever_pin_x = 10.000;
fulcrum_x = 5.000;
fulcrum_z = 7.750;
pin_r = 0.475;                           // pin d=0.95
fulcrum_rest_z = fulcrum_z + pin_r;      // bar bottom rests on top of pin
lever_fulcrum_along_bar = 13.625;         // grip end to fulcrum contact
lever_hole_along_bar = 18.625;            // grip end to hole center (19.625 - 1.0)

lever_angle = 87;

// lever_pin_z: Cross_Back top (z_local=+1.25) at grip end (x_local=-18.625)
// aligns with Clamp notch bottom (Z=22.706)
_clamp_notch_z = 22.500;
lever_pin_z = _clamp_notch_z - 18.625*sin(lever_angle) - 1.25*cos(lever_angle);  // ≈ 3.875

// Load pin world Z after brown assembly rotation around Spacer
_lp_dx = lever_pin_x - spacer_x;   // 3.375
_lp_dz = lever_pin_z - spacer_z;   // -14.625
_lp_R = sqrt(_lp_dx*_lp_dx + _lp_dz*_lp_dz);
_lp_phi = atan2(_lp_dz, _lp_dx);
load_pin_z = spacer_z + _lp_R * sin(_lp_phi + pull_angle);

// Lever rotates around load pin (hole goes around it)
// Hole center in bar-local coords: (18.625, 0, 1.0)
cross_center_y = (1.500 + 8.000) / 2;  // 4.750

// --- Press assembly ---

// --- Baseboards (Part D) standing vertical at 1/3 point on feet ---
// Feet are 48" long; 1/3 = 16". Baseboard 15" wide along X, 12" tall in Z.
// Slot is vertical (baseboard rotated so the 8x2 slot runs up/down).
// One on each foot, against the inside face of each vertical leg.

// Left side — resting on left base, origin side (Y=1.5 to 1.75)
%translate([16.000, 2.000 - T, T])
    rotate([0, 0, 0])
        rotate([90, 0, 0])
            rotate([0, 0, 90])
                D_Side_Left();

// Right side — inner face at shelf right edge (Y=7.750), between shelf and bracket
%translate([16.000, 7.750 + T, T])
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
shelf_z = load_pin_z + 6.250;  // piston hole (1" from bottom of 7.25" plate) aligns with Load pin
color("teal")
translate([4.000, 1.750, shelf_z])
    cube([12.000, 6.000, T]);


// --- Braces (11x2x0.25) under shelf, welded to pistons ---
// Vertical (standing on edge), 11" along X, 2" tall in Z, T thick in Y
bracket_left_inner = 1.750 + 0.500 + T;   // Y=2.500
bracket_right_inner = 7.750 - 0.500 - T;  // Y=7.000

// Left brace
color("teal")
translate([4.500, bracket_left_inner, shelf_z - 2.000])
    cube([11.000, T, 2.000]);

// Right brace
color("teal")
translate([4.500, bracket_right_inner - T, shelf_z - 2.000])
    cube([11.000, T, 2.000]);

// --- Piston plates (4x 7.250x6.000x0.25, welded in pairs = 0.5" thick each) ---
// Vertical in X-Z plane, thin in Y, rotated 90° from drawing orientation
// Rotated: 6.000 in X, 7.250 in Z, hole at X=3.000 from left, Z=1.000 from bottom
// Hole aligns with Load bar at X=10.0
piston_x = 10.000 - 3.000;     // 7.000, positions hole at X=10.0
piston_z = shelf_z - 7.250;    // top flush with shelf bottom

// Left piston pair: 6.000 x 0.500 x 7.250, welded to left brace
color("teal")
translate([piston_x, bracket_left_inner + 0.250, piston_z])
    difference() {
        cube([6.000, 2*T, 7.250]);
        translate([3.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2*T+0.02, $fn=32);
    }

// Right piston pair: 6.000 x 0.500 x 7.250, welded to right brace
color("teal")
translate([piston_x, bracket_right_inner - 2*T - 0.250, piston_z])
    difference() {
        cube([6.000, 2*T, 7.250]);
        translate([3.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2*T+0.02, $fn=32);
    }

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

// Spacer — 1" dia bar, 3" long, through Pivot/Wing upper holes (FIXED — rotation axis)
spacer_length = 3.000;
color("purple")
translate([spacer_x, 4.750 - spacer_length/2, spacer_z])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=spacer_length);

roller_y_start = ramp_y1 - 1.000;           // 1.750
roller_length = (ramp_y2 + T) - ramp_y1 + 2.000;  // 6.000

// Fulcrum pin — through side plate holes
color("purple")
translate([fulcrum_x, 0.500, fulcrum_z])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);

// === MOVING ASSEMBLY — rotates around Spacer pin ===
translate([spacer_x, 0, spacer_z])
    rotate([0, pull_angle, 0])
        translate([-spacer_x, 0, -spacer_z]) {

// Roller — moves with assembly
color("purple")
translate([10.000, roller_y_start, 18.500])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=roller_length);

// Load pin — moves with assembly
color("purple")
translate([lever_pin_x, 0.500, lever_pin_z])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);

} // pause MOVING ASSEMBLY for module definition

// Lever bar profile: R0.25" rounded bottom corners, square top corners
// X = bar length (0=grip, 19.625=load), Y = bar height (0=bottom, 2=top)
// Grip end (X=0) = square corners (welded to crosses)
// Load end (X=19.625) = R0.25" rounded corners (closest to origin)
module lever_bar_profile() {
    difference() {
        polygon([
            [0, 0],              // grip bottom-left (square)
            [19.375, 0],         // bottom straight to load arc
            [19.418, 0.004],     // load bottom arc (center 19.375, 0.25, r=0.25)
            [19.461, 0.015],
            [19.500, 0.033],
            [19.536, 0.058],
            [19.567, 0.089],
            [19.592, 0.125],
            [19.610, 0.165],
            [19.621, 0.207],
            [19.625, 0.250],     // load right side
            [19.625, 1.750],     // load right side up to top arc
            [19.621, 1.793],     // load top arc (center 19.375, 1.75, r=0.25)
            [19.610, 1.835],
            [19.592, 1.875],
            [19.567, 1.911],
            [19.536, 1.942],
            [19.500, 1.967],
            [19.461, 1.985],
            [19.418, 1.996],
            [19.375, 2.000],     // load top arc end
            [0, 2.000],          // grip top-left (square)
        ]);
        // 1" dia hole for load pin
        translate([18.625, 1.0])
            circle(d=1.000, $fn=32);
    }
}

// Resume MOVING ASSEMBLY
translate([spacer_x, 0, spacer_z])
    rotate([0, pull_angle, 0])
        translate([-spacer_x, 0, -spacer_z]) {

// Lever assembly — all parts move as one unit
color("orange")
translate([lever_pin_x, 0, lever_pin_z])
    rotate([0, lever_angle, 0]) {
        // Left lever bar
        translate([0, cross_center_y - 8.000/2, 0])
            translate([-lever_hole_along_bar, T, -1.0])
                rotate([90, 0, 0])
                    linear_extrude(height=T)
                        lever_bar_profile();

        // Right lever bar
        translate([0, cross_center_y + 8.000/2 - T, 0])
            translate([-lever_hole_along_bar, T, -1.0])
                rotate([90, 0, 0])
                    linear_extrude(height=T)
                        lever_bar_profile();

        // Cross_Back (8x2) — at grip end, flat on top of bars
        translate([-lever_hole_along_bar, cross_center_y - 8.000/2, 1.0])
            cube([2.000, 8.000, T]);

        // Cross_Front (8x2) — at grip end, flat on bottom of bars
        translate([-lever_hole_along_bar, cross_center_y - 8.000/2, -1.0 - T])
            cube([2.000, 8.000, T]);

        // Spacer — welded between crosses, 1.5x2x4 with 1" Roller hole
        // Spans from crosses toward load pin, between Tail inner faces
        translate([-17.625, 4.000, -1.0])
            difference() {
                cube([4.000, 1.500, 2.000]);
                // 1" dia hole for Roller at local x=3.0, z=1.0
                translate([3.000, -0.01, 1.000])
                    rotate([-90, 0, 0])
                        cylinder(d=1.000, h=1.520);
            }
    }

// Pivot block — standing above ramps
// Right face at X=7.625 (touching tail tips)
// Pivot: X=5.625..7.625, Y=3.75..5.75, Z=17.5..23.5
color("brown")
translate([5.625, 3.750, 17.500])
    Pivot();

// Handle — 6' (72") bar in Pivot sunk hole, extends upward
// Sunk hole: 1" dia, center at (6.625, 4.750), Z=19.5..23.5
color("brown")
translate([6.625, 4.750, 19.500])
    cylinder(d=0.95, h=72.000);

// Axle — 7/16" dia, 3" long, through front block hole
// Center: X=5.228, Z=23.103, Y centered at 4.75
axle_x = 5.625 + (-1.000 + 0.397);      // 5.022
axle_z = 17.500 + (6 - 0.500);           // 23.000
color("purple")
translate([axle_x, 4.750 - 1.500, axle_z])
    rotate([-90, 0, 0])
        cylinder(d=0.437, h=3.000);

// Clamp assembly — rotates around Axle to grab Cross_Front
// Cross_Front top surface at grip-end left corner (x_local=-18.625, z_local=-1.0):
//   world X ≈ 7.87, Z ≈ 22.73 at lever_angle ≈ 86.5°
// Notch bar-bottom-right (profile [2.929, 0]) unrotated: world (7.657, 22.706)
// Notch is already at the cross bar — rotate Clamp slightly to engage

// Cross_Front top surface at grip-end left edge
_cf_top_z = 18.625*sin(lever_angle) - cos(lever_angle) + lever_pin_z;

// Scoop contact point — low end of segment 2: clamp (3.652, 0.345)
// Unrotated world: X = 4.625 + 3.652 = 8.277, Z = 22.500 + 0.345 = 22.845
_scoop_dx = 4.625 + 3.652 - axle_x;   // 3.255
_scoop_dz = 22.500 + 0.345 - axle_z;  // -0.155
_scoop_R = sqrt(_scoop_dx*_scoop_dx + _scoop_dz*_scoop_dz);
_scoop_phi = atan2(_scoop_dz, _scoop_dx);

// Rotate clamp so scoop low point Z aligns with Cross_Front top
_clamp_target_dz = _cf_top_z - axle_z;
clamp_angle = asin(_clamp_target_dz / _scoop_R) - _scoop_phi;

color("pink")
translate([axle_x, 0, axle_z])
    rotate([0, -clamp_angle, 0])
        translate([-axle_x, 0, -axle_z]) {
            translate([4.625, 3.625, 22.500])
                rotate([90, 0, 0])
                    Clamp_Left();

            translate([4.625, 5.875 + T, 22.500])
                rotate([90, 0, 0])
                    Clamp_Right();

            // Cap
            translate([8.505, 4.750 - 2.750/2, 22.500])
                rotate([0, atan(0.267/1.000), 0])
                    cube([T, 2.750, 1.000]);
        }

// Wing and Tail plates — horizontal, holes surround Spacer (X=10, Z=18.5)
// After rotate([0,0,90]) rotate([0,90,0]):
//   plate X = -height..0, Y = 0..T, Z = 0..2
//   hole offset = (-1.250, 0, 1.0)
// translate([11.250, Y, 17.500]) puts hole at (10.0, Y, 18.5)
// Tail tip at X=7.625, Wing tip at X=5.625

// Wings — flat against Pivot Y faces (sides)
// Wing_Left: Y=3.50..3.75, touching Pivot left face at Y=3.75
color("brown")
translate([11.250, 3.750 - T, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Wing_Left();

// Wing_Right: Y=5.75..6.00, touching Pivot right face at Y=5.75
color("brown")
translate([11.250, 5.750, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Wing_Right();

// Tails — inside Pivot Y range, tips touching Pivot right face at X=7.625
// Tail_Left: Y=3.75..4.00
color("brown")
translate([11.250, 3.750, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Tail_Left();

// Tail_Right: Y=5.50..5.75
color("brown")
translate([11.250, 5.750 - T, 19.500])
    rotate([0, 0, 90])
        rotate([0, 90, 0])
            Tail_Right();

} // === END MOVING ASSEMBLY ===

// --- Front and Back (7.5x6.5x0.25) — welded to outside of shelf ---
// 6.5" in Y (connecting sides), 7.5" in Z (hanging from top), T in X
// Top flush with side tops at Z=15.25
// Front: outside shelf front edge (X=4.0-T)
%translate([4.000 - T, 1.500, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);

// Back: outside shelf back edge (X=16.0)
%translate([4.000 + 12.000, 1.500, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);

// --- end press assembly ---

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

