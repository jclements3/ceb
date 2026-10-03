"""
Export an animation of the CINVA-Ram press for the three.js viewer in animation/.

Writes animation/press.json:
  meta    reference pose and linkage constants (inches)
  groups  one mesh per rigid body (frame, lid, piston, yoke, latch, handle), vertex colours
  frames  one row per frame at FPS: phase, phase progress, yoke tilt, handle angle, pin P
          height, lid angle, latch slide, brick bottom/top, hand force

Every position comes from the same kinematics that cinva_ram_b123d.verify() checks,
so the animation shows the press exactly as drawn.

Usage:
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 cinva_animation.py [--brick 14x7x4] [--model simple|full]
"""

from __future__ import annotations

import argparse
import json
import math
import os

import importlib

import cinva_ram_b123d as m

MODELS = {"full": "cinva_ram_b123d", "simple": "cinva_simple"}

FPS = 30
GROUP_OF = {
    "rail": "frame", "tie": "frame", "side": "frame", "end": "frame", "post": "frame", "eroll": "frame",
    "eaxle": "frame", "wlug": "frame", "hpin": "frame",
    "cover": "lid", "rib": "lid", "clug": "lid", "stop": "lid",
    "cap": "piston", "web": "piston", "diaph": "piston", "ppin": "piston",
    "bar": "yoke", "qpin": "yoke", "ctie": "yoke", "tspacer": "yoke", "cstop": "yoke",
    "claw": "claw", "cthumb": "claw",
    "catch": "handle", "cheek": "handle", "sroll": "handle", "axle": "handle", "bridge": "handle", "bridgeb": "handle",
    "htube": "handle",
}


def meshes(p: m.Params, ref: m.Pose):
    colors = {pt.key: m.COLORS[pt.color] for pt in m.parts(p)}
    group_of = getattr(m, "GROUP_OF", GROUP_OF)
    groups = {}
    for key, name, solid in m.assembly(p, ref):
        g = groups.setdefault(group_of[key], {"positions": [], "indices": [], "colors": []})
        verts, tris = solid.tessellate(0.008, 0.12)
        base = len(g["positions"]) // 3
        for v in verts:
            g["positions"] += [round(v.X, 3), round(v.Y, 3), round(v.Z, 3)]
            g["colors"] += [round(c, 3) for c in colors[key]]
        for t in tris:
            g["indices"] += [base + i for i in t]
    for grp, solid, rgb in (m.extra_meshes(p) if hasattr(m, "extra_meshes") else []):
        g = groups.setdefault(grp, {"positions": [], "indices": [], "colors": []})
        verts, tris = solid.tessellate(0.008, 0.12)
        base = len(g["positions"]) // 3
        for v in verts:
            g["positions"] += [round(v.X, 3), round(v.Y, 3), round(v.Z, 3)]
            g["colors"] += [round(c, 3) for c in rgb]
        for t in tris:
            g["indices"] += [base + i for i in t]
    return [dict(name=k, **v) for k, v in groups.items()]


def ease(s):
    return s * s * (3 - 2 * s)


def timeline(p: m.Params):
    ps = m.poses(p)
    th_f, th_e = ps["fill"].theta, ps["eject"].theta
    psi0, psi1 = p.psi0, p.psi_stop
    zt, fill_top = p.zt, p.zt
    brick_bot = zt - p.brick_h
    Ly = p.yoke_len
    F = p.f_work
    hand = lambda psi: p._stroke_point(psi, F)[2]
    ptop = lambda zp: zp + p.pin_below_cap

    # (name, seconds, function(s) -> state dict)
    op = m.claw_geom(p)["open"]

    def st(theta, psi, zp, cover, latch, bb, bt, force=0.0):          # latch: 0 = claws shut, 1 = open
        return dict(theta=theta, psi=psi, zp=zp, cover=cover, latch=latch * op, bb=bb, bt=bt, force=force)

    phases = [
        ("Fill the mold with loose soil mix", 2.5,
         lambda s: st(th_f, psi0, p.zp_fill, p.lid_open, 0.0, ptop(p.zp_fill), ptop(p.zp_fill) + p.fill * ease(s))),
        ("Close the lid", 1.5,
         lambda s: st(th_f, psi0, p.zp_fill, p.lid_open * (1 - ease(s)), 0.0, ptop(p.zp_fill), zt)),
        ("Swing handle and yoke upright together", 1.5,
         lambda s: st(th_f * (1 - ease(s)), psi0, p.zp_fill, 0.0, 0.0, ptop(p.zp_fill), zt)),
        ("Flip the latch claw open onto its stop", 0.8,
         lambda s: st(0.0, psi0, p.zp_fill, 0.0, ease(s), ptop(p.zp_fill), zt)),
        ("Pull the handle over onto the stop (pressing)", 4.0,
         lambda s: (lambda psi: st(0.0, psi, p.q_z(psi) - Ly, 0.0, 1.0, ptop(p.q_z(psi) - Ly), zt,
                                   hand(min(psi, 89.9))))(psi0 + (psi1 - psi0) * ease(s))),
        ("Locked over centre: brick pressed to 4 in", 1.0,
         lambda s: st(0.0, psi1, p.q_z(psi1) - Ly, 0.0, 1.0, ptop(p.q_z(psi1) - Ly), zt)),
        ("Raise the handle back upright", 1.8,
         lambda s: (lambda psi: st(0.0, psi, p.q_z(psi) - Ly, 0.0, 1.0, brick_bot, zt))(psi1 + (psi0 - psi1) * ease(s))),
        ("Drop the latch claw onto the catch bar", 0.8,
         lambda s: st(0.0, psi0, p.zp_fill, 0.0, 1 - ease(s), brick_bot, zt)),
        ("Tilt handle and yoke back onto the eject roller", 1.5,
         lambda s: st(th_f * ease(s), psi0, p.zp_fill, 0.0, 0.0, brick_bot, zt)),
        ("Open the lid", 1.5,
         lambda s: st(th_f, psi0, p.zp_fill, p.lid_open * ease(s), 0.0, brick_bot, zt)),
        ("Push the handle down to eject the brick", 3.0,
         lambda s: (lambda th: (lambda zp: st(th, psi0, zp, p.lid_open, 0.0, max(brick_bot, ptop(zp)),
                                               max(brick_bot, ptop(zp)) + p.brick_h))(m.zp_for_theta(p, th)))(th_f + (th_e - th_f) * ease(s))),
        ("Lift the brick off and stack it", 2.2,
         lambda s: st(th_e, psi0, p.zp_eject, p.lid_open, 0.0, ptop(p.zp_eject), ptop(p.zp_eject) + p.brick_h)),
        ("Raise the handle: piston drops for the next fill", 1.5,
         lambda s: (lambda th: st(th, psi0, m.zp_for_theta(p, th), p.lid_open, 0.0, 0.0, 0.0))(th_e + (th_f - th_e) * ease(s))),
    ]
    return phases, dict(phase_press=4, phase_pressed=5, phase_lift=11)


def frames_of(phases):
    frames = []
    for i, (name, dur, fn) in enumerate(phases):
        n = max(2, round(dur * FPS))
        for k in range(n):
            s = k / (n - 1)
            d = fn(s)
            frames.append([i, round(s, 4), round(d["theta"], 3), round(d["psi"], 3), round(d["zp"], 4),
                           round(d["cover"], 2), round(d["latch"], 2), round(d["bb"], 4), round(d["bt"], 4),
                           round(d["force"], 1), round(d.get("theta_show", d["theta"]), 2),
                           round(d.get("psi_show", d["psi"]), 2), round(d.get("feed", 0.0), 3),
                           round(d.get("gate", 0.0), 3)])
    return [n for n, _, _ in phases], frames


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brick", default="14x7x4")
    ap.add_argument("--out", help="default animation/press.json (simple) or animation/press-full.json (full)")
    ap.add_argument("--model", choices=sorted(MODELS), default="simple")
    a = ap.parse_args()
    global m
    m = importlib.import_module(MODELS[a.model])
    a.out = a.out or ("animation/press.json" if a.model == "simple" else "animation/press-full.json")
    p = m.Params(**m.parse_brick(a.brick))
    ref = m.anim_ref(p) if hasattr(m, "anim_ref") else m.Pose("reference", 0.0, p.psi0, p.zp_fill, 0.0)
    hx, hz = m.hinge_axis(p)
    phases, roles = m.timeline(p) if hasattr(m, "timeline") else timeline(p)
    names, frames = frames_of(phases)
    meta = dict(label=p.label, fps=FPS, xc=p.xc, hinge=[hx, hz], yoke=p.yoke_len, zp_ref=ref.zp, psi_ref=ref.psi,
                zt=p.zt, L=p.brick_l, W=p.brick_w, H=p.brick_h, clear=p.clear, fill=p.fill,
                pin_below_cap=p.pin_below_cap, rail_y=p.rail_y, title=getattr(m, "TITLE", "CINVA-Ram"),
                p_work=p.p_work, psi_stop=p.psi_stop, handle_len=p.handle_len, **roles)
    if hasattr(m, "anim_meta"):
        meta.update(m.anim_meta(p))
    elif hasattr(m, "claw_geom"):
        meta.update(claw_pivot=[p.xc + m.claw_geom(p)["C"][0], ref.zp + p.yoke_len + m.claw_geom(p)["C"][1]],
                    claw_open=m.claw_geom(p)["open"])
    data = dict(
        meta=meta,
        phases=names,
        columns=["phase", "s", "theta", "psi", "zp", "cover", "claw", "brick_bottom", "brick_top", "hand_force",
                 "theta_show", "psi_show", "feed", "gate"],
        frames=frames,
        groups=meshes(p, ref),
    )
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    nv = sum(len(g["positions"]) // 3 for g in data["groups"])
    print(f"wrote {a.out}: {len(frames)} frames ({len(frames) / FPS:.1f} s), {nv:,} vertices, "
          f"{os.path.getsize(a.out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
