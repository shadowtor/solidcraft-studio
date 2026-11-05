#!/usr/bin/env python3
"""Static checks that run anywhere: skill files exist, scripts compile, manifests parse, SKILL.md has its frontmatter."""
import json, os, py_compile, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills", "solidcraft-studio")
bad = []
for f in ("SKILL.md", "assets/materials.json", "references/clean-supports.md", "references/slicer.md",
          "references/render-animation.md", "references/texture-pipeline.md"):
    if not os.path.exists(os.path.join(SK, f)):
        bad.append("missing " + f)
for d, _, fs in os.walk(os.path.join(SK, "scripts")):
    for f in fs:
        if f.endswith(".py"):
            try:
                py_compile.compile(os.path.join(d, f), cfile=os.path.join(tempfile.gettempdir(), "sc_smoke.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                bad.append(str(e))
for f in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "skills/solidcraft-studio/assets/materials.json"):
    try:
        json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
    except Exception as e:
        bad.append("%s: %s" % (f, e))
head = open(os.path.join(SK, "SKILL.md"), encoding="utf-8").read(400)
if not head.startswith("---") or "name: solidcraft-studio" not in head:
    bad.append("SKILL.md frontmatter")
print("FAIL\n" + "\n".join(bad) if bad else "ok")
sys.exit(1 if bad else 0)
