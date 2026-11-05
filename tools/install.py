#!/usr/bin/env python3
"""Install (or remove) the solidcraft-studio skill for Claude Code, Codex CLI, Gemini CLI, rules-based agents or any folder.

  python tools/install.py                 # Claude Code + Codex, copy mode (default)
  python tools/install.py --claude        # only ~/.claude/skills/solidcraft-studio
  python tools/install.py --codex         # only ~/.codex/skills/solidcraft-studio
  python tools/install.py --gemini        # only ~/.gemini/skills/solidcraft-studio
  python tools/install.py --rules         # Cursor, Copilot, Windsurf and others: ./.solidcraft-studio + AGENTS.md + .cursor/rules
  python tools/install.py --dest DIR      # DIR/solidcraft-studio
  python tools/install.py --project       # ./.claude/skills/solidcraft-studio in the current project
  python tools/install.py --link          # symlink instead of copy (may need admin on Windows)
  python tools/install.py --uninstall     # remove the chosen targets
  python tools/install.py --check         # run the setup check afterwards

Installing replaces an existing solidcraft-studio folder in the target. Nothing is downloaded and no packages are installed.
--rules never overwrites AGENTS.md: it appends a short section once.
"""
import argparse, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills", "solidcraft-studio")
NAME = "solidcraft-studio"
MARK = "<!-- solidcraft-studio -->"
BLURB = f"""{MARK}
## solidcraft-studio

For anything designed in SolidCraft (3D prints checked in OrcaSlicer for the H2C, Blender or EffectCraft renders and exploded-view animations, MaterialCraft and TextureCraft textured models), read `.solidcraft-studio/SKILL.md` first and follow it.
"""
CURSOR_RULE = """---
description: Design 3D models in SolidCraft through its MCP, then finish them for print, render or textured use
alwaysApply: false
---

Read `.solidcraft-studio/SKILL.md` and follow it for any SolidCraft modelling, 3D print, render, animation or texture task.
"""


def targets(a):
    home = os.path.expanduser("~")
    only = a.claude or a.codex or a.gemini or a.dest or a.project or a.rules
    t = []
    if a.dest:
        t.append(os.path.join(os.path.abspath(a.dest), NAME))
    if a.project:
        t.append(os.path.join(os.getcwd(), ".claude", "skills", NAME))
    if a.rules:
        t.append(os.path.join(os.getcwd(), "." + NAME))
    if a.claude or not only:
        t.append(os.path.join(home, ".claude", "skills", NAME))
    if a.codex or not only:
        t.append(os.path.join(home, ".codex", "skills", NAME))
    if a.gemini:
        t.append(os.path.join(home, ".gemini", "skills", NAME))
    return t


def remove(path):
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def rules(uninstall):
    agents, cursor = os.path.join(os.getcwd(), "AGENTS.md"), os.path.join(os.getcwd(), ".cursor", "rules", NAME + ".mdc")
    if uninstall:
        if os.path.exists(cursor):
            os.remove(cursor)
        if os.path.exists(agents):
            text = open(agents, encoding="utf-8").read()
            if MARK in text:
                open(agents, "w", encoding="utf-8").write(text.split(MARK)[0].rstrip() + "\n")
        return
    text = open(agents, encoding="utf-8").read() if os.path.exists(agents) else ""
    if MARK not in text:
        open(agents, "a", encoding="utf-8").write(("\n" if text else "") + BLURB)
        print("updated", agents)
    os.makedirs(os.path.dirname(cursor), exist_ok=True)
    open(cursor, "w", encoding="utf-8").write(CURSOR_RULE)
    print("wrote  ", cursor)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f in ("--claude", "--codex", "--gemini", "--project", "--rules", "--link", "--uninstall", "--check"):
        ap.add_argument(f, action="store_true")
    ap.add_argument("--dest")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(SRC, "SKILL.md")):
        sys.exit(f"error: {SRC} has no SKILL.md; run this from a full clone of the repository")
    for t in targets(a):
        if a.uninstall:
            remove(t)
            print("removed", t)
            continue
        os.makedirs(os.path.dirname(t), exist_ok=True)
        remove(t)
        if a.link:
            os.symlink(SRC, t, target_is_directory=True)
            print("linked ", t, "->", SRC)
        else:
            shutil.copytree(SRC, t, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print("copied ", t)
    if a.rules:
        rules(a.uninstall)
    if a.uninstall:
        return
    if a.check:
        subprocess.call([sys.executable, os.path.join(SRC, "scripts", "check_setup.py")])
    else:
        print("\nNext: python skills/solidcraft-studio/scripts/check_setup.py   (finds SolidCraft, OrcaSlicer, Blender, ffmpeg and the other Craft apps)")
        print("Then start a new agent session and ask for something to build.")


if __name__ == "__main__":
    main()
