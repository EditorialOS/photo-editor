---
description: First-run setup — checks and installs everything Photo Editor needs
argument-hint:
---

Run first-time setup.

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.
Read the setup skill from `${CLAUDE_PLUGIN_ROOT}/skills/setup.md`.

Execute every check in order: ExifTool, Python MCP dependency, namespace
round-trip, working folders, client configuration. Run installs on the
user's behalf where possible; give one plain-language action when you can't.
The user should never need to open a terminal themselves.
