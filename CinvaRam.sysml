/*
 * CinvaRam.sysml -- running example: simple 14 x 7 x 4 CINVA-Ram CEB press
 * Source of truth: github.com/jclements3/ceb
 *   cinva_simple.py   Params, poses, checks   (simulation / analysis)
 *   drawings/simple-14x7x4/manifest.json      (sheets, stock, masses)
 *   ASSEMBLY.md                               (operation, test procedure)
 * Units: inches, lbf, lb (USCustomaryUnits).
 *
 * Sections
 *   1 Library imports, materials, constants
 *   2 Items (soil, brick) and metadata (CAD/sim links)
 *   3 Structure: Component, sub-assemblies, CinvaRam
 *   4 Load path (connections)
 *   5 Behavior: operating states, MakeBrick action
 *   6 Calcs: press force, strength checks
 *   7 Requirements
 *   8 Analysis (external solver) and verification
 *   9 Configured instance (results + satisfy: CinvaRamResults.sysml)
 */
package CinvaRamExample {

    // =================================================================
    // 1  Imports, materials, constants
    // =================================================================
    private import ScalarValues::*;
    private import ISQ::*;
    private import SI::*;
    private import USCustomaryUnits::*;
    private import NumericalFunctions::*;   // sum
    private import TrigFunctions::pi;
    private import ControlFunctions::*;     // forAll
    private import VerificationCases::*;    // VerdictKind

    enum def Material { A36; AR400; steel4140PH; steel1018; sch80Pipe; }

    package MaterialData {
        attribute fy_A36   : PressureValue =  36000 [lbf/'in'**2];
        attribute fu_A36   : PressureValue =  58000 [lbf/'in'**2];
        attribute fy_4140  : PressureValue =  95000 [lbf/'in'**2];
        attribute fy_1018  : PressureValue =  50000 [lbf/'in'**2];
        attribute fy_AR400 : PressureValue = 145000 [lbf/'in'**2];
    }
    private import MaterialData::*;

    // =================================================================
    // 2  Items and metadata
    // =================================================================
    item def LooseSoil {
        attribute fillDepth : LengthValue;
    }
    item def Brick {
        attribute l : LengthValue;
        attribute w : LengthValue;
        attribute h : LengthValue;
    }

    /* Link to the generated ISO 128 sheet and DXF in drawings/simple-14x7x4/ */
    metadata def Dwg {
        attribute sheet : Integer;
        attribute dxf   : Boolean;
    }
    /* External tool that computes or checks a value */
    metadata def ExternalSolver {
        attribute command : String;
        attribute output  : String;
    }

    // =================================================================
    // 3  Structure
    // =================================================================
    abstract part def Component {
        attribute itemNo   : Integer;
        attribute qty      : Integer;
        attribute stock    : String;
        attribute material : Material;
        attribute unitMass : MassValue;
        attribute mass     : MassValue = qty * unitMass;
    }

    part def Frame {
        part side   : Component { :>> itemNo = 1; :>> qty = 2; :>> stock = "0.625 plate A36";          :>> material = Material::A36;         :>> unitMass = 40.7 [lb]; @Dwg { sheet = 5;  dxf = true;  } }
        part endPl  : Component { :>> itemNo = 2; :>> qty = 2; :>> stock = "0.500 plate A36";          :>> material = Material::A36;         :>> unitMass =  7.4 [lb]; @Dwg { sheet = 6;  dxf = true;  } }
        part foot   : Component { :>> itemNo = 3; :>> qty = 4; :>> stock = "2 x 2 x 1/4 angle";      :>> material = Material::A36;         :>> unitMass =  0.8 [lb]; @Dwg { sheet = 7;  dxf = false; } }
        part fpin   : Component { :>> itemNo = 4; :>> qty = 2; :>> stock = "1.250 round 1018";           :>> material = Material::steel1018;   :>> unitMass =  0.5 [lb]; @Dwg { sheet = 8;  dxf = false; } }
        part gpin   : Component { :>> itemNo = 5; :>> qty = 2; :>> stock = "1.000 round 1018";           :>> material = Material::steel1018;   :>> unitMass =  0.3 [lb]; @Dwg { sheet = 9;  dxf = false; } }
        attribute mass : MassValue = sum((side.mass, endPl.mass, foot.mass, fpin.mass, gpin.mass));
    }

    part def Lid {
        part plate   : Component { :>> itemNo = 6;  :>> qty = 1; :>> stock = "0.625 plate A36";        :>> material = Material::A36;         :>> unitMass = 19.2 [lb]; @Dwg { sheet = 10; dxf = true;  } }
        part ramp    : Component { :>> itemNo = 7;  :>> qty = 2; :>> stock = "0.750 plate AR400";        :>> material = Material::AR400;       :>> unitMass =  6.9 [lb]; @Dwg { sheet = 11; dxf = true;  } }
        part strap   : Component { :>> itemNo = 8;  :>> qty = 2; :>> stock = "0.375 plate A36";        :>> material = Material::A36;         :>> unitMass =  2.7 [lb]; @Dwg { sheet = 12; dxf = true;  } }
        part hrest   : Component { :>> itemNo = 9;  :>> qty = 2; :>> stock = "0.195 x 1/2 flat bar";   :>> material = Material::A36;         :>> unitMass =  0.1 [lb]; @Dwg { sheet = 13; dxf = true;  } }
        part lhandle : Component { :>> itemNo = 23; :>> qty = 1; :>> stock = "0.500 round 1018, bent"; :>> material = Material::steel1018;   :>> unitMass =  0.5 [lb]; @Dwg { sheet = 27; dxf = false; } }
        attribute mass : MassValue = sum((plate.mass, ramp.mass, strap.mass, hrest.mass, lhandle.mass));
    }

    part def Piston {
        part cap : Component { :>> itemNo = 10; :>> qty = 1; :>> stock = "0.500 plate A36";            :>> material = Material::A36;         :>> unitMass = 13.5 [lb]; @Dwg { sheet = 14; dxf = true;  } }
        part web : Component { :>> itemNo = 11; :>> qty = 4; :>> stock = "0.375 plate A36";            :>> material = Material::A36;         :>> unitMass =  6.5 [lb]; @Dwg { sheet = 15; dxf = true;  } }
        attribute mass : MassValue = sum((cap.mass, web.mass));
    }

    part def Yoke {
        part arm  : Component { :>> itemNo = 12; :>> qty = 2; :>> stock = "0.500 plate A36";           :>> material = Material::A36;         :>> unitMass =  9.2 [lb]; @Dwg { sheet = 16; dxf = true;  } }
        part xbar : Component { :>> itemNo = 13; :>> qty = 2; :>> stock = "0.375 plate A36";           :>> material = Material::A36;         :>> unitMass = 2.0 [lb]; @Dwg { sheet = 17; dxf = true;  } }
        part pinP : Component { :>> itemNo = 14; :>> qty = 1; :>> stock = "1.750 round 4140 prehard";   :>> material = Material::steel4140PH; :>> unitMass = 7.2 [lb]; @Dwg { sheet = 18; dxf = false; } }
        attribute mass : MassValue = sum((arm.mass, xbar.mass, pinP.mass));
    }

    /* "L-cam" head: Q at the corner, cam pin at the foot, handle on the other leg */
    part def Head {
        part cheek  : Component { :>> itemNo = 15; :>> qty = 2; :>> stock = "0.500 plate A36";         :>> material = Material::A36;         :>> unitMass = 5.7 [lb]; @Dwg { sheet = 19; dxf = true;  } }
        part pinQ   : Component { :>> itemNo = 16; :>> qty = 2; :>> stock = "1.250 round 4140 prehard";     :>> material = Material::steel4140PH; :>> unitMass =  0.6 [lb]; @Dwg { sheet = 20; dxf = false; } }
        part camPin : Component { :>> itemNo = 17; :>> qty = 1; :>> stock = "1.375 round 4140 prehard";  :>> material = Material::steel4140PH; :>> unitMass = 3.5 [lb]; @Dwg { sheet = 21; dxf = false; } }
        part bridge : Component { :>> itemNo = 18; :>> qty = 2; :>> stock = "0.375 plate A36";         :>> material = Material::A36;         :>> unitMass = 2.1 [lb]; @Dwg { sheet = 22; dxf = false; } }
        part handle : Component { :>> itemNo = 19; :>> qty = 1; :>> stock = "2 sch 80 pipe";  :>> material = Material::sch80Pipe;   :>> unitMass = 33.8 [lb]; @Dwg { sheet = 23; dxf = false; } }
        part latch  : Component { :>> itemNo = 20; :>> qty = 2; :>> stock = "0.375 plate A36";         :>> material = Material::A36;         :>> unitMass =  0.4 [lb]; @Dwg { sheet = 24; dxf = true;  } }
        part lbar   : Component { :>> itemNo = 21; :>> qty = 1; :>> stock = "3/8 x 1-1/8 flat bar";  :>> material = Material::A36;         :>> unitMass =  0.4 [lb]; @Dwg { sheet = 25; dxf = false; } }
        part lpin   : Component { :>> itemNo = 22; :>> qty = 1; :>> stock = "0.500 round 1018";  :>> material = Material::steel1018;   :>> unitMass = 0.5 [lb]; @Dwg { sheet = 26; dxf = false; } }
        attribute camOffset : LengthValue = 2.132 ['in'];   // Q -> cam pin, hold +/-0.010
        attribute mass : MassValue = sum((cheek.mass, pinQ.mass, camPin.mass, bridge.mass,
                                          handle.mass, latch.mass, lbar.mass, lpin.mass));
    }

    /* Feeder (rev C): funnel on a sliding feed box with a knife-gate floor. Parks on the +Y side, slides
       across the mold at fill only; bolted to the side plates, so it is an attachment (its mass is reported
       separately as feederMass). */
    part def Feeder {
        part endPin     : Component { :>> itemNo = 24; :>> qty = 1; :>> stock = "10 ga sheet A36, bent"; :>> material = Material::A36; :>> unitMass = 5.0 [lb]; @Dwg { sheet = 28; dxf = false; } }
        part endLid     : Component { :>> itemNo = 25; :>> qty = 1; :>> stock = "10 ga sheet A36"; :>> material = Material::A36; :>> unitMass = 4.9 [lb]; @Dwg { sheet = 29; dxf = true; } }
        part strikeWall : Component { :>> itemNo = 26; :>> qty = 1; :>> stock = "10 ga sheet A36"; :>> material = Material::A36; :>> unitMass = 7.2 [lb]; @Dwg { sheet = 30; dxf = true; } }
        part funnelWall : Component { :>> itemNo = 27; :>> qty = 1; :>> stock = "10 ga sheet A36, bent"; :>> material = Material::A36; :>> unitMass = 7.5 [lb]; @Dwg { sheet = 31; dxf = false; } }
        part gate       : Component { :>> itemNo = 28; :>> qty = 1; :>> stock = "3/16 plate A36"; :>> material = Material::A36; :>> unitMass = 5.9 [lb]; @Dwg { sheet = 32; dxf = false; } }
        part gateHandle : Component { :>> itemNo = 29; :>> qty = 1; :>> stock = "0.500 round 1018, bent"; :>> material = Material::steel1018; :>> unitMass = 0.7 [lb]; @Dwg { sheet = 33; dxf = false; } }
        part boxHandle  : Component { :>> itemNo = 30; :>> qty = 1; :>> stock = "0.500 round 1018, bent"; :>> material = Material::steel1018; :>> unitMass = 0.7 [lb]; @Dwg { sheet = 34; dxf = false; } }
        part stopLug    : Component { :>> itemNo = 31; :>> qty = 1; :>> stock = "1/2 flat bar A36"; :>> material = Material::A36; :>> unitMass = 0.2 [lb]; @Dwg { sheet = 35; dxf = true; } }
        part rail       : Component { :>> itemNo = 32; :>> qty = 2; :>> stock = "1.5 x 1.5 x 3/16 angle"; :>> material = Material::A36; :>> unitMass = 1.8 [lb]; @Dwg { sheet = 36; dxf = false; } }
        part nearTie    : Component { :>> itemNo = 33; :>> qty = 1; :>> stock = "1.5 x 1.5 x 3/16 angle"; :>> material = Material::A36; :>> unitMass = 2.2 [lb]; @Dwg { sheet = 37; dxf = false; } }
        part farTie     : Component { :>> itemNo = 34; :>> qty = 1; :>> stock = "1.5 x 1.5 x 3/16 angle"; :>> material = Material::A36; :>> unitMass = 2.2 [lb]; @Dwg { sheet = 38; dxf = false; } }
        part leg        : Component { :>> itemNo = 35; :>> qty = 2; :>> stock = "1.5 x 1.5 x 3/16 angle"; :>> material = Material::A36; :>> unitMass = 4.2 [lb]; @Dwg { sheet = 39; dxf = false; } }
        part legTie     : Component { :>> itemNo = 36; :>> qty = 1; :>> stock = "1.5 x 1.5 x 3/16 angle"; :>> material = Material::A36; :>> unitMass = 2.2 [lb]; @Dwg { sheet = 40; dxf = false; } }
        part railBracket: Component { :>> itemNo = 37; :>> qty = 1; :>> stock = "3 x 3 x 3/8 angle"; :>> material = Material::A36; :>> unitMass = 1.1 [lb]; @Dwg { sheet = 41; dxf = false; } }
        part stopPost   : Component { :>> itemNo = 38; :>> qty = 1; :>> stock = "1/2 x 2 flat bar A36"; :>> material = Material::A36; :>> unitMass = 1.0 [lb]; @Dwg { sheet = 42; dxf = false; } }
        attribute mass : MassValue = sum((endPin.mass, endLid.mass, strikeWall.mass, funnelWall.mass, gate.mass,
                                          gateHandle.mass, boxHandle.mass, stopLug.mass, rail.mass, nearTie.mass,
                                          farTie.mass, leg.mass, legTie.mass, railBracket.mass, stopPost.mass));
    }

    /* Stand (rev F): welded steel frame, top at the plane the press bolts to. */
    part def Stand {
        part rail      : Component { :>> itemNo = 39; :>> qty = 2; :>> stock = "3 x 2 x 3/16 rect tube"; :>> material = Material::A36; :>> unitMass = 14.2 [lb]; @Dwg { sheet = 43; dxf = false; } }
        part crossTube : Component { :>> itemNo = 40; :>> qty = 3; :>> stock = "2 x 2 x 3/16 sq tube"; :>> material = Material::A36; :>> unitMass = 2.7 [lb]; @Dwg { sheet = 44; dxf = false; } }
        part leg       : Component { :>> itemNo = 41; :>> qty = 4; :>> stock = "2 x 2 x 3/16 sq tube"; :>> material = Material::A36; :>> unitMass = 3.8 [lb]; @Dwg { sheet = 45; dxf = false; } }
        part footPlate : Component { :>> itemNo = 42; :>> qty = 4; :>> stock = "1/4 plate A36"; :>> material = Material::A36; :>> unitMass = 1.1 [lb]; @Dwg { sheet = 46; dxf = true; } }
        attribute mass : MassValue = sum((rail.mass, crossTube.mass, leg.mass, footPlate.mass));
    }

    part def CinvaRam {
        // --- design parameters (cinva_simple.Params) ---
        attribute brickL    : LengthValue default 14.0 ['in'];
        attribute brickW    : LengthValue default  7.0 ['in'];
        attribute brickH    : LengthValue default  4.0 ['in'];
        attribute rise      : LengthValue default  2.75 ['in'];
        attribute ejectOver : LengthValue default  0.125 ['in'];
        attribute handleLen : LengthValue default 90.0 ['in'];   // Q -> grip
        attribute dPinP     : LengthValue default  1.75 ['in'];
        attribute dPinQ     : LengthValue default  1.25 ['in'];
        attribute dCam      : LengthValue default  1.375 ['in'];
        attribute tSide     : LengthValue default  0.625 ['in'];
        attribute wArm      : LengthValue default  3.00 ['in'];
        attribute tArm      : LengthValue default  0.50 ['in'];
        attribute tCheek    : LengthValue default  0.50 ['in'];
        attribute tWeb      : LengthValue default  0.375 ['in'];
        attribute armY      : LengthValue default  4.1875 ['in']; // inner face of yoke arm from centreline
        attribute cheekY    : LengthValue default  3.625 ['in'];   // inner face of cheek
        attribute psi0      : PlaneAngleValue default -110.0 ['°'];
        attribute psiLock   : PlaneAngleValue default    3.0 ['°'];
        attribute thetaEject: PlaneAngleValue default   80.0 ['°'];
        attribute pWork     : PressureValue default 150.0 [lbf/'in'**2];
        attribute pDesign   : PressureValue default 306 [lbf/'in'**2];

        // --- derived ---
        attribute fill    : LengthValue = brickH + rise;
        attribute area    : AreaValue   = brickL * brickW;
        attribute fWork   : ForceValue  = PressForce(pWork, area);
        attribute fDesign : ForceValue  = PressForce(pDesign, area);

        // --- results: declared here, valued in CinvaRamResults.sysml (generated) ---
        attribute peakHandleForce  : ForceValue;   // at pWork
        attribute peakEjectForce   : ForceValue;   // ~112 lbf
        attribute lockAngle        : PlaneAngleValue;
        attribute interferences    : Integer;      // part pairs intersecting over the sweep
        attribute functionalFails  : Integer;      // failed verify() checks
        attribute stressChecks     : StressCheck[*];
        attribute minMargin        : Real;         // smallest allow/sigma - 1 over stressChecks
        attribute steelMass        : MassValue;    // solver BOM weight, press only (tracks variants; totalMass is the drawing BOM)
        attribute feederMass       : MassValue;    // solver BOM weight, feeder
        attribute standMass        : MassValue;    // solver BOM weight, stand
        attribute heaviestPart     : MassValue;    // heaviest single part, press or feeder
        attribute feedCapacity     : VolumeValue;  // soil the box and funnel hold above the gate
        attribute chargeVolume     : VolumeValue;  // one loose charge: the mold at fill

        // --- structure ---
        part moldBox : Frame;
        part lid    : Lid;
        part piston : Piston;
        part yoke   : Yoke;
        part head   : Head;
        part feeder : Feeder;
        part stand  : Stand;

        attribute totalMass : MassValue =
            sum((moldBox.mass, lid.mass, piston.mass, yoke.mass, head.mass));

        // --- strength (section 6) ---
        attribute sPinQBend  : PressureValue =
            PinBendingStress(fDesign / 2, (armY + tArm/2) - (cheekY + tCheek/2), dPinQ);
        attribute sPinPShear : PressureValue = fDesign / 2 / (pi * dPinP**2 / 4);
        attribute sArmNetTen : PressureValue = fDesign / 2 / ((wArm - dPinP - 0.03125 ['in']) * tArm);
        attribute sArmBear   : PressureValue = fDesign / 2 / (dPinP * tArm);

        // --- behavior ---
        exhibit state cycle : PressCycle;
        perform action makeBrick : MakeBrick;
    }

    // =================================================================
    // 4  Load path: brick -> piston -> P -> yoke -> Q -> head -> cam -> ramp -> lid
    //    (does NOT pass through the mold box welds)
    // =================================================================
    connection def LoadTransfer {
        end part a;
        end part b;
        attribute share : Real;     // fraction of press force through this joint per instance
    }

    part def LoadPathView :> CinvaRam {
        connection webToP   : LoadTransfer connect piston.web    to yoke.pinP  { :>> share = 0.25; }
        connection pToArm   : LoadTransfer connect yoke.pinP     to yoke.arm   { :>> share = 0.50; }
        connection armToQ   : LoadTransfer connect yoke.arm      to head.pinQ  { :>> share = 0.50; }
        connection qToCheek : LoadTransfer connect head.pinQ     to head.cheek { :>> share = 0.50; }
        connection cheekCam : LoadTransfer connect head.cheek    to head.camPin{ :>> share = 0.50; }
        connection camRamp  : LoadTransfer connect head.camPin   to lid.ramp   { :>> share = 0.50; }
        connection rampLid  : LoadTransfer connect lid.ramp      to lid.plate  { :>> share = 0.50; }
    }

    // =================================================================
    // 5  Behavior
    // =================================================================
    attribute def PushBox;
    attribute def PullGate;
    attribute def PushGate;
    attribute def PullBox;
    attribute def CloseLid;
    attribute def StandUp;
    attribute def PullHandle;
    attribute def RaiseHandle;
    attribute def Tilt;
    attribute def OpenLid;
    attribute def PushHandle;

    state def PressCycle {
        attribute psi : PlaneAngleValue;    // head angle, cam->Q from vertical

        entry; then fill;

        state fill {
            doc /* lid on stand, latch shut, yoke on fixed pins ~33 deg; the feeder delivers one charge */
            entry; then parked;
            state parked   { doc /* feed box against the far tie, gate shut, funnel loaded */ }
            state boxOver  { doc /* pushed by the gate handle until the lug lands on the stop post */ }
            state gateOpen { doc /* gate pulled open: the charge drops into the mold */ }
            state gateShut { doc /* gate pushed shut: the charge is sheared off at the mold top */ }
            state returned { doc /* box pulled back to park: the lid may swing over */ }
            transition first parked   accept PushBox  then boxOver;
            transition first boxOver  accept PullGate then gateOpen;
            transition first gateOpen accept PushGate then gateShut;
            transition first gateShut accept PullBox  then returned;
        }
        transition first fill.returned accept CloseLid then closed;
        state closed  { doc /* lid swung over the mold */ }
        state seated  { doc /* cam pin up the long leg, dropped into both scoops */ }
        state pressing{ doc /* knee straightens about cam pin; piston rises 2.75 */ }
        state locked  { doc /* 3 deg over centre, cheeks on handle rests */ }
        state tilted  { doc /* handle back past upright, latch dropped, yoke on fixed pins */ }
        state ejecting{ doc /* lid open, handle pushed down, piston top +0.125 at 80 deg */ }

        transition first closed   accept StandUp     then seated;
        transition first seated   accept PullHandle  then pressing;
        transition first pressing if psi >= 3.0 ['°'] then locked;
        transition first locked   accept RaiseHandle then tilted;
        transition first tilted   accept OpenLid     then ejecting;
        transition first ejecting accept PushHandle  then fill;
    }

    action def MakeBrick {
        in  item soil  : LooseSoil;
        out item brick : Brick;

        action fillMold { in item soil : LooseSoil; }
        then action closeLid;
        then action standUp;
        then action press;
        then action release;
        then action openLid;
        then action eject { out item brick : Brick; }

        bind fillMold.soil = soil;
        bind brick = eject.brick;
    }

    // =================================================================
    // 6  Calcs
    // =================================================================
    attribute def StressCheck {
        attribute name  : String;
        attribute basis : String;
        attribute sigma : PressureValue;
        attribute allow : PressureValue;
        attribute margin : Real = allow / sigma - 1;
    }

    calc def PressForce {
        in p : PressureValue;
        in a : AreaValue;
        return f : ForceValue = p * a;
    }

    calc def PinBendingStress {
        in force : ForceValue;     // load per side
        in arm   : LengthValue;    // moment arm
        in d     : LengthValue;    // pin diameter
        return sigma : PressureValue = force * arm / (pi * d**3 / 32);
    }

    // =================================================================
    // 7  Requirements
    // =================================================================
    requirement def BrickSize {
        doc /* Pressed brick 14 x 7 x 4 from a 6.75 loose fill. */
        subject press : CinvaRam;
        require constraint {
            press.brickL == 14 ['in'] and press.brickW == 7 ['in'] and
            press.brickH == 4 ['in'] and press.fill == 6.75 ['in']
        }
    }

    requirement def HandleForceLimit {
        doc /* Peak pull for one operator at the working pressure (pWork). The peak comes with the grip about
               67 in above the ground and the handle 30 deg above horizontal, so the applicable limit is
               CCOHS Table 2 "pull down, above head height": 540 N (120 lbf), adopted from Eastman Kodak,
               Ergonomic Design for People at Work, vol. 2 (1986). CCOHS: repetitive tasks should be designed
               for considerably lower forces; this is a ceiling, not a target. */
        subject press : CinvaRam;
        attribute limit : ForceValue = 120 [lbf];
        require constraint { press.peakHandleForce <= limit }
    }

    requirement def OverCentreLock {
        doc /* Handle stays down unaided: lock 3 deg past straight. */
        subject press : CinvaRam;
        require constraint { press.lockAngle >= 3.0 ['°'] }
    }

    requirement def PinAndArmStrength {
        doc /* At 306 psi design pressure. Allowables per cinva_simple.checks(). */
        subject press : CinvaRam;
        require constraint { press.sPinQBend  <= 0.6 * fy_4140 }
        require constraint { press.sPinPShear <= 0.4 * fy_4140 }
        require constraint { press.sArmNetTen <= 0.5 * fu_A36 }
        require constraint { press.sArmBear   <= 0.9 * fy_A36 }
    }

    requirement def NoCollision {
        doc /* No interference through fill -> lock -> eject sweep; all functional checks pass. */
        subject press : CinvaRam;
        require constraint { press.interferences == 0 and press.functionalFails == 0 }
    }

    requirement def AllStressChecks {
        doc /* Every solver strength check at 306 psi within its allowable. */
        subject press : CinvaRam;
        require constraint { press.stressChecks->forAll { in c : StressCheck; c.sigma <= c.allow } }
    }

    requirement def FeedCapacity {
        doc /* The feeder holds at least one loose charge above its gate. */
        subject press : CinvaRam;
        require constraint { press.feedCapacity >= press.chargeVolume }
    }

    requirement def PartHandlingLimit {
        doc /* Every single part can be lifted by one person during fabrication and assembly: heaviest part
               at most the NIOSH Revised Lifting Equation load constant, 23 kg (51 lb), the recommended limit
               under ideal lifting conditions. No standard caps the total steel of a bolted-down press, so
               totalMass is reported, not limited. */
        subject press : CinvaRam;
        attribute limit : MassValue = 51 [lb];
        require constraint { press.heaviestPart <= limit }
    }

    // =================================================================
    // 8  Analysis and verification
    // =================================================================
    analysis def KinematicsAndClearance {
        doc /* Solves fill/start/locked/eject poses, sweeps for interference,
               writes peakHandleForce, peakEjectForce, lockAngle, interferences,
               functionalFails, stressChecks via sysml_sync.py. */
        @ExternalSolver {
            command = "python3 sysml_sync.py";
            output  = "CinvaRamResults.sysml";
        }
        subject press : CinvaRam;
        objective { doc /* Feasible stroke; force and clearance results. */ }
        return peak : ForceValue = press.peakHandleForce;
    }

    analysis def DrawingGeneration {
        @ExternalSolver {
            command = "python3 cinva_drawings.py --model simple";
            output  = "drawings/simple-14x7x4/{sheets,dxf,manifest.json,.pdf,.step}";
        }
        subject press : CinvaRam;
    }

    verification def LoadTest {
        doc /* ASSEMBLY.md Step 8: light fills up to full 6.75; check after 20 bricks
               that P, Q, cam are straight, scoops undented, sides unbulged, welds sound. */
        subject press : CinvaRam;
        objective {
            verify requirement : HandleForceLimit;
            verify requirement : OverCentreLock;
        }
        attribute measuredPull : ForceValue;
        return verdict : VerdictKind =
            if measuredPull <= 165 [lbf] ? VerdictKind::pass else VerdictKind::fail;
    }

    // =================================================================
    // 9  Configured instance
    // =================================================================
    part cinvaRam : CinvaRam;     // as designed; analysed variant in CinvaRamResults.sysml

    requirement brickSize   : BrickSize;
    requirement handleForce : HandleForceLimit;
    requirement lock        : OverCentreLock;
    requirement strength    : PinAndArmStrength;
    requirement noCollision : NoCollision;
    requirement handling    : PartHandlingLimit;
    requirement stresses    : AllStressChecks;
    requirement feedCap     : FeedCapacity;

}
