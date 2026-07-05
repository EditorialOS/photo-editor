---
name: regenerate-metadata
description: >
  Re-embeds metadata into images after rights or product data changes. Use when
  the user says "re-tag", "update rights", "refresh metadata", "rights changed",
  or when a look file has been manually edited and needs re-embedding.
---

# Regenerate Metadata

Re-embed look data into images when the source look file has been updated. Common triggers: rights changed, SKU updated, product description corrected, rental renewed.

## What You Need

- Updated look file(s) in `work/shoots/{shoot_id}/looks/`
- Photo Editor MCP connected (tools: embed_look_data, read_metadata, list_images)

## When to Use

- Rights change: `editorial` → `commercial` (or vice versa)
- SKU correction: typo fixed, SKU reassigned
- Product data update: description changed, price updated
- Rental renewal: `available_date` extended
- Bulk update: client config changed (e.g., namespace update)

## Steps

### 1. Identify what changed

Compare the current look file against what's embedded in the images.

Read metadata from one image in the look:
```
read_metadata(path="{first_image}")
```

Compare:
- `XMP-editorialOS:skus` vs look file products[].sku
- `XMP-editorialOS:rights` vs look file products[].rights
- `XMP-dc:Rights` vs computed rights summary
- `XMP-dc:Subject` vs expected keyword list

If they match → nothing to do. Skip.

### 2. Re-embed all images in the look

For each image in `images/{look_id}/`:

```
embed_look_data(
    path="{image_path}",
    look_id="{look_id}",
    image_seq={seq},
    products={updated_products},
    rights="{updated_rights}",
    theme="{theme}",
    notes="{notes}"
)
```

Re-tagging replaces the embedded XMP in place. The image's `_original` backup (created on first tag) still holds the pristine untagged file — re-tags never stack additional backups.

### 3. Verify

Spot-check 1-2 images after re-embedding:
```
read_metadata(path="{sample}")
```

Confirm the new values are in place.

### 4. Update look file

Keep status as `tagged` (or `audited` if it was already audited — the re-tag doesn't change audit status, but note in the log that a re-audit may be warranted).

Add a note to the look file:
```yaml
notes: "Re-tagged {date}: {reason}. Original notes here."
```

### 5. Log

Append to `logbook.md`:
```
[{timestamp}] RETAG {look_id}: {N} images re-embedded. Reason: {reason}. Changed fields: {field_list}.
```

If rights changed:
```
[{timestamp}] RIGHTS_CHANGE {look_id}: {old_rights} → {new_rights}. {N} images updated.
```

## Batch Mode

`/regenerate-shoot {shoot_id}` — re-tag ALL looks in the shoot. Use after a bulk rights update or namespace change.

For each look: check if embedded data differs from file → re-embed only if different → log.

## Caution

- This replaces the embedded XMP. Previous *tagged* values live only in logbook history; the pristine untagged original is preserved as the `_original` backup from the first tag.
- If the user asks to re-tag, confirm the change before proceeding: "This will update {N} images in {look_id}. The rights will change from editorial to commercial. Proceed?"
