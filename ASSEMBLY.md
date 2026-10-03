# Simple CINVA-Ram Press, 14 x 7 x 4 — Welding & Assembly Guide

Fabrication sequence for the press in `drawings/simple-14x7x4/` (drawing set `SCR-14x7x4-00` to `-23`).
Part numbers below are the item numbers on the parts list (sheet 1). All dimensions in inches.

This press is a scale-up of the permies.com replica (thread 33406). His part drawings are
`cinva1-7.jpg`; the SketchUp model and his video show how the parts go together. Each of his
parts is scaled from his 11.5 x 6 x 3-5/8 brick to our 14 x 7 x 4:
- lengths along the mold x 1.217;
- widths across it x 1.167;
- heights x 1.102 (his 6-1/8 loose fill becomes 6-3/4).

The heavy-duty version, with a claw latch and an eject roller on posts, is in `ASSEMBLY_full.md`.

**How it works (read this first).**
- **Mold, piston and yoke.** The piston slides in the mold box. Main pin **P** runs through its four
  webs, out through vertical slots in both side plates, and into the two **yoke arms** outside the box.
  At the top the arms are tied by two **cross bars** into a box. They carry the **head** on two stub
  pins **Q**.
- **The head (his "L-cam").** It is shaped like an L: pin Q at the corner, the **cam pin** at the foot,
  2.132 from Q, and the handle along the other leg.
- **The ramps.** The two **V ramps** on the lid each have a half-round **scoop** at the peak, right over
  the middle of the mold.
- **Pressing.** Stand the yoke up, and the cam pin rides up the long leg of the ramps and drops into the
  scoops. Pulling the handle over then works like straightening a knee: the head pivots on the cam pin
  and swings Q up and over it. The yoke lifts the piston 2.75, squeezing the soil against the lid.
- **The lock.** At 3 deg past straight, the cheeks land on the two **handle rests** and the handle stays
  down on its own.
- **Where the force goes.** Through the brick, piston, pin P, yoke, pins Q, cam pin, ramps and lid. It
  does **not** go through the mold box welds.
- **Latch.** His **latch hooks** (item 20) hang from the head and drop over the pull-end cross bar. That
  holds head and yoke together while you tilt them.
- **Ejecting.** With the lid swung over, the yoke leans on the two **fixed pins** on the side plates.
  Pushing the handle down levers the piston up and the brick out.

See sheet 3 for the four positions and sheet 4 for the operating steps and loads.

## What changed from his drawings, and why

| Item | Part | His drawing | This press | Reason |
|---|---|---|---|---|
| 1 | Side plate slot | 2.000 wide for a 1 in pin | pin + 1/16 (1.813) | **His error**: the supplier later changed it to 1 in; a 2 in slot lets the pin wander |
| 1 | Side plate slot top | ends 1 in into the chamber | ends below the loose soil | soil would push out through the slot at fill |
| 4 | Fixed pins | 7.71 up (7 x 1.102) | 7.48 up | set so the eject stroke ends at 80 deg with the wider 3 in arms |
| 1 | Side plate | 1/4 plate | 5/8 plate | soil pressure on a 14 in wall (1/2 left a 7% stress margin; trade study in `sysml_trade.py`) |
| 2 | End plate | 1/4, 6 x 6 | 1/2, 7 x 7.5 | spans 7 in; reaches the piston at fill |
| 6 | Lid plate | 1/4, covers the side plates | 5/8; narrow except at the pull end | would dish; the head swings down past its edges while standing up |
| 7 | V ramp | 1/4 | 3/4 AR400 | the cam pin carries the whole press force in the scoop |
| 10, 11 | Piston cap, webs | 1/4 | 1/2 cap, 3/8 webs | cap would dish |
| 12 | Yoke arm | 2 x 1/4 bar | 3 x 1/2 plate, 2.3 in longer | pin loads; room for the cross-bar box over the head |
| 14, 16, 17 | Pins P, Q, cam | 1 in mild steel | 1-3/4, 1-1/4, 1-3/8 4140 prehard | 1 in mild-steel pins bend at 20,000 lbf; 1-1/4 cam pin left a 6% margin |
| 15 | Head | his link plates and 3 x 2 plates | one L-shaped cheek per side | same job, fewer pieces |
| 20 | Latch hook | notch on the side | notch at the tip | the hook drops straight onto the cross bar |

Two more changes:
- **The lid swings on his 11 in bars.** They pivot on pins near the bottom of the side plates at the
  pull end, so the lid swings over onto the stand.
- **The press bolts to a 12 in stand** that reaches 12 in past the pull end. This keeps the eject
  stroke at a workable height (the grip ends 23 in above the ground), and the open lid lies on it.
  Build the stand from timber or steel; it is not detailed.

## General welding rules

- Process: SMAW with E7018 or GMAW with ER70S-6. Fillet welds 1/4 unless noted.
- **AR400 ramps (item 7):** low-hydrogen only, preheat the joint to 300 F, cool slowly under a blanket.
- **No weld, spatter or grinding marks inside the mold or on the lid underside.** Weld outside only.
- **4140 pins (items 14, 16, 17):**
  - Weld only the Q stubs into the cheeks and the cam pin ends to the cheeks.
  - Keep those welds small and cool them slowly.
  - Never weld pin P.
- Line-bore the piston web holes for pin P after welding.
- Tack, check, then run final welds in short alternating passes.

## Purchased and turned items

| Item | Part | Stock / spec | Qty | Notes |
|---|---|---|---|---|
| 4 | Fixed pin | 1.250 round 1018, 1.563 long | 2 | Welded in the side plates |
| 5 | Lid pivot pin | 1.000 round 1018, 1.531 long | 2 | Washer and 1/8 cotter outside the strap |
| 14 | Main pin P | 1.750 round 4140 prehard, 10.625 long | 1 | Two 9/32 cross holes, 1/4 hitch pins |
| 16 | Pin Q (stub) | 1.250 round 4140 prehard, 1.688 long | 2 | One 9/32 cross hole each |
| 17 | Cam pin | 1.375 round 4140 prehard, 8.250 long | 1 | |
| 19 | Handle | 1-1/2 sch 80 pipe, 66.0 long | 1 | Grip end 74 from Q (rev D: was 64.0 / 72) |
| 22 | Latch pivot | 0.500 round 1018, 8.250 long | 1 | Cotter each end |
| 23 | Lid handle | 0.500 round 1018, bent into a U (horseshoe), 4 between legs | 1 | About 11 in of bar |
| — | Hardware | 1/2 bolts (4) for the foot clips, 1/4 hitch pins (4), 1/8 cotters (4), washers | | |
| — | Grease | lithium grease for pins P and Q, the scoops, the cam pin and the fixed pins | | |

Cut all plates from the DXF files in `drawings/simple-14x7x4/dxf/` (1:1, inches).
**The V ramp top edge and scoop must come from the DXF**: the scoop position sets the stroke.

## Step 1 — Mold box (items 1, 2, 3, 4, 5)

1. Cut both side plates from the DXF. Each has:
   - the corrected slot, centred on the length;
   - the fixed-pin hole, near the top at one end;
   - the lid-pivot hole, at the other end;
   - two 9/16 bolt holes along the bottom.
   The two plates are identical; one is flipped to face the other.
2. Stand the side plates on a flat table 7.000 apart (inside faces). Set the end plates between them,
   flush with the top edges and the plate ends.
3. Square the box: inside 14.000 x 7.000 at the top, diagonals equal within 1/32. Clamp stiff bars
   across top and bottom and weld the end plates outside only.
4. Slide a straight 1-3/4 bar through both slots: it must pass freely over the full length.
5. Weld the fixed pins (item 4) through their holes, inner end flush inside, and the lid pivot pins
   (item 5) the same way. Keep both square to the plates.
6. Bolt the four foot clips (item 3) through the bottom holes. The two at the pull end sit 3 in in from
   the plate end so the lid straps swing past them. Bolt or lag the clips to the stand.

## Step 2 — Piston (items 10, 11)

1. Weld the four webs under the cap in two pairs. The outer webs sit flush with the cap's long edges;
   the inner ones sit 1/2 inboard of them. All four are centred on the cap length.
2. Line-bore the 1.781 holes for pin P through all four webs after welding, 1.102 above the web bottoms.
3. The piston must slide the full depth of the mold with about 1/16 all round.

## Step 3 — Lid (items 6, 7, 8, 9)

1. Cut the lid plate from the DXF. It is 6.969 wide (inside the side plates) except the last 3 in at the
   pull end, which is full width and sits on the side plates.
2. Weld the V ramps along both long edges of the lid top, outer faces 3.563 from the centreline.
   - Put the long leg (lower end 0.276) at the fixed-pin end.
   - The scoops sit right over the middle of the mold.
   - Use low-hydrogen rod and preheat.
3. Weld the lid straps (item 8) to the edges of the wide part, reaching down to the lid pivot pins.
4. Weld the two handle rests (item 9) on the wide part along each edge, under where the head cheeks
   land. Fit them in Step 7.
5. Bend the lid handle (item 23) from 1/2 round into a U, 4 between leg centres, 3.25 overall. Weld the
   leg ends to the lid's fixed-pin end face, centred and level with the lid, so the U sticks straight
   out. Lift the lid by it to swing the lid over onto the stand, and to swing it back.

## Step 4 — Yoke (items 12, 13)

1. Cut both arms from the DXF and drill P and Q with the arms clamped together.
2. Weld the two cross bars (item 13) on edge between the arm tops to make a box. The pull-end bar's outer
   face is 0.875 from the arm centreline; the other is its mirror.
   - The head rests on the pull-end bar's lower edge.
   - The latch hooks drop over its top edge.

## Step 5 — Head (items 15 to 22)

1. Cut both cheeks from the DXF. Clamp them together and drill:
   - Q (1.250);
   - the cam pin (1.391), **2.132 below Q, hold +/-0.010**;
   - the latch pivot (0.531).
2. Weld a Q stub (item 16) into each cheek, inner end flush inside, sticking out.
3. Weld the two bridges (item 18) between the cheeks at the far end of the handle leg, 8.0 and 9.75 from
   Q; slide the handle (item 19) through both and weld all round.
4. Push the cam pin (item 17) through both cheeks, flush outside; weld the ends.
5. Weld the latch bar (item 21) across the two latch hooks (item 20). Hang them between the cheeks on the
   latch pivot (item 22), with a cotter at each end.

## Step 6 — Final assembly

1. Lower the piston into the mold from the top until its holes line up with the slots.
2. Hang the yoke arms outside the side plates and push pin P through: arm, slot, four webs, slot, arm.
   Hitch pins outside the arms.
3. Fit the head between the arm tops with the Q stubs in the arms' Q holes; washers and hitch pins
   outside. Grease.
4. Put the lid straps on the lid pivot pins; washers and cotters.

## Step 7 — Adjust and test (empty)

1. **Fill position:** lid swung over onto the stand by its handle, latch shut, yoke leaning on the fixed pins at about
   33 deg.
2. Swing the lid on and lift the handle and yoke upright. The cam pin must ride up the long leg of both
   ramps and drop into both scoops. The piston lifts about 3/4 on the way and settles back.
3. Lift the latch bar. Pull the handle over: the piston top should rise from 6.750 to 4.000 below the mold
   top. The cheeks land on the handle rests with the handle 3 deg below horizontal.
   - Grind or shim the rests so the stop is exactly there.
   - The handle must stay down by itself.
4. Raise the handle back past upright, drop the latch, tilt back onto the fixed pins, and swing the lid
   over. Push the handle down: the piston top must come up 1/8 above the mold top with the yoke at
   about 80 deg.
5. Grease the scoops, cam pin, pins P and Q and the fixed pins.

## Step 8 — Load test before production

Press a few light fills, then work up to a full 6.750 loose fill.
- **Handle force:** the peak comes about 70% of the way through the pull, with the grip about 67 in
  above the ground (head height), not at the end: the over-centre geometry takes the force away in the last
  few degrees before the lock. Peak 119 lbf at the 150 psi working pressure with the 74 in handle.
- **Ergonomic limit:** 120 lbf for pulling down above head height (CCOHS Table 2, from Kodak's *Ergonomic
  Design for People at Work*). Rev D runs at 150 psi with a 74 in handle so one operator stays under it.
  Do not raise the working pressure without a second operator: at 200 psi the peak is 159 lbf. For
  repetitive work CCOHS recommends considerably lower forces.
- **After 20 bricks:** check that pins P, Q and the cam pin are straight, the scoops are not dented,
  the side plates have not bulged, and no weld has cracked.
- **If the head will not reach the rests**, the fill is too heavy. Take soil out; don't force it.

## Step 9 — Feeder (items 24 to 38, rev C)

A funnel on a sliding feed box, parked on the **+Y side** (the side you shovel from). It slides across the
mold top at fill only.

**Why it is laid out this way.**
- Everything that moves above the mold stays within 5.31 of the centreline over the whole cycle (the Q stubs).
  The lid swings over the pull end and the yoke leans over the fixed-pin end, so the only free side is ±Y.
- The yoke arms, Q stubs and lid straps sweep the strip from the side plate out to y 5.875, so nothing fixed
  can bridge it. The box therefore has a **knife-gate floor**: shut while it crosses that gap, pulled open over
  the mold, pushed shut again. Pushing it shut shears the charge off level with the mold top, so every
  brick gets the same loose volume.
- At fill the head cheek tips hang 0.9 to 2.7 above the mold top over the first 1.4 at the fixed-pin end.
  The box's pin end is a 3/4 lip and a 45 deg chute that pass under them (0.36 clearance); the chute is
  steeper than the soil's angle of repose, so that end of the mold still fills.
- The rail bracket and stop post bolt to the side plates at x 9.25 to 11.25: the yoke arms reach no further
  than x 8.62 and the lid straps start at x 11.83.

**Fabrication.**
1. Cut the lid end wall (25), strike wall (26) and stop lug (31) from the DXFs. Bend the pin end (24) and the
   funnel wall (27) to their sheets: 10 ga, lip / chute / upright, and upright / 30 deg flare.
2. Tack the box square on a flat table: strike wall across both end walls, funnel wall between them. The
   strike wall's bottom edge is the strike-off: keep it straight and flush. The end walls and funnel wall stand
   7/32 up off the table (the gate runs under them); shim them while tacking. Weld outside only.
3. Weld the stop lug to the strike wall outside, 1/4 up from its bottom edge, at x 9.5 to 11.0.
4. Gate (28): bevel the leading edge on top, 30 deg. Weld the 3/16 square stop strip across it and the gate
   handle (29) on its tail. Weld the box handle (30) to the flared face, 11 up.
5. Frame: weld the two rails (32) on the near tie (33) and against the far tie's upright leg (34), upright
   legs outside and 1/16 clear of the box walls. Weld the legs (35) and leg tie (36).

**Fitting.**
1. Drill both side plates for the two new 9/16 holes (rev C): 10.25 and 11.25 from the plate's fixed-pin end
   (9.75 and 10.75 from the inside of the mold), 2.25 below the top edge. Both plates stay identical.
2. Bolt the rail bracket (37) to the +Y side plate and the stop post (38) to the -Y side plate, 1/2 bolts.
3. Set the frame on the bracket with the rail tops level with the mold top (shim the legs), bolt the near tie
   to the bracket, and lag or stake the legs.
4. With the press at fill, slide the empty box over: the lug must land on the post with the box square over
   the mold, and the tails still between the rails. Pull the gate open: it stops 3/16 short of the far wall.
5. Cycle the press through stand-up, pressing and eject with the box parked: nothing may touch it.

**Use** (fill step): shovel into the funnel (it holds about 2.3 charges). Push the box over by the gate handle
until the lug stops on the post. Hold the box handle, pull the gate open, tap the box. Push the gate shut and
pull the box back to park by its handle. Only then swing the lid on and stand the yoke up.
