# Client Configuration

_Edit this file to match your organization — or run `/setup` and the agent
walks you through it. The Photo Editor reads these values as defaults when
look files don't specify their own._

## Brand

| Field | Value |
|-------|-------|
| Brand code | AV _(example — set yours)_ |
| Client code | NG _(example — set yours)_ |
| Full name | _(your brand name)_ |

## Defaults

| Setting | Value |
|---------|-------|
| Rights default | editorial |
| XMP namespace | editorialOS |
| Namespace URI | http://ns.editorialos.com/1.0/ |
| Tracking ID format | `{BRAND}_{CLIENT}_{SEASON}_{SHOOT}_{GARMENT}_{SEQ}` |

## Paths

| Path | Location |
|------|----------|
| Active shoots | work/shoots/ |
| Archive | work/archive/ |
| Look files | work/shoots/{shoot_id}/looks/ |
| Image folders | work/shoots/{shoot_id}/images/ |

## Sensitive Flags

| Flag | Description |
|------|-------------|
| Embargo dates | _(none set)_ |
| Talent restrictions | _(none set)_ |
| Geo restrictions | _(none set)_ |

## Email (for morning summaries)

| Field | Value |
|-------|-------|
| Enabled | false |
| Recipients | _(your email)_ |
| Subject prefix | Photo Editor — |
