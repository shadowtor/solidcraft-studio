#!/usr/bin/env python3
"""Assemble _site/ (what GitHub Pages serves): site/ plus the example media the page shows.

  python tools/build_site.py          # then: python -m http.server -d _site 8000
"""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
SHOWN = (".png", ".gif", ".mp4", ".glb")  # media only: scripts and .blend files stay on GitHub

shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(os.path.join(ROOT, "site"), OUT)
for name in os.listdir(os.path.join(ROOT, "examples")):
    src = os.path.join(ROOT, "examples", name)
    if not os.path.isdir(src):
        continue
    dst = os.path.join(OUT, "examples", name)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if f.endswith(SHOWN):
            shutil.copy2(os.path.join(src, f), dst)
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("built", OUT)
