#!/usr/bin/env python3
"""Create a project folder.   python new_project.py "<name>" --mode print|render|textured [--material PETG] [--root .]

Makes <root>/<name>/{project.json, build/, exports/, renders/, textures/, shots/}. Point solidcraft's --allow-path at this folder.
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--mode", required=True, choices=["print", "render", "textured"])
ap.add_argument("--material", default="PETG")
ap.add_argument("--printer", default="Bambu Lab H2C")
ap.add_argument("--root", default=".")
a = ap.parse_args()
d = os.path.abspath(os.path.join(a.root, a.name))
for s in ("build", "exports", "renders", "textures", "shots"):
    os.makedirs(os.path.join(d, s), exist_ok=True)
cfg = {"name": a.name, "mode": a.mode, "assumptions": [], "parameters": {}}
if a.mode == "print":
    cfg.update(material=a.material.upper(), printer=a.printer)
p = os.path.join(d, "project.json")
if not os.path.exists(p):
    json.dump(cfg, open(p, "w"), indent=2)
print(d)
