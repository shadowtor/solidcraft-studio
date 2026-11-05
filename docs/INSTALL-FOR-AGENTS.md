# Installing solidcraft-studio (instructions for an AI agent)

Follow these steps in order. Stop and report if a step fails.

1. Get the repository: `git clone https://github.com/shadowtor/solidcraft-studio.git`, or `git pull` if it exists.
2. Install for the agent you are running in, from the repository root:
   - Claude Code: `python tools/install.py --claude`
   - Codex CLI: `python tools/install.py --codex`
   - Gemini CLI: `python tools/install.py --gemini`
   - Cursor, GitHub Copilot, Windsurf or any agent that reads `AGENTS.md` or Cursor rules: `python tools/install.py --rules` (run it inside the user's project folder)
   - Another skills folder: `python tools/install.py --dest <its skills folder>`
   Only the `skills/solidcraft-studio` folder is copied. Do not edit it.
3. Run `python skills/solidcraft-studio/scripts/check_setup.py`.
   - `FAIL solidcraft-cli` means SolidCraft is not installed: tell the user and stop.
   - A `WARN` for OrcaSlicer, Blender, ffmpeg, MaterialCraft, TextureCraft or EffectCraft only disables that finish (slicer check, renders, GIF/MP4, textures, effects).
4. Tell the user where the skill was installed, the check result, and that a new session is needed.
5. Do not commit, push, download anything else, or open a SolidCraft or Blender project.
