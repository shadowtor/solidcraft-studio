#!/usr/bin/env python3
"""Rewrite a Z-up OBJ (SolidCraft) as Y-up (TextureCraft, glTF, most game engines): (x, y, z) -> (x, z, -y), normals likewise.

  python obj_zup_to_yup.py in.obj out.obj [--scale 0.001]     # --scale: mm -> m for engines that expect metres
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
k = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
out = []
for ln in open(src, encoding="utf-8"):
    p = ln.split()
    if p and p[0] in ("v", "vn") and len(p) >= 4:
        x, y, z = map(float, p[1:4])
        s = k if p[0] == "v" else 1.0
        out.append("%s %.9g %.9g %.9g%s\n" % (p[0], x * s, z * s, -y * s, " " + " ".join(p[4:]) if p[4:] else ""))
    else:
        out.append(ln)
open(dst, "w", encoding="utf-8").writelines(out)
