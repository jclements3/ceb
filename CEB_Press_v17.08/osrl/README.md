# OSRL "Resilient Living" CEB press, rev 1.1: build123d clone

This is a clone of the **Open Source Resilient Living CEB press, rev 1.1**:
* *OSRL CEB Press Drawings 1-1*: 11 sheets, Dec 2011, design team Damien Gendron and Butte Metz.
* The OSRL *Manual CEB Press*.
* Licence: CC BY-SA 3.0, www.osrliving.org.
* Source PDFs: `../pdfcoffee.com_osrl-ceb-press-drawings-1-1-2-pdf-free.pdf` and `../pdfcoffee.com_manual-ceb-press-pdf-free.pdf`.

It is a manual CINVA-type press for a 12 x 6 x 4 block with two 2-3/8 cores.
* **Frame:** two C6x13 channels on a base plate, with 1/4 side plates. Two 2 in pipe guide rods form the cores.
* **Piston:** a lower insert on two pipe guides, carried on a 1 in pin by a two-arm yoke.
* **Toggle and latch:** the toggle has a square-tube body that takes a 48 in pipe lever, and two 2 in followers. A latch hooks the lever to the yoke.
* **Lid:** hinged and counterweighted. Its two rails climb to a 2 in scoop that seats the followers.
* **Ejection:** the yoke tilts onto two eject rollers on the front channel.

## Files

| Path | What it is |
|---|---|
| `osrl_press.py` | Parametric model: every part on their 11 sheets, kinematics, poses, strength checks, functional checks and collision sweeps (`--check`) |
| `build_drawings.py` | ISO 128 drawing set built with `../../cinva_drawings.py`, output to `drawings/` |
| `drawings/` | `sheets/*.svg` (4 assembly sheets + 42 part sheets), `dxf/`, `OSRL-CEB-Press_12x6x4.pdf`, `.step`, `manifest.json` |
| `build_animation.py` | Exports `animation/press.json` |
| `animation/index.html` | The repo's three.js viewer, extended for the toggle pivot sitting off the yoke axis |
| `check.log` | Last `--check` results |

```
export LD_LIBRARY_PATH=$HOME/miniconda3/lib
python3 CEB_Press_v17.08/osrl/osrl_press.py --check      # summary, strength, functional checks, collision sweeps
python3 CEB_Press_v17.08/osrl/build_drawings.py          # ISO 128 set
python3 CEB_Press_v17.08/osrl/build_animation.py         # animation/press.json
cd CEB_Press_v17.08 && python3 -m http.server             # then open /osrl/animation/
```

## How the press works (as reconstructed)

1. **Stand up.** With the lever latched along the yoke, standing the yoke up rolls the followers up the rail slopes. They drop into the scoops with the piston still on the bottom (0.04 in off). This is the manual's "letting the lower rollers fall into place".
2. **Press.** Release the latch and pull the lever over to horizontal toward the rear channel. The toggle turns about the seated followers and lifts the piston 3.5 in. At horizontal it is at dead centre.
3. **Block thickness.**
   * The head bolts into arm holes 1-5, giving blocks of 7.06, 6.07, 5.08, **4.09** and 3.10 in from a 7.625 in loose fill.
   * Hole 4 gives the 4 in block, matching the manual's "adjustable in 1 in increments".
4. **Eject.** The arms rest on the eject rollers. The axle sits in the 7 in hole, as drawn on sheet 2. Pushing the lever down ejects the block: the yoke tilts from 38 to 88 deg and the lever end ends 17 in off the ground.

## Placements the drawings leave open

* **Toggle:** it sits behind the yoke head, on the side the lever swings to. It pivots in pivot mounts 2-3/4 behind the arm centre line, with the followers 2.875 behind the toggle axle when the lever is upright.
  * The other way round, the lever would hit the head bodies before it reached horizontal.
  * The followers sitting at the yoke line at standing-up is consistent with sheet 1.
  * Their sheet-1 3D view shows the yoke leaning forward with the toggle above the head.
* **Toggle axle height:** 3-3/4 below the head top, with the pivot mounts' top edge on the head bodies.
  * Sheet 1 scales to 1/2 lower. That would make a 3.6 in block at hole 4 and seat the followers with the piston 1/2 off the bottom, so the touching layout is used.
* **Counterweight arm hinge hole:** not dimensioned. It is placed 1-1/2 from the block's rear end and 15/16 up, which puts the pin at the lid's hinge edge as on sheet 9.
* **Lid hinge:** detail A puts the hole over the side plates' front edge, 1-1/8 above their top.

## Deviations

* **Hinge pin:** 5/8 long, not their 1-3/8. Longer, it fouls the followers (inside) or the yoke arms (outside).

## Findings (their design as drawn)

See `check.log` for the full list. The design notes and the strength table are on sheet 4 of the drawing set.

* **Lever force.**
  * The manual quotes 80 lbf. On the 48 in lever, 80 lbf makes only about **80 psi**.
  * 200 psi needs about 200 lbf, which is two people.
* **Strength at 300 psi (overfill design load).** These parts are over allowable:
  * the 1/4 side plates: they span 12 in between the channel flanges with no stiffener;
  * the 3/16 lid, both between and outside the rails;
  * the lid and rails as a beam;
  * the 1 in piston pin, which is 1-1/8 out from the piston side to the arm;
  * the toggle axle;
  * the 1-1/4 sch 40 lever.

  At their 80 psi most of these pass.
* **Counterweights vs the yoke head.**
  * With the yoke resting on the eject rollers, the counterweights sit against the head bodies.
  * Swinging the lid open or shut, the counterweights pass through the head and pivot mounts.
  * They only clear once the lid is fully open: 74 deg, where it rests on the front channel.
  * This is a reconstruction-level finding: it depends on the open placements above.
* **Start pose.** With the followers seated, the yoke leans 17 deg forward. The head's front corner then meets the counterweight-arm blocks and the hinge pins at the lid's hinge edge, and the pivot mounts touch the lid's front edge.
* **No over-centre stop.** The lever stops at dead centre (horizontal) with no positive stop, so the operator holds it there.
* **Lid in the block's path.** At 74 deg the lid leans over the front of the mold, so a rising block meets it unless the lid is lifted further by hand.
