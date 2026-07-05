---
description: Process a new shoot list into look files
argument-hint: [shoot_id]
---

Ingest shoot "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.
Read the ingest skill from `${CLAUDE_PLUGIN_ROOT}/skills/ingest_shoot.md`.
Read client config from `${CLAUDE_PLUGIN_ROOT}/data/client_config.md`.

Ask what they have if no source was provided — a CSV, spreadsheet, doc, pasted list, or just image folders all work.
Execute the ingest skill: normalize the source into a proposal table, get the user's confirmation, then write look files, scan for existing images, and log results. Never write look files before the user confirms the proposal. Never infer rights.
