#!/usr/bin/env python3
"""
sysml_sync.py -- close the loop between CinvaRam.sysml and cinva_simple.py

  1. Drift check: design parameters and BOM in CinvaRam.sysml vs cinva_simple.Params / parts().
  2. Run the solver: summary values, strength checks, functional + collision verify().
  3. Emit CinvaRamResults.sysml: an analysed instance specializing cinvaRam, with every
     result valued, and the satisfy relations.

Exit status: 0 all good, 1 drift between model and code, 2 a check failed. CI-friendly.

Usage (repo root, CinvaRam.sysml beside this script or given by --model):
    LD_LIBRARY_PATH=$HOME/miniconda3/lib python3 sysml_sync.py [--model CinvaRam.sysml] [--no-sweep]
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import subprocess
import sys
from pathlib import Path

import cinva_simple as cs

# SysML attribute (in part def CinvaRam) -> Params attribute
PARAM_MAP = {
    "brickL": "brick_l", "brickW": "brick_w", "brickH": "brick_h", "rise": "rise",
    "ejectOver": "eject_over", "handleLen": "handle_len", "dPinP": "d_pin", "dPinQ": "d_q",
    "dCam": "d_cam", "tSide": "t_side", "wArm": "w_arm", "tArm": "t_arm", "tCheek": "t_cheek", "tWeb": "t_web",
    "armY": "arm_y", "cheekY": "cheek_y", "psi0": "psi0", "psiLock": "psi_lock",
    "thetaEject": "theta_eject", "pWork": "p_work", "pDesign": "p_design",
}
TOL = 1e-3


def block(text: str, header: str) -> str:
    """Body of the first `header { ... }` block, brace-matched."""
    i = text.index(header)
    i = text.index("{", i)
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise ValueError(f"unbalanced block: {header}")


def model_params(text: str) -> dict:
    body = block(text, "part def CinvaRam")
    out = {}
    for m in re.finditer(r"attribute\s+(\w+)\s*:\s*\w+\s*(?:=|default)\s*(-?[\d.]+)\s*\[", body):
        out[m.group(1)] = float(m.group(2))
    return out


def model_bom(text: str) -> dict:
    out = {}
    for m in re.finditer(r"part\s+(\w+)\s*:\s*Component\s*\{(.*?)@Dwg", text):
        f = dict(re.findall(r":>>\s*(\w+)\s*=\s*([^;]+);", m.group(2)))
        item = int(f["itemNo"])
        out[item] = dict(name=m.group(1), qty=int(f["qty"]), stock=f["stock"].strip().strip('"'),
                         mass=float(re.match(r"\s*([\d.]+)", f["unitMass"]).group(1)))
    return out


def drift(text: str, p: cs.Params) -> list[str]:
    errs = []
    mp = model_params(text)
    for k, attr in PARAM_MAP.items():
        if k not in mp:
            errs.append(f"param {k}: missing in model")
            continue
        v = getattr(p, attr)
        if abs(mp[k] - v) > TOL:
            errs.append(f"param {k}: model {mp[k]:g}, code {v:g}")
    bom = model_bom(text)
    for pt in cs.parts(p):
        m = bom.get(pt.item)
        if m is None:
            errs.append(f"item {pt.item} {pt.name}: missing in model")
            continue
        w = round(pt.weight(p), 1)
        if m["qty"] != pt.qty:
            errs.append(f"item {pt.item} {pt.name}: qty model {m['qty']}, code {pt.qty}")
        if abs(m["mass"] - w) > 0.05:
            errs.append(f"item {pt.item} {pt.name}: unit mass model {m['mass']}, code {w}")
        if m["stock"] != stock(pt):
            errs.append(f"item {pt.item} {pt.name}: stock model '{m['stock']}', code '{stock(pt)}'")
    co = re.search(r"attribute camOffset\s*:\s*\w+\s*(?:=|default)\s*([\d.]+)", text)
    if co is None:
        errs.append("camOffset: missing in model")
    elif abs(float(co.group(1)) - round(p.e, 3)) > 1e-9:
        errs.append(f"camOffset: model {co.group(1)}, code {p.e:.3f}")
    extra = set(bom) - {pt.item for pt in cs.parts(p)}
    errs += [f"item {i} {bom[i]['name']}: in model, not in code" for i in sorted(extra)]
    return errs


def stock(pt) -> str:
    return pt.stock.replace('"', "")          # SysML string: drop inch marks


def fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".") if v != int(v) else f"{v:.1f}"


def update(text: str, p: cs.Params) -> str:
    """Rewrite the model's design parameters, BOM qty/stock/unit mass and camOffset from the code."""
    i = text.index("part def CinvaRam")
    j = text.index("// --- derived", i)
    seg = text[i:j]
    for k, attr in PARAM_MAP.items():
        v = getattr(p, attr)
        seg = re.sub(rf"(attribute\s+{k}\s*:\s*\w+\s*(?:=|default)\s*)(-?[\d.]+)",
                     lambda m: m.group(0) if abs(float(m.group(2)) - v) <= TOL else m.group(1) + fmt(v), seg)
    text = text[:i] + seg + text[j:]
    for pt in cs.parts(p):
        def fix(m):
            body = m.group(0)
            body = re.sub(r":>>\s*qty\s*=\s*\d+", f":>> qty = {pt.qty}", body)
            body = re.sub(r':>>\s*stock\s*=\s*"[^"]*"', f':>> stock = "{stock(pt)}"', body)
            w = round(pt.weight(p), 1)
            body = re.sub(r":>>\s*unitMass\s*=\s*([\d.]+)",
                          lambda mm: mm.group(0) if abs(float(mm.group(1)) - w) <= 0.05 else f":>> unitMass = {w:.1f}",
                          body)
            return body
        text = re.sub(rf"part\s+\w+\s*:\s*Component\s*\{{[^@]*?:>>\s*itemNo\s*=\s*{pt.item};[^@]*@Dwg", fix, text)
    text = re.sub(r"(attribute camOffset\s*:\s*\w+\s*(?:=|default)\s*)[\d.]+",
                  lambda m: m.group(1) + f"{p.e:.3f}", text)
    return text


def model_limits(text: str) -> dict:
    """Numeric requirement limits the pilot cannot evaluate (unit-bearing): read them from the model."""
    get = lambda pat: float(re.search(pat, text, re.S).group(1))
    return dict(
        handle=get(r"requirement def HandleForceLimit.*?attribute limit\s*:\s*\w+\s*=\s*([\d.]+)\s*\[lbf\]"),
        steel=get(r"requirement def SteelBudget.*?attribute budget\s*:\s*\w+\s*=\s*([\d.]+)\s*\[lb\]"),
    )


def req_checks(text: str, p: cs.Params) -> list:
    lim = model_limits(text)
    peak = p.peak_hand()
    mass = sum(pt.weight(p) * pt.qty for pt in cs.parts(p))
    return [("HandleForceLimit", peak <= lim["handle"], f"peak pull {peak:.1f} lbf <= {lim['handle']:g}"),
            ("SteelBudget", mass <= lim["steel"], f"steel {mass:.1f} lb <= {lim['steel']:g}")]


def git_rev() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', "'") + '"'


def ident(s: str) -> str:
    w = re.sub(r"[^0-9A-Za-z]+", " ", s).split()
    return w[0].lower() + "".join(x.capitalize() for x in w[1:])


def emit(p: cs.Params, stress, func, n_interf, sweep: bool) -> str:
    ps = cs.poses(p)
    peak = p.peak_hand()
    eject = cs.max_eject_hand(p)
    lock = p.psi_lock if any(n.startswith("Locks over centre") and ok for n, ok, _ in func) else 0.0
    fails = sum(not ok for _, ok, _ in func)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    L = []
    a = L.append
    a("/* GENERATED by sysml_sync.py -- do not hand-edit")
    a(f" * ceb @ {git_rev()}  {stamp}  sweep={'on' if sweep else 'off'}")
    a(" */")
    a("package CinvaRamResults {")
    a("    private import ScalarValues::*;")
    a("    private import ISQ::*;")
    a("    private import SI::*;")
    a("    private import USCustomaryUnits::*;")
    a("    private import CinvaRamExample::*;")
    a("")
    a("    part cinvaRamAnalysed :> cinvaRam {")
    a(f"        :>> peakHandleForce = {peak:.1f} [lbf];     // at {p.p_work:g} psi")
    a(f"        :>> peakEjectForce  = {eject:.1f} [lbf];")
    a(f"        :>> lockAngle       = {lock:g} ['°'];")
    a(f"        :>> interferences   = {n_interf};")
    a(f"        :>> functionalFails = {fails};")
    a(f"        :>> minMargin       = {min(al / sg - 1 for _, _, sg, al in stress):.4f};")
    a(f"        :>> steelMass       = {sum(pt.weight(p) * pt.qty for pt in cs.parts(p)):.1f} [lb];")
    a("")
    a("        // poses solved by the knee kinematics (yoke tilt, + toward fixed pins)")
    for k, v in ps.items():
        a(f"        attribute theta_{k} : PlaneAngleValue = {v.theta:.2f} ['°'];")
    a("")
    for item, basis, sig, allow in stress:
        n = ident(item)
        a(f"        attribute {n} : StressCheck {{")
        a(f"            :>> name = {q(item)}; :>> basis = {q(basis)};")
        a(f"            :>> sigma = {sig:,.0f} [lbf/'in'**2]; :>> allow = {allow:,.0f} [lbf/'in'**2];".replace(",", ""))
        a("        }")
    a("        :>> stressChecks = (" + ", ".join(ident(i) for i, *_ in stress) + ");")
    a("    }")
    a("")
    a("    /* functional checks, verify() */")
    a("    attribute def CheckResult { attribute name : String; attribute ok : Boolean; attribute detail : String; }")
    for name, ok, detail in func:
        a(f"    attribute {ident(name)} : CheckResult {{ :>> name = {q(name)}; :>> ok = {str(ok).lower()}; "
          f":>> detail = {q(detail)}; }}")
    a("")
    for r in ("brickSize", "handleForce", "lock", "strength", "noCollision", "steel", "stresses"):
        a(f"    satisfy CinvaRamExample::{r} by cinvaRamAnalysed;")
    a("}")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=str(Path(__file__).with_name("CinvaRam.sysml")))
    ap.add_argument("--out", default=None, help="default: CinvaRamResults.sysml beside the model")
    ap.add_argument("--no-sweep", action="store_true", help="skip the collision sweeps (fast)")
    ap.add_argument("--update", action="store_true",
                    help="on drift, rewrite the model's parameters and BOM from the code, then continue")
    a = ap.parse_args()

    mpath = Path(a.model)
    text = mpath.read_text()
    p = cs.Params()

    errs = drift(text, p)
    for e in errs:
        print(f"DRIFT  {e}")
    if errs and a.update:
        text = update(text, p)
        mpath.write_text(text)
        errs = drift(text, p)
        print(f"updated {mpath}; remaining drift: {len(errs)}")
        for e in errs:
            print(f"DRIFT  {e}")

    stress = cs.checks(p)
    func = cs.verify(p, sweep=not a.no_sweep)
    n_interf = 0
    for name, ok, detail in func:
        if name.startswith("All positions") and not ok:
            n_interf = len(detail.split("; "))          # verify() lists at most 10
    for item, _, sig, allow in stress:
        m = allow / sig - 1
        flag = "OVER" if sig > allow else ("tight" if m < 0.10 else "ok")
        print(f"{flag:5s}  {item:32s} {sig / 1e3:6.1f} / {allow / 1e3:5.1f} ksi  margin {m:+.0%}")
    for name, ok, detail in func:
        print(f"{'PASS' if ok else 'FAIL'}   {name}")

    reqs = req_checks(text, p)
    for name, ok, detail in reqs:
        print(f"{'PASS' if ok else 'FAIL'}   requirement {name}: {detail}")

    out = Path(a.out) if a.out else mpath.with_name("CinvaRamResults.sysml")
    out.write_text(emit(p, stress, func, n_interf, not a.no_sweep))
    print(f"wrote {out}")

    if errs:
        return 1
    if (any(s > al for _, _, s, al in stress) or not all(ok for _, ok, _ in func)
            or not all(ok for _, ok, _ in reqs)):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
