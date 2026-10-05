#!/usr/bin/env python3
"""Extract CEB press part outlines from the frozen 14x7 DXF libraries.

Method: cluster LINE/ARC/CIRCLE (+ exploded LWPOLYLINE) entities into
connected components with a TIGHT gap (0.05"), then merge interior-feature
clusters (holes, slots, score lines) into the smallest cluster whose bbox
fully contains them.  Assign each cluster the nearest MTEXT/TEXT label.
The four L-Q2 plates carry no label and are identified as the unlabeled
7.000 x 2.000 plates near L-Q1.  Chosen parts are de-rotated (if drawn
tilted) and translated so the bbox lower-left corner is the (0,0) datum.
One JSON per part type is written to freecad/parts_json/ (units: inches).

Usage: python3 extract_parts.py [--summary]
"""
import json
import math
import os
import sys

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))
DXF_DIR = os.path.join(HERE, "..", "ceb_press_cnc_package", "dxf")
OUT_DIR = os.path.join(HERE, "parts_json")

FILES = {
    "half_inch_steel_library_14x7.dxf": {
        "thickness": 0.5, "material": "A36",
        "wanted": ["L-F9", "L-F10", "L-F6", "L-F12", "L-F8",
                   "L-D2", "L-D3", "L-D5"]},
    "quarter_inch_steel_library_14x7.dxf": {
        "thickness": 0.25, "material": "A36",
        "wanted": ["L-Q1", "L-Q2", "L-Q3", "L-Q4", "L-Q5"]},
    "eighth_inch_steel_library_14x7.dxf": {
        "thickness": 0.125, "material": "A36",
        "wanted": ["L-H1", "L-H2", "L-H3", "L-H4", "L-H5",
                   "L-H6", "L-H8", "L-H9", "L-H10", "L-H12"]},
}

TIGHT = 0.05   # inches: entities closer than this are one connected chain
EPS = 0.05     # containment tolerance


def arc_bbox(cx, cy, r, a0, a1):
    pts = [(cx + r * math.cos(math.radians(a)),
            cy + r * math.sin(math.radians(a))) for a in (a0, a1)]
    a0n = a0 % 360.0
    sweep = (a1 - a0) % 360.0
    for q in range(4):
        if (q * 90.0 - a0n) % 360.0 <= sweep:
            pts.append((cx + r * math.cos(math.radians(q * 90.0)),
                        cy + r * math.sin(math.radians(q * 90.0))))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def rec_bbox(rec):
    if rec["type"] == "line":
        x0, y0 = rec["start"]
        x1, y1 = rec["end"]
        return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
    if rec["type"] == "circle":
        (cx, cy), r = rec["center"], rec["radius"]
        return cx - r, cy - r, cx + r, cy + r
    (cx, cy), r = rec["center"], rec["radius"]
    return arc_bbox(cx, cy, r, rec["start_angle"], rec["end_angle"])


def entity_records(msp):
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            x0, y0 = e.dxf.start.x, e.dxf.start.y
            x1, y1 = e.dxf.end.x, e.dxf.end.y
            if math.hypot(x1 - x0, y1 - y0) < 1e-9:
                continue
            yield {"type": "line", "start": [x0, y0], "end": [x1, y1]}
        elif t == "ARC":
            yield {"type": "arc",
                   "center": [e.dxf.center.x, e.dxf.center.y],
                   "radius": e.dxf.radius,
                   "start_angle": e.dxf.start_angle,
                   "end_angle": e.dxf.end_angle}
        elif t == "CIRCLE":
            yield {"type": "circle",
                   "center": [e.dxf.center.x, e.dxf.center.y],
                   "radius": e.dxf.radius}
        elif t == "LWPOLYLINE":
            pts = list(e.get_points("xyb"))
            n = len(pts)
            segs = n if e.closed else n - 1
            for i in range(segs):
                x0, y0, b = pts[i]
                x1, y1, _ = pts[(i + 1) % n]
                chord = math.hypot(x1 - x0, y1 - y0)
                if chord < 1e-9:
                    continue
                if abs(b) < 1e-12:
                    yield {"type": "line", "start": [x0, y0],
                           "end": [x1, y1]}
                else:
                    theta = 4.0 * math.atan(b)
                    r = chord / (2.0 * math.sin(abs(theta) / 2.0))
                    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                    d = math.sqrt(max(r * r - (chord / 2.0) ** 2, 0.0))
                    nx, ny = -(y1 - y0) / chord, (x1 - x0) / chord
                    if theta > 0:
                        cx, cy = mx - nx * d, my - ny * d
                    else:
                        cx, cy = mx + nx * d, my + ny * d
                    a0 = math.degrees(math.atan2(y0 - cy, x0 - cx))
                    a1 = math.degrees(math.atan2(y1 - cy, x1 - cx))
                    if theta < 0:
                        a0, a1 = a1, a0
                    yield {"type": "arc", "center": [cx, cy], "radius": r,
                           "start_angle": a0, "end_angle": a1}


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def cluster(records, gap):
    n = len(records)
    boxes = [rec_bbox(r) for r in records]
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    cell = 4.0
    grid = {}
    for i, bb in enumerate(boxes):
        for gx in range(int(bb[0] // cell), int(bb[2] // cell) + 1):
            for gy in range(int(bb[1] // cell), int(bb[3] // cell) + 1):
                grid.setdefault((gx, gy), []).append(i)
    for bucket in grid.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                i, j = bucket[a], bucket[b]
                ri, rj = find(i), find(j)
                if ri != rj and bbox_gap(boxes[i], boxes[j]) < gap:
                    parent[rj] = ri
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for idxs in groups.values():
        bbs = [boxes[i] for i in idxs]
        out.append({"bbox": (min(b[0] for b in bbs), min(b[1] for b in bbs),
                             max(b[2] for b in bbs), max(b[3] for b in bbs)),
                    "entities": [records[i] for i in idxs]})
    return out


def contains(a, b):
    """bbox a fully contains bbox b (with EPS slack)."""
    return (a[0] - EPS <= b[0] and a[1] - EPS <= b[1]
            and a[2] + EPS >= b[2] and a[3] + EPS >= b[3])


def area(bb):
    return max(bb[2] - bb[0], 0.0) * max(bb[3] - bb[1], 0.0)


def merge_interior(clusters):
    """Merge each cluster into the smallest strictly-larger cluster whose
    bbox fully contains it (interior holes / slots / score lines)."""
    clusters.sort(key=lambda c: area(c["bbox"]))
    alive = [True] * len(clusters)
    for i, ci in enumerate(clusters):
        best, best_a = None, None
        for j in range(i + 1, len(clusters)):
            if not alive[j]:
                continue
            cj = clusters[j]
            aj = area(cj["bbox"])
            if aj > area(ci["bbox"]) * 1.2 + 1e-9 and \
                    contains(cj["bbox"], ci["bbox"]):
                if best_a is None or aj < best_a:
                    best, best_a = j, aj
        if best is not None:
            clusters[best]["entities"].extend(ci["entities"])
            alive[i] = False
    return [c for i, c in enumerate(clusters) if alive[i]]


def point_bbox_dist(p, bb):
    dx = max(bb[0] - p[0], p[0] - bb[2], 0.0)
    dy = max(bb[1] - p[1], p[1] - bb[3], 0.0)
    return math.hypot(dx, dy)


def label_clusters(msp, clusters):
    labels = []
    for e in msp:
        if e.dxftype() == "MTEXT":
            txt, p = e.plain_text().strip(), (e.dxf.insert.x, e.dxf.insert.y)
        elif e.dxftype() == "TEXT":
            txt, p = e.dxf.text.strip(), (e.dxf.insert.x, e.dxf.insert.y)
        else:
            continue
        if txt.startswith("L-"):
            labels.append((txt, p))
    for c in clusters:
        c["label"], c["label_dist"] = None, None
    for txt, p in labels:
        best, bd = None, None
        for c in clusters:
            d = point_bbox_dist(p, c["bbox"])
            if bd is None or d < bd:
                best, bd = c, d
        if best is not None and (best["label_dist"] is None
                                 or bd < best["label_dist"]):
            best["label"], best["label_dist"] = txt, bd
    return clusters


def rotate_pt(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def normalize(entities):
    """De-rotate a tilted part and move its bbox lower-left to (0,0).
    Returns (entities, rotation_deg)."""
    bins = {}
    total = 0.0
    for r in entities:
        if r["type"] != "line":
            continue
        dx = r["end"][0] - r["start"][0]
        dy = r["end"][1] - r["start"][1]
        ln = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx)) % 90.0
        bins[round(ang, 1)] = bins.get(round(ang, 1), 0.0) + ln
        total += ln
    rot = 0.0
    if bins and total > 0:
        dom = max(bins, key=bins.get)
        axis_mass = sum(v for k, v in bins.items()
                        if min(k, 90.0 - k) < 1.0)
        if 1.0 < dom < 89.0 and axis_mass < 0.2 * total:
            rot = -dom
    if rot:
        a = math.radians(rot)
        for r in entities:
            if r["type"] == "line":
                r["start"] = list(rotate_pt(r["start"][0], r["start"][1], a))
                r["end"] = list(rotate_pt(r["end"][0], r["end"][1], a))
            else:
                r["center"] = list(rotate_pt(r["center"][0],
                                             r["center"][1], a))
                if r["type"] == "arc":
                    r["start_angle"] += rot
                    r["end_angle"] += rot
    bbs = [rec_bbox(r) for r in entities]
    x0 = min(b[0] for b in bbs)
    y0 = min(b[1] for b in bbs)
    for r in entities:
        if r["type"] == "line":
            r["start"] = [r["start"][0] - x0, r["start"][1] - y0]
            r["end"] = [r["end"][0] - x0, r["end"][1] - y0]
        else:
            r["center"] = [r["center"][0] - x0, r["center"][1] - y0]
    return entities, rot


def main():
    summary = "--summary" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    for fname, spec in FILES.items():
        doc = ezdxf.readfile(os.path.join(DXF_DIR, fname))
        msp = doc.modelspace()
        clusters = merge_interior(cluster(list(entity_records(msp)), TIGHT))
        clusters = label_clusters(msp, clusters)
        if summary:
            print("==", fname, "-", len(clusters), "clusters")
            for c in sorted(clusters, key=lambda c: -area(c["bbox"])):
                bb = c["bbox"]
                print("  label=%-8s size=%8.3f x %8.3f at (%8.1f,%6.1f) n=%d"
                      % (c["label"], bb[2] - bb[0], bb[3] - bb[1],
                         bb[0], bb[1], len(c["entities"])))
            continue

        chosen = {}
        for c in clusters:
            lab = c["label"]
            if lab in spec["wanted"] and (
                    lab not in chosen
                    or len(c["entities"]) > len(chosen[lab]["entities"])):
                chosen[lab] = c

        if "L-Q2" in spec["wanted"] and "L-Q2" not in chosen:
            cands = [c for c in clusters if c["label"] is None
                     and abs((c["bbox"][2] - c["bbox"][0]) - 7.0) < 0.1
                     and abs((c["bbox"][3] - c["bbox"][1]) - 2.0) < 0.1]
            if cands:
                chosen["L-Q2"] = max(cands, key=lambda c: len(c["entities"]))
                print("L-Q2: identified as unlabeled 7.000 x 2.000 plate "
                      "(%d candidates found)" % len(cands))

        for lab in spec["wanted"]:
            if lab not in chosen:
                print("MISSING: %s in %s" % (lab, fname))
                continue
            ents, rot = normalize(chosen[lab]["entities"])
            bbs = [rec_bbox(r) for r in ents]
            w = max(b[2] for b in bbs)
            h = max(b[3] for b in bbs)
            data = {"name": lab, "source": fname,
                    "thickness": spec["thickness"],
                    "material": spec["material"],
                    "rotation_applied_deg": rot,
                    "size": [w, h], "entities": ents}
            with open(os.path.join(
                    OUT_DIR, lab.replace("-", "_") + ".json"), "w") as f:
                json.dump(data, f, indent=1)
            print("wrote %-8s size %7.3f x %7.3f  n=%-3d rot=%g"
                  % (lab, w, h, len(ents), rot))

    for name, (w, h, t, mat) in {
            "PRESS_FOOT": (14.0, 7.0, 1.0, "AR300"),
            "DOUBLER_STRIP": (9.0, 1.5, 0.5, "A36")}.items():
        data = {"name": name, "source": "modeled (not in DXF)",
                "thickness": t, "material": mat,
                "rotation_applied_deg": 0.0, "size": [w, h],
                "entities": [
                    {"type": "line", "start": [0, 0], "end": [w, 0]},
                    {"type": "line", "start": [w, 0], "end": [w, h]},
                    {"type": "line", "start": [w, h], "end": [0, h]},
                    {"type": "line", "start": [0, h], "end": [0, 0]}]}
        with open(os.path.join(OUT_DIR, name + ".json"), "w") as f:
            json.dump(data, f, indent=1)
        print("wrote %-13s %.1f x %.1f x %.2f (%s)" % (name, w, h, t, mat))


if __name__ == "__main__":
    main()
