---
description: Close a shoot and move to long-term storage
argument-hint: [shoot_id]
---

Archive shoot "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.
Read the archive skill from `${CLAUDE_PLUGIN_ROOT}/skills/archive_shoot.md`.

Run pre-flight checks (all looks tagged, decision_log flags reviewed), update all statuses to archived, rebuild the shoot log one final time, move to archive location if configured.
