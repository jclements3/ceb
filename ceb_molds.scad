// CEB Dome Brick Molds — Frequency 14
// Standard frustum shapes: outer face larger, inner face smaller
// Outer/inner ratio: 0.96875 (R_inner/R_outer = 186.0/192.0)
// Units: inches

// PENTAGON skylight mold (outer edge 8.086", inner edge 7.833")
// MOLD: Pentagon skylight
// Outer edge: 9.506"
// Inner edge: 9.209"
// Depth: 7.00" (6.0" brick + 1.0" margin)
difference() {
  translate([0,0,3.500])
    cube([17.380,16.628,7.000], center=true);
  // Frustum cavity: outer face at top, inner face at bottom
  translate([0,0,1.0])
    hull() {
      linear_extrude(height=0.01) polygon(points=[[0.0000,7.8333],[-7.4499,2.4206],[-4.6043,-6.3372],[4.6043,-6.3372],[7.4499,2.4206]]);
      translate([0,0,6.0]) linear_extrude(height=0.01) polygon(points=[[0.0000,8.0859],[-7.6902,2.4987],[-4.7528,-6.5417],[4.7528,-6.5417],[7.6902,2.4987]]);
    }
}

translate([19, 0, 0]) {
// HEXAGON brick mold (outer edge 9.545", inner edge 9.247")
// MOLD: Hexagon brick
// Outer edge: 9.545"
// Inner edge: 9.247"
// Depth: 7.00" (6.0" brick + 1.0" margin)
difference() {
  translate([0,0,3.500])
    cube([21.090,18.532,7.000], center=true);
  // Frustum cavity: outer face at top, inner face at bottom
  translate([0,0,1.0])
    hull() {
      linear_extrude(height=0.01) polygon(points=[[9.2466,0.0000],[4.6233,8.0078],[-4.6233,8.0078],[-9.2466,0.0000],[-4.6233,-8.0078],[4.6233,-8.0078]]);
      translate([0,0,6.0]) linear_extrude(height=0.01) polygon(points=[[9.5449,0.0000],[4.7724,8.2661],[-4.7724,8.2661],[-9.5449,0.0000],[-4.7724,-8.2661],[4.7724,-8.2661]]);
    }
}
}