# Materials and textures: MaterialCraft -> TextureCraft

Installed here: `C:\Program Files\MaterialCraft\materialcraft-cli.exe` (0.1.2) and `C:\Program Files\TextureCraft	exturecraft-cli.exe` (0.3.2), both MCP over stdio. **Verified end to end** (headless, one session per app via `craft_mcp.py run steps.json`): SolidCraft OBJ -> MaterialCraft `metal_plates` graph -> 6 PBR maps + a 3D beauty render -> TextureCraft project on the SolidCraft mesh with the maps applied by triplanar projection -> AO and curvature bake (GPU) -> 6 exported texture maps + a textured GLB, and the viewport render was read and looked right. Also verified: `paint_stroke` and `layer.add.decal` (below), **UV-based texturing** and the **GLB imported into Blender** (below). Not verified: Unreal/Unity import, `.mcmat` sharing between the apps.

Paths in both apps are **relative to the folder given by `--allow`** (read and write root). Files outside are refused.

## The verified sequence

1. SolidCraft `export` OBJ (mm, Z up). **Convert to Y up before TextureCraft**: `python <skill>/scripts/obj_zup_to_yup.py exports/a.obj exports/a_yup.obj [--scale 0.001]`. Without it the model imported on its side (seen, then fixed).
2. MaterialCraft (`--app materialcraft`): `graph_new {"template":"metal_plates","size":512}` (templates: empty, pbr, bricks, stone_tiles, wood, metal_plates, rusty_metal, lava, marble, wicker, fabric, ground), then `view_render {"scene":"rounded_cube","hq":true}` to look, `outputs_export {"dir":"tex/m","format":"png"}` (writes `<graph>_basecolor|normal|roughness|metallic|height|ambientocclusion.png`), `package_save {"path":"tex/m.sbs"}`. Build your own look with `library_list`, `node_add`, `node_connect`, `node_param` instead of a template.
3. TextureCraft (`--app texturecraft`), all in one `run`:
```json
[{"tool":"mesh_import","args":{"path":"ex/a_yup.obj","resolution":1024}},
 {"tool":"resource_import","args":{"path":"tex/m/m_basecolor.png"}},
 {"tool":"command_run","args":{"id":"layer.add.image","params":{"name":"m_basecolor.png","channel":"baseColor","projection":"triplanar","scale":0.08}}},
 {"tool":"bake","args":{"maps":["ambientOcclusion","curvature"],"resolution":1024}},
 {"tool":"viewport_render","args":{"width":640,"height":640,"yaw":35,"pitch":20}},
 {"tool":"textures_export","args":{"dir":"tex/out"}},
 {"tool":"mesh_export","args":{"path":"tex/out/a.glb","format":"glb"}}]
```
Repeat the `resource_import` + `layer.add.image` pair for `roughness`, `metallic` and `normal` (channel names as the project uses them). `viewport_render` returns an image in the tool result; with the MCP tools loaded you see it, from `craft_mcp.py` it is only reported as image bytes. Tune `scale` until the pattern suits the part (0.08 gave one tile larger than a 60 mm face).

Known result details: all bodies of one OBJ land in one material set (`Default`), so they share one texture set; give bodies separate materials upstream if they need separate maps.

## UVs: SolidCraft meshes have none (verified fix)

```bash
python <skill>/scripts/obj_add_uvs.py exports/a.obj exports/a_uv.obj      # Blender Smart UV Project, Y up out, names kept
```

Then `mesh_import` `a_uv.obj` and use `"projection":"uv"` in `layer.add.image`. Checked: 2442 UV coordinates, the textured result looked right, and `viewport_render {"view":"2d"}` shows the UV islands. Smart UV makes many small islands, so seams show on patterned art; hand-unwrap in Blender for hero assets. Triplanar needs no UVs and is fine for tiling materials.

## GLB into Blender (verified)

TextureCraft's GLB imported into the live Blender with `bpy.ops.import_scene.gltf`: upright, one mesh with a UV layer, a Principled material with 4 image textures (1024 px) and a normal map. **Scale:** a SolidCraft mm model arrives 1000 times too large (60 mm showed as 60 m). Pass `--scale 0.001` to `obj_zup_to_yup.py` before TextureCraft for metre-based engines. Unreal and Unity were not tried.

## Painting and decals (verified)

Both take **viewport pixels** (origin top-left). Render the view first and read the picture to pick coordinates: `viewport_render {"width":640,"height":640}` with no yaw/pitch shows the camera the strokes use, and pass `"viewport":[640,640]` so the points mean those pixels (the default session viewport is 1280 x 800).

```json
{"tool":"command_run","args":{"id":"layer.add.paint","params":{"name":"hand paint"}}},
{"tool":"paint_stroke","args":{"color":"#e4572e","hardness":80,"size":30,"viewport":[640,640],"points":[[200,400],[260,385],[340,380],[420,390],[480,410]]}},
{"tool":"command_run","args":{"id":"layer.add.decal","params":{"image":"plates_basecolor.png","x":320,"y":205,"viewport":[640,640],"size":30,"rotation":10,"name":"Decal"}}}
```

`paint_stroke` returns `{"stamps":N}`; `0` means the points missed the mesh. A stroke or decal projects along the view onto every surface under it, so a stroke across a base also marks a post in front of it, and a decal wraps over neighbouring faces within its depth. A decal at a point with no mesh fails with `nothing under that point`. Use `craft_mcp.py --img-dir <folder>` to save the renders a tool returns, then look at them.

## Tools

| App | MCP tools |
|---|---|
| MaterialCraft | `graph_new`, `node_add`, `node_connect`, `node_param`, `library_list`, `bitmap_import`, `package_open`, `package_save`, `outputs_export`, `view_render`, `view_screenshot`, `command_list`, `command_run`, `command_batch`, `session_inspect` |
| TextureCraft | `project_new`, `project_open`, `project_save`, `mesh_import`, `mesh_export`, `mesh_reimport`, `material_load`, `material_save`, `paint_stroke`, `bake`, `bake_mesh_add`, `textures_export`, `resource_import`, `viewport_render`, `viewport_screenshot`, `command_list`, `command_run`, `command_batch` |

Confine files: `materialcraft-cli mcp --read-root DIR --write-root DIR`, same for TextureCraft. `craft_mcp.py --allow DIR` sets both.

## Recipe: vinyl figure or merch (same sequence, different material)

1. Model the body in SolidCraft, export **OBJ** (one clean shell per part), convert to Y up.
2. MaterialCraft: `graph_new`, build a vinyl/plastic look (base colour, low roughness, subtle orange-peel normal), `outputs_export` maps (base colour, normal, roughness, metallic, height, AO) or save as `.mcmat`.
3. TextureCraft: `project_new` from the mesh, `material_load` the `.mcmat`, `paint_stroke` details or `resource_import` the artwork as a layer, `bake` AO and curvature, `textures_export`.
4. Look: `viewport_render` / `viewport_screenshot`, read the picture, fix.
5. Hand the maps plus `mesh_export` (GLB, if offered) to Blender for the final render (see render-animation.md).

## Recipe: game asset

Same as above with: low part count, power-of-two maps (1024 or 2048), a metallic/roughness convention that matches the engine, and a baked normal from the detailed model onto the low one (`bake_mesh_add` then `bake`). State the engine's channel packing if the user names one.

## Limits to tell the user

- SolidCraft exports faceted meshes without UVs. TextureCraft or Blender must unwrap, and a poor automatic unwrap shows as seams in the maps.
- Colour on screen is not a print proof; a 3D-printed multi-colour result needs the slicer's filament assignment, not a texture.
- Animation of materials or effects (glow pulses, dissolve, sparks) is EffectCraft's job, not these two apps'.
