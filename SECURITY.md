# Security

## What counts

The skill runs local scripts and talks to SolidCraft, MaterialCraft, TextureCraft and EffectCraft over their stdio MCP servers, and can drive OrcaSlicer and Blender on the command line. A vulnerability here is anything that lets the skill's scripts do more than the user asked: writing outside the project folder, sending data off the machine, overwriting your slicer or Blender profiles, or running code from untrusted input such as model or preset files.

File access of each MCP server is limited to the folder you pass with `--allow`. The live Blender add-on executes arbitrary Python by design; keep its socket on localhost. Problems in the apps themselves belong with their authors (Tangency Labs for SolidCraft, storytold for the other Craft apps).

## Reporting

Use GitHub's private vulnerability reporting: **Security** tab, then **Report a vulnerability**. Please do not open a public issue for a security problem.

I aim to reply within 7 days and to fix confirmed issues in the next release. This is a one-person project, so those are goals and not guarantees.

## Supported versions

Only the latest release on `main`.
