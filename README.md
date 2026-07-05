# Photo Editor — Editorial OS

  > **[GitHub](https://github.com/EditorialOS/photo-editor)** · [Download v1.0.1](https://github.com/EditorialOS/photo-editor/raw/main/releases/photo-editor-v1.0.1.zip) · Apache 2.0

  Post-shoot metadata pipeline that makes every image self-identifying. Embeds XMP/IPTC metadata directly into image files via ExifTool — products, rights, dates, and tracking IDs become part of the file itself.

  Six months later, someone finds a stray TIFF and ExifTool tells them everything: what's in it, who owns it, how it can be used, and when it expires.

  ## Install

  1. **Download** [photo-editor-v1.0.1.zip](https://github.com/EditorialOS/photo-editor/raw/main/releases/photo-editor-v1.0.1.zip)
  2. **Unzip** into your working directory
  3. **Run `/setup`** in Claude — the agent installs and verifies ExifTool and Python dependencies

  Or clone the repo:
  ```
  git clone https://github.com/EditorialOS/photo-editor.git
  ```

  ## Two ways to run the same pipeline

  **Agent-operated (Cowork).** An AI teammate with an identity (`teammate.md`), skills (`skills/`), standing orders, and an append-only memory runs the workflow conversationally. It handles the messy edge — your shoot list can be a CSV, an Excel export, a doc, or a pasted email — and normalizes it into strict look files, showing you a proposal you confirm before anything is written.

  **Deterministic (CLI/cron).** `runtime/runtime.py` runs the identical pipeline on the identical folders with zero inference and zero dependencies beyond Python's standard library. This is the overnight watcher and the no-agent fallback. Same look files, same ExifTool config, same results.

  The division of labor is the design: **intelligence at intake, determinism at embed.** The agent may propose; only validated look files ever drive what gets written into an image. Rights are never inferred — stated, asked, or defaulted, and anything the agent did infer stays flagged `needs_review` in every audit until a human clears it.

  ## How it works

  1. **Ingest** — hand over any shoot source. The agent proposes look files; you confirm. (Or: `runtime.py ingest-shoot {id} {file.csv}` for zero-inference CSV ingest.)
  2. **Tag** — for each look with a matching image folder, embed all metadata into every image. First tag preserves the pristine original as an ExifTool `_original` backup.
  3. **Audit** — orphan images (fingerprinted), rights conflicts, expiring rentals, unreviewed inferences.
  4. **Archive** — close the shoot and move to long-term storage.

  ## Commands

  | Command | What it does |
  |---------|-------------|
  | `/setup` | First-run onboarding — the agent installs and verifies everything |
  | `/ingest-shoot {id}` | Normalize any shoot source into look files (with confirmation) |
  | `/tag-shoot {id}` | Embed metadata into all untagged images |
  | `/audit-shoot {id}` | Check for orphans, rights issues, expirations, unreviewed inferences |
  | `/archive-shoot {id}` | Close and archive a completed shoot |
  | `/find-image {tracking_id}` | Reverse lookup by tracking ID |
  | `/find-product {sku}` | Find every image containing a SKU |

  Every command has a deterministic CLI equivalent — see `standing_orders.md`.

  ## What gets embedded

  Standard fields (readable by Bridge, Lightroom, any DAM):
  - `XMP-dc:Identifier` — unique tracking ID per image
  - `XMP-dc:Subject` / `IPTC:Keywords` — SKU list + theme
  - `XMP-dc:Rights` — rights summary
  - `XMP-dc:Description` — product descriptions

  Custom namespace (`editorialOS:`, defined once in `exiftool/editorialos.config`):
  - `lookId`, `shootId`, `trackingId`, `skus`, `productTypes`, `rights`, `theme`, `availableDates`, `notes`
  - `productData` — the **full product records as JSON**, including every extra column from your source spreadsheet. Granular info travels inside the image.

  ## Requirements

  - **ExifTool** on the host — a double-click installer from [exiftool.org](https://exiftool.org) (or `brew install exiftool`)
  - **Python 3.9+**; the MCP server needs `pip install -r server/requirements.txt`. The CLI runtime needs nothing.
  - Or just run `/setup` and let the agent handle it.

  ## Files

  | File | Purpose |
  |------|---------|
  | `teammate.md` | Agent identity and voice |
  | `standing_orders.md` | Operating cadence, naming conventions, backup policy |
  | `skills/` | Seven skill files — the procedures, in markdown |
  | `commands/` | Slash-command entry points |
  | `data/client_config.md` | Brand defaults, paths, namespace config |
  | `data/rights_templates.md` | Rights level definitions and rules |
  | `exiftool/editorialos.config` | The custom XMP namespace — persistent, checked in |
  | `server/photo_editor_mcp.py` | MCP server wrapping ExifTool (5 tools) |
  | `runtime/runtime.py` | Deterministic CLI — the no-agent fallback and cron watcher |
  | `OPERATOR_GUIDE.md` | The non-coder runbook |
  | `logbook.md` / `decision_log.md` | Append-only memory: history and open flags |
  | `work/shoots/F26_DEMO/` | Sample fixture with a fictional brand — try the pipeline on it |

  ## Try it in two minutes

  ```
  /setup
  /ingest-shoot F26_DEMO        (point it at work/shoots/F26_DEMO/shot_list.csv)
  ```
  Drop any JPG copies into `work/shoots/F26_DEMO/images/AV_NG_F26_DEMO_SUIT_1/`, then:
  ```
  /tag-shoot F26_DEMO
  /audit-shoot F26_DEMO
  ```
  Open a tagged image in Adobe Bridge, or run
  `exiftool -config exiftool/editorialos.config -a -G1 -s <image>` — the look,
  SKUs, rights, and full product JSON are inside the file.

  ## License

  Apache 2.0 — see [LICENSE](LICENSE).
  