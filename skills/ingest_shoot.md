---
name: ingest-shoot
description: >
  Normalizes ANY shoot source — CSV, Excel, markdown, a pasted list, a call
  sheet, or just the image folder names — into validated look files. Use when
  the user says "ingest this shoot", "process this list", "I have a new shoot",
  or drops any file or text describing what was shot.
---

# Ingest Shoot

Turn whatever the user has into look files. The look file is the strict,
validated contract everything downstream trusts; ingestion is the soft,
intelligent edge that gets there. **You normalize; you never silently guess.**

## The Contract

- Input: anything that describes what was shot
- Output: one look file per look in `work/shoots/{shoot_id}/looks/`, in the
  exact schema below
- In between: a **proposal the human confirms before you write anything**

## Accepted Inputs

| Source | How to handle |
|--------|---------------|
| CSV / spreadsheet export | Map columns to schema; preserve unknown columns into products |
| Excel file | Read it, treat as CSV |
| Markdown table or doc | Extract rows/sections into looks |
| Pasted list / email text | Parse structure from prose; one look per described item |
| Call sheet / shot list PDF | Extract looks, products, themes |
| Image folder names only | Propose skeleton looks from folder names; everything else needs_review |

If the user has a plain CSV with a `look_id` column, note that the
deterministic runtime can also ingest it with zero inference:
`python3 runtime/runtime.py ingest-shoot {shoot_id} {file.csv}`.

## Field Tiers — what you may infer, what you must not

**Tier 1 — take as given.** Anything explicitly stated in the source:
look IDs, SKUs, descriptions, rights, dates, types.

**Tier 2 — may infer, must mark.** Reasonable inferences from context:
- `look_id` generated from the client_config pattern when absent
- `theme` from folder names, headings, or grouping in the source
- `priority` (default: medium)
- sequence/grouping of products into looks
Every inferred value gets provenance: add `needs_review: true` to the look
file and note what was inferred in `notes` (e.g., "theme inferred from
folder name").

**Tier 3 — NEVER infer.** Rights and usage terms. "Rights are not
suggestions." If rights are absent from the source:
1. Ask the user, or
2. Apply the client_config default (most restrictive if none configured:
   `editorial`), and say so explicitly in the proposal.
Also never invent: SKUs, available/expiration dates, talent or embargo
restrictions. Absent means absent — leave blank and flag.

## Steps

### 1. Identify the shoot

Get a shoot ID (ask if not provided — e.g., `F26_DEMO`). Create:

```
work/shoots/{shoot_id}/
├── looks/
└── images/
```

### 2. Read the source and build a proposal

Parse whatever was provided. Then show a proposal table BEFORE writing:

```
Proposed looks for {shoot_id} — review before I write anything:

| Look ID | Products (SKUs) | Rights | Theme | Source |
|---------|-----------------|--------|-------|--------|
| AV_NG_F26_DEMO_SUIT_1 | AVD-1042, AVD-1043 | editorial (stated) | Wedding Party | rows 1–2 |
| AV_NG_F26_DEMO_KNIT_2 | AVD-2210 | commercial (stated) | Casual Layers (inferred from heading) | row 3 |
| AV_NG_F26_DEMO_ACC_3 | — none found — | editorial (config default) | — | folder name only |

2 fields inferred, 1 rights defaulted. Confirm, or correct anything above.
```

Wait for confirmation. Apply corrections. Only then write.

### 3. Write look files

One per look, to `work/shoots/{shoot_id}/looks/{look_id}.md`:

```yaml
---
look_id: AV_NG_F26_DEMO_SUIT_1
shoot: F26_DEMO
date: 2026-09-14
priority: high
theme: Wedding Party
status: untagged
images_tagged: 0
needs_review: false        # true if ANY field was inferred
notes: Couple shot
products:
  - sku: AVD-1042
    description: Slate Two-Button Suit Coat — Charcoal
    type: rental
    rights: editorial
    available_date: 2026-09-20
    campaign: Fall Formal      # unknown source columns are preserved —
    vendor: Northgate Textiles # they travel into the embedded productData
---
```

**Preserve every extra column** from the source into the product records.
The embed layer writes the full products array as JSON into
`XMP-editorialOS:productData`, so granular info travels inside the image.

### 4. Scan for existing images

Check `images/` for folders matching look IDs. Report matches and gaps.

### 5. Log and report

Append to `logbook.md`:
```
[{timestamp}] INGEST {shoot_id}: {N} looks created from {source}. {I} inferred fields flagged needs_review. {M} with image folders.
```

Tell the user: looks created, looks ready to tag, looks waiting on images,
and — separately and clearly — which looks carry `needs_review: true` and
why. The audit skill will keep flagging them until a human clears the flag.

## Next Step

"Shoot {shoot_id} ingested — {N} looks. {R} need review (inferred fields).
Run `/tag-shoot {shoot_id}` when ready, or the overnight watcher will pick
up confirmed looks."
