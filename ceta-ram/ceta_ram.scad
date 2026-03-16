// CETA-RAM Brick Making Machine — OpenSCAD Model
// Source: https://en.oho.wiki/wiki/Brick_Making_Machine_CETA-RAM_-_for_soil_bricks
// Organization: Centro de Experimentación en Tecnología Apropiada (CETA)
// Redesigned by: OHO e.V. — J. Rosciano (created), A. Morillo (approved)
// Version: 1.1, Date: 28/07/2021
// License: CC-BY-SA 4.0
// All dimensions in mm
//
// Coordinate system:
//   X = width (between sides)
//   Y = depth (front to back)
//   Z = height (vertical)
//
// Assembly origin: center of base structure, bottom

$fn = 36;

// ============================================================
// PARAMETERS
// ============================================================

// Lever angle: 0 = horizontal (pressed), 90 = vertical (up)
lever_angle = 45; // [0:90]

// Show individual assemblies
show_structure  = true;
show_top        = true;
show_piston     = true;
show_support    = true;
show_lever      = true;
show_platform   = true;

// Colors
col_steel  = [0.7, 0.7, 0.75];   // ASTM A36 steel plates
col_rod    = [0.6, 0.6, 0.65];   // DIN C45 rods/tubes
col_wood   = [0.8, 0.6, 0.3];    // Kiln dried wood
col_bolt   = [0.4, 0.4, 0.45];   // Fasteners

// ============================================================
// 1.0 STRUCTURE ASSEMBLY
// ============================================================

// 1.1 Side — 13mm plate, 344 x 203
module side() {
    color(col_steel)
    cube([13, 344, 203]);
}

// 1.2 Base structure — 10mm plate, 432 x 152, holes
module base_structure() {
    color(col_steel)
    difference() {
        cube([432, 152, 10]);
        // 4x ∅13 bolt holes (corners for M12 bolts)
        translate([29, 32, -1]) cylinder(d=13, h=12);
        translate([29, 152-32, -1]) cylinder(d=13, h=12);
        translate([432-29, 32, -1]) cylinder(d=13, h=12);
        translate([432-29, 152-32, -1]) cylinder(d=13, h=12);
        // 2x M14 tapped holes (for bolts structure 1.10)
        translate([432-80, 76, -1]) cylinder(d=14, h=12);
        translate([432-140, 76, -1]) cylinder(d=14, h=12);
    }
}

// 1.3 Beam 1 — C-channel 152x52x8, 457 long, ∅20 hole
module beam1() {
    color(col_steel) {
        difference() {
            union() {
                // Bottom flange
                cube([457, 152, 8]);
                // Left web
                cube([457, 8, 52]);
                // Right web
                translate([0, 152-8, 0]) cube([457, 8, 52]);
            }
            // ∅20 hole at 181 from end, 26 from bottom
            translate([181, -1, 26])
                rotate([-90, 0, 0])
                cylinder(d=20, h=154);
        }
    }
}

// 1.4 Beam 2 — C-channel 152x52x8, 457 long, no hole
module beam2() {
    color(col_steel) {
        // Bottom flange
        cube([457, 152, 8]);
        // Left web
        cube([457, 8, 52]);
        // Right web
        translate([0, 152-8, 0]) cube([457, 8, 52]);
    }
}

// 1.5 Cap insurance — tube ∅44 OD / ∅32 ID, 52 long
module cap_insurance() {
    color(col_rod)
    difference() {
        cylinder(d=44, h=52);
        translate([0, 0, -1]) cylinder(d=32, h=54);
    }
}

// 1.6 Cap insurance 1 — plate 52 x 40 x 6
module cap_insurance_1() {
    color(col_steel)
    cube([52, 40, 6]);
}

// 1.7 Support structure — tube ∅40 OD / ∅20 ID, 36 long
module support_structure() {
    color(col_rod)
    difference() {
        cylinder(d=40, h=36);
        translate([0, 0, -1]) cylinder(d=20, h=38);
    }
}

// 1.8 Support structure 1 — ∅20 rod, 248 long, 2x R3 grooves
module support_structure_1() {
    color(col_rod)
    cylinder(d=20, h=248);
}

// 1.9 Bars structure — ∅60 rod, 457 long
module bars_structure() {
    color(col_rod)
    cylinder(d=60, h=457);
}

// Structure Assembly (1.0)
module structure_assembly() {
    // Base structure (1.2) — centered at origin
    translate([-432/2, -152/2, 0])
        base_structure();

    // Two sides (1.1) at edges of base
    // Left side
    translate([-432/2 + (432-344)/2, -13/2 - 152/2, 10])
        rotate([0, 0, 0])
        side();
    // Right side
    translate([-432/2 + (432-344)/2, 152/2 - 13/2, 10])
        rotate([0, 0, 0])
        side();

    // Beam 1 (1.3) — front, at bottom between sides
    translate([-457/2, -152/2, 10])
        rotate([0, 0, 0])
        beam1();

    // Beam 2 (1.4) — rear, at top between sides
    translate([-457/2, -152/2, 10 + 203 - 52])
        beam2();

    // Two bars structure (1.9) — vertical ∅60 rods
    // Left bar
    translate([-432/2 + (432-344)/2 + 344/4, 0, 10 + 203])
        bars_structure();
    // Right bar
    translate([-432/2 + (432-344)/2 + 3*344/4, 0, 10 + 203])
        bars_structure();

    // Support structure tubes (1.7) at top of bars
    translate([-432/2 + (432-344)/2 + 344/4, 0, 10 + 203 + 457])
        support_structure();
    translate([-432/2 + (432-344)/2 + 3*344/4, 0, 10 + 203 + 457])
        support_structure();

    // Support structure 1 (1.8) — horizontal ∅20 rod through support tubes
    translate([0, 0, 10 + 203 + 457 + 18])
        rotate([0, 90, 0])
        support_structure_1();

    // Cap insurance (1.5) at top center
    translate([0, 0, 10 + 203 + 457 + 36])
        cap_insurance();

    // Cap insurance 1 (1.6) — plate on top of cap
    translate([-52/2, -40/2, 10 + 203 + 457 + 36 + 52])
        cap_insurance_1();
}

// ============================================================
// 2.0 TOP ASSEMBLY
// ============================================================

// 2.1 Top — 10mm plate, 406 x 178, ∅32 hole
module top_plate() {
    color(col_steel)
    difference() {
        cube([406, 178, 10]);
        // ∅32 hole at 28 from edge, 136 from bottom
        translate([28, 136, -1]) cylinder(d=32, h=12);
    }
}

// 2.2 Top support — 13mm plate, 304 x 51, hook end R25, 18° ramp
module top_support() {
    color(col_steel) {
        difference() {
            union() {
                // Main bar 304 x 51 x 13
                cube([304, 51, 13]);
                // Hook end — R25 semicircle at far end
                translate([304 - 25, 51/2, 0])
                    cylinder(r=25, h=13);
            }
            // Hook hole (where it grabs the bar)
            translate([304 - 25, 51/2, -1])
                cylinder(r=12, h=15);
            // 18° ramp cut at the ramp end
            translate([0, 0, 13])
                rotate([0, -18, 0])
                translate([-10, -1, 0])
                cube([100, 53, 30]);
        }
    }
}

// 2.3 Bottom top — ∅32 rod, 105 long
module bottom_top() {
    color(col_rod)
    cylinder(d=32, h=105);
}

// 2.4 Bottom top 1 — 13mm plate, 97 x 26 (approx), R2 chamfers
module bottom_top_1() {
    color(col_steel)
    cube([97, 26, 13]);
}

// Top Assembly (2.0)
module top_assembly() {
    // Top plate (2.1)
    translate([-406/2, -178/2, 0])
        top_plate();

    // Two top supports (2.2) on top of plate
    translate([-304/2, -178/2 + 18, 10])
        top_support();
    translate([-304/2, 178/2 - 18 - 51, 10])
        top_support();

    // Bottom top rod (2.3) hanging below plate
    translate([-406/2 + 28, -178/2 + 136, -105])
        bottom_top();

    // Bottom top 1 (2.4) attached to bottom of rod
    translate([-406/2 + 28 - 97/2, -178/2 + 136 - 26/2, -105 - 13])
        bottom_top_1();
}

// ============================================================
// 3.0 PISTON ASSEMBLY
// ============================================================

// 3.1 Piston top — 10mm plate, 320 x 152, 2x ∅70 holes
module piston_top() {
    color(col_steel)
    difference() {
        cube([320, 152, 10]);
        // Two ∅70 holes at 77 spacing, 76 from bottom
        translate([320/2 - 77/2, 76, -1]) cylinder(d=70, h=12);
        translate([320/2 + 77/2, 76, -1]) cylinder(d=70, h=12);
    }
}

// 3.2 Piston caps — 10mm plate, 216 x 152, ∅44 hole
module piston_caps() {
    color(col_steel)
    difference() {
        cube([216, 152, 10]);
        // ∅44 hole at 44 from right edge, 76 from bottom
        translate([216-44, 76, -1]) cylinder(d=44, h=12);
    }
}

// 3.3 Piston caps 1 — 10mm plate, 305 x 38
module piston_caps_1() {
    color(col_steel)
    cube([305, 38, 10]);
}

// 3.4 Piston rod — tube ∅70 OD / ∅60 ID, 254 long
module piston_rod() {
    color(col_rod)
    difference() {
        cylinder(d=70, h=254);
        translate([0, 0, -1]) cylinder(d=60, h=256);
    }
}

// 3.5 Piston rod 1 — tube ∅44 OD / ∅32 ID, 190 long
module piston_rod_1() {
    color(col_rod)
    difference() {
        cylinder(d=44, h=190);
        translate([0, 0, -1]) cylinder(d=32, h=192);
    }
}

// Piston Assembly (3.0)
module piston_assembly() {
    // Piston top (3.1) — horizontal plate at top
    translate([-320/2, -152/2, 0])
        piston_top();

    // Two piston rods (3.4) hanging down through holes
    translate([-77/2, 0, -254])
        piston_rod();
    translate([77/2, 0, -254])
        piston_rod();

    // Two piston caps (3.2) — vertical plates on sides
    translate([-320/2, -152/2, -182])
        rotate([90, 0, 0])
        translate([0, 0, -10])
        piston_caps();
    translate([-320/2, 152/2, -182])
        rotate([90, 0, 0])
        piston_caps();

    // Two piston caps 1 (3.3) — horizontal strips
    translate([-305/2, -152/2 - 10, -10])
        piston_caps_1();
    translate([-305/2, 152/2, -10])
        piston_caps_1();

    // Piston rod 1 (3.5) — center tube
    translate([0, 0, -190])
        piston_rod_1();
}

// ============================================================
// 4.0 SUPPORT ASSEMBLY
// ============================================================

// 4.1 Support piston — 13mm plate, 636 x 64, 2x ∅32 holes
module support_piston() {
    color(col_steel)
    difference() {
        cube([13, 64, 636]);
        // Bottom hole: 38 from bottom, 32 from edge
        translate([-1, 32, 38]) rotate([0, 90, 0])
            cylinder(d=32, h=15);
        // Top hole: 108 from top (636-108=528)
        translate([-1, 32, 636-108]) rotate([0, 90, 0])
            cylinder(d=32, h=15);
    }
}

// 4.2 Support piston 1 — 13mm plate, 208 x 64
module support_piston_1() {
    color(col_steel)
    cube([13, 64, 208]);
}

// 4.3 Bar support — 13mm plate, 64 x 51, ∅32 hole
module bar_support() {
    color(col_steel)
    difference() {
        cube([13, 64, 51]);
        translate([-1, 32, 26]) rotate([0, 90, 0])
            cylinder(d=32, h=15);
    }
}

// 4.4 Axis support — ∅32 rod, 266 long, R3 grooves
module axis_support() {
    color(col_rod)
    cylinder(d=32, h=266);
}

// 4.5 Internal support — 13mm plate, 126 x 64, ∅32 hole
module internal_support() {
    color(col_steel)
    difference() {
        cube([13, 64, 126]);
        translate([-1, 32, 126-32]) rotate([0, 90, 0])
            cylinder(d=32, h=15);
    }
}

// Support Assembly (4.0)
module support_assembly() {
    spacing = 266;  // width between support pistons

    // Two support pistons (4.1)
    translate([-spacing/2 - 13, -64/2, 0])
        support_piston();
    translate([spacing/2, -64/2, 0])
        support_piston();

    // Two support piston 1 (4.2) — cross pieces at top
    translate([-spacing/2 - 13, -64/2, 636 - 208])
        support_piston_1();
    translate([spacing/2, -64/2, 636 - 208])
        support_piston_1();

    // Two internal supports (4.5)
    translate([-54/2 - 13, -64/2, 636 - 140])
        internal_support();
    translate([54/2, -64/2, 636 - 140])
        internal_support();

    // Two bar supports (4.3) — at bottom
    translate([-spacing/2 - 13 - 13, -64/2, 0])
        bar_support();
    translate([spacing/2 + 13, -64/2, 0])
        bar_support();

    // Axis support rod (4.4) — horizontal through bottom holes
    translate([0, 0, 38])
        rotate([0, 90, 0])
        translate([0, 0, -spacing/2])
        axis_support();
}

// ============================================================
// 5.0 LEVER ASSEMBLY
// ============================================================

// 5.1 Cover bracket — 13mm plate, 138 x 64, 2x ∅32 holes
module cover_bracket() {
    color(col_steel)
    difference() {
        cube([138, 64, 13]);
        // Two ∅32 holes at 32 from edges
        translate([32, 32, -1]) cylinder(d=32, h=15);
        translate([138-32, 32, -1]) cylinder(d=32, h=15);
    }
}

// 5.2 Barrette — ∅32 rod, 240 long, grooves
module barrette() {
    color(col_rod)
    cylinder(d=32, h=240);
}

// 5.3 Barrette 1 — ∅32 rod, 170 long, grooves
module barrette_1() {
    color(col_rod)
    cylinder(d=32, h=170);
}

// 5.4 Barrette 2 — ∅12 rod, 95 long
module barrette_2() {
    color(col_rod)
    cylinder(d=12, h=95);
}

// 5.5 Support barrette — tube ∅50 OD / ∅32 ID, 32 long
module support_barrette() {
    color(col_rod)
    difference() {
        cylinder(d=50, h=32);
        translate([0, 0, -1]) cylinder(d=32, h=34);
    }
}

// 5.6 Side lever — 6mm plate, 142 x 32, 135° bend, ∅13 hole
module side_lever() {
    color(col_steel) {
        // Straight section
        difference() {
            cube([110, 32, 6]);
            // ∅13 hole at end, 16 from end
            translate([110 - 16, 16, -1]) cylinder(d=13, h=8);
        }
        // Bent section at 135°
        translate([0, 0, 0])
            rotate([0, 0, 180-135])
            cube([50, 32, 6]);
    }
}

// 5.7 Side lever 1 — 6mm plate, 90 x 51
module side_lever_1() {
    color(col_steel)
    cube([90, 51, 6]);
}

// 5.8 Cover lever — 50x50x6 angle, 230 long, ∅32 hole
module cover_lever() {
    color(col_steel)
    difference() {
        union() {
            // Vertical leg
            cube([230, 6, 50]);
            // Horizontal leg
            cube([230, 50, 6]);
        }
        // ∅32 hole at 32 from end, 21 from edge
        translate([230-32, -1, 21])
            rotate([-90, 0, 0])
            cylinder(d=32, h=52);
    }
}

// 5.9 Bar lever — ∅44 rod, 450 long (handle)
module bar_lever() {
    color(col_rod)
    cylinder(d=44, h=450);
}

// Lever Assembly (5.0)
module lever_assembly() {
    // The lever pivots at the barrette (5.2) axis
    // Cover brackets (5.1) — two, horizontal at pivot
    translate([-138/2, -64/2, -13/2])
        cover_bracket();
    translate([-138/2, -64/2, 13/2])
        cover_bracket();

    // Cover levers (5.8) — two vertical arms
    lever_length = 356;
    translate([-230/2, -50, 13/2])
        rotate([90, 0, 0])
        translate([0, 0, -6])
        cover_lever();
    translate([-230/2, 50 - 6, 13/2])
        rotate([90, 0, 0])
        translate([0, 0, -6])
        cover_lever();

    // Bar lever (5.9) — handle, extending upward
    translate([0, 0, lever_length])
        bar_lever();

    // Barrette (5.2) — main pivot pin
    translate([0, 0, -240/2])
        rotate([0, 0, 0])
        barrette();

    // Barrette 1 (5.3) — secondary pin
    translate([138/2 - 32, 0, -170/2])
        barrette_1();
}

// ============================================================
// 6.0 FIXING SUPPORT / PLATFORM ASSEMBLY
// ============================================================

// 6.1 Platform — wood, 2000 x 268 x 70
module platform() {
    color(col_wood)
    difference() {
        cube([2000, 268, 70]);
        // 2x ∅25 holes for bars structure
        translate([806, 268/2, -1]) cylinder(d=25, h=72);
        translate([806 + 1083 - 806, 268/2, -1]) cylinder(d=25, h=72);
        // 4x ∅16 holes for M12 bolts
        translate([806 - 50, 268/2 - 40, -1]) cylinder(d=16, h=72);
        translate([806 - 50, 268/2 + 40, -1]) cylinder(d=16, h=72);
        translate([806 + 50, 268/2 - 40, -1]) cylinder(d=16, h=72);
        translate([806 + 50, 268/2 + 40, -1]) cylinder(d=16, h=72);
    }
}

// 6.2 Platform base — wood, 400 x 152 x 51
module platform_base() {
    color(col_wood)
    cube([400, 152, 51]);
}

// 6.3 Flat — 10mm plate, 152 x 52, 2x ∅16 holes
module flat_plate() {
    color(col_steel)
    difference() {
        cube([152, 52, 10]);
        translate([32, 26, -1]) cylinder(d=16, h=12);
        translate([152-32, 26, -1]) cylinder(d=16, h=12);
    }
}

// Platform Assembly (6.0)
module platform_assembly() {
    // Three platform bases (6.2) — cross pieces underneath
    translate([-200, -152/2, 0])
        platform_base();
    translate([2000/2 - 400/2 - 200, -152/2, 0])
        platform_base();
    translate([2000 - 400 - 200, -152/2, 0])
        platform_base();

    // Platform (6.1) — on top of bases
    translate([-200, -268/2, 51])
        platform();

    // Two flats (6.3) — metal plates for bolt-down
    translate([2000/2 - 400/2 - 200 + 100, -52/2, 51 + 70])
        flat_plate();
    translate([2000/2 - 400/2 - 200 + 250, -52/2, 51 + 70])
        flat_plate();
}

// ============================================================
// FULL ASSEMBLY
// ============================================================

module full_assembly() {
    // Platform at ground level
    if (show_platform)
        translate([0, 0, 0])
        platform_assembly();

    // Structure sits on platform
    // Platform top surface is at z = 51 + 70 = 121
    // Structure base sits on platform
    structure_z = 121;
    if (show_structure)
        translate([2000/2 - 200, 0, structure_z])
        structure_assembly();

    // Top assembly sits on top of structure (on top of bars)
    // Bars top: structure_z + 10 + 203 + 457 = structure_z + 670
    top_z = structure_z + 10 + 203 + 457 + 36;
    if (show_top)
        translate([2000/2 - 200, 0, top_z])
        rotate([0, 0, 0])
        top_assembly();

    // Piston assembly inside structure
    // Piston top sits at structure top: beam2 top = structure_z + 10 + 203
    piston_z = structure_z + 10 + 203 - 10;
    if (show_piston)
        translate([2000/2 - 200, 0, piston_z])
        piston_assembly();

    // Support assembly — the tall vertical support arms
    // Sits on beam1 through axis_support hole
    // axis_support at z=38 from support base
    support_z = structure_z + 10;
    if (show_support)
        translate([2000/2 - 200, 0, support_z])
        support_assembly();

    // Lever assembly — pivots at top of support assembly
    // Pivot point at top of support: support_z + 636 - 108
    lever_pivot_z = support_z + 636 - 108;
    if (show_lever)
        translate([2000/2 - 200, 0, lever_pivot_z])
        rotate([0, -lever_angle, 0])
        lever_assembly();
}

// ============================================================
// RENDER
// ============================================================

full_assembly();
