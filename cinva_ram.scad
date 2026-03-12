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

module Wing() {
    difference() {
        toggle_link(2.000, 5.625, 1.250);
        // Second hole aligns with Pivot Y-through hole
        translate([1.000, 4.625, -0.01])
            cylinder(d=1.000, h=T+0.02);
    }
}

module Tail() {
    toggle_link(2.000, 3.625, 1.250);
}


// ==========================================================
// SHEET 3 — Clamp
// Clamp — latch bracket from cinva3.jpg
// Two horizontal lines (tab 0.309, bar 2.929) with angled notch between
// Notch: 0.354 and 0.518 walls (parallel, 13.3° from vert), 0.625 bottom
// Left face: 1.035 hypotenuse (vert 1.000, horiz 0.267)
module Clamp() {
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

module Spacer() {
    plate(1.000, 2.750);
}





// ==========================================================
// SHEET 7 — Baseboard and Piston
//
// 1x baseboard:  15.000 x 12.000
//    1.000" dia pivot hole, 2x 0.500" bolt holes
//    8.000 x 2.000 piston slot (5" from bottom, 5" from right)
// 1x piston cap:  6.000 x 6.000
// ==========================================================

module Side() {
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

// --- Shelf: flat plate the brick sits on, spans between slotted sides ---
module Shelf() {
    plate(6.000, 12.000);
}

// --- Shelf bracket: 11x2x0.25, welded under shelf ---
module Bracket() {
    plate(11.000, 2.000);
}

// --- Piston plate: 6x6x0.25, welded in pairs (0.5" thick) ---
// 1.000" dia hole at 0.500" from bottom, centered on width
module Piston() {
    plate_with_hole(6.000, 6.000, 1.000, 3.000, 0.500);
}

// --- End plate: 7.5x6.5x0.25, welded to outside of shelf ---
module EndPlate() {
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
            // R0.625" scoop at peak center
            translate([12 - right_peak_x + 0.625, peak_y])
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

// --- Base brackets: symmetric about Y=0, feet pointing outward ---
color("green")
translate([4.000, -2.750, 0])
    mirror([0, 1, 0])
        Base_Bracket();
color("green")
translate([4.000, 3.000 + T, 0])
    Base_Bracket();

// --- Animation & Assembly ---
// === ANIMATION: Pivot assembly rolls along ramp ===
// _anim: 0 = start (right slope), ~0.5 = peak/notch, 1 = end (left slope)
// Roller rolls up right slope, over peak notch, down left slope
// Use _t_override from command line (-D _t_override=0.5), else $t
_t_override = 0.5;
_anim = (_t_override >= 0) ? _t_override : $t;

// Roller X position driven by _anim
_roller_start_x = 13.500;   // right slope (low side)
_roller_end_x = 7.000;      // left slope (past peak)
_raw_roller_x = _roller_start_x + _anim * (_roller_end_x - _roller_start_x);

// Scoop notch at peak — roller (r=0.5) sits inside scoop (R=0.625)
_scoop_cx = 4.0 + 12 - 6.624 + 0.625;   // 10.001 world X
_scoop_cz = 15.5 + 3.0;                 // 18.500 world Z (at peak surface)
_scoop_r = 0.625;
_roller_r = 0.500;
_scoop_eff = _scoop_r - _roller_r;       // 0.125
// Scoop opening half-width at peak surface
_scoop_half_w = _scoop_r;                // 0.625 (full radius, center at peak)
_in_scoop = (abs(_raw_roller_x - _scoop_cx) <= _scoop_half_w);

// When in scoop, roller snaps to scoop center and sits at bottom
roller_x = _in_scoop ? _scoop_cx : _raw_roller_x;

// Ramp surface Z at roller X (piecewise: right slope / peak / left slope)
// Ramp placed at translate([4, y, 15.5]): local_x = world_x - 4
// Right slope: (11.626, 18.5) to (16.0, 16.5)
// Left slope: (4.0, 15.75) to (9.376, 18.5)
_ramp_lx = _raw_roller_x - 4.0;
_ramp_flat_z =
    (_ramp_lx > 7.626) ? 15.5 + 1.0 + (12 - _ramp_lx) / 4.374 * 2.0 :
    (_ramp_lx < 5.376) ? 15.5 + 0.25 + _ramp_lx / 5.376 * 2.75 :
    15.5 + 3.0;

roller_z = _in_scoop ?
    _scoop_cz - _scoop_r + _roller_r :    // 18.375 — roller bottom at scoop bottom
    _ramp_flat_z + _roller_r;


// Assembly shift: entire Pivot assembly translates with roller
// Rest position: roller in scoop (bottom at scoop bottom)
_asm_dx = roller_x - _scoop_cx;
_asm_dz = roller_z - (_scoop_cz - _scoop_r + _roller_r);

// Spacer world position (moves with assembly)
spacer_x = 6.625 + _asm_dx;
spacer_z = 18.500 + _asm_dz;

// --- Lever — roller goes through lever spacer block hole ---
lever_pin_x = 10.000;   // load bar X (fixed in side slot)
fulcrum_x = 5.000;
fulcrum_z = 7.750;
pin_r = 0.475;
fulcrum_rest_z = fulcrum_z + pin_r;
lever_fulcrum_along_bar = 13.625;
lever_hole_along_bar = 18.625;

// Lever spacer block hole is 14.625" from load bar hole
// Roller position constrains lever angle and load bar Z
_lever_roller_dist = 14.625;
lever_angle = 87;   // tilted toward origin — cross barely touches clamp notch
load_pin_z = roller_z - _lever_roller_dist * sin(lever_angle);

cross_center_y = 0;  // centered on Y=0

// Axle world position (moves with assembly)
_axle_x = 5.022 + _asm_dx;
_axle_z = 23.000 + _asm_dz;

// Cross_Front top-left corner in world coords (lever-driven)
_cf_world_x = lever_pin_x - 18.625*cos(lever_angle) - sin(lever_angle);
_cf_world_z = load_pin_z + 18.625*sin(lever_angle) - cos(lever_angle);

// Clamp angle: scoop on clamp must reach Cross_Front (world coords)
// Scoop offset from axle is constant: (3.255, -0.155)
_scoop_R = sqrt(3.255*3.255 + 0.155*0.155);   // 3.259
_scoop_phi = atan2(-0.155, 3.255);              // -2.73°
_clamp_target_dz = _cf_world_z - _axle_z;
clamp_angle = asin(min(1, max(-1, _clamp_target_dz / _scoop_R))) - _scoop_phi;

// pull_angle not used for rotation — assembly translates along ramp
pull_angle = 0;

// --- Press assembly (centered on Y=0) ---

// --- Side plates — vertical, symmetric about Y=0 ---
// 15x12" plates with slot, bolted to feet
%translate([16.000, -3.000 + T, T])
    rotate([90, 0, 0])
        rotate([0, 0, 90])
            Side();
%mirror([0, 1, 0])
translate([16.000, -3.000 + T, T])
    rotate([90, 0, 0])
        rotate([0, 0, 90])
            Side();

// --- Hinge assembly ---
hinge_cx = 4.250;                // hinge center X
hinge_cy = 3.750;                // hinge center Y (tangent to Side)
hinge_side_top = T + 15.000;     // 15.250, top of Side plates
hinge_pin_d = 0.500;
hinge_od = 1.000;
hinge_cyl_h = 2.000;

// Receiver — white cylinder with hole, welded to +Y Side plate, top flush with Side top
color("white")
translate([hinge_cx, hinge_cy, hinge_side_top - hinge_cyl_h])
    difference() {
        cylinder(d=hinge_od, h=hinge_cyl_h);
        translate([0, 0, -0.01])
            cylinder(d=hinge_pin_d, h=hinge_cyl_h + 0.02);
    }

// Tab — red bracket welded to Top plate, from Ramp to Receiver
color("red")
translate([0, 0, hinge_side_top + T])
    linear_extrude(height=T)
        difference() {
            hull() {
                // Rectangle at ramp end (butts against +Y ramp face)
                translate([hinge_cx - hinge_od/2, ramp_y + T])
                    square([hinge_od, 0.01]);
                // Circle conforming to Receiver
                translate([hinge_cx, hinge_cy])
                    circle(d=hinge_od);
            }
            // Pin hole
            translate([hinge_cx, hinge_cy])
                circle(d=hinge_pin_d);
        }

// Pin — red, drops from Tab through Top into Receiver
color("red")
translate([hinge_cx, hinge_cy, hinge_side_top - hinge_cyl_h + 0.125])
    cylinder(d=hinge_pin_d - 0.060, h=hinge_cyl_h - 0.125 + 2*T);

// --- Top plate + Ramps (hinged assembly) ---
ramp_z = T + 15.000 + T;
ramp_y = 1.000 + 2*T + 0.500;   // 2.000 from center

// Top plate (12.5x6.5)
color("red")
translate([4.000 - T, -3.250, T + 15.000])
    cube([12.500, 6.500, T]);

// Ramps — symmetric about Y=0
color("red")
translate([4.000, -ramp_y + T, ramp_z])
    rotate([90, 0, 0])
        Ramp(depth=T);
color("red")
translate([4.000, ramp_y + T, ramp_z])
    rotate([90, 0, 0])
        Ramp(depth=T);

// --- Shelf (12x6) spanning between the two sides ---
shelf_z = load_pin_z + 6.250;
color("teal")
translate([4.000, -3.000, shelf_z])
    cube([12.000, 6.000, T]);

// --- Braces (11x2) under shelf, welded to pistons — mirrored ---
bracket_inner_y = 3.000 - 0.500 - T;   // 2.250 from center

color("teal")
translate([4.500, -bracket_inner_y - T, shelf_z - 2.000])
    cube([11.000, T, 2.000]);
color("teal")
translate([4.500, bracket_inner_y, shelf_z - 2.000])
    cube([11.000, T, 2.000]);

// --- Piston plates (2 pairs) — mirrored ---
piston_x = 10.000 - 3.000;     // 7.000
piston_z = shelf_z - 7.250;

color("teal")
translate([piston_x, -bracket_inner_y + 0.250, piston_z])
    difference() {
        cube([6.000, 2*T, 7.250]);
        translate([3.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2*T+0.02, $fn=32);
    }
color("teal")
translate([piston_x, bracket_inner_y - 2*T - 0.250, piston_z])
    difference() {
        cube([6.000, 2*T, 7.250]);
        translate([3.000, -0.01, 1.000])
            rotate([-90, 0, 0])
                cylinder(d=1.000, h=2*T+0.02, $fn=32);
    }

spacer_length = 3.000;
roller_y_start = -3.000;   // centered on Y=0, spans between ramps
roller_length = 6.000;

// Fulcrum pin — through side plate holes (FIXED)
color("purple")
translate([fulcrum_x, -4.250, fulcrum_z])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);

// Roller — rolls along ramp surface
color("purple")
translate([roller_x, roller_y_start, roller_z])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=roller_length);

// === MOVING ASSEMBLY — translates along ramp with roller ===
translate([_asm_dx, 0, _asm_dz]) {
} // pause for module definition

// Load bar — constrained to side slot, rises with lever mechanism
color("purple")
translate([lever_pin_x, -4.250, load_pin_z])
    rotate([-90, 0, 0])
        cylinder(d=0.95, h=8.500);

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

// Lever assembly — pivots around load bar, angle tracks roller
color("orange")
translate([lever_pin_x, 0, load_pin_z])
    rotate([0, lever_angle, 0]) {
        // Lever bars — mirrored about Y=0
        for (s = [-1, 1])
            translate([0, s * (4.000 - T), 0])
                translate([-lever_hole_along_bar, T, -1.0])
                    rotate([90, 0, 0])
                        linear_extrude(height=T)
                            lever_bar_profile();

        // Cross_Back (8x2) — at grip end, flat on top of bars
        translate([-lever_hole_along_bar, -4.000, 1.0])
            cube([2.000, 8.000, T]);

        // Cross_Front (8x2) — at grip end, flat on bottom of bars
        translate([-lever_hole_along_bar, -4.000, -1.0 - T])
            cube([2.000, 8.000, T]);

        // Lever spacer block — welded between crosses, with roller hole
        translate([-17.625, -0.750, -1.0])
            difference() {
                cube([4.000, 1.500, 2.000]);
                translate([3.000, -0.01, 1.000])
                    rotate([-90, 0, 0])
                        cylinder(d=1.000, h=1.520);
            }
    }

// Resume MOVING ASSEMBLY — translates along ramp with roller
translate([_asm_dx, 0, _asm_dz]) {

// Spacer — 1" dia, through Pivot/Wing upper holes
color("brown")
translate([6.625, -spacer_length/2, 18.500])
    rotate([-90, 0, 0])
        cylinder(d=1.000, h=spacer_length);

// Pivot block — centered on Y=0
color("brown")
translate([5.625, -1.000, 17.500])
    Pivot();

// Handle — 6' (72") bar in Pivot sunk hole
color("brown")
translate([6.625, 0, 19.500])
    cylinder(d=0.95, h=72.000);

// Axle — 7/16" dia, 3" long, through front block hole
_axle_rest_x = 5.022;
_axle_rest_z = 23.000;
color("purple")
translate([_axle_rest_x, -1.500, _axle_rest_z])
    rotate([-90, 0, 0])
        cylinder(d=0.437, h=3.000);

// Clamp assembly — rotates around Axle to grab Cross_Front
color("pink")
translate([_axle_rest_x, 0, _axle_rest_z])
    rotate([0, -clamp_angle, 0])
        translate([-_axle_rest_x, 0, -_axle_rest_z]) {
            // Clamp brackets — mirrored
            translate([4.625, -1.125, 22.500])
                rotate([90, 0, 0])
                    Clamp();
            translate([4.625, 1.125 + T, 22.500])
                rotate([90, 0, 0])
                    mirror([0, 0, 1])
                        translate([0, 0, -T])
                            Clamp();

            // Cap
            translate([8.505, -2.750/2, 22.500])
                rotate([0, atan(0.267/1.000), 0])
                    cube([T, 2.750, 1.000]);
        }

// Wings — flat against Pivot outer faces, mirrored
color("brown")
translate([11.250, -1.000 - T, 19.500])
    rotate([0, 0, 90]) rotate([0, 90, 0]) Wing();
color("brown")
translate([11.250, 1.000, 19.500])
    rotate([0, 0, 90]) rotate([0, 90, 0]) Wing();

// Tails — inside Pivot Y range, mirrored
color("brown")
translate([11.250, -1.000, 19.500])
    rotate([0, 0, 90]) rotate([0, 90, 0]) Tail();
color("brown")
translate([11.250, 1.000 - T, 19.500])
    rotate([0, 0, 90]) rotate([0, 90, 0]) Tail();

} // === END MOVING ASSEMBLY ===

// --- End plates — welded to outside of shelf ---
%translate([4.000 - T, -3.250, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);
%translate([4.000 + 12.000, -3.250, T + 15.000 - 7.500])
    cube([T, 6.500, 7.500]);

// --- end press assembly ---

/*  --- HIDDEN FOR NOW ---

// --- Side walls ---
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

// --- Row 1: Toggle links ---
row3_y = 13.0;
translate([ox, row3_y, 0])
    ToggleLink_Long();
translate([ox + 2.000 + gap, row3_y, 0])
    ToggleLink_Long();
translate([ox + 2*(2.000 + gap), row3_y, 0])
    ToggleLink_Short();
translate([ox + 3*(2.000 + gap), row3_y, 0])
    ToggleLink_Short();

// --- Row 2: Sides ---
row8_y = row3_y + 3.625 + gap;
translate([ox, row8_y, 0])
    Side_Left();
translate([ox + 15.000 + gap, row8_y, 0])
    Side_Right();

// --- Row 9: Piston parts ---
row9_y = row8_y + 12.000 + gap;
translate([ox, row9_y, 0])
    Shelf();
translate([ox + 6.000 + gap, row9_y, 0])
    Shelf_Left();
translate([ox + 6.000 + gap + 6.000 + gap, row9_y, 0])
    Shelf_Right();
translate([ox + 3*(6.000 + gap), row9_y, 0])
    K_Piston_Left();
translate([ox + 3*(6.000 + gap) + 2.000 + gap, row9_y, 0])
    K_Piston_Right();

*/  // --- END PARTS LAYOUT ---

