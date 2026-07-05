# Photo Editor — Operator Guide

*For photo coordinators, producers, and studio managers. No coding, no
terminal. If you can drag files into folders, you can run this.*

## One-time setup (10 minutes)

**Using Cowork:**

1. Install **Cowork** and this plugin (your admin may have done this already).
2. Open Cowork and type: `/setup`
3. The agent checks everything for you. The only thing it may ask you to do
   yourself is install ExifTool — that's a normal double-click installer
   from exiftool.org, like any Mac app.
4. The agent will walk you through the brand settings (your brand code, your
   default rights level). Answer its questions; it writes the config.

**Using Claude Desktop (standard MCP):**

1. Install ExifTool from exiftool.org (double-click installer, like any Mac app).
2. In Claude Desktop's MCP settings, add this plugin with the **working
   directory (`cwd`) set to the folder where you unpacked Photo Editor.**
   The MCP server path (`server/photo_editor_mcp.py`) is relative to that
   folder. If your admin set this up for you, you can skip this step.
3. Install the Python dependency once in a terminal:
   `pip install mcp` (run this from the photo-editor folder).
4. Type `/setup` in Claude Desktop — the agent verifies everything is working.

That's it. You never do this again.

## The folder rule (the only convention to learn)

Every shoot lives in one folder:

```
work/shoots/F26_DEMO/
├── looks/     ← the agent creates these — don't touch
└── images/    ← YOU put photographer deliveries here,
                 one subfolder per look, named by look ID
```

Example: images for look `AV_NG_F26_DEMO_SUIT_1` go in
`images/AV_NG_F26_DEMO_SUIT_1/`.

## The four commands you'll actually use

**1. New shoot?** Give the agent whatever you have — the master
spreadsheet, a doc, even a pasted list from an email:

> `/ingest-shoot F26_DEMO` *(then attach or paste your shoot list)*

The agent shows you a table of what it understood — **check it**, especially
rights. Say "confirmed" or correct anything. It never writes files until
you approve.

**2. Photos delivered?** Once images are in their look folders:

> `/tag-shoot F26_DEMO`

Every image now carries its products, rights, and tracking ID *inside the
file*. (The originals are kept automatically as `_original` backups — leave
those files alone.)

**3. Before anything ships:**

> `/audit-shoot F26_DEMO`

The agent flags orphan images, rights conflicts, rentals about to expire,
and anything it guessed during ingest that a human hasn't confirmed yet.
Flags land in `decision_log.md` — that file is your to-review list.

**4. Shoot wrapped?**

> `/archive-shoot F26_DEMO`

## Finding things later

- "Where's image AV_NG_F26_DEMO_SUIT_1_002?" → `/find-image AV_NG_F26_DEMO_SUIT_1_002`
- "Every shot with SKU AVD-1042?" → `/find-product AVD-1042`
- Found a mystery file outside the system? Open it in Adobe Bridge or ask
  the agent to read it — the metadata inside the file tells you the shoot,
  look, products, and rights. That's the whole point.

## Things the agent will never do

- Guess rights. If your shoot list doesn't say, it asks you or uses your
  configured default — and tells you it did.
- Pick selects, judge photos, or decide what's on-brand. That's your job.
- Silently write anything from a messy source. You always confirm first.

## If something breaks

Type `/setup` again — it re-checks everything and tells you in plain
language what's wrong and the one thing to do about it.
