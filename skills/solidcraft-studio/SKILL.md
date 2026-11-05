---
name: solidcraft-studio
description: Design 3D models with the user in SolidCraft (Tangency Labs parametric CAD) through its local MCP server (`solidcraft-cli mcp`, docs at solidcraft.io/mcp), then take them to three finishes. Print (3D-printable parts for a Bambu Lab H2C in PLA, PETG, ASA and others, checked in OrcaSlicer for supports and orientation), Render (hero stills, scenes, lighting, backgrounds and exploded-view animation via Blender or EffectCraft), or Textured (PBR materials and painted textures for vinyl, game or showcase models via MaterialCraft and TextureCraft). Use whenever the user wants anything modelled, checked for printing, rendered, animated or textured starting from SolidCraft.
---

# solidcraft-studio

You model in SolidCraft by sending engine commands to its MCP server, look at the result, and fix it. The user supplies measurements, artwork and taste. Downstream apps (OrcaSlicer, Blender, EffectCraft, MaterialCraft, TextureCraft) take the exported files.

## 0. Connect (always first)

Normal route: the loaded `solidcraft` MCP tools (`execute`, `batch`, `measure`, `screenshot`, `export`, `skill_reference`...). Watching live: the `solidcraft-live` server (app started with `solidcraft --control 7878`). No MCP tools loaded:

```bash
python <skill>/scripts/craft_mcp.py ping            # headless solidcraft-cli mcp
python <skill>/scripts/craft_mcp.py --allow <project> call batch @steps.json
```

`solidcraft.io/mcp/` is documentation, not an endpoint: the server is **stdio** (`solidcraft-cli mcp`, `C:\Program Files\SolidCraft\solidcraft-cli.exe`). `solidcraft-cli mcp setup` registers it in Claude Code. Each `craft_mcp.py` call is a fresh headless session, so send multi-step work as one `batch` (it can end with an `export` step), or use `--live PORT`.

Rules that protect the user's work:
- **Files are confined.** The agent reads and writes only in the open design's folder (inside the home folder, not hidden), SolidCraft's recovery folder, and each `--allow-path`. When a save or export is refused, ask the user to add the project folder to the server's args. Do not work around it.
- **Never replace a design the user has open.** `new_design` and `open` discard it. In the live app, ask first. Headless sessions are yours.
- **Never** save over or delete the user's files. Outputs go in the project folder.
- Headless output says "the user cannot see this work". Say so, and offer `solidcraft-live` when watching matters.

Learn the command shapes from the app, not memory: `skill_reference {"skill":"solidcraft-modeling"}` (also `-editing`, `-checking`, `-mechanisms`), `list_commands {"filter":"sketch."}`, `describe_command {"id":...}`. Read `solidcraft-modeling` once before the first build; it carries the plane table, id rules and traps.

## 1. Pick the finish (the selector)

Ask once, recommend **Print** unless the brief says otherwise, and do not model before it is answered. A project can chain finishes (model, then print, then render).

| Finish | For | Built as | Output |
|---|---|---|---|
| **Print** | Parts printed on the user's printer | Fit tolerances, wall rules, orientation, one body per printed part | 3MF per part + STEP, slicer report |
| **Render** | Hero shots, scenes, exploded views, turntables, process clips | Real-scale model with named bodies and appearances | PNG, MP4/GIF, OBJ/3MF for the scene |
| **Textured** | Vinyl figures, game assets, merch with artwork or surface finish | Clean single-shell bodies, sensible UV surfaces | Maps (base, normal, roughness, metallic, height, AO), mesh |

For Print also ask the **filament** (mainly Bambu PLA, PETG, ASA; others in `assets/materials.json`), the **nozzle** (0.2, 0.4 or 0.6; it sets feature size, layer height and wall counts) and the **build plate** (cool, supertack, textured-cool, engineering, high-temp, textured-pei), and use the **Bambu Lab H2C** unless told otherwise. `python <skill>/scripts/print_profile.py ASA` prints that filament's fits, minimum wall (scaled by `--nozzle`), overhang and bridge limits; `--batch` emits the `parameters.change` steps to load them. Background: [references/materials.md](references/materials.md), [references/print-rules.md](references/print-rules.md).

Then `python <skill>/scripts/new_project.py "<name>" --mode print|render|textured [--material PETG]` makes `project.json`, `build/`, `exports/`, `renders/`, `textures/`, `shots/`.

## 2. Brief, parameters, build

Ask for what you cannot invent: real sizes of anything the model must fit, filament, artwork files, where the result is shown. Put assumed numbers in `project.json` under `assumptions` and say them out loud.

Every measurable number becomes a SolidCraft **parameter** (`parameters.change`): measured (`can_dia`), fit (the print profile's `fit_*`, `min_wall`) and derived (expressions). Fits are **diametral**. Feature fields take expressions (`"can_dia + fit_close"`), so one number change reflows the model. Build in a few `batch` calls with `expect` (`volume_mm3`, `bodies`, `bbox`) computed from your own numbers, and `measure` after each stage. One body per physical part, named for the part. Fillets last.

**Look at every `screenshot`** before moving on. If the picture and the numbers disagree, trust the picture and find the bug. `check_parameters` rebuilds with other values and reports; use it as the parametric test.

## 3. Finish: Print

1. `measure` shows closed bodies and the expected size. Check walls against `min_wall`, overhangs against the filament limit, bridges, small holes (add `hole_comp`), bed fit (H2C: see print-rules).
2. `export` each body as **3MF** (plus **STEP** for the master). One printed part per file.
3. Slice-check in OrcaSlicer on the H2C profiles, with the user's nozzle, plate and filament:
   ```bash
   python <skill>/scripts/slicer_check.py exports/part.3mf --material PLA --nozzle 0.6 --bed supertack [--filament "Bambu PLA Matte"] [--process "0.12mm High Quality"]
   ```
   It reports watertight or not, time, filament, bed temperature, whether supports are needed (forced-support slice using the clean-support settings), and whether your orientation matches the slicer's best. Add `--on-plate-only` or `--support-type normal(auto)` to compare variants. **Needs the Bambu profile JSON** from Bambu Studio's `%APPDATA%\BambuStudio\system\BBL` (open Bambu Studio once), or `--profiles` / `ORCA_PROFILES`. Verified here: 0.2/0.4/0.6 nozzles, all six plates (bed temperatures differ as expected), PLA/PETG/ASA; a plain block needs no supports, a part with a 30 mm ledge does. GUI and MCP alternatives: [references/slicer.md](references/slicer.md).
4. **Smooth surfaces and clean supports** ([references/clean-supports.md](references/clean-supports.md)): first design the support away (orientation, 45 degree chamfers, split parts), choose the layer height for visible faces, and only then accept supports with a tight solid interface sized to the layer height and filament (PLA 1.0x, ASA 1.25x, PETG 1.5x). State the support setting as a starting point and name the first test print.
5. Fit that matters: print a coupon (holes against pins at four clearances) first and write the winner into the `fit_*` parameter. Name the first test print.

## 4. Finish: Render

SolidCraft has a native CPU product renderer (`render.preflight` / `render.start` / `render.status` / `render.export` through `execute`; PNG, no HDRI, no refraction, no animation). Use it for quick studio shots. For scenes, lighting, backgrounds, glass, vinyl and animation, export **OBJ** (or 3MF, one body per part) and build the scene in **Blender** through the `blender` MCP (see the `blender-studio` skill if installed; the same rules apply: never discard the user's scene, look at every render). Exploded view, verified end to end: export OBJ, then `python <skill>/scripts/blender_explode.py exports/assembly.obj renders/ex_ --anim --order Base,Post,Lid`, then ffmpeg to MP4. Details, options and process clips: [references/render-animation.md](references/render-animation.md). **EffectCraft** (`effectcraft-cli mcp`) is the verified route for compositing a rendered PNG sequence with titles, keyframes and effects into an MP4 (`craft_mcp.py --app effectcraft run fx.json`, recipe in the reference).

## 5. Finish: Textured

SolidCraft makes geometry and flat appearances only. Surface work goes: **MaterialCraft** (procedural tileable PBR materials, `.sbs` / `.mcmat`) -> **TextureCraft** (paint, bake, UV-based texture export on a mesh) -> maps and mesh into Blender or a game engine. Export the SolidCraft body as OBJ first, keep it one clean shell, and say that SolidCraft does not unwrap UVs: TextureCraft or Blender must supply them. Verified sequence (SolidCraft OBJ -> `obj_zup_to_yup.py` -> MaterialCraft maps -> TextureCraft triplanar apply, bake, export maps and GLB, run with `craft_mcp.py --app ... run steps.json`). Vinyl and game-asset recipes and the exact tool sequence: [references/texture-pipeline.md](references/texture-pipeline.md). Animated effects go to EffectCraft.

## 6. Verify before saying done

1. `measure`: sizes in mm match the brief, bodies closed, `expect` passed.
2. Screenshots from iso, front and one underside or section view, read by you.
3. Parametric test: `check_parameters` on the main measured parameter, back to the original.
4. Print: `slicer_check.py` result quoted, or "not run" with the reason. Render/Textured: first and last frame, or the baked maps opened and looked at.
5. State what is **not** proven: no test print, colours on screen are not print proofs, clearances are starting values for a 0.4 mm nozzle.

## 7. Hand over

Files with sizes, the parameter list and where to change it, assumptions, exact commands to re-export or re-render, and the first test print or next likely ask.

## What this skill does not do

- It does not send jobs to the printer or pick temperatures and speeds. It slices only to check a model.
- It does not replace a test print, or promise a fabricator will match a render.
- It does not unwrap UVs or sculpt organic forms in SolidCraft; that is mesh work for Blender or TextureCraft.
- It does not use someone else's artwork or brand without the user confirming the right to it.
