# solidcraft-studio

This repository is an Agent Skill that designs 3D models in SolidCraft through its MCP, then finishes them for H2C printing (OrcaSlicer check), Blender or EffectCraft renders, or MaterialCraft and TextureCraft textures.

If you are an AI agent asked to design, print-check, render or texture a model, read `skills/solidcraft-studio/SKILL.md` first and follow it. Its scripts are in `skills/solidcraft-studio/scripts/`, its references in `skills/solidcraft-studio/references/`. To install it for an agent, follow `docs/INSTALL-FOR-AGENTS.md`.

Working on the repository itself: run `python tools/smoke_test.py` before finishing, keep `SKILL.md` short, and mark anything you did not run as untested.
