---
name: build-shoot-log
description: >
  Aggregates look files into a shoot master log. Use when the user says "build
  the shoot log", "summarize this shoot", "generate the master log", or after
  tagging/auditing to produce a consolidated shoot record.
---

# Build Shoot Log

Aggregate all look files in a shoot into a single `shoot_log.md` — a master record of what was shot, what's tagged, and current status.

## What You Need

- Look files in `work/shoots/{shoot_id}/looks/`
- Shoot context (date range, photographer, location — ask if not in client_config)

## Steps

### 1. Read all look files

Parse every `.md` file in `work/shoots/{shoot_id}/looks/`. Extract:
- look_id, status, theme, priority
- Product count, SKU list
- images_tagged count
- Any notes

### 2. Compute aggregates

- Total looks
- By status: untagged / tagged / audited / archived
- Total images tagged (sum of images_tagged across all looks)
- Total unique SKUs
- Total unique products
- By type: rental / purchase / sample / gifted
- By rights: editorial / commercial / all
- Themes represented

### 3. Write shoot_log.md

```markdown
# Shoot Log: {shoot_id}

**Date:** {shoot_date_range}
**Photographer:** {photographer}
**Location:** {location}
**Generated:** {timestamp}

## Summary

| Metric | Count |
|--------|-------|
| Total looks | {N} |
| Total images tagged | {M} |
| Unique SKUs | {S} |
| Unique products | {P} |

## Status

| Status | Count |
|--------|-------|
| Untagged | {n} |
| Tagged | {n} |
| Audited | {n} |
| Archived | {n} |

## By Type

| Type | Count |
|------|-------|
| Rental | {n} |
| Purchase | {n} |
| Sample | {n} |
| Gifted | {n} |

## By Theme

| Theme | Looks | Images |
|-------|-------|--------|
| Wedding Party | {n} | {m} |
| Casual Friday | {n} | {m} |

## Look Index

| Look ID | Status | Theme | Products | Images | Priority |
|---------|--------|-------|----------|--------|----------|
| AV_NG_F26_DEMO_SUIT_1 | tagged | Wedding Party | 2 | 12 | high |
| AV_NG_F26_DEMO_KNIT_2 | tagged | Wedding Party | 3 | 8 | medium |
| ... | | | | | |

## Notes

{any_aggregated_notes}
```

Save to `work/shoots/{shoot_id}/shoot_log.md`.

### 4. Log

Append to `logbook.md`:
```
[{timestamp}] SHOOT_LOG {shoot_id}: Generated. {N} looks, {M} images, {S} SKUs. Status: {summary}.
```

## When to Rebuild

Re-run this skill after any status change (tagging, auditing, archiving) to keep the shoot log current. The log is a snapshot — it's regenerated, not appended.
