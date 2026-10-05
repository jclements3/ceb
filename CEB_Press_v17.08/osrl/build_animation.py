"""
Animation of the OSRL Resilient Living CEB press for the three.js viewer in osrl/animation/index.html
(the repo viewer, extended with an off-axis toggle pivot 'head'). Uses ../../cinva_animation.py.

Usage (from the repo root):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 CEB_Press_v17.08/osrl/build_animation.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import cinva_animation as A  # noqa: E402
import osrl_press as M  # noqa: E402

OUT = os.path.join(HERE, "animation", "press.json")


def main():
    A.m = M
    p = M.Params()
    ref = M.anim_ref(p)
    hx, hz = M.hinge_axis(p)
    phases, roles = M.timeline(p)
    names, frames = A.frames_of(phases)
    meta = dict(label=p.label, fps=A.FPS, xc=p.xc, hinge=[hx, hz], yoke=p.yoke_len, zp_ref=ref.zp, psi_ref=0.0,
                zt=p.zt, L=p.brick_l, W=p.brick_w, H=p.brick_h, clear=p.clear, fill=p.fill,
                pin_below_cap=p.pin_below_cap, rail_y=p.rail_y + 3.0, title=M.TITLE, p_work=p.p_work,
                psi_stop=p.psi_stop, handle_len=p.handle_len, over_at=1e9, **roles)
    meta.update(M.anim_meta(p))
    data = dict(meta=meta, phases=names,
                columns=["phase", "s", "theta", "psi", "zp", "cover", "claw", "brick_bottom", "brick_top", "hand_force",
                         "theta_show", "psi_show", "feed", "gate"],
                frames=frames, groups=A.meshes(p, ref))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    nv = sum(len(g["positions"]) // 3 for g in data["groups"])
    print(f"wrote {OUT}: {len(frames)} frames ({len(frames) / A.FPS:.1f} s), {nv:,} vertices, "
          f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
