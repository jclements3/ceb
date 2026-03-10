/*
 * CINVA-Ram Block Press — Assembly Model
 *
 * Shows all parts in their assembled positions.
 * Based on engineering drawings (cinva0-7) and
 * reference photos (Blockpress*.jpg).
 *
 * Coordinate system:
 *   X = left / right
 *   Y = front (toward operator) / back (toward baseboard)
 *   Z = up / down (vertical)
 *
 * Units: inches.
 */

use <cinva_ram.scad>;

$fn = 48;

T = 0.250;

// ============================================================
// Key reference positions
// ============================================================

// Baseboard stands vertical at the back (Y=0 plane)
// 15" wide in X, 12" tall in Z
baseboard_w = 15.000;
baseboard_h = 12.000;

// Mold box is centered on baseboard in X
// Side walls face X (thin in X), extend in Y away from baseboard
// End walls face Y (thin in Y), span between side walls
mold_inner_w = 6.000;   // between side walls (X), = short end wall width
mold_inner_d = 6.750;   // between end walls (Y), = side wall width - 2*T
side_wall_len = 7.250;  // side wall dimension in Y
side_wall_h = 6.000;    // side wall height

// Mold box bottom Z — sits above the baseboard slot
mold_z = 6.500;

// Mold box centered on baseboard
mold_x_left = (baseboard_w - mold_inner_w) / 2 - T;  // left side wall outer face

// Baseboard pivot hole (for handle)
pivot_x = 5.000;
pivot_z = 9.500;

// Piston position (adjustable — 0 = flush with mold bottom)
piston_rise = 0.0;  // set to ~4 for "pressed" position

// Handle angle (0 = horizontal, positive = raised)
handle_angle = 45;  // degrees from horizontal

// Cover angle (0 = closed, 90 = fully open)
cover_angle = 70;


// ============================================================
// Colors for clarity
// ============================================================

clr_frame     = [0.45, 0.42, 0.40];  // baseboard, dark steel
clr_mold      = [0.55, 0.52, 0.50];  // mold box walls
clr_piston    = [0.60, 0.58, 0.55];  // piston
clr_cover     = [0.50, 0.48, 0.45];  // cover
clr_handle    = [0.40, 0.38, 0.35];  // handle
clr_toggle    = [0.65, 0.55, 0.45];  // toggle links
clr_bearing   = [0.50, 0.45, 0.40];  // bearing plates
clr_latch     = [0.55, 0.50, 0.45];  // latch
clr_pin       = [0.70, 0.70, 0.70];  // pivot pins


// ============================================================
// 1" diameter pivot pins (shop-made from round bar)
// ============================================================

module pin(length) {
    color(clr_pin)
        cylinder(d=0.95, h=length, center=true);
}


// ============================================================
// BASEBOARD (Part D) — vertical frame plate
// ============================================================

module assy_baseboard() {
    color(clr_frame)
    // Stand the baseboard vertical in XZ plane at Y=0
    translate([0, T, 0])
        rotate([90, 0, 0])
            D_Side();
}


// ============================================================
// MOLD BOX (Part C) — four walls welded into open-ended box
// ============================================================

module assy_mold_box() {
    // Left side wall — stands in YZ plane
    color(clr_mold)
    translate([mold_x_left, T, mold_z])
        rotate([0, 0, 0])
            cube([T, side_wall_len, side_wall_h]);

    // Right side wall
    color(clr_mold)
    translate([mold_x_left + T + mold_inner_w, T, mold_z])
        cube([T, side_wall_len, side_wall_h]);

    // Short end wall (near baseboard)
    // Fits between side walls
    color(clr_mold)
    translate([mold_x_left + T, T, mold_z])
        cube([mold_inner_w, T, 11.500]);

    // Tall end wall (far from baseboard)
    // 6.500" wide — extends 0.250" past each side wall
    color(clr_mold)
    translate([mold_x_left + T - 0.250, T + side_wall_len - T, mold_z])
        cube([6.500, T, 12.000]);
}


// ============================================================
// PISTON (Part K) — slides vertically inside mold box
//
// The piston is a rectangular body topped with the 6x6 cap.
// The body extends below the mold box through the guide plates.
// A 1" hole through the body connects to the toggle mechanism.
// ============================================================

module assy_piston() {
    cap_size = 5.750;  // slightly smaller than cavity for clearance
    body_h = 4.000;    // piston body below cap
    body_w = 1.750;    // body width (visible in Blockpress003.jpg)
    body_d = 5.500;    // body depth

    piston_z = mold_z + piston_rise;

    color(clr_piston) {
        // Cap — top pressing face
        translate([mold_x_left + T + (mold_inner_w - cap_size)/2,
                   T + T + (mold_inner_d - cap_size)/2,
                   piston_z])
            cube([cap_size, cap_size, T]);

        // Body — extends below cap
        translate([mold_x_left + T + (mold_inner_w - body_w)/2,
                   T + T + (mold_inner_d - body_d)/2,
                   piston_z - body_h])
            difference() {
                cube([body_w, body_d, body_h]);
                // 1" pivot hole through body (for toggle pin)
                translate([-0.1, body_d/2, body_h * 0.3])
                    rotate([0, 90, 0])
                        cylinder(d=1.000, h=body_w+0.2);
            }
    }
}


// ============================================================
// GUIDE PLATES (Parts I & J) — welded to mold box bottom
// ============================================================

module assy_guide_plates() {
    color(clr_bearing) {
        // Left guide plate — on left side wall, below mold box
        translate([mold_x_left - 0.5, T + side_wall_len/2 - 1.5, mold_z - 2.5])
            rotate([0, 0, 0])
                cube([T + 0.5, 3.000, 2.500]);

        // Right guide plate
        translate([mold_x_left + T + mold_inner_w, T + side_wall_len/2 - 1.5, mold_z - 2.5])
            cube([T + 0.5, 3.000, 2.500]);
    }
}


// ============================================================
// UPPER SADDLE / BEARING PLATES (Part B)
// Welded to piston body, provide pivot for toggle links
// ============================================================

module assy_bearing_plates() {
    piston_z = mold_z + piston_rise;
    body_h = 4.000;
    plate_z = piston_z - body_h * 0.7;

    color(clr_bearing) {
        // Left bearing plate on piston body
        translate([mold_x_left + T + mold_inner_w/2 - 1.5 - T,
                   T + side_wall_len/2 - 1.000,
                   plate_z - 1.000])
            rotate([90, 0, 0])
                translate([0, 0, 0])
                    cube([3.000, 2.000, T]);

        // Right bearing plate
        translate([mold_x_left + T + mold_inner_w/2 + 1.5,
                   T + side_wall_len/2 - 1.000,
                   plate_z - 1.000])
            rotate([90, 0, 0])
                cube([3.000, 2.000, T]);
    }
}


// ============================================================
// HANDLE (Part N) — pivots at baseboard, operator pulls down
// ============================================================

module assy_handle() {
    bar_len = 19.625;
    bar_w = 2.000;
    cross_upper = 11.000;
    cross_lower = 8.000;

    // Handle spacing (distance between the two bars)
    bar_spacing = 6.000;

    color(clr_handle)
    // Pivot at baseboard hole
    translate([pivot_x, T/2, pivot_z])
        rotate([0, -handle_angle, 0]) {
            // Pivot is 1" from end of bar, so offset
            translate([-1.000, -bar_spacing/2 - bar_w/2, -bar_w/2]) {
                // Left handle bar
                cube([bar_len, bar_w, T]);

                // Right handle bar
                translate([0, bar_spacing + bar_w - T, 0])
                    cube([bar_len, bar_w, T]);

                // Upper cross bar (near pivot end)
                translate([0.5, bar_w, 0])
                    cube([T, bar_spacing - T, bar_w]);

                // Lower cross bar (toward grip end)
                translate([bar_len * 0.6, bar_w + (bar_spacing - cross_lower + bar_w)/2, 0])
                    cube([T, cross_lower - bar_w, bar_w]);
            }
        }
}


// ============================================================
// TOGGLE LINKS — connect handle to piston
// Two pairs: long links (upper) and short links (lower)
// ============================================================

module assy_toggle_links() {
    // Approximate toggle positions
    // Upper pivot: on the handle, near the cross bar
    // Lower pivot: on the piston bearing plates

    piston_z = mold_z + piston_rise;
    toggle_upper_z = pivot_z - 2.0;  // below handle pivot
    toggle_lower_z = piston_z - 3.5; // at piston bearing plates

    link_y_offset = T + side_wall_len/2;

    color(clr_toggle) {
        // Left pair
        translate([pivot_x - 0.5, link_y_offset - 2.5, 0]) {
            // Long link (from handle area down)
            translate([0, 0, toggle_upper_z])
                rotate([90, 0, 0])
                    translate([0, 0, 0])
                        cube([T, 3.625, 2.000]);

            // Short link (from toggle knee to piston)
            translate([0, 0, toggle_lower_z])
                rotate([90, 0, 0])
                    cube([T, 3.000, 2.000]);
        }

        // Right pair
        translate([pivot_x - 0.5, link_y_offset + 0.5, 0]) {
            translate([0, 0, toggle_upper_z])
                rotate([90, 0, 0])
                    cube([T, 3.625, 2.000]);

            translate([0, 0, toggle_lower_z])
                rotate([90, 0, 0])
                    cube([T, 3.000, 2.000]);
        }
    }
}


// ============================================================
// LEVER LATCH (Part M) — holds handle in raised position
// Welded to tall end wall near the top
// ============================================================

module assy_latch() {
    latch_z = mold_z + 11.000;  // near top of tall end wall

    color(clr_latch) {
        // Left bracket
        translate([mold_x_left + T + 0.5,
                   T + side_wall_len - T - 0.1,
                   latch_z])
            rotate([90, 0, 0])
                cube([4.147, 1.035, T]);

        // Right bracket
        translate([mold_x_left + T + mold_inner_w - 4.647,
                   T + side_wall_len - T - 0.1,
                   latch_z])
            rotate([90, 0, 0])
                cube([4.147, 1.035, T]);
    }
}


// ============================================================
// COVER (Part A) — V-shaped lid, hinges at top of end walls
// ============================================================

module assy_cover() {
    // Cover hinges at the top of the tall end wall
    hinge_x = mold_x_left + T + mold_inner_w / 2;
    hinge_y = T + side_wall_len - T/2;  // at tall end wall
    hinge_z = mold_z + 12.000;          // top of tall end wall

    color(clr_cover)
    translate([hinge_x, hinge_y, hinge_z])
        rotate([cover_angle, 0, 0])   // open/close rotation
            translate([-6.000, -3.250, 0])  // center the cover
                A_Cover();
}


// ============================================================
// PIVOT PINS — 1" round bar through pivot holes
// ============================================================

module assy_pins() {
    // Handle pivot pin (through baseboard)
    translate([pivot_x, T/2, pivot_z])
        rotate([90, 0, 0])
            pin(8.0);

    // Mold box side wall pins (cover hinge / mounting)
    // Through side wall holes at 6.250" from front, 3.000" from bottom
    translate([mold_x_left + T/2,
               T + 6.250,
               mold_z + 3.000])
        rotate([0, 90, 0])
            pin(mold_inner_w + 2*T + 1.0);
}


// ============================================================
// FOOT BRACKETS — L-shaped mounting feet at baseboard bottom
// ============================================================

module assy_foot_brackets() {
    foot_inset = 2.000;  // inset from baseboard edges
    foot_len   = 72.000; // 6 feet

    color(clr_frame) {
        // Left foot bracket — runs front-to-back (Y axis)
        // Centered on baseboard in Y, vertical leg against baseboard
        translate([foot_inset, -foot_len/2 + baseboard_h/2, 0])
            rotate([0, 0, 90])
                Base_Bracket();

        // Right foot bracket
        translate([baseboard_w - foot_inset, -foot_len/2 + baseboard_h/2, 0])
            rotate([0, 0, 90])
                Base_Bracket();
    }
}


// ============================================================
// ASSEMBLE EVERYTHING
// ============================================================

assy_baseboard();
assy_foot_brackets();
assy_mold_box();
assy_piston();
assy_guide_plates();
assy_bearing_plates();
assy_handle();
assy_toggle_links();
assy_latch();
assy_cover();
assy_pins();

// Ground reference plane (optional — comment out if unwanted)
%translate([-2, -5, 0])
    cube([baseboard_w + 4, 15, 0.01]);
