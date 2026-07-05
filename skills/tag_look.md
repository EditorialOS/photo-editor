---
name: tag-look
description: >
  Embeds look data into images via ExifTool MCP. Use when the user says "tag this
  shoot", "tag this look", "embed metadata", or when the overnight watcher finds
  untagged looks with matching image folders.
---

# Tag Look

For each look file with status `untagged` and a matching image folder, embed XMP/IPTC metadata into every image using the Photo Editor MCP server.

## What You Need

- Look files at status `untagged` in `work/shoots/{shoot_id}/looks/`
- Matching image folders in `work/shoots/{shoot_id}/images/{look_id}/`
- Photo Editor MCP connected (tools: embed_look_data, read_metadata, list_images)
- Client config for namespace and rights defaults

## Steps

### 1. Find taggable looks

Scan look files. For each with `status: untagged`, check if `images/{look_id}/` exists and contains images.

Use the MCP `list_images` tool:
```
list_images(folder="work/shoots/{shoot_id}/images/{look_id}/")
```

### 2. For each image in the look folder

Call `embed_look_data` with:
- `path`: absolute path to the image file
- `look_id`: from the look file
- `shoot_id`: the shoot this look belongs to
- `image_seq`: sequential number (1, 2, 3...) based on sorted filename order
- `products`: the full products array from the look file
- `rights`: the rights value (use client default if look file says inherit)
- `theme`: from the look file
- `notes`: from the look file

This embeds:
- `XMP-dc:Identifier` = `{look_id}_001`
- `XMP-dc:Subject` / `IPTC:Keywords` = SKU list + theme
- `XMP-editorialOS:shootId` and a full `productData` JSON payload (every product column travels in the file)

The first tag of each image preserves an ExifTool `_original` backup — the pristine untagged file. `list_images` already skips these backups; never tag or count them. Re-tags overwrite in place without stacking backups.
- `XMP-dc:Rights` = rights summary
- `XMP-editorialOS:lookId` = look ID
- `XMP-editorialOS:trackingId` = full tracking ID
- `XMP-editorialOS:skus` = comma-separated SKUs
- `XMP-editorialOS:productTypes` = rental/purchase/etc
- `XMP-editorialOS:rights` = rights level
- `XMP-editorialOS:theme` = theme
- `XMP-editorialOS:availableDates` = availability dates
- `XMP-editorialOS:notes` = notes

### 3. Verify each embedding

After `embed_look_data`, call `read_metadata` on the same file.
Confirm:
- `XMP-dc:Identifier` matches expected tracking ID
- `XMP-editorialOS:lookId` matches
- Keywords contain all SKUs

If verification fails → log the error, skip the image, continue.

### 4. Update the look file

After all images in a look are tagged:
```yaml
status: tagged          # was: untagged
images_tagged: 12       # actual count
```

Write the updated YAML back to the look file.

### 5. Log

Append to `logbook.md`:
```
[{timestamp}] TAG {look_id}: {N} images embedded. Tracking IDs {look_id}_001 through {look_id}_{N:03d}. Verified: {pass}/{total}.
```

If any images failed verification:
```
[{timestamp}] TAG WARNING {look_id}: {M} images failed verification — see decision_log.
```

Append details to `decision_log.md`:
```
[{timestamp}] VERIFY_FAIL {tracking_id}: Expected XMP-dc:Identifier={expected}, got {actual}. File: {path}.
```

## Batch mode (tag-shoot)

When called as `/tag-shoot {shoot_id}`, iterate over ALL untagged looks in the shoot.

Report at the end:
- Looks tagged: {N}
- Total images embedded: {M}
- Verification failures: {F}
- Looks skipped (no image folder): {S}

## Next Step

"Shoot {shoot_id}: {N} looks tagged, {M} images embedded. Run `/audit-shoot {shoot_id}` to check for orphans, rights conflicts, and expiring rentals."
