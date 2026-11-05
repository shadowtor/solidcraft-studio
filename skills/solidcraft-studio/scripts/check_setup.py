#!/usr/bin/env python3
"""Report which tools the skill can use on this machine. Exit 1 only if SolidCraft itself is missing."""
import glob, os, shutil, subprocess, sys


def find(name, globs):
    p = os.environ.get(name.upper().replace("-", "_")) or shutil.which(name)
    for g in globs:
        p = p or next(iter(sorted(glob.glob(g))[::-1]), None)
    return p


def ver(p):
    try:
        return subprocess.run([p, "--version"], capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0]
    except Exception:
        return p


PF = "C:/Program Files"
CHECKS = [
    ("solidcraft-cli", True, "modelling", [f"{PF}/SolidCraft/solidcraft-cli.exe"]),
    ("orca-slicer", False, "slicer check (print finish)", [f"{PF}/OrcaSlicer/orca-slicer.exe", f"{PF}/Orca*/orca-slicer.exe"]),
    ("blender", False, "renders and exploded views", [f"{PF}/Blender Foundation/Blender */blender.exe"]),
    ("ffmpeg", False, "GIF and MP4", []),
    ("materialcraft-cli", False, "materials", [f"{PF}/MaterialCraft/materialcraft-cli.exe"]),
    ("texturecraft-cli", False, "texturing", [f"{PF}/TextureCraft/texturecraft-cli.exe"]),
    ("effectcraft-cli", False, "effects and video", [f"{PF}/EffectCraft/effectcraft-cli.exe"]),
]
bad = 0
for name, need, use, globs in CHECKS:
    p = find(name, globs)
    if p:
        print("OK   %-18s %s (%s)" % (name, p if name == "orca-slicer" else ver(p), use))
    else:
        print("%s %-18s not found: no %s" % ("FAIL" if need else "WARN", name, use))
        bad += need
bst = os.path.join(os.environ.get("APPDATA", ""), "BambuStudio", "system", "BBL")
print(("OK   Bambu Studio profiles found" if os.path.isdir(bst) else "WARN Bambu Studio profiles missing: slicer_check.py needs them for the H2C presets"))
sys.exit(1 if bad else 0)
