---
name: audit-rights
description: >
  Audits a shoot for orphan images, rights conflicts, and expiring rentals.
  Use when the user says "audit this shoot", "check for problems", "any rights
  issues?", or after tagging is complete.
---

# Audit Rights

Scan a tagged shoot for anomalies: images without looks, looks without images, rights conflicts, and rentals approaching expiration.

## What You Need

- Look files (ideally at status `tagged`) in `work/shoots/{shoot_id}/looks/`
- Image folders in `work/shoots/{shoot_id}/images/`
- Photo Editor MCP connected (tools: read_metadata, list_images, compute_fingerprint)

## Checks

### 1. Orphan images (images without a look)

Scan `work/shoots/{shoot_id}/images/` for image files that don't belong to any look folder, or folders that don't match any look_id.

```
list_images(folder="work/shoots/{shoot_id}/images/", recursive=True)
```

Cross-reference against look file look_ids. Any image in an unmatched folder or at the root level → orphan.

For orphans, compute fingerprint:
```
compute_fingerprint(path="{orphan_path}")
```

Log to `decision_log.md`:
```
[{timestamp}] ORPHAN {path}: No matching look file. MD5: {hash}. Size: {dims}. Action needed: assign to look or discard.
```

### 2. Looks without images

Look files at `status: untagged` with no matching image folder.

These might be expected (images not yet delivered) or might indicate a naming mismatch.

Log:
```
[{timestamp}] MISSING_IMAGES {look_id}: Look file exists but no image folder at images/{look_id}/. Expected? If photographer hasn't delivered, ignore. If mismatch, check folder names.
```

### 3. Inferred fields awaiting review

Look files with `needs_review: true` contain fields the ingest step inferred rather than took from the source. Flag every one:

```
[{timestamp}] NEEDS_REVIEW {look_id}: inferred fields awaiting human confirmation — see look file notes.
```

These stay flagged in every audit until a human clears the flag (sets `needs_review: false`).

### 3b. Rights conflicts

For each tagged look file, check products array for conflicts:

- **Mixed rights in one look**: One product is `editorial`, another is `commercial` → the most restrictive applies to the whole image. Flag if not explicit.
- **Rental without available_date**: type is `rental` but no `available_date` set → flag.
- **Rights mismatch**: Client config says default `editorial` but look says `commercial` (or vice versa) → informational flag, not a blocker.

### 4. Expiring rentals

Check all products where `type: rental` and `available_date` is set.

Flag rentals expiring within:
- 90 days → `RENTAL_WARNING`
- 30 days → `RENTAL_URGENT`
- Already expired → `RENTAL_EXPIRED`

```
[{timestamp}] RENTAL_WARNING {look_id}: SKU {sku} ({description}) — rental available_date {date} is within 90 days. Review for renewal or takedown.
```

### 5. Metadata integrity spot-check

For each tagged look, read metadata from 1-2 images and verify the embedded data matches the look file:
```
read_metadata(path="{sample_image}")
```

Check:
- `XMP-editorialOS:lookId` matches look file
- `XMP-dc:Subject` contains all expected SKUs
- `XMP-dc:Rights` is populated

If mismatch → flag in decision_log as `INTEGRITY_FAIL`.

## Update Look Status

Looks that pass all checks:
```yaml
status: audited    # was: tagged
```

Looks with issues remain at `tagged` until resolved.

## Report

```
Audit complete for {shoot_id}:

Looks audited: {N} (of {total})
Orphan images: {O} — see decision_log for fingerprints
Looks missing images: {M}
Rights flags: {R}
  - {count} mixed-rights looks
  - {count} rentals without available_date
Expiring rentals: {E}
  - {count} within 90 days
  - {count} within 30 days
  - {count} already expired
Integrity issues: {I}
```

## Morning Email Format (for watcher mode)

When run by the overnight cron:
```
Subject: Photo Editor — {shoot_id} audit complete

{N} looks audited, {M} images verified.

Flags:
- 3 rentals expiring within 90 days (SKUs: AVD-1042, AVD-1043, AVD-2210)
- 2 orphan images in images/ root
- 1 look missing image folder (AV_NG_F26_DEMO_ACC_3)

Full details in decision_log.md.
```

## Next Step

"Audit complete. {N} looks clean, {F} flagged. Review the flags in decision_log, then `/archive-shoot {shoot_id}` when ready to close."
