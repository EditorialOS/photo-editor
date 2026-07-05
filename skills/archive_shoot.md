---
name: archive-shoot
description: >
  Closes a shoot and moves it to long-term storage. Use when the user says
  "archive this shoot", "close the shoot", "we're done with this shoot",
  or after auditing is complete and all flags are resolved.
---

# Archive Shoot

Close a completed shoot: update all statuses to `archived`, rebuild the shoot log, and move to long-term storage.

## What You Need

- Shoot at status `audited` (all looks should be audited, or at minimum tagged)
- All decision_log flags for this shoot resolved (or explicitly accepted)
- Archive location from `data/client_config.md`

## Pre-flight Checks

Before archiving, verify:

1. **All looks are at least tagged** — refuse to archive if any look is `untagged`
2. **Decision log flags reviewed** — check for unresolved flags for this shoot_id. If any exist, show them and ask: "These flags are still open. Archive anyway?"
3. **Shoot log is current** — run `build_shoot_log` to regenerate

## Steps

### 1. Update all look files

For each look file in `work/shoots/{shoot_id}/looks/`:
```yaml
status: archived    # was: tagged or audited
```

### 2. Rebuild shoot log (final version)

Run the build_shoot_log skill one final time to capture the archived state.

Add a closing section to shoot_log.md:
```markdown
## Archive Record

**Archived:** {timestamp}
**Archived by:** {user}
**Final counts:** {N} looks, {M} images, {S} SKUs
**Unresolved flags:** {count} (accepted at archive time)
**Archive location:** {archive_path}
```

### 3. Move to archive

If `archive_location` is set in client_config:

```
work/shoots/{shoot_id}/  →  {archive_location}/{shoot_id}/
```

The entire shoot folder moves: looks/, images/, shoot_log.md.

If no archive location configured → leave in place, just update statuses. Tell the user: "Shoot archived in place. Set `archive_location` in client_config to enable automatic moving."

### 4. Log

Append to `logbook.md`:
```
[{timestamp}] ARCHIVE {shoot_id}: Closed. {N} looks, {M} images. Moved to {archive_path}. Unresolved flags: {F}.
```

### 5. Summary

```
Shoot {shoot_id} archived.

Final record:
- {N} looks, {M} images tagged
- {S} unique SKUs across {P} products
- {F} flags accepted at archive time
- Shoot log: {shoot_log_path}
- Archive location: {archive_path}

The images are self-identifying — ExifTool can read the look ID, SKUs, and rights from any file at any time.
```

## Reopening an Archived Shoot

If the user needs to update an archived shoot (e.g., rights renewal):
1. Move the shoot folder back to `work/shoots/` (or work in place)
2. Update the relevant look files
3. Run `regenerate_metadata` on changed looks
4. Re-audit if needed
5. Re-archive

The agent doesn't block this — archiving is a status, not a lock.
