---
description: Embed metadata into all untagged looks in a shoot
argument-hint: [shoot_id]
---

Tag all untagged looks in shoot "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.
Read the tag skill from `${CLAUDE_PLUGIN_ROOT}/skills/tag_look.md`.
Read client config from `${CLAUDE_PLUGIN_ROOT}/data/client_config.md`.

Execute in batch mode: iterate over all untagged looks with matching image folders, embed metadata into every image via the Photo Editor MCP, verify embeddings, update look file statuses.
