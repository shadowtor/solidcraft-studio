# Smooth prints and supports that come off clean

The best support is the one that is not there. Work down this list in order; `slicer_check.py` measures each step.

## 1. Design the support away (in SolidCraft, before slicing)

- **Orient** so the visible and mating faces are vertical or on top, not underhangs. Check the slicer's own best orientation in the report; if it differs from your export, compare time and support lines.
- **Chamfer instead of overhang:** a 45 degree chamfer prints unsupported where a flat underside of the same part does not. Use `solid.chamfer` on the underside edge of any shelf, boss or hole roof. Round the top of horizontal holes into a teardrop or diamond (point up).
- **Split the part** at an overhang and print the halves flat (pins or a snap joint to rejoin). Cheaper than any support.
- **Bridges:** keep them under the filament's `bridge_max` (see `print_profile.py`).
- **Cosmetic faces up or vertical.** Put the support scar on the hidden side.

## 2. Settings that give smooth walls

Use the smallest layer height the nozzle allows and the default for the rest unless a test says otherwise.

| Nozzle | Smooth (visible parts) | Normal | Fast / big parts |
|---|---|---|---|
| 0.2 | 0.08 mm High Quality | 0.12 mm Balanced Quality | 0.16 mm |
| 0.4 | 0.12 mm High Quality | 0.20 mm Standard | 0.24-0.28 mm |
| 0.6 | 0.18-0.20 mm | 0.30 mm Standard | 0.36-0.40 mm |

Pass the process with `--process "0.12mm High Quality"`. Beyond layer height (set these in the slicer, or tell the user):
- Lower outer-wall speed and acceleration for glossy PLA; a cooler fan-off for ASA/ABS layer bonding.
- Seam on the hidden edge or a corner, not a flat face.
- Ironing only on flat top faces that people touch.
- Dry filament (PETG and ASA especially): wet filament shows as stringing and rough walls.
- Avoid a first-layer "elephant foot" on mating faces: chamfer the bottom edge 0.4 to 0.6 mm in the model.

## 3. When supports are unavoidable: how to make them release

`slicer_check.py --support-quality clean` (the default) builds a forced-support slice with these starting values, derived from the Bambu Wiki and community reports (treat as starting points, not guarantees):

| Setting | Clean value | Why |
|---|---|---|
| Top Z distance | PLA 1.0 x layer height, ASA/ABS 1.25 x, PETG 1.5 x | The gap between support and part. Bigger = easier to remove, rougher underside. PETG bonds harder to itself so it needs more. Bambu's wiki says larger values ease removal but lower interface quality |
| Top interface layers | 3 | A solid skin under the part gives a smooth underside and a clean peel line. 2 to 3 is the common range |
| Interface spacing | 0 (solid) | A dense roof gives a smoother face; a forum report says non-zero spacing may not compute the interface correctly |
| Interface pattern | rectilinear | Predictable peel line |
| Bottom interface layers | 2 | Support base separates from the plate cleanly |
| XY distance | about 0.875 x nozzle | Keeps the support wall off vertical faces |
| Threshold angle | 40 degrees | Do not support gentle overhangs the printer can bridge |

Variants to try, in this order, one change per test print:
1. **Tree vs normal:** `--support-type tree(auto)` (default) touches the part least; `normal(auto)` is sturdier under large flats.
2. **`--on-plate-only`:** no support scars on the part at all, only usable when nothing sits under the overhang.
3. **Different interface material (the H2C's second nozzle makes this practical):** print the interface layers in a filament that does not bond to the part. PETG interface under PLA, or PLA under PETG, releases well because they barely bond. Bambu's Support for PLA/PETG allows a top Z distance of 0. Warning from users: both filaments' temperature ranges must overlap or the nozzle clogs. Slice-checked here, not printed: `slicer_check.py --material PLA --interface-filament "Bambu PETG Basic"` slices the 30 mm ledge test with filament 2 as the support interface and reports grams per filament (`1.30, 2.66`: the second filament carried most of the support). To get a slice out of the CLI the script switches the prime tower off (its default 60 mm tower does not fit the plate in the CLI), so the time and grams are estimates: set the tower or purge and the nozzle assignment in Bambu Studio for the real print, and check the PLA and PETG temperatures overlap.
4. **Reduce the gap further** only on glossy PLA (gap = 0.8 x layer height). Under about 0.1 mm supports may need prying. Never go below on PETG.

## 4. Removal

- Let the plate cool: PLA and PETG release at room temperature, ASA/ABS after the plate is below about 40 C.
- Slide a flexible plate flat off, then remove supports from the plate side, pulling along the layer lines, not across.
- Needle-nose pliers for trees; a deburring tool or hobby knife for the roof scar. Do not twist: it tears the underside.
- Finish: 400 to 800 grit wet sand, or a quick pass with a heat gun on PLA/PETG (briefly, it softens). ASA: acetone vapour smooths it, ventilated, away from flames.

## Sources and confidence

- Bambu Lab Wiki, [support settings](https://wiki.bambulab.com/en/software/bambu-studio/support): top Z distance trade-off, 0 allowed with Bambu's support filament. Official.
- Community reports (Bambu forum threads on top Z distance and support interface filament, Reddit r/BambuLab, Polyfab3D's Orca support guide) for the multipliers and interface layers. Unofficial; values vary by user, and some guide pages read as unreviewed. Verify with a test print on your filament and plate.
- Orca/Bambu preset defaults (Z distance 0.2, 2 interface layers, 0.5 spacing) read directly from the installed H2C profile.
