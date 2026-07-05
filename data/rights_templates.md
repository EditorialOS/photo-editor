# Rights Templates

Standard rights configurations. Referenced by look files via the `rights` field in each product.

## editorial

Usage limited to editorial contexts: press coverage, blog posts, social media storytelling, behind-the-scenes content. Not for paid advertising, product pages, or commercial promotional material.

**XMP-dc:Rights**: "Editorial use only. Contact {brand} for commercial licensing."

## commercial

Full commercial usage rights. Can be used in advertising, product pages, email marketing, paid social, print collateral, and point-of-sale.

**XMP-dc:Rights**: "Commercial use licensed. {brand} © {year}."

## all

Unrestricted usage across all channels. Typically applies to owned product photography with no talent, no licensed locations, and no third-party IP.

**XMP-dc:Rights**: "All rights reserved. {brand} © {year}."

---

## Product Type Rules

| Type | Typical Rights | Notes |
|------|---------------|-------|
| rental | editorial | Rental items may have time-limited availability — check available_date |
| purchase | commercial | Owned inventory, typically full commercial rights |
| sample | editorial | Sample items may need to be returned — limited usage window |
| gifted | commercial | Gifted items are owned — typically full rights |

## Mixed Rights in a Single Look

When a look contains products with different rights levels, the **most restrictive** applies to the image as a whole:

- `editorial` + `commercial` → `editorial` for the image
- `editorial` + `all` → `editorial` for the image
- `commercial` + `all` → `commercial` for the image

Flag mixed-rights looks in `decision_log.md` so the team is aware.
