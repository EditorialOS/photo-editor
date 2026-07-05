---
description: Reverse lookup — find an image by tracking ID
argument-hint: [tracking_id]
---

Find the image with tracking ID "$ARGUMENTS".

Read the teammate identity from `${CLAUDE_PLUGIN_ROOT}/teammate.md`.

Search strategy:
1. Parse the tracking ID to extract the look_id (everything before the last _NNN)
2. Find the look file in work/shoots/*/looks/{look_id}.md (search all shoots)
3. Read the look file to get context (products, rights, theme)
4. Check images/{look_id}/ for the specific image (sequence number from tracking ID)
5. Run read_metadata on the image via the Photo Editor MCP to show what's embedded
6. Report: look context, embedded metadata, file location, rights status
