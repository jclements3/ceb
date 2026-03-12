
# CINVA-Ram Block Press

OpenSCAD model of a CINVA-Ram compressed earth block press.
All dimensions in inches. Material: 1/4" (0.250") steel plate unless noted.

Primary file: `cinva_ram.scad`

## Parts by Assembly

### Brown — Pivot assembly (moves along ramp)
| Part       | Description                                                     |
|------------|-----------------------------------------------------------------|
| **Pivot**  | Solid 2x2x6 block — holds handle, wings/tails pivot around it   |
| **Wing**   | Long toggle link (2 holes) — connects spacer pin to roller pin  |
| **Tail**   | Short toggle link (1 hole) — connects spacer pin to pivot block |
| **Handle** | 6' round bar in pivot sunk hole (cylinder, no module)           |

### Orange — Lever assembly (pivots around load pin)
| Part                   | Description                                                                    |
|------------------------|--------------------------------------------------------------------------------|
| **Lever bar**          | Long arm the operator pulls to press the brick (inline, `lever_bar_profile()`) |
| **Cross**              | Cross bars welded between lever bars at grip end (inline cubes)                |
| **Lever spacer block** | Block between crosses with roller hole (inline cube)                           |

### Pink — Clamp (rotates on axle)
| Part       | Description                                                        |
|------------|--------------------------------------------------------------------|
| **Clamp**  | Hook-shaped bracket on axle that grabs the cross to lock the lever |
| **Spacer** | Plate between left and right clamp brackets                        |

### Purple — Pins and bars (round stock)
| Part            | Description                                          |
|-----------------|------------------------------------------------------|
| **Fulcrum Pin** | Fixed pin through side plate holes                   |
| **Load Pin**    | Pin in side slots, rises with lever mechanism        |
| **Roller**      | Rolls along ramp surface, drives the lever           |
| **Spacer Pin**  | Through pivot/wing upper holes, moves with assembly  |
| **Axle**        | 7/16" pin through front block, clamp rotates on this |

### Teal — Shelf assembly (rises to press brick)
| Part        | Description                                                 |
|-------------|-------------------------------------------------------------|
| **Shelf**   | Flat plate the brick sits on, rises in the side slots       |
| **Bracket** | Vertical brace under shelf, connects shelf to piston plates |
| **Piston**  | Vertical plate pair connecting shelf to load pin            |

### Red — Ramps and Top
| Part     | Description                                                                 |
|----------|-----------------------------------------------------------------------------|
| **Top**  | Flat plate on top of side plates — ramps sit on this                        |
| **Ramp** | V-shaped profile the roller rolls along to convert pull into downward press |

### Gray (ghost) — Structure
| Part         | Description                                                     |
|--------------|-----------------------------------------------------------------|
| **Side**     | Tall vertical plate with piston slot, bolted to feet            |
| **EndPlate** | Plate welded to shelf front/back edges, forms the brick chamber |

### White — Hinge (Top+Ramps swing open to eject brick)
| Part           | Description                                                   |
|----------------|---------------------------------------------------------------|
| **Receiver**   | Cylinder with 0.5" hole welded to Side plate — receives the pin |
| **Tab**        | Bracket welded to Top plate, extends over Receiver              |
| **Pin**        | 0.5" dia cylinder welded to Tab, drops into Receiver            |

### Green — Base
| Part             | Description                                                        |
|------------------|--------------------------------------------------------------------|
| **Base_Bracket** | L-shaped feet — bolts to ground, side plates mount to vertical leg |

## Animation

The model animates with OpenSCAD's `$t` variable (0 to 1):
- **t=0**: Roller at right side of ramp, lever tilted right
- **t=0.5**: Roller near peak, lever nearly vertical
- **t=1**: Roller past peak on left slope, lever tilted left

To render specific frames from the command line:
```
openscad -o frame.png -D '_t_override=0.5' cinva_ram.scad
```

## DXF Export

Run `export_dxf.sh` to export 2D projections of all parts as DXF files in `./dxf/`:
```
bash export_dxf.sh
```

## Reference Drawings

| Drawing | Description |
|---------|-------------|
| cinva1.jpg | Sheet 1 — Mold box walls |
| cinva2.jpg | Sheet 2 — Toggle links (Wing/Tail) |
| cinva3.jpg | Sheet 3 — Clamp bracket |
| cinva4.jpg | Sheet 4 — Lever handle and cross bars |
| cinva5.jpg | Sheet 5 — Cover |
| cinva6.jpg | Sheet 6 — Bearing plates |
| cinva7.jpg | Sheet 7 — Baseboard (Side) and piston |

## Reference Photos

| Photo | Description |
|-------|-------------|
| ![](Blockpress.jpg) | Baseboard frame and mold box sub-assemblies before final assembly |
| ![](Blockpress1.jpg) | Mold box welded, cover open showing hinge and interior |
| ![](Blockpress003.jpg) | Piston body close-up — rectangular with pivot hole and bronze bushing |
| ![](Compressedearthblockpressing17.jpg) | Complete press in use, ejecting a compressed earth block |
