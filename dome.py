#!/usr/bin/env python3
"""
CEB Geodesic Dome Generator
Goldberg GP(n,0) Class I — default frequency 14

Generates:
  - Geometry report  (stdout)
  - ceb_dome.scad    (OpenSCAD, each brick a polyhedron, units = inches)

Key geometry facts:
  • Underlying structure: 20-triangle icosahedron, each triangle subdivided
    into FREQ² sub-triangles (Class I geodesic subdivision).
  • Total tiles: 10·FREQ²+2  (12 pentagon + rest hexagon)
  • Goldberg tile edge ≈ (ico_edge/FREQ) / √3
  • Each brick: outer face on R_OUTER sphere, inner face on R_INNER sphere,
    connected by six (or five) trapezoidal side faces.

Usage:  python3 ceb_dome_gen.py
"""

import math
from collections import defaultdict
from itertools import combinations

# ────────────────────────────────────────────────────────────────────────────
# Parameters — edit these
# ────────────────────────────────────────────────────────────────────────────
R_OUTER  = 192.0   # outer sphere radius, inches (32 ft diameter dome)
WALL     = 6.0     # wall thickness, inches
FREQ     = 14      # geodesic subdivision frequency  (try 20 for ~35 lb hex)
DENSITY  = 120.0   # CEB density, lb/ft³
PHI      = (1 + math.sqrt(5)) / 2
R_INNER  = R_OUTER - WALL

# ────────────────────────────────────────────────────────────────────────────
# Vector helpers
# ────────────────────────────────────────────────────────────────────────────
def norm3(v):
    m = math.sqrt(v[0]**2+v[1]**2+v[2]**2); return (v[0]/m,v[1]/m,v[2]/m)
def scale3(v,R):
    n=norm3(v); return (n[0]*R,n[1]*R,n[2]*R)
def sub3(a,b):  return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def mul3(v,s):  return (v[0]*s,v[1]*s,v[2]*s)
def dot3(a,b):  return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross3(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dist3(a,b): return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2)
def centroid3(pts):
    n=len(pts)
    return (sum(p[0] for p in pts)/n,sum(p[1] for p in pts)/n,sum(p[2] for p in pts)/n)
def area_poly3(pts):
    if len(pts)<3: return 0.0
    c=centroid3(pts); n=len(pts); a=0.0
    for i in range(n):
        ab=sub3(pts[i],c); ac=sub3(pts[(i+1)%n],c)
        cr=cross3(ab,ac); a+=math.sqrt(cr[0]**2+cr[1]**2+cr[2]**2)
    return a/2

# ────────────────────────────────────────────────────────────────────────────
# Truncated icosahedron (60 vertices on unit sphere)
# ────────────────────────────────────────────────────────────────────────────
def build_trunc_ico():
    p=PHI; raw=[]
    for s1 in [1,-1]:
        for s2 in [1,-1]:
            raw+=[(0,s1,s2*3*p),(s1,s2*3*p,0),(s2*3*p,0,s1)]
    for s1 in [1,-1]:
        for s2 in [1,-1]:
            for s3 in [1,-1]:
                raw+=[(s1*2,s2*(1+2*p),s3*p),(s2*(1+2*p),s3*p,s1*2),(s3*p,s1*2,s2*(1+2*p)),
                      (s1,s2*(2+p),s3*2*p),(s2*(2+p),s3*2*p,s1),(s3*2*p,s1,s2*(2+p))]
    verts=[]
    for r in raw:
        n=norm3(r)
        if not any(dist3(n,v)<1e-9 for v in verts): verts.append(n)

    all_d=sorted({round(dist3(verts[i],verts[j]),6)
                  for i in range(len(verts)) for j in range(i+1,len(verts))})
    elen=all_d[0]; tol=elen*0.05
    adj=defaultdict(list)
    for i in range(len(verts)):
        for j in range(i+1,len(verts)):
            if dist3(verts[i],verts[j])<elen+tol:
                adj[i].append(j); adj[j].append(i)

    faces=[]; seen=set()
    for start in range(len(verts)):
        for nxt in adj[start]:
            face=[start,nxt]; prev,cur=start,nxt; ok=True
            for _ in range(8):
                if cur==start and len(face)>2: break
                cands=[nb for nb in adj[cur] if nb!=prev]
                if not cands: ok=False; break
                cv=verts[cur]; inc=sub3(cv,verts[prev]); nrm=norm3(cv)
                d=dot3(inc,nrm); inc=sub3(inc,mul3(nrm,d))
                best=-math.inf; bnb=None
                for nb in cands:
                    ev=sub3(verts[nb],cv); d2=dot3(ev,nrm); ev=sub3(ev,mul3(nrm,d2))
                    a=math.atan2(dot3(cross3(inc,ev),nrm),dot3(inc,ev))
                    if a>best: best,bnb=a,nb
                prev,cur=cur,bnb; face.append(cur)
            if ok and len(face)>2 and face[-1]==start:
                face=face[:-1]; mi=face.index(min(face))
                face=face[mi:]+face[:mi]; key=tuple(face)
                if key not in seen and 5<=len(face)<=6:
                    seen.add(key); faces.append(face)

    return verts,[f for f in faces if len(f)==5],[f for f in faces if len(f)==6]

# ────────────────────────────────────────────────────────────────────────────
# Build Goldberg tiles via geodesic subdivision
# Returns (pent_cells, hex_cells) — each cell is an ordered list of
# 3D points (the tile polygon vertices) on sphere of radius R.
# ────────────────────────────────────────────────────────────────────────────
def goldberg_cells(base_verts, pent_faces, hex_faces, freq, R):
    # Icosahedron vertices = pentagon face centres of truncated ico
    ico_verts=[norm3(centroid3([base_verts[i] for i in f])) for f in pent_faces]

    # Pentagon adjacency via shared hex face neighbours
    def near_pents(hf,k=3):
        hc=centroid3([base_verts[i] for i in hf])
        return [pi for _,pi in sorted((dist3(hc,iv),pi) for pi,iv in enumerate(ico_verts))[:k]]

    padj=defaultdict(set)
    for hf in hex_faces:
        near=near_pents(hf)
        for a,b in combinations(near,2): padj[a].add(b); padj[b].add(a)

    ico_tris=[]
    for pi in range(len(ico_verts)):
        for qi in sorted(padj[pi]):
            if qi>pi:
                for ri in padj[pi]:
                    if ri>qi and ri in padj[qi]:
                        ico_tris.append((pi,qi,ri))

    # Subdivide each ico triangle into freq×freq sub-triangles on unit sphere
    pt_map={}; all_pts_unit=[]
    def get_pt(p):
        k=(round(p[0],7),round(p[1],7),round(p[2],7))
        if k not in pt_map: pt_map[k]=len(all_pts_unit); all_pts_unit.append(norm3(p))
        return pt_map[k]

    all_grids=[]
    for (pi,qi,ri) in ico_tris:
        A,B,C=ico_verts[pi],ico_verts[qi],ico_verts[ri]
        grid=[]
        for i in range(freq+1):
            row=[]
            for j in range(freq+1-i):
                kk=freq-i-j
                raw=(A[0]*(i/freq)+B[0]*(j/freq)+C[0]*(kk/freq),
                     A[1]*(i/freq)+B[1]*(j/freq)+C[1]*(kk/freq),
                     A[2]*(i/freq)+B[2]*(j/freq)+C[2]*(kk/freq))
                row.append(get_pt(raw))
            grid.append(row)
        all_grids.append(grid)

    all_pts=[scale3(p,R) for p in all_pts_unit]

    # For each sub-triangle, compute its centroid projected to sphere.
    # Accumulate surrounding triangle centroids for each grid vertex.
    pt_surr=defaultdict(list)
    def add_tri(a,b,c):
        tc=scale3(centroid3([all_pts[a],all_pts[b],all_pts[c]]),R)
        pt_surr[a].append(tc); pt_surr[b].append(tc); pt_surr[c].append(tc)

    for grid in all_grids:
        rows=len(grid)
        for i in range(rows-1):
            for j in range(len(grid[i])-1):
                if j<len(grid[i+1]):
                    add_tri(grid[i][j],grid[i][j+1],grid[i+1][j])
                if j+1<len(grid[i+1]):
                    add_tri(grid[i][j+1],grid[i+1][j+1],grid[i+1][j])

    def dedup(pts,tol=0.5):
        out=[]
        for p in pts:
            if not any(dist3(p,q)<tol for q in out): out.append(p)
        return out

    def sort_ccw(center,pts):
        nrm=norm3(center)
        ref=sub3(pts[0],center); d=dot3(ref,nrm); ref=sub3(ref,mul3(nrm,d))
        rm=math.sqrt(dot3(ref,ref))
        if rm<1e-10: return pts
        ref=mul3(ref,1/rm)
        def ang(p):
            ev=sub3(p,center); d2=dot3(ev,nrm); ev=sub3(ev,mul3(nrm,d2))
            return math.atan2(dot3(cross3(ref,ev),nrm),dot3(ref,ev))
        return sorted(pts,key=ang)

    pent_cells=[]; hex_cells=[]
    for pidx in range(len(all_pts)):
        surr=dedup(pt_surr[pidx])
        if len(surr)<3: continue
        surr=sort_ccw(all_pts[pidx],surr)
        if len(surr)==5: pent_cells.append(surr)
        elif len(surr)==6: hex_cells.append(surr)
    return pent_cells, hex_cells

# ────────────────────────────────────────────────────────────────────────────
# OpenSCAD brick (one polyhedron per tile)
# ────────────────────────────────────────────────────────────────────────────
def scad_brick(outer_pts,wall,label):
    n=len(outer_pts)
    R0=math.sqrt(outer_pts[0][0]**2+outer_pts[0][1]**2+outer_pts[0][2]**2)
    inner=[scale3(p,R0-wall) for p in outer_pts]
    pts=list(outer_pts)+list(inner)
    of=list(range(n)); inf=list(range(n,2*n))[::-1]
    sides=[[i,(i+1)%n,(i+1)%n+n] for i in range(n)]+[[i,(i+1)%n+n,i+n] for i in range(n)]
    ps=",".join(f"[{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}]" for p in pts)
    fs=",".join(str(f) for f in [of,inf]+sides)
    return f"    // {label}\n    polyhedron(points=[{ps}],faces=[{fs}],convexity=4);\n"

def brick_weight(outer,wall,density):
    R0=math.sqrt(outer[0][0]**2+outer[0][1]**2+outer[0][2]**2)
    aout=area_poly3(outer); ain=area_poly3([scale3(p,R0-wall) for p in outer])
    return (aout+ain)/2*wall/1728*density

# ────────────────────────────────────────────────────────────────────────────
# Analytical geometry (for report header)
# ────────────────────────────────────────────────────────────────────────────
def tile_geometry(R,wall,freq,density):
    ca=2*math.asin(1/math.sqrt(PHI**2+1))
    ico_edge=R*2*math.sin(ca/2)
    sub_edge=ico_edge/freq
    goldberg_edge=sub_edge/math.sqrt(3)
    sub_area=math.sqrt(3)/4*sub_edge**2
    # hex tile owns 2 sub-triangles worth of area, pent tile owns 5/3
    hex_area=2*sub_area;  pent_area=5/3*sub_area
    r_ratio=(R-wall)/R
    def wt(area_out): return (area_out+area_out*r_ratio**2)/2*wall/1728*density
    return dict(ico_edge=ico_edge, sub_edge=sub_edge, goldberg_edge=goldberg_edge,
                hex_area=hex_area, pent_area=pent_area,
                hex_wt=wt(hex_area), pent_wt=wt(pent_area))

# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────
if __name__==u"__main__":
    g=tile_geometry(R_OUTER,WALL,FREQ,DENSITY)
    NP=12; NHH=10*FREQ**2-10; NHH2=NHH//2+5
    tw=NP*g['pent_wt']+NHH2*g['hex_wt']

    print("="*56)
    print("CEB GEODESIC DOME — GEOMETRY REPORT")
    print("="*56)
    print(f"  Dome diameter:           {R_OUTER*2/12:.0f} ft")
    print(f"  Outer radius:            {R_OUTER:.3f}\"")
    print(f"  Inner radius:            {R_INNER:.3f}\"")
    print(f"  Wall thickness:          {WALL:.3f}\"")
    print(f"  Geodesic frequency:      {FREQ}")
    print(f"  Total tiles (10n²+2):    {10*FREQ**2+2}")
    print()
    print(f"  Icosahedron edge:        {g['ico_edge']:.4f}\"")
    print(f"  Sub-triangle edge:       {g['sub_edge']:.4f}\"  (ico/freq)")
    print(f"  Goldberg tile edge:      {g['goldberg_edge']:.4f}\"  (sub/√3)")
    print()
    print("  PENTAGON BRICK (12 total):")
    print(f"    Outer face area:       {g['pent_area']:.2f} in²")
    print(f"    Wall:                  {WALL:.2f}\"")
    print(f"    Weight:                {g['pent_wt']:.2f} lb")
    print()
    print(f"  HEXAGON BRICK (~{NHH2} in hemisphere):")
    print(f"    Outer face area:       {g['hex_area']:.2f} in²")
    print(f"    Wall:                  {WALL:.2f}\"")
    print(f"    Weight:                {g['hex_wt']:.2f} lb")
    print()
    print(f"  TOTAL HEMISPHERE:        ~{NP+NHH2} bricks")
    print(f"  TOTAL WEIGHT:            {tw:.0f} lb  ({tw/2000:.1f} tons)")
    print()
    # Suggest frequency for ≤35 lb hex brick
    for f in range(FREQ, 40):
        gg=tile_geometry(R_OUTER,WALL,f,DENSITY)
        if gg['hex_wt']<=35.0:
            print(f"  ⚠  For hex ≤ 35 lb:  use FREQ = {f}  "
                  f"(hex={gg['hex_wt']:.1f} lb, pent={gg['pent_wt']:.1f} lb)")
            break
    print("="*56)

    print(f"\nBuilding frequency {FREQ} geodesic subdivision...")
    bv,pf,hf=build_trunc_ico()
    print(f"  Base: {len(bv)} verts, {len(pf)} pentagons, {len(hf)} hexagons")

    pent_cells,hex_cells=goldberg_cells(bv,pf,hf,FREQ,R_OUTER)
    print(f"  Tiles: {len(pent_cells)} pent + {len(hex_cells)} hex = {len(pent_cells)+len(hex_cells)}")

    thresh=-R_OUTER*0.02
    hemi_pent=[c for c in pent_cells if centroid3(c)[2]>=thresh]
    hemi_hex =[c for c in hex_cells  if centroid3(c)[2]>=thresh]
    n_total=len(hemi_pent)+len(hemi_hex)
    print(f"  Hemisphere: {len(hemi_pent)} pent + {len(hemi_hex)} hex = {n_total} bricks")

    if hemi_pent: print(f"  Sample pent weight: {brick_weight(hemi_pent[0],WALL,DENSITY):.2f} lb")
    if hemi_hex:  print(f"  Sample hex weight:  {brick_weight(hemi_hex[0], WALL,DENSITY):.2f} lb")

    actual_tw=(sum(brick_weight(c,WALL,DENSITY) for c in hemi_pent)+
               sum(brick_weight(c,WALL,DENSITY) for c in hemi_hex))
    print(f"  Actual total weight: {actual_tw:.0f} lb ({actual_tw/2000:.1f} tons)")

    print("\nWriting ceb_dome.scad...")
    out=[]
    out.append(f"// CEB Geodesic Dome — Class I Frequency {FREQ}")
    out.append(f"// Outer R={R_OUTER}\"  Inner R={R_INNER}\"  Wall={WALL}\"  density={DENSITY} lb/ft3")
    out.append(f"// {len(hemi_pent)} pentagon + {len(hemi_hex)} hexagon hemisphere bricks")
    out.append(f"// Goldberg tile edge ~{g['goldberg_edge']:.3f}\"")
    out.append(f"// Est. hemisphere weight: {actual_tw/2000:.1f} tons    Units: inches")
    out.append("")
    out.append("union() {")
    out.append(f"  // ── PENTAGON BRICKS ({len(hemi_pent)}) ──")
    out.append("  color(\"DarkOrange\")")
    out.append("  union() {")
    for i,c in enumerate(hemi_pent):
        out.append(scad_brick(c,WALL,f"pent {i+1}/{len(hemi_pent)}"))
    out.append("  }")
    out.append(f"  // ── HEXAGON BRICKS ({len(hemi_hex)}) ──")
    out.append("  color(\"SteelBlue\")")
    out.append("  union() {")
    for i,c in enumerate(hemi_hex):
        out.append(scad_brick(c,WALL,f"hex {i+1}/{len(hemi_hex)}"))
    out.append("  }")
    out.append("}")

    scad="\n".join(out)
    with open("ceb_dome.scad","w") as f: f.write(scad)
    print(f"  ceb_dome.scad  ({len(scad)//1024} KB, {n_total} bricks)")
    print("  Open in OpenSCAD → F5 preview  (F6 for full render, slow)")
