#!/usr/bin/env python3
"""Package the skill as dist/solidcraft-studio.zip (for UIs that take a skill upload, or a release asset).

  python tools/package_skill.py

The skill runs scripts and talks to a local Blender session, so use it in a code-capable agent on the machine that runs Blender.
"""
import os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "solidcraft-studio")
DIST = os.path.join(ROOT, "dist")
SKIP = {"__pycache__", ".DS_Store"}

os.makedirs(DIST, exist_ok=True)
out = os.path.join(DIST, "solidcraft-studio.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(SKILL):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fn in filenames:
            if fn in SKIP or fn.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, fn)
            z.write(full, os.path.join("solidcraft-studio", os.path.relpath(full, SKILL)))
print(f"{out}  {os.path.getsize(out) / 1e3:.0f} KB")
