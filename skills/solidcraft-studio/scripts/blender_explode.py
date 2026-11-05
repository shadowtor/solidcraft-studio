#!/usr/bin/env python3
"""Exploded-view render of a SolidCraft OBJ/3MF/STL assembly in a background Blender (no add-on, no MCP needed).

  python blender_explode.py assembly.obj out/ex_ --frames 1,24,48          # still check frames
  python blender_explode.py assembly.obj out/ex_ --anim --end 48 --step 2   # a_0001.png.. then: ffmpeg -framerate 12 -i out/ex_%04d.png -c:v libx264 -pix_fmt yuv420p ex.mp4
  options: --order Base,Post,Lid  (assembly order, bottom to top; default: by height)  --axis z|x|y  --gap 40 (mm)
           --size 700  --samples 32  --engine EEVEE|CYCLES  --colors "#c8d0d8,#e4572e,#2e86ab"  --glass Lid  --transparent  --blend out.blend

SolidCraft objects are millimetres; this scales by 0.001. Each body keeps its name (the OBJ `o` line). Part i moves
(i - middle) x gap along the axis, staggered from the centre outward, eased in and out. Finds Blender via BLENDER_EXE, PATH or
C:/Program Files/Blender Foundation/Blender */blender.exe. Runs itself inside Blender (`blender -b --python`).
"""
import glob, os, shutil, subprocess, sys

ARGS = sys.argv[1:]
if "bpy" not in sys.modules:
    try:
        import bpy  # noqa: F401  (already inside Blender)
    except ImportError:
        exe = os.environ.get("BLENDER_EXE") or shutil.which("blender") or (sorted(glob.glob("C:/Program Files/Blender Foundation/Blender */blender.exe")) or [None])[-1]
        if not exe:
            sys.exit("Blender not found. Set BLENDER_EXE.")
        sys.exit(subprocess.call([exe, "-b", "--python", os.path.abspath(__file__), "--"] + ARGS))

import argparse, math
import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("prefix")
ap.add_argument("--frames", default="1,24,48"); ap.add_argument("--anim", action="store_true")
ap.add_argument("--start", type=int, default=1); ap.add_argument("--end", type=int, default=48); ap.add_argument("--step", type=int, default=1)
ap.add_argument("--order"); ap.add_argument("--axis", default="z", choices=["x", "y", "z"]); ap.add_argument("--gap", type=float, default=40)
ap.add_argument("--size", type=int, default=700); ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--engine", default="EEVEE"); ap.add_argument("--colors", default="#8a96a3,#e4572e,#2e86ab,#f2c14e,#7a9e7e")
ap.add_argument("--glass", help="comma list of body names to make clear glass/acrylic (use --engine CYCLES)"); ap.add_argument("--power", type=float, default=0.012); ap.add_argument("--transparent", action="store_true"); ap.add_argument("--blend")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ARGS)
AX = "xyz".index(a.axis)

LIVE = not bpy.app.background  # inside the user's live Blender (MCP add-on): never reset it, build in a NEW scene instead
if LIVE:
    sc = bpy.data.scenes.new("SolidCraft Explode")
    bpy.context.window.scene = sc
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)  # background process only: wipes the add-on, so never in a live session
    sc = bpy.context.scene
ext = os.path.splitext(a.model)[1].lower()
if ext == ".obj":
    bpy.ops.wm.obj_import(filepath=a.model, forward_axis="Y", up_axis="Z")  # SolidCraft is Z up
elif ext == ".stl":
    bpy.ops.wm.stl_import(filepath=a.model)
else:
    sys.exit("use OBJ or STL")
parts = [o for o in sc.objects if o.type == "MESH"]
from mathutils import Matrix
for o in parts:
    o.data.transform(Matrix.Scale(0.001, 4))  # mm -> m
    for p in o.data.polygons:
        p.use_smooth = False
bpy.context.view_layer.update()


def centre(o):
    return sum((o.matrix_world @ Vector(c) for c in o.bound_box), Vector()) / 8


if a.order:
    byname = {o.name.split(".")[0]: o for o in parts}
    parts = [byname[n] for n in a.order.split(",")]
else:
    parts.sort(key=lambda o: centre(o)[AX])

cols = [tuple(int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,) for h in a.colors.split(",")]
for i, o in enumerate(parts):
    m = bpy.data.materials.new(o.name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = cols[i % len(cols)]
    b.inputs["Roughness"].default_value = 0.35
    if a.glass and o.name.split(".")[0] in a.glass.split(","):
        for k, v in (("Transmission Weight", 1.0), ("Roughness", 0.03), ("IOR", 1.49)):
            if k in b.inputs:
                b.inputs[k].default_value = v
        m.surface_render_method = "BLENDED" if a.engine.upper() != "CYCLES" else m.surface_render_method  # EEVEE needs this for see-through
    o.data.materials.clear(); o.data.materials.append(m)

# ---- explode: part i travels (i - mid) * gap, staggered outward from the middle, eased
mid = (len(parts) - 1) / 2
hold = 4
for i, o in enumerate(parts):
    home = o.location.copy(); far = home.copy(); far[AX] += a.gap / 1000 * (i - mid)
    t0, t1 = a.start + hold, a.end - hold
    for f, loc in ((a.start, home), (t0, home), (t1, far), (a.end, far)):
        o.location = loc; o.keyframe_insert("location", frame=f)
    o.location = home
    if o.animation_data:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
sc.frame_start, sc.frame_end = a.start, a.end

# ---- scene: floor, three-point light, camera
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for o in parts:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
cen = (lo + hi) / 2
rad = max((hi - lo).length / 2 + a.gap / 1000 * len(parts) / 2, 0.01)
bpy.ops.mesh.primitive_plane_add(size=rad * 14, location=(cen.x, cen.y, lo.z - a.gap / 1000 * (len(parts) / 2) if a.axis == "z" else lo.z))
floor = bpy.context.object; floor.name = "Floor"
fm = bpy.data.materials.new("Floor"); fm.use_nodes = True
next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.45, 0.46, 0.5, 1)
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Roughness"].default_value = 1.0
for k in ("Specular IOR Level", "Specular"):
    if k in fb.inputs:
        fb.inputs[k].default_value = 0.0
floor.data.materials.append(fm)
w = bpy.data.worlds.new("W"); w.use_nodes = True; sc.world = w
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0.8, 0.82, 0.86, 1); bg.inputs[1].default_value = 0.6
for name, loc, e in (("Key", (1, -1, 1.2), 400), ("Fill", (-1.2, -0.6, 0.6), 150), ("Rim", (0, 1.2, 1), 250)):
    d = bpy.data.lights.new(name, "AREA"); d.energy = a.power * e / 400 * 60 * (3 * rad * (Vector(loc).length)) ** 2 * 10; d.size = rad * 2  # ~watts scale with distance squared
    L = bpy.data.objects.new(name, d); sc.collection.objects.link(L)
    L.location = cen + Vector(loc) * rad * 3
    L.rotation_euler = (cen - L.location).to_track_quat("-Z", "Y").to_euler()
cd = bpy.data.cameras.new("Cam"); cd.lens = 70
cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
az, el = math.radians(-30), math.radians(30)
cam.location = cen + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * rad * 3.0
cam.rotation_euler = (cen - cam.location).to_track_quat("-Z", "Y").to_euler()
r = sc.render
r.resolution_x = r.resolution_y = a.size; r.film_transparent = a.transparent; r.fps = 24
for eng in ({"EEVEE": ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"], "CYCLES": ["CYCLES"]}[a.engine.upper()]):
    try:
        r.engine = eng; break
    except TypeError:
        pass
if r.engine == "CYCLES":
    sc.cycles.samples = a.samples
elif hasattr(sc, "eevee") and hasattr(sc.eevee, "taa_render_samples"):
    sc.eevee.taa_render_samples = a.samples
sc.view_settings.view_transform = "Standard"
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA" if a.transparent else "RGB"
if LIVE:
    sc.frame_set(a.end)
    print("built scene", sc.name, "parts", [o.name for o in parts], "- look with the MCP `look` tool (mode camera / frames), render with F12")
else:
    os.makedirs(os.path.dirname(os.path.abspath(a.prefix)), exist_ok=True)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend), copy=True)
    frames = range(a.start, a.end + 1, a.step) if a.anim else [int(x) for x in a.frames.split(",")]
    for n, f in enumerate(frames, 1):
        sc.frame_set(f); r.filepath = "%s%04d.png" % (a.prefix, n if a.anim else f)  # animation files are numbered 1..N so ffmpeg can read them
        bpy.ops.render.render(write_still=True)
        print("rendered", r.filepath, "engine", r.engine)
    print("parts:", [o.name for o in parts], "sizes_mm:", [[round(x * 1000, 1) for x in o.dimensions] for o in parts])
