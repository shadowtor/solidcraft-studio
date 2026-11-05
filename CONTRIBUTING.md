# Contributing

Issues and pull requests are welcome.

- **Reporting a problem:** include the output of `check_setup.py`, the script that failed and the error text.
- **Adding to the notes:** only add what you ran. Mark anything unrun **untested**.
- **Adding a recipe or helper:** keep `SKILL.md` short and put detail in `skills/solidcraft-studio/references/`. A script goes in `scripts/` only if two workflows need it.
- **Before a pull request:** run `python tools/smoke_test.py`. It compiles the scripts and checks the skill files and plugin manifests.
- **Copy:** public pages and docs should read like a person wrote them. Run the slopmonster check if you have it.
- Open an issue before a large change so we agree on the direction first. Replies take about a week.
- Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md). Security problems go through [`SECURITY.md`](SECURITY.md), not a public issue.
- Do not commit generated zips, secrets, customer artwork or models you do not have the right to share.
