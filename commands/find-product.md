---
description: Find every image containing a product SKU
argument-hint: [sku]
---

Find all images containing SKU "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.

Search strategy:
1. Grep all look files across all shoots for the SKU
2. For each matching look file, report: look_id, shoot_id, theme, rights, image count
3. List all tracking IDs that contain this product
4. Show rights status for each (editorial/commercial/all)
5. Flag any expiring rentals for this SKU
