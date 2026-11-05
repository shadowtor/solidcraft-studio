# Checking the model in the slicer

A model that passes the design checks can still print badly. The slicer is where orientation, supports and real print time are decided, so a finished print-mode model goes through it before it is called done. There are three ways, from most to least automated.

## 1. OrcaSlicer from the command line (no MCP, verified)

`scripts/slicer_check.py` drives OrcaSlicer headless on the Bambu Lab H2C profiles:

```bash
python <skill>/scripts/slicer_check.py exports/part.3mf --material PETG
```

```text
can-holder.3mf in PETG (Bambu PETG Basic @BBL H2C, Textured PEI Plate bed)
  geometry : 72.0 x 72.0 x 58.2 mm, 39.15 cm3, watertight
  as exported: 1h 32m 5s, 36.66 g, 291 layers, support lines: 0
  supports on: 1h 32m 5s, 36.66 g, support lines: 0  ->  no support generated: this orientation needs none
  best orientation by the slicer: up = [-0.0, -0.0, 1.0]  ->  matches your export
```

What it does, and why each step is there:

| Step | How | What you learn |
|---|---|---|
| Geometry | `orca-slicer --info part.3mf` | Size and volume, and whether the mesh is watertight (`manifold = yes`) |
| As exported | slice with the H2C machine, `0.20mm Standard` process, the material's Bambu filament and its bed plate | Print time, filament grams, layer count |
| Supports forced on | the same slice with a copy of the process preset that has `enable_support = 1`, tree supports | If no support extrusion appears, the orientation needs none. If it does, you see the time and filament cost |
| Best orientation | `--orient 1`, the slicer's own orientation search, parsed from its output | Whether your export orientation is the one the slicer would choose |

A positive control: a part with a 25 mm flat ledge reported `supports ARE needed`, +9 minutes, +2 g, and a different best orientation, while the can holder reported none of that.

**How the CLI is driven, in case you need to do it by hand** (all of this was run on Windows with OrcaSlicer 2.5.0-dev):

```bash
orca-slicer --info part.3mf
orca-slicer --load-settings "<BBL>/machine/Bambu Lab H2C 0.4 nozzle.json;<BBL>/process/0.20mm Standard @BBL H2C.json" \
            --load-filaments "<BBL>/filament/Bambu PETG Basic @BBL H2C.json" \
            --curr-bed-type "Textured PEI Plate" --slice 1 --outputdir out part.3mf
```

Things learned the hard way:

- `<BBL>` is the Bambu Lab system profile folder that Bambu Studio or OrcaSlicer downloads (`%APPDATA%/BambuStudio/system/BBL`). Open Bambu Studio once so it exists.
- **Use Windows paths** (`C:/Users/...`) for the profile arguments. A Git Bash style `/c/Users/...` path is reported as "can not find setting file".
- `--curr-bed-type` is required for some filaments: PETG on the default Cool Plate fails with "Cool Plate does not support filament 1".
- The CLI cannot apply a partial setting file that inherits from a system preset. To change a setting (supports on), **flatten** the preset: merge its `inherits` chain into one file, remove `inherits`, set `"from": "User"`, and change the keys. `slicer_check.py` does this for you.
- `--orient 1` on its own does not exit. Combine it with `--slice 1`, and read the `best:` line it prints.
- Results land in `plate_1.gcode`. The header carries `total estimated time`, `filament used [g]` and `total layer number`; `; FEATURE:` lines name each extrusion type.
- It does not print warnings the way the GUI does and it cannot show you the supports. Open the GUI for that.

## 2. The GUI, by hand

1. Export the printed part: `export(body, "exports/part", "3mf")`.
2. Open it in OrcaSlicer or Bambu Studio. Confirm scale and units first.
3. Try two or three orientations. For each, note support volume, print time, where the first layer sits, and any warnings.
4. Pick the orientation that needs the least support, keeps layers off the main load and puts critical fits in the XY plane. If every orientation needs ugly support, change the model (a chamfer, a split, a teardrop) and loop back.

## 3. The orcaslicer-mcp server (optional, not run here)

[maxellis/orcaslicer-mcp](https://github.com/maxellis/orcaslicer-mcp) lets the agent drive a **running** OrcaSlicer GUI instead of a headless one: it can load a model, change settings, slice, read warnings and breakdowns, and render the plate. What follows comes from its README, so check each tool against the version you install.

What it needs:

- A **custom OrcaSlicer build** from the MaxEllis/OrcaSlicer releases (based on 2.3.2) with an embedded local API. Stock OrcaSlicer does not work. Remote API is switched on in Preferences and its token goes in `ORCA_API_TOKEN`. The API listens on `http://127.0.0.1:13130`.
- `uv` to run `uvx orcaslicer-mcp`, and an MCP client.
- Some tools need newer builds: STEP import from v2.3.2-mcp.3, renders from mcp.4, multi-plate from v2.4.2-mcp.13.
- AGPL-3.0, an early public release. Printer tools are read-only (Klipper or OctoPrint), so a Bambu printer is not covered.

Tools worth using for a model check: `load_model`, `describe_plate`, `auto_orient`, `transform_object`, `check_placement`, `diagnose_plate`, `slice_and_wait`, `get_slice_warnings`, `get_slice_breakdown`, `compare_slices`, `render_plate`, `set_object_config`, `check_profile_physics`.

Rules if you use it: do not edit the user's presets (use `set_object_config` or a scratch copy), never add keys to `ORCA_MCP_ALLOW_KEYS` for the user, and do not call `arrange_plate` on a multi-plate project because it repacks every plate that is not locked.

Choose it over the CLI when you want the result to appear in the user's own GUI, or when you need renders and per-feature breakdowns. Choose the CLI when you want something that works with the stock slicer today.

## The loop

1. Export the 3MF. Run `slicer_check.py` (or the GUI, or the MCP).
2. Read the result: watertight? supports needed? does the best orientation match yours?
3. Feed it back to the model:
   - supports on a face that matters: add a chamfer or fillet, or reorient;
   - a long bridge: add a rib or split the part;
   - thin walls the slicer drops or fills: thicken to a multiple of the extrusion width (0.4 mm nozzle: 0.8, 1.2, 1.6 mm);
   - a first-layer or bed-contact warning: add a bed-edge chamfer or a larger flat face;
   - not watertight: fix the model, do not repair the mesh in the slicer.
4. Rebuild in SolidCraft, re-export, check once more.
5. Record the orientation, support plan and findings in `project.json`.

## Support choices (starting points)

- **Prefer no supports.** Redesign first: 45 degree chamfers instead of shelves, teardrops instead of horizontal round holes, split parts.
- **Tree or organic supports** touch the part less and remove more easily on curved or delicate areas. **Normal or grid supports** hold broad flat undersides better. Both leave marks, so keep supports off faces that matter.
- Support **interface layers** and a small Z gap improve the surface under the support at the cost of removal effort. PETG sticks hard to its supports, PLA releases more easily.
- A brim or small mouse-ear tabs help warp-prone materials with large flat footprints.
- Use support enforcers or blockers on the object when the automatic result is wrong. Do not mark the whole plate.

Option names differ between OrcaSlicer, Bambu Studio and other slicers, so look each one up in the slicer's own help before changing it.

## What to tell the user

Which orientation was chosen and why, the support plan, the print time and filament from the slice, which warnings remain and why they are acceptable, and what changed in the model because of the slicer. If the slicer step was skipped, say so: the model was checked against the material profile only.
