// CETA-RAM Brick Making Machine — OpenSCAD Model (IMPERIAL VERSION)
// Based on: https://en.oho.wiki/wiki/Brick_Making_Machine_CETA-RAM_-_for_soil_bricks
// Original design: CETA / OHO e.V. (CC-BY-SA 4.0)
// Imperial conversion: uses standard US steel sizes
// All dimensions in inches
//
// Coordinate system:
//   X = width (between sides)
//   Y = depth (front to back)
//   Z = height (vertical)
//
// Assembly origin: center of base structure, bottom
//
// ============================================================
// IMPERIAL STEEL SIZE SUBSTITUTIONS
// ============================================================
//
// Metric         → Imperial           Notes
// -------------- → ----------------   -------------------------
// 13mm plate     → 1/2" plate         (12.7mm, -0.3mm)
// 10mm plate     → 3/8" plate         (9.525mm, -0.475mm)
// 6mm plate      → 1/4" plate         (6.35mm, +0.35mm)
// 8mm C-chan web  → 5/16" web          (7.94mm) — use C6x8.2
// ∅60 rod        → 2-3/8" rod         (60.33mm, +0.33mm)
// ∅44 rod        → 1-3/4" rod         (44.45mm, +0.45mm)
// ∅32 rod        → 1-1/4" rod         (31.75mm, -0.25mm)
// ∅20 rod        → 3/4" rod           (19.05mm, -0.95mm)
// ∅12 rod        → 1/2" rod           (12.7mm, +0.7mm)
// ∅70/60 tube    → 2-3/4" OD / 2-3/8" ID tube
// ∅44/32 tube    → 1-3/4" OD / 1-1/4" ID tube
// ∅50/32 bush.   → 2" OD / 1-1/4" ID bushing
// ∅40/20 tube    → 1-1/2" OD / 3/4" ID tube
// 152x52x8 chan  → C6x8.2 (6" x 1.92" x 0.200" web, 0.343" flange)
// M14 bolt       → 1/2"-13 bolt
// M12 bolt       → 1/2"-13 bolt
// 152mm depth    → 6" (brick width)
// 320mm length   → 12-5/8" → 12" (standard brick length)
//
// Brick size: 12" x 6" x ~4" (compressed)
// ============================================================

$fn = 36;

// ============================================================
// PARAMETERS
// ============================================================

lever_angle = 45; // [0:90]

show_structure  = true;
show_top        = true;
show_piston     = true;
show_support    = true;
show_lever      = true;
show_platform   = true;

// Standard imperial plate thicknesses
T_half  = 1/2;     // 1/2" plate (replaces 13mm)
T_3_8   = 3/8;     // 3/8" plate (replaces 10mm)
T_qtr   = 1/4;     // 1/4" plate (replaces 6mm)
T_5_16  = 5/16;    // 5/16" (replaces 8mm C-channel web)

// Standard imperial rod/tube diameters
D_2_375 = 2 + 3/8;     // 2-3/8" rod (replaces ∅60)
D_1_75  = 1 + 3/4;     // 1-3/4" rod (replaces ∅44)
D_1_25  = 1 + 1/4;     // 1-1/4" rod (replaces ∅32)
D_3_4   = 3/4;         // 3/4" rod (replaces ∅20)
D_half  = 1/2;         // 1/2" rod (replaces ∅12)

// Tube OD/ID pairs
T70_OD = 2 + 3/4;  T70_ID = D_2_375;   // piston rod tube
T44_OD = D_1_75;    T44_ID = D_1_25;    // piston rod 1 tube
T50_OD = 2;          T50_ID = D_1_25;    // support barrette bushing
T40_OD = 1 + 1/2;   T40_ID = D_3_4;     // support structure tube
T_cap_OD = D_1_75;   T_cap_ID = D_1_25;  // cap insurance tube

// C-channel: C6x8.2
chan_width = 6;          // flange-to-flange
chan_depth = 1 + 15/16;  // ~1.92" depth
chan_web   = 0.200;      // web thickness
chan_flange = 0.343;     // flange thickness

// Bolt holes
bolt_half_hole = 9/16;  // clearance hole for 1/2" bolt
bolt_half_tap  = 1/2;   // tapped hole for 1/2" bolt

// Colors
col_steel  = [0.7, 0.7, 0.75];
col_rod    = [0.6, 0.6, 0.65];
col_wood   = [0.8, 0.6, 0.3];
col_bolt   = [0.4, 0.4, 0.45];

// ============================================================
// DERIVED DIMENSIONS (scaled from metric, rounded to imperial)
// ============================================================

// Structure
side_length = 13 + 1/2;    // 344mm → 13.54" → 13-1/2"
side_height = 8;            // 203mm → 7.99" → 8"
base_width  = 17;           // 432mm → 17.01" → 17"
base_depth  = 6;            // 152mm → 5.98" → 6"
beam_length = 18;           // 457mm → 17.99" → 18"
beam_depth  = chan_width;   // C6 channel
beam_height = chan_depth;
bars_length = 18;           // 457mm → 18"
struct_outer = 16 + 5/8;   // 423mm → 16.65" → 16-5/8"

// Top assembly
top_width  = 16;            // 406mm → 15.98" → 16"
top_depth  = 7;             // 178mm → 7.01" → 7"
top_support_length = 12;    // 304mm → 11.97" → 12"
top_support_width  = 2;     // 51mm → 2.01" → 2"
bottom_top_length  = 4 + 1/8;  // 105mm → 4.13" → 4-1/8"
bottom_top_1_length = 3 + 13/16; // 97mm → 3.82" → 3-13/16"
bottom_top_1_width  = 1;    // 26mm → 1.02" → 1"
top_hole_offset = 1 + 1/8;  // 28mm → 1.10" → 1-1/8"
top_hole_y = 5 + 3/8;       // 136mm → 5.35" → 5-3/8"

// Piston assembly
piston_top_width = 12 + 5/8;  // 320mm → 12.60" → 12-5/8"
piston_top_depth = 6;          // 152mm → 6"
piston_caps_width = 8 + 1/2;  // 216mm → 8.50" → 8-1/2"
piston_caps_depth = 6;
piston_caps_1_width = 12;     // 305mm → 12.01" → 12"
piston_caps_1_depth = 1 + 1/2; // 38mm → 1.50" → 1-1/2"
piston_rod_length = 10;        // 254mm → 10.0" → 10"
piston_rod_1_length = 7 + 1/2; // 190mm → 7.48" → 7-1/2"
piston_hole_spacing = 3 + 1/16; // 77mm → 3.03" → 3-1/16"
piston_hole_y = 3;             // 76mm → 2.99" → 3"
piston_cap_hole_x = 1 + 3/4;  // 44mm → 1.73" → 1-3/4"
piston_inner_h = 7 + 3/16;    // 182mm → 7.17" → 7-3/16"

// Support assembly
support_height = 25;            // 636mm → 25.04" → 25"
support_width  = 2 + 1/2;      // 64mm → 2.52" → 2-1/2"
support_spacing = 10 + 1/2;    // 266mm → 10.47" → 10-1/2"
support_piston_1_h = 8 + 3/16; // 208mm → 8.19" → 8-3/16"
support_bot_hole = 1 + 1/2;    // 38mm → 1.50" → 1-1/2"
support_top_hole_from_top = 4 + 1/4; // 108mm → 4.25" → 4-1/4"
bar_support_height = 2;        // 51mm → 2.01" → 2"
internal_support_h = 5;        // 126mm → 4.96" → 5"
axis_support_length = 10 + 1/2; // 266mm → 10-1/2"
internal_spacing = 2 + 1/8;    // 54mm → 2.13" → 2-1/8"
support_top_section = 5 + 1/2; // 140mm → 5.51" → 5-1/2"

// Lever assembly
cover_bracket_length = 5 + 7/16; // 138mm → 5.43" → 5-7/16"
cover_bracket_width  = 2 + 1/2;  // 64mm → 2-1/2"
barrette_length = 9 + 7/16;      // 240mm → 9.45" → 9-7/16"
barrette_1_length = 6 + 11/16;   // 170mm → 6.69" → 6-11/16"
barrette_2_length = 3 + 3/4;     // 95mm → 3.74" → 3-3/4"
side_lever_length = 5 + 5/8;     // 142mm → 5.59" → 5-5/8"
side_lever_width  = 1 + 1/4;     // 32mm → 1.26" → 1-1/4"
side_lever_1_length = 3 + 9/16;  // 90mm → 3.54" → 3-9/16"
side_lever_1_width  = 2;         // 51mm → 2"
cover_lever_length = 9 + 1/16;   // 230mm → 9.06" → 9-1/16"
cover_lever_leg = 2;              // 50mm → 1.97" → 2"
bar_lever_length = 17 + 3/4;     // 450mm → 17.72" → 17-3/4"
lever_arm_length = 14;            // 356mm → 14.02" → 14"
support_barrette_length = 1 + 1/4; // 32mm → 1-1/4"

// Platform
platform_length = 78 + 3/4;   // 2000mm → 78.74" → 78-3/4"
platform_width  = 10 + 9/16;  // 268mm → 10.55" → 10-9/16"
platform_height = 2 + 3/4;    // 70mm → 2.76" → 2-3/4"
platform_base_length = 15 + 3/4;  // 400mm → 15.75" → 15-3/4"
platform_base_width  = 6;     // 152mm → 6"
platform_base_height = 2;     // 51mm → 2.01" → 2"
flat_length = 6;               // 152mm → 6"
flat_width  = 2 + 1/16;       // 52mm → 2.05" → 2-1/16"
platform_mount_zone = 30 + 3/4; // 780mm → 30.71" → 30-3/4"
platform_sym = 36 + 3/8;       // 924mm → 36.38" → 36-3/8"
platform_base_depth = 11 + 13/16; // 300mm → 11.81" → 11-13/16"
platform_hole_spacing = 31 + 3/4; // 806mm → 31.73" → 31-3/4"

// ============================================================
// 1.0 STRUCTURE ASSEMBLY
// ============================================================

// 1.1 Side — 1/2" plate, 13-1/2" x 8"
module side() {
    color(col_steel)
    cube([T_half, side_length, side_height]);
}

// 1.2 Base structure — 3/8" plate, 17" x 6"
module base_structure() {
    color(col_steel)
    difference() {
        cube([base_width, base_depth, T_3_8]);
        // 4x bolt clearance holes (corners)
        translate([1-1/8, 1-1/4, -0.1]) cylinder(d=bolt_half_hole, h=T_3_8+0.2);
        translate([1-1/8, base_depth-1-1/4, -0.1]) cylinder(d=bolt_half_hole, h=T_3_8+0.2);
        translate([base_width-1-1/8, 1-1/4, -0.1]) cylinder(d=bolt_half_hole, h=T_3_8+0.2);
        translate([base_width-1-1/8, base_depth-1-1/4, -0.1]) cylinder(d=bolt_half_hole, h=T_3_8+0.2);
        // 2x tapped holes for 1/2" bolts
        translate([base_width-3-1/8, base_depth/2, -0.1]) cylinder(d=bolt_half_tap, h=T_3_8+0.2);
        translate([base_width-5-1/2, base_depth/2, -0.1]) cylinder(d=bolt_half_tap, h=T_3_8+0.2);
    }
}

// 1.3 Beam 1 — C6x8.2 channel, 18" long, 3/4" hole
module beam1() {
    color(col_steel) {
        difference() {
            union() {
                cube([beam_length, chan_width, chan_flange]);
                cube([beam_length, chan_web, chan_depth]);
                translate([0, chan_width - chan_web, 0])
                    cube([beam_length, chan_web, chan_depth]);
            }
            // 3/4" hole at 7-1/8" from end, 1" from bottom
            translate([7+1/8, -0.1, 1])
                rotate([-90, 0, 0])
                cylinder(d=D_3_4, h=chan_width+0.2);
        }
    }
}

// 1.4 Beam 2 — C6x8.2 channel, 18" long, no hole
module beam2() {
    color(col_steel) {
        cube([beam_length, chan_width, chan_flange]);
        cube([beam_length, chan_web, chan_depth]);
        translate([0, chan_width - chan_web, 0])
            cube([beam_length, chan_web, chan_depth]);
    }
}

// 1.5 Cap insurance — 1-3/4" OD / 1-1/4" ID tube, 2-1/16" long
module cap_insurance() {
    color(col_rod)
    difference() {
        cylinder(d=T_cap_OD, h=2+1/16);
        translate([0, 0, -0.1]) cylinder(d=T_cap_ID, h=2+1/16+0.2);
    }
}

// 1.6 Cap insurance 1 — 1/4" plate, 2-1/16" x 1-9/16"
module cap_insurance_1() {
    color(col_steel)
    cube([2+1/16, 1+9/16, T_qtr]);
}

// 1.7 Support structure — 1-1/2" OD / 3/4" ID tube, 1-7/16" long
module support_structure() {
    color(col_rod)
    difference() {
        cylinder(d=T40_OD, h=1+7/16);
        translate([0, 0, -0.1]) cylinder(d=T40_ID, h=1+7/16+0.2);
    }
}

// 1.8 Support structure 1 — 3/4" rod, 9-3/4" long
module support_structure_1() {
    color(col_rod)
    cylinder(d=D_3_4, h=9+3/4);
}

// 1.9 Bars structure — 2-3/8" rod, 18" long
module bars_structure() {
    color(col_rod)
    cylinder(d=D_2_375, h=bars_length);
}

// Structure Assembly (1.0)
module structure_assembly() {
    side_offset = (base_width - side_length) / 2;

    translate([-base_width/2, -base_depth/2, 0])
        base_structure();

    // Two sides
    translate([-base_width/2 + side_offset, -T_half/2 - base_depth/2, T_3_8])
        side();
    translate([-base_width/2 + side_offset, base_depth/2 - T_half/2, T_3_8])
        side();

    // Beam 1 — bottom
    translate([-beam_length/2, -base_depth/2, T_3_8])
        beam1();

    // Beam 2 — top
    translate([-beam_length/2, -base_depth/2, T_3_8 + side_height - chan_depth])
        beam2();

    // Two bars structure — vertical rods on top of sides
    translate([-base_width/2 + side_offset + side_length/4, 0, T_3_8 + side_height])
        bars_structure();
    translate([-base_width/2 + side_offset + 3*side_length/4, 0, T_3_8 + side_height])
        bars_structure();

    // Support structure tubes at top of bars
    translate([-base_width/2 + side_offset + side_length/4, 0, T_3_8 + side_height + bars_length])
        support_structure();
    translate([-base_width/2 + side_offset + 3*side_length/4, 0, T_3_8 + side_height + bars_length])
        support_structure();

    // Support structure 1 — horizontal rod through support tubes
    translate([0, 0, T_3_8 + side_height + bars_length + (1+7/16)/2])
        rotate([0, 90, 0])
        support_structure_1();

    // Cap insurance at top
    translate([0, 0, T_3_8 + side_height + bars_length + 1+7/16])
        cap_insurance();

    // Cap insurance 1 plate
    translate([-(2+1/16)/2, -(1+9/16)/2, T_3_8 + side_height + bars_length + 1+7/16 + 2+1/16])
        cap_insurance_1();
}

// ============================================================
// 2.0 TOP ASSEMBLY
// ============================================================

// 2.1 Top — 3/8" plate, 16" x 7"
module top_plate() {
    color(col_steel)
    difference() {
        cube([top_width, top_depth, T_3_8]);
        translate([top_hole_offset, top_hole_y, -0.1])
            cylinder(d=D_1_25, h=T_3_8+0.2);
    }
}

// 2.2 Top support — 1/2" plate, 12" x 2", hook end R1", 18° ramp
module top_support() {
    color(col_steel) {
        difference() {
            union() {
                cube([top_support_length, top_support_width, T_half]);
                translate([top_support_length - 1, top_support_width/2, 0])
                    cylinder(r=1, h=T_half);
            }
            translate([top_support_length - 1, top_support_width/2, -0.1])
                cylinder(r=0.5, h=T_half+0.2);
            translate([0, 0, T_half])
                rotate([0, -18, 0])
                translate([-0.5, -0.1, 0])
                cube([4, top_support_width+0.2, 1.5]);
        }
    }
}

// 2.3 Bottom top — 1-1/4" rod, 4-1/8" long
module bottom_top() {
    color(col_rod)
    cylinder(d=D_1_25, h=bottom_top_length);
}

// 2.4 Bottom top 1 — 1/2" plate, 3-13/16" x 1"
module bottom_top_1() {
    color(col_steel)
    cube([bottom_top_1_length, bottom_top_1_width, T_half]);
}

// Top Assembly (2.0)
module top_assembly() {
    translate([-top_width/2, -top_depth/2, 0])
        top_plate();

    translate([-top_support_length/2, -top_depth/2 + 3/4, T_3_8])
        top_support();
    translate([-top_support_length/2, top_depth/2 - 3/4 - top_support_width, T_3_8])
        top_support();

    translate([-top_width/2 + top_hole_offset, -top_depth/2 + top_hole_y, -bottom_top_length])
        bottom_top();

    translate([-top_width/2 + top_hole_offset - bottom_top_1_length/2,
               -top_depth/2 + top_hole_y - bottom_top_1_width/2,
               -bottom_top_length - T_half])
        bottom_top_1();
}

// ============================================================
// 3.0 PISTON ASSEMBLY
// ============================================================

// 3.1 Piston top — 3/8" plate, 12-5/8" x 6", 2x 2-3/4" holes
module piston_top() {
    color(col_steel)
    difference() {
        cube([piston_top_width, piston_top_depth, T_3_8]);
        translate([piston_top_width/2 - piston_hole_spacing/2, piston_hole_y, -0.1])
            cylinder(d=T70_OD, h=T_3_8+0.2);
        translate([piston_top_width/2 + piston_hole_spacing/2, piston_hole_y, -0.1])
            cylinder(d=T70_OD, h=T_3_8+0.2);
    }
}

// 3.2 Piston caps — 3/8" plate, 8-1/2" x 6", 1-3/4" hole
module piston_caps() {
    color(col_steel)
    difference() {
        cube([piston_caps_width, piston_caps_depth, T_3_8]);
        translate([piston_caps_width - piston_cap_hole_x, piston_hole_y, -0.1])
            cylinder(d=D_1_75, h=T_3_8+0.2);
    }
}

// 3.3 Piston caps 1 — 3/8" plate, 12" x 1-1/2"
module piston_caps_1() {
    color(col_steel)
    cube([piston_caps_1_width, piston_caps_1_depth, T_3_8]);
}

// 3.4 Piston rod — 2-3/4" OD / 2-3/8" ID tube, 10" long
module piston_rod() {
    color(col_rod)
    difference() {
        cylinder(d=T70_OD, h=piston_rod_length);
        translate([0, 0, -0.1]) cylinder(d=T70_ID, h=piston_rod_length+0.2);
    }
}

// 3.5 Piston rod 1 — 1-3/4" OD / 1-1/4" ID tube, 7-1/2" long
module piston_rod_1() {
    color(col_rod)
    difference() {
        cylinder(d=T44_OD, h=piston_rod_1_length);
        translate([0, 0, -0.1]) cylinder(d=T44_ID, h=piston_rod_1_length+0.2);
    }
}

// Piston Assembly (3.0)
module piston_assembly() {
    translate([-piston_top_width/2, -piston_top_depth/2, 0])
        piston_top();

    translate([-piston_hole_spacing/2, 0, -piston_rod_length])
        piston_rod();
    translate([piston_hole_spacing/2, 0, -piston_rod_length])
        piston_rod();

    translate([-piston_top_width/2, -piston_top_depth/2, -piston_inner_h])
        rotate([90, 0, 0])
        translate([0, 0, -T_3_8])
        piston_caps();
    translate([-piston_top_width/2, piston_top_depth/2, -piston_inner_h])
        rotate([90, 0, 0])
        piston_caps();

    translate([-piston_caps_1_width/2, -piston_top_depth/2 - T_3_8, -T_3_8])
        piston_caps_1();
    translate([-piston_caps_1_width/2, piston_top_depth/2, -T_3_8])
        piston_caps_1();

    translate([0, 0, -piston_rod_1_length])
        piston_rod_1();
}

// ============================================================
// 4.0 SUPPORT ASSEMBLY
// ============================================================

// 4.1 Support piston — 1/2" plate, 25" x 2-1/2", 2x 1-1/4" holes
module support_piston() {
    color(col_steel)
    difference() {
        cube([T_half, support_width, support_height]);
        translate([-0.1, support_width/2, support_bot_hole])
            rotate([0, 90, 0])
            cylinder(d=D_1_25, h=T_half+0.2);
        translate([-0.1, support_width/2, support_height - support_top_hole_from_top])
            rotate([0, 90, 0])
            cylinder(d=D_1_25, h=T_half+0.2);
    }
}

// 4.2 Support piston 1 — 1/2" plate, 8-3/16" x 2-1/2"
module support_piston_1() {
    color(col_steel)
    cube([T_half, support_width, support_piston_1_h]);
}

// 4.3 Bar support — 1/2" plate, 2-1/2" x 2", 1-1/4" hole
module bar_support() {
    color(col_steel)
    difference() {
        cube([T_half, support_width, bar_support_height]);
        translate([-0.1, support_width/2, bar_support_height/2])
            rotate([0, 90, 0])
            cylinder(d=D_1_25, h=T_half+0.2);
    }
}

// 4.4 Axis support — 1-1/4" rod, 10-1/2" long
module axis_support() {
    color(col_rod)
    cylinder(d=D_1_25, h=axis_support_length);
}

// 4.5 Internal support — 1/2" plate, 5" x 2-1/2", 1-1/4" hole
module internal_support() {
    color(col_steel)
    difference() {
        cube([T_half, support_width, internal_support_h]);
        translate([-0.1, support_width/2, internal_support_h - D_1_25])
            rotate([0, 90, 0])
            cylinder(d=D_1_25, h=T_half+0.2);
    }
}

// Support Assembly (4.0)
module support_assembly() {
    // Two support pistons
    translate([-support_spacing/2 - T_half, -support_width/2, 0])
        support_piston();
    translate([support_spacing/2, -support_width/2, 0])
        support_piston();

    // Two support piston 1 — cross pieces at top
    translate([-support_spacing/2 - T_half, -support_width/2, support_height - support_piston_1_h])
        support_piston_1();
    translate([support_spacing/2, -support_width/2, support_height - support_piston_1_h])
        support_piston_1();

    // Two internal supports
    translate([-internal_spacing/2 - T_half, -support_width/2, support_height - support_top_section])
        internal_support();
    translate([internal_spacing/2, -support_width/2, support_height - support_top_section])
        internal_support();

    // Two bar supports at bottom
    translate([-support_spacing/2 - T_half - T_half, -support_width/2, 0])
        bar_support();
    translate([support_spacing/2 + T_half, -support_width/2, 0])
        bar_support();

    // Axis support rod — horizontal through bottom holes
    translate([0, 0, support_bot_hole])
        rotate([0, 90, 0])
        translate([0, 0, -support_spacing/2])
        axis_support();
}

// ============================================================
// 5.0 LEVER ASSEMBLY
// ============================================================

// 5.1 Cover bracket — 1/2" plate, 5-7/16" x 2-1/2", 2x 1-1/4" holes
module cover_bracket() {
    color(col_steel)
    difference() {
        cube([cover_bracket_length, cover_bracket_width, T_half]);
        translate([D_1_25, cover_bracket_width/2, -0.1])
            cylinder(d=D_1_25, h=T_half+0.2);
        translate([cover_bracket_length - D_1_25, cover_bracket_width/2, -0.1])
            cylinder(d=D_1_25, h=T_half+0.2);
    }
}

// 5.2 Barrette — 1-1/4" rod, 9-7/16" long
module barrette() {
    color(col_rod)
    cylinder(d=D_1_25, h=barrette_length);
}

// 5.3 Barrette 1 — 1-1/4" rod, 6-11/16" long
module barrette_1() {
    color(col_rod)
    cylinder(d=D_1_25, h=barrette_1_length);
}

// 5.4 Barrette 2 — 1/2" rod, 3-3/4" long
module barrette_2() {
    color(col_rod)
    cylinder(d=D_half, h=barrette_2_length);
}

// 5.5 Support barrette — 2" OD / 1-1/4" ID bushing, 1-1/4" long
module support_barrette() {
    color(col_rod)
    difference() {
        cylinder(d=T50_OD, h=support_barrette_length);
        translate([0, 0, -0.1]) cylinder(d=T50_ID, h=support_barrette_length+0.2);
    }
}

// 5.6 Side lever — 1/4" plate, 5-5/8" x 1-1/4", 135° bend, 1/2" hole
module side_lever() {
    color(col_steel) {
        straight = 4 + 5/16;
        difference() {
            cube([straight, side_lever_width, T_qtr]);
            translate([straight - 5/8, side_lever_width/2, -0.1])
                cylinder(d=bolt_half_hole, h=T_qtr+0.2);
        }
        rotate([0, 0, 180-135])
            cube([2, side_lever_width, T_qtr]);
    }
}

// 5.7 Side lever 1 — 1/4" plate, 3-9/16" x 2"
module side_lever_1() {
    color(col_steel)
    cube([side_lever_1_length, side_lever_1_width, T_qtr]);
}

// 5.8 Cover lever — 2"x2"x1/4" angle, 9-1/16" long, 1-1/4" hole
module cover_lever() {
    color(col_steel)
    difference() {
        union() {
            cube([cover_lever_length, T_qtr, cover_lever_leg]);
            cube([cover_lever_length, cover_lever_leg, T_qtr]);
        }
        translate([cover_lever_length - D_1_25, -0.1, cover_lever_leg/2 + 1/8])
            rotate([-90, 0, 0])
            cylinder(d=D_1_25, h=cover_lever_leg+0.2);
    }
}

// 5.9 Bar lever — 1-3/4" rod, 17-3/4" long (handle)
module bar_lever() {
    color(col_rod)
    cylinder(d=D_1_75, h=bar_lever_length);
}

// Lever Assembly (5.0)
module lever_assembly() {
    translate([-cover_bracket_length/2, -cover_bracket_width/2, -T_half/2])
        cover_bracket();
    translate([-cover_bracket_length/2, -cover_bracket_width/2, T_half/2])
        cover_bracket();

    translate([-cover_lever_length/2, -cover_lever_leg, T_half/2])
        rotate([90, 0, 0])
        translate([0, 0, -T_qtr])
        cover_lever();
    translate([-cover_lever_length/2, cover_lever_leg - T_qtr, T_half/2])
        rotate([90, 0, 0])
        translate([0, 0, -T_qtr])
        cover_lever();

    translate([0, 0, lever_arm_length])
        bar_lever();

    translate([0, 0, -barrette_length/2])
        barrette();

    translate([cover_bracket_length/2 - D_1_25, 0, -barrette_1_length/2])
        barrette_1();
}

// ============================================================
// 6.0 FIXING SUPPORT / PLATFORM ASSEMBLY
// ============================================================

// 6.1 Platform — wood, 78-3/4" x 10-9/16" x 2-3/4"
module platform() {
    color(col_wood)
    difference() {
        cube([platform_length, platform_width, platform_height]);
        // 2x 1" holes for bars
        translate([platform_hole_spacing, platform_width/2, -0.1])
            cylinder(d=1, h=platform_height+0.2);
        translate([platform_hole_spacing + 10+7/8, platform_width/2, -0.1])
            cylinder(d=1, h=platform_height+0.2);
        // 4x 5/8" holes for bolts
        translate([platform_hole_spacing - 2, platform_width/2 - 1.5, -0.1])
            cylinder(d=5/8, h=platform_height+0.2);
        translate([platform_hole_spacing - 2, platform_width/2 + 1.5, -0.1])
            cylinder(d=5/8, h=platform_height+0.2);
        translate([platform_hole_spacing + 2, platform_width/2 - 1.5, -0.1])
            cylinder(d=5/8, h=platform_height+0.2);
        translate([platform_hole_spacing + 2, platform_width/2 + 1.5, -0.1])
            cylinder(d=5/8, h=platform_height+0.2);
    }
}

// 6.2 Platform base — wood, 15-3/4" x 6" x 2"
module platform_base() {
    color(col_wood)
    cube([platform_base_length, platform_base_width, platform_base_height]);
}

// 6.3 Flat — 3/8" plate, 6" x 2-1/16", 2x 5/8" holes
module flat_plate() {
    color(col_steel)
    difference() {
        cube([flat_length, flat_width, T_3_8]);
        translate([D_1_25, flat_width/2, -0.1])
            cylinder(d=5/8, h=T_3_8+0.2);
        translate([flat_length - D_1_25, flat_width/2, -0.1])
            cylinder(d=5/8, h=T_3_8+0.2);
    }
}

// Platform Assembly (6.0)
module platform_assembly() {
    offset_x = 8;  // offset from left end

    // Three bases
    translate([-offset_x, -platform_base_width/2, 0])
        platform_base();
    translate([platform_length/2 - platform_base_length/2 - offset_x, -platform_base_width/2, 0])
        platform_base();
    translate([platform_length - platform_base_length - offset_x, -platform_base_width/2, 0])
        platform_base();

    // Platform on bases
    translate([-offset_x, -platform_width/2, platform_base_height])
        platform();

    // Two flats
    translate([platform_length/2 - platform_base_length/2 - offset_x + 4, -flat_width/2,
               platform_base_height + platform_height])
        flat_plate();
    translate([platform_length/2 - platform_base_length/2 - offset_x + 10, -flat_width/2,
               platform_base_height + platform_height])
        flat_plate();
}

// ============================================================
// FULL ASSEMBLY
// ============================================================

module full_assembly() {
    platform_top = platform_base_height + platform_height;  // 2 + 2.75 = 4.75"

    if (show_platform)
        platform_assembly();

    structure_x = platform_length/2 - 8;
    structure_z = platform_top;

    if (show_structure)
        translate([structure_x, 0, structure_z])
        structure_assembly();

    // Top assembly on bars
    top_z = structure_z + T_3_8 + side_height + bars_length + 1+7/16;
    if (show_top)
        translate([structure_x, 0, top_z])
        top_assembly();

    // Piston inside structure
    piston_z = structure_z + T_3_8 + side_height - T_3_8;
    if (show_piston)
        translate([structure_x, 0, piston_z])
        piston_assembly();

    // Support assembly
    support_z = structure_z + T_3_8;
    if (show_support)
        translate([structure_x, 0, support_z])
        support_assembly();

    // Lever
    lever_pivot_z = support_z + support_height - support_top_hole_from_top;
    if (show_lever)
        translate([structure_x, 0, lever_pivot_z])
        rotate([0, -lever_angle, 0])
        lever_assembly();
}

// ============================================================
// RENDER
// ============================================================

full_assembly();
