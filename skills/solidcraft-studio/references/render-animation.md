# Renders, scenes and animation

Status on this machine (SolidCraft 0.30.1, Blender 5.2.3, ffmpeg 9.0.1): **verified** SolidCraft OBJ export -> `scripts/blender_explode.py` (background Blender, EEVEE) -> PNG frames -> ffmpeg MP4. A 3-part assembly (60 mm base, 16 mm post, 50 mm lid) imported at the right size in mm, exploded with eased motion and soft shadows, and encoded to a 24-frame MP4 (about 15 s to render). **Live add-on verified too** (Blender 5.2.3, MCP add-on protocol 13; it reports protocol 15 expected, run `uvx mcp-for-blender install-addon` to update, it still worked). **Also verified:** Cycles (`--engine CYCLES`, 24 to 48 samples at 500 px, about 1 minute a frame on this machine's GPU/CPU mix), clear glass or acrylic bodies (`--glass Lid`: the lid rendered translucent with the part visible through it; where a glass body touches another part the contact area renders dark, so leave a small gap or tolerate it), and GIF output.

## Choose

| Need | Route |
|---|---|
| Quick studio PNG, plain background | SolidCraft `screenshot` (`source: "model"`, `width`, `height`, `camera`, `grid:false`, `axes:false`) or `render.start` jobs (CPU raytrace, PNG, transparent background optional) |
| Hero shot, backdrop, lighting rig, glass, vinyl, HDRI | Export OBJ, build in Blender (`blender` MCP) |
| Exploded view, turntable, assembly or process clip | Blender keyframes (below), render PNG sequence, ffmpeg to MP4/GIF |
| Titles, camera moves, particles, glow, compositing a render sequence | EffectCraft (`effectcraft-cli mcp`, project -> render queue) |

## Getting the model out of SolidCraft

SolidCraft `export` writes STEP, 3MF, STL and OBJ (no GLB). Use **OBJ** (with its `.mtl`) or **3MF** for Blender, one body per part so each can be moved and given a material. Keep millimetres in mind: Blender imports unit-less, so scale by 0.001 (or set the importer scale) and check with a dimension. Name bodies for what they are (`Lid`, `Base`, `Pin`); the names become the object names you animate.

## Exploded view in Blender

Fast route (verified, no add-on needed):

```bash
python <skill>/scripts/blender_explode.py exports/assembly.obj renders/ex_ --frames 1,24,48 --order Base,Post,Lid   # check frames, then read them
python <skill>/scripts/blender_explode.py exports/assembly.obj renders/ex_ --anim --end 48 --step 2 --size 720 --order Base,Post,Lid
ffmpeg -framerate 12 -i renders/ex_%04d.png -c:v libx264 -pix_fmt yuv420p renders/ex.mp4
```

Options: `--axis`, `--gap` (mm), `--colors`, `--transparent`, `--engine CYCLES`, `--power` (light strength: **0.012 default; 0.05 blew everything to white**, so adjust in small steps and look), `--blend` to save a scene for hand tuning. It uses `read_factory_settings` in its own background process only, never in a user's live session. For a hand-built or custom scene use the steps below in the live add-on.

**Live add-on route (verified):** the same script builds the scene inside the user's running Blender without wiping it. In `execute_blender_code`:

```python
import sys
sys.argv = ["x", "<abs>/exports/assembly.obj", "unused_", "--order", "Base,Post,Lid", "--end", "48"]
src = open(r"<skill>/scripts/blender_explode.py", encoding="utf-8").read()
exec(compile(src, "blender_explode.py", "exec"), {"__name__": "__main__", "__file__": "blender_explode.py"})
```

In a live session it creates a NEW scene (`SolidCraft Explode`), switches the window to it, builds parts, keys, lights and camera, and stops without rendering. The user's own scene and objects are untouched (checked: the default Cube was still there). Look with `look {mode:"camera", shading:"rendered"}` or `look {mode:"frames", view:"camera", frames:[1,24,48]}`. When done, switch back (`bpy.context.window.scene = bpy.data.scenes["Scene"]`) and remove the test scene, or leave it if the user wants it. Never call `read_factory_settings` live: it disables the add-on.

1. Import each part. Keep the assembled pose as keyframe 1.
2. Per part, choose a direction (usually the axis it was inserted along) and a distance of 0.5 to 1.5 times the part's size, larger for the outer parts.
3. Keyframe the offset at frame 1 (assembled), hold, ease out to the exploded pose over 40 to 60 frames, hold, repeat in reverse for a loop. Stagger the start by 3 to 6 frames per part from the centre outward.
4. Camera: fixed three-quarter view, or a slow orbit; keep every part in frame at full explosion.
5. Light: three-point or an HDRI studio, soft shadows, floor shadow catcher for a transparent background. Glass and vinyl need Cycles.
6. Render check frames first (first, middle, last, 24 to 48 samples at 700 px), look at them, then render the sequence in the background and encode.

Tip: a short assembled "process" clip (parts flying in one after another) is the same keys played backwards with the stagger reversed.

## GIF

Verified: palette GIF from the PNG sequence, 24 frames at 360 px, 12 fps, 0.43 MB:

```bash
ffmpeg -framerate 12 -i renders/ex_%04d.png -vf "fps=12,scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4" renders/ex.gif
```

Keep GIFs under about 8 MB (smaller width, fewer colours, `--step 2` frames). MP4 for anything longer.

## EffectCraft (verified)

Verified end to end on this machine (EffectCraft 0.21.1, headless, CPU render): the 24-frame exploded PNG sequence became a 2.4 s 480 px H.264 MP4 (72 frames, 30 fps) with a looped sequence, a title that fades in, and a vignette, read back from the video file. Also verified: **GPU render** (`craft_mcp.py --app effectcraft --arg=--gpu ...`; `get_project` then reports `renderer.active: gpu`, an RTX 2080 Super via Vulkan; 48 frames to MP4) and a **shape layer** (`layer.newShape {kind:"rounded", size:[360,60], fill:"#e4572e", position:[240,420]}`) with a scale keyframe and a Glow effect. Also verified: **3D layers, a camera and audio**: `layer.setSwitch {layers:[..], switch:"threeD", value:true}`, `layer.newCamera {preset:"50mm", position:[240,240,-800], poi:[240,240,0]}`, a keyframed `transform/position` move (frames showed the perspective orbit), `file.import` of a WAV and `layer.addItem` for it; the rendered MP4 had an H.264 video stream and an AAC audio stream, both 2.4 s. Not verified: the bridge to the live EffectCraft app.

Run it as one session (each `craft_mcp.py` call is a new session, `run` keeps one):

```bash
python <skill>/scripts/craft_mcp.py --app effectcraft --allow <project> run fx.json
```

```json
[{"tool":"execute_command","args":{"command":"file.import","params":{"paths":["<abs>/renders/ex_0001.png"],"sequence":true}}},
 {"tool":"execute_command","args":{"command":"comp.new","params":{"name":"Exploded","width":480,"height":480,"frameRate":30,"duration":2.4,"background":"#cfd3da"}}},
 {"tool":"execute_command","args":{"command":"layer.addItem","params":{"item":1,"time":0}}},
 {"tool":"execute_command","args":{"command":"layer.addItem","params":{"item":1,"time":0.8}}},
 {"tool":"execute_command","args":{"command":"layer.newText","params":{"text":"EXPLODED VIEW","size":34,"fill":"#1d2733","position":[240,430]}}},
 {"tool":"add_keyframe","args":{"layer":"#1","path":"transform/opacity","keys":[{"time":0,"value":0},{"time":0.6,"value":100}],"interpolation":"easyEase"}},
 {"tool":"execute_command","args":{"command":"layer.newAdjustment","params":{}}},
 {"tool":"add_effect","args":{"layer":"#1","effect":"ec.stylize.ccvignette"}},
 {"tool":"render_frame","args":{"time":1.2,"path":"<abs>/renders/fx_frame.png"}},
 {"tool":"execute_command","args":{"command":"renderQueue.add","params":{"format":"h264","output":"<abs>/renders/fx.mp4"}}},
 {"tool":"execute_command","args":{"command":"renderQueue.render","params":{"wait":true}}}]
```

Notes from the run:
- File parameters must be **absolute paths inside the allowed folder** (`--allow` becomes `--automation-read-root` and `--automation-write-root`). Layers are addressed by the id a command returned, or `"#1"` (top of the stack).
- An imported image sequence plays at the comp frame rate: 24 frames at 30 fps is 0.8 s, so add the item several times at `time` offsets to loop it, or slow it with `layer.timing`.
- `add_effect` takes the effect id from `list_effects {"filter":"glow","compact":true}` (found: `ec.stylize.glow`, `ec.stylize.ccvignette`); `add_effect` returns the parameter paths (`effects/#1/amount`) to set with `set_property`.
- `render_frame` with `path` writes a PNG you can read before spending time on the queue. Verify the MP4 by extracting frames with ffmpeg, not by trusting the log.
- `list_commands {"filter":"renderQueue.","compact":true}` lists render-queue commands (formats: h264, hevc, av1, prores, webm, png, gif, and more). Scripting (`run_script`, After Effects style) exists for anything the commands do not cover.

## Output sizes

Stills: 1920 px wide, or the size named. Social loop GIF: 480 px, 24 fps, under 8 MB. Web hero video: 1080p MP4, H.264. Keep the transparent PNG too when a store page or crowdfunding page will composite it.
