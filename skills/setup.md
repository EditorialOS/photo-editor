---
name: setup
description: >
  First-run onboarding. Checks and installs everything Photo Editor needs,
  with zero terminal knowledge required from the user. Use when the user says
  "set up", "setup", "get started", "install", or on any tool failure that
  suggests missing dependencies.
---

# Setup

You onboard the user. They should never have to open a terminal themselves —
you run the checks and installs on their behalf and report in plain language.

## Checks, in order

### 1. ExifTool

Run: `exiftool -ver`

- **Found** → report the version, move on.
- **Not found** → do not send them to Homebrew. Give the friendly path:
  - **Mac:** "Download the ExifTool installer from https://exiftool.org — it's
    a standard .pkg you double-click, like any Mac app. Come back and run
    `/setup` again when it's done."
  - **Windows:** the Windows installer from the same page.
  - If they say they have Homebrew, `brew install exiftool` works too.
- Also honor `EXIFTOOL_PATH` if they installed somewhere unusual.

### 2. Python + the MCP dependency

Run: `python3 --version`, then check `python3 -c "import mcp"`.

- If `mcp` is missing, install it yourself:
  `pip3 install -r "${CLAUDE_PLUGIN_ROOT}/server/requirements.txt" --user`
  (fall back to `--break-system-packages` if the environment requires it,
  and say you're doing so).
- The deterministic runtime (`runtime/runtime.py`) is stdlib-only and needs
  no installs — mention this if the pip step fails; they still have a
  working pipeline.

### 3. Namespace config

Verify `${CLAUDE_PLUGIN_ROOT}/exiftool/editorialos.config` exists, then
prove the round-trip: create a tiny test image (or use one the user
provides), embed a test field with the MCP `write_xmp` tool, read it back
with `read_metadata`, then delete the test image and its `_original`.

### 4. Working folders

Create if missing:
```
work/shoots/
work/archive/
```

### 5. Client configuration — the only part that needs the human

Open `data/client_config.md` with them and fill in together:
- Brand code and client code (used in look IDs)
- Default rights level
- Archive location (optional)
- Email for morning summaries (optional)

Explain each in one sentence as you go. Write the file for them.

## Report

```
Setup complete.

ExifTool: 13.10 ✓
Python MCP server: connected ✓
Namespace round-trip: verified ✓
Folders: work/shoots, work/archive ✓
Client config: brand AV, default rights editorial ✓

You're ready. Drop a shoot list (any format — CSV, a doc, even a pasted
list) and run /ingest-shoot with a shoot ID.
```

If anything failed, say exactly which step, what you tried, and the one
action the user needs to take — never a wall of errors.
