---
description: Check for orphans, rights conflicts, and expiring rentals
argument-hint: [shoot_id]
---

Audit shoot "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.
Read the audit skill from `${CLAUDE_PLUGIN_ROOT}/skills/audit_rights.md`.
Read rights templates from `${CLAUDE_PLUGIN_ROOT}/data/rights_templates.md`.

Execute the full audit: orphan images, looks without images, rights conflicts, expiring rentals, metadata integrity spot-checks. Log all anomalies to decision_log.md.
