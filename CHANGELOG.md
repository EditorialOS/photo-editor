# Changelog

## 1.0.2 — mcp path regression fix

- **Restored `${CLAUDE_PLUGIN_ROOT}` in `.mcp.json`.** The v1.0.1 change to
  a bare relative path (`server/photo_editor_mcp.py`) fixed the unzipped-folder
  flow but broke the plugin-install flow: when Claude Desktop installs a
  `.claude-plugin` package it copies it to a cache directory, so the working
  directory is never the plugin root and a relative path silently fails. The
  spec-correct form — `${CLAUDE_PLUGIN_ROOT}/server/photo_editor_mcp.py` —
  works for plugin installs; the unzipped-folder case is now handled by the
  `/setup` fallback (see below).
- **Added MCP server connectivity check to `/setup` (check 6 of 7).** If the
  MCP server isn't reachable after install, `/setup` probes with a read-only
  tool call, determines the absolute path to `server/photo_editor_mcp.py` on
  the current machine, and writes it directly into the Claude Desktop config
  (`mcpServers.photo-editor.args`). The user only needs to relaunch Claude
  Desktop — no manual JSON editing. This makes the loose-folder flow
  self-healing and consistent with `/setup`'s existing premise of fixing its
  own environment.

## 1.0.1 — distribution fixes

- **Cleaned `plugin.json` placeholders.** Removed unfilled draft annotations
  from the `homepage` and `repository` fields so the package ships without
  internal author notes visible to new users.
- **Fixed `.mcp.json` for Claude Desktop compatibility.** Changed to a
  relative path and added Claude Desktop setup instructions to
  `OPERATOR_GUIDE.md` (reverted in 1.0.2 — see above).
- **Added re-ingest conflict detection in CLI runtime.** `ingest-shoot` now
  checks for existing look files before writing and exits with a clear error
  listing the conflicting look IDs rather than silently appending products
  and creating duplicates.
- **Added lock file to `watch-once` watcher.** A PID-based lock file
  (`work/.watch.lock`) prevents two overlapping cron invocations from tagging
  the same looks concurrently. Stale locks (from crashed processes) are
  detected and cleaned up automatically.
- **Enforced mixed-rights resolution in MCP server.** `embed_look_data` now
  applies the same "most restrictive product right wins" logic as the CLI
  runtime, overriding the caller-supplied `rights` parameter when per-product
  rights are stricter. The return dict includes `rights_resolved: true` when
  this override occurs so the agent can log it.

## 1.0.0 — first public release

Merges two internal lineages: the deterministic local runtime prototype and
the Cowork plugin. One pipeline, two interfaces.

- **Agent + CLI dual path.** The Cowork teammate and `runtime/runtime.py`
  run the same pipeline on the same folders. The runtime is stdlib-only.
- **Flexible ingest.** The agent normalizes any source (CSV, Excel, docs,
  pasted lists, folder names) into look files via a propose-and-confirm
  workflow. Rights are never inferred; inferred fields carry
  `needs_review: true` and are flagged in every audit until cleared.
- **Zero data loss, for real.** First tag preserves the pristine original
  as an ExifTool `_original` backup; re-tags never stack backups; backups
  are excluded from listing, tagging, and counting.
- **Persistent namespace config.** `exiftool/editorialos.config` is checked
  in and shared by the server and the CLI — no runtime config generation.
- **Richer embeds.** Added `shootId` and `productData` (full product
  records as JSON — arbitrary source-spreadsheet columns travel inside the
  image).
- **Honest tooling.** `compute_fingerprint` documents exact-match limits
  (perceptual hashing is planned for v2); `write_xmp` correctly scopes
  custom-namespace writes to editorialOS.
- **`/setup` onboarding.** The agent verifies and installs its own
  dependencies; non-coders never open a terminal.
- Sample fixture (`F26_DEMO`) with a fictional brand for a two-minute trial.
