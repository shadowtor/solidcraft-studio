#!/usr/bin/env python3
"""Add UVs to an OBJ (SolidCraft meshes have none) with Blender's Smart UV Project, in a background Blender. Keeps the body names.

  python obj_add_uvs.py in.obj out.obj [--angle 66] [--margin 0.02]      # in: any axis; out: Y up, as TextureCraft expects
Runs `blender -b --python`: BLENDER_EXE, PATH or C:/Program Files/Blender Foundation/Blender */blender.exe.
"""
import glob, os, shutil, subprocess, sys

if "bpy" not in sys.modules:
    try:
        import bpy  # noqa: F401
    except ImportError:
        exe = os.environ.get("BLENDER_EXE") or shutil.which("blender") or (sorted(glob.glob("C:/Program Files/Blender Foundation/Blender */blender.exe")) or [None])[-1]
        if not exe:
            sys.exit("Blender not found. Set BLENDER_EXE.")
        sys.exit(subprocess.call([exe, "-b", "--python", os.path.abspath(__file__), "--"] + sys.argv[1:]))
import math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst = argv[0], argv[1]
angle = float(argv[argv.index("--angle") + 1]) if "--angle" in argv else 66
margin = float(argv[argv.index("--margin") + 1]) if "--margin" in argv else 0.02
bpy.ops.wm.read_factory_settings(use_empty=True)  # background process only
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")  # SolidCraft: Z up
for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.wm.obj_export(filepath=dst, forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True, export_materials=False, global_scale=1.0)
print("wrote", dst, [(o.name, len(o.data.uv_layers)) for o in bpy.context.scene.objects if o.type == "MESH"])
