# Designing for the filament

The material changes the design, so Print mode asks for it before any geometry and loads a profile:

```bash
python <skill>/scripts/print_profile.py PETG          # fits, min wall, overhang, bridge, slicer filament
python <skill>/scripts/print_profile.py PETG --batch  # SolidCraft parameters.change steps
```

The numbers live in [`assets/materials.json`](../assets/materials.json). Materials: PLA, PETG, ABS, ASA, TPU, PA (nylon), PC, PLA-CF, PETG-CF, PA-CF.

## Fits are diametral

A **diametral** clearance is the total gap across both sides of a mating pair. A pin in a hole with 0.2 mm diametral clearance has 0.1 mm per side. The profile's `fit_*` parameters are diametral, and a hole is drawn as `pin_dia + fit_close`. State per-side or total whenever you write a clearance. A radial allowance changes a diameter twice, an axial one usually changes a height once (HazAT).

| Fit | Meaning | Markforged published, diametral | This project's base, hobby 0.4 mm FDM, diametral |
|---|---|---|---|
| Press | Needs force to assemble | 0.00 to 0.05 mm | 0.10 mm |
| Close | Assembles by hand, negligible play | 0.05 to 0.10 mm | 0.25 mm |
| Free | Slides or rotates easily | 0.10 to 0.20 mm | 0.40 mm |

Markforged's figures are for their printers and are tighter than a hobby printer holds. The base column is a conservative default of this project, not a published figure. The material then adds an offset (PLA 0, PETG +0.05, ABS and ASA +0.10, nylon +0.15 and so on, see the JSON). **Do not apply a global shrink percentage**, and keep the fit allowance separate from any material compensation you calibrate later. Both points come from the HazAT guide.

## Calibrate with a coupon, not a guess

Build (as a SolidCraft batch) a coupon:  a plate of holes and a bar of matching pins at four clearances. It prints in minutes. Print it in the real filament on the real printer, pick the clearance that gives the fit you want, and write that value into `fit_close` (or whichever fit). Markforged calls this a 3D printed unit test: isolate the critical feature, keep the print under about 6 hours, vary the dimension, then update the model.

## What the profile holds, and where it comes from

| Value | Source |
|---|---|
| Overhang limit, 35 to 55 degrees from vertical by material | All3DP: under 45 to 60 degrees from vertical, or protruding under 5 mm. Per-material limits are this project's defaults |
| Minimum wall, 1.2 mm (1.6 mm for flexible and nylon) | Objective3D: about 1 to 2 mm, thicker for load. 1.2 mm is three perimeters on a 0.4 mm nozzle |
| Bridge limit, 10 to 30 mm by material | This project's defaults. PLA bridges best, TPU worst |
| Hole compensation, +0.15 to +0.25 mm on holes under 6 mm | All3DP: small horizontal holes deform. The amount is this project's default |
| Fit offsets per material | This project's defaults |

Only the overhang rule, the wall range and the fit ranges are published figures. Everything labelled a default is a starting value. A different filament brand, nozzle or printer moves them.

## Rules the checks cannot see (apply them while modelling)

- **Orientation decides strength.** Parts are weakest between layers. Keep the main load across the XY plane, not along Z. For carbon-filled filaments the fibres lie along the toolpath, so XY strength is highest and Z is weakest (Markforged).
- **Critical dimensions in the XY plane.** Features parallel to the bed print most accurately. Put critical fits there.
- **Largest flat face on the bed.** It improves adhesion and cuts supports. Warp-prone materials (ABS, ASA, nylon, PC) dislike big flat faces, so round the corners.
- **Edges normal to the bed:** fillet them to reduce warping. **Edges on the bed:** chamfer them (about 0.4 to 0.6 mm) so the first layer does not splay and the part comes off cleanly. A fillet on a bed-contact edge creates a steep first-layer overhang, so prefer the chamfer. Chamfer hole entries so mating parts line up.
- **Round holes printed on their side** deform and their top half overhangs. Make them oversize (`hole_comp`), a teardrop, or a 45 degree diamond, or print them small and drill (All3DP).
- **Threads:** printed threads rarely fit metal ones without adjusting the dimensions. Use a heat-set insert where you need threads. Use a dowel pin for alignment or a wear surface, and a bushing for concentric bearings (Markforged).
- **Small fillets** may not survive slicing. Treat a cosmetic radius as cosmetic, not as proof of strength (HazAT).
- **Split a part** when orientation, supports or strength pull in different directions, or when one section wears and should be replaceable.
- **Infill is a slicer choice.** Do not model hollows to save plastic unless the geometry needs them.

## Per-material notes

Each entry in the JSON carries notes that `print_profile.py` prints. In short:

| | Enclosure | Snap fits | Watch for |
|---|---|---|---|
| PLA | No | Poor | Softens in heat, brittle |
| PETG | No | Good | Strings, sags on bridges, sticks to smooth plates |
| ABS, ASA | Yes | Good | Warps, fumes. ASA is UV stable |
| TPU | No | The part flexes | Thin tall features, bridges, closing slots |
| PA (nylon) | Yes | Good | Absorbs water, warps |
| PC | Yes | Good | Very high warp risk |
| PLA-CF, PETG-CF, PA-CF | By base | Poor to fair | Abrasive: hardened nozzle. Strongest in XY |

No temperatures or speeds are stored here. Those belong in the slicer profile, matched to the filament maker's guidance.

## Sources

- Markforged, [3D printing design tips](https://markforged.com/resources/learn/design-for-additive-manufacturing-plastics-composites/3d-printing-strategies-for-composites/composites-3d-printing-design-tips)
- All3DP, [3D modeling for printing: best practices](https://all3dp.com/2/3d-modeling-for-3d-printing-the-main-considerations/)
- Objective3D, [Optimising 3D print designs](https://www.objective3d.com.au/resource/blog/optimising-3d-print-designs/)
- HazAT, [codex-fusion-360](https://github.com/HazAT/codex-fusion-360)
