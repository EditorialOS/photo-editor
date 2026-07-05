# Photo Editor — Standing Orders

## Active Shoots

| Shoot ID | Status | Priority | Notes |
|----------|--------|----------|-------|
| _(none yet)_ | | | |

Update this table as shoots are ingested and archived.

## Operating Cadence

### First run
- `/setup` — the agent checks and installs everything (ExifTool, Python deps, folders, config). The user never opens a terminal.

### On-demand (user-triggered)
- `/ingest-shoot {shoot_id}` — normalize ANY source (CSV, doc, list, folders) into look files, with confirmation before writing
- `/tag-shoot {shoot_id}` — tag all untagged looks in a shoot
- `/audit-shoot {shoot_id}` — run rights and integrity audit
- `/archive-shoot {shoot_id}` — close and archive
- `/find-image {tracking_id}` — reverse lookup by tracking ID
- `/find-product {sku}` — find every image containing a SKU

### Deterministic fallback (no agent)
`runtime/runtime.py` runs the same pipeline from a terminal or cron:
`ingest-shoot` (CSV only, zero inference), `tag-shoot`, `tag-look`,
`audit-shoot`, `archive-shoot`, `find-image`, `find-product`, `watch-once`.

### Overnight watcher (when configured)
Cron at 02:00 local: `python3 runtime/runtime.py watch-once`
1. Scan all shoots for looks at `status: untagged` with matching image folders
2. Tag each qualifying look (looks at `needs_review: true` are still tagged, but the audit keeps flagging them)
3. Run audit on any shoot that had looks tagged
4. Write summary to `logbook.md`

### Default Rights Rules
- If look file specifies rights → use them
- If look file omits rights → use `data/client_config.md` default
- If no default configured → use `editorial` (most restrictive, safest)
- Mixed rights in a single look → flag in decision_log, use most restrictive for the image
- **Rights are never inferred at ingest.** Stated, asked, or defaulted — nothing else.

### Backup Policy
- First tag of an image → ExifTool `_original` backup preserved (the pristine untagged file)
- Re-tags → overwrite in place; one backup per image, never a stack
- `_original` files are never tagged, listed, or counted

### Naming Conventions
- Look IDs: `{BRAND}_{CLIENT}_{SEASON}_{SHOOT}_{GARMENT}_{SEQ}`
  - Example: `AV_NG_F26_DEMO_SUIT_1`
- Tracking IDs: `{look_id}_{image_seq:03d}`
  - Example: `AV_NG_F26_DEMO_SUIT_1_001`
- Shoot folders: `work/shoots/{SHOOT_ID}/`
- Archive: `work/archive/{SHOOT_ID}/`

### What Gets Logged Where
| Event | logbook.md | decision_log.md |
|-------|-----------|----------------|
| Ingest | shoot_id, look count, source, inferred-field count | — |
| Tag | look_id, image count, tracking IDs | Verification failures |
| Audit | summary counts | Orphans, rights conflicts, expiring rentals, needs_review |
| Retag | look_id, reason, changed fields | — |
| Archive | shoot_id, final counts | Unresolved flags accepted |
