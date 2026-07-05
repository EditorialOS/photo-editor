---
name: setup
description: >
  Verifies and self-heals the Photo Editor install: ExifTool binary, version,
  namespace config, Python MCP dependency, and work/ directory tree. Run on
  first install or any time something seems broken. Each check is independent —
  a failure in one never blocks the others from running.
---

# Setup — Verify and Repair

Run every check listed below in order. For each one, print a one-line result:
`✓ PASS` or `✗ FAIL — <specific action>`. After all checks, print a summary
and the next step.

---

## Check 1 — ExifTool binary

Run:
```
exiftool -ver
```

- **PASS** — command exits 0 and prints a version string.
- **FAIL** — command not found or exits non-zero.

If `EXIFTOOL_PATH` is set in the environment, test that path instead. If it
is set but wrong, the action is: `Unset EXIFTOOL_PATH or correct it to the
full path of the exiftool binary, then re-run /setup.`

Standard FAIL action:
```
Install ExifTool from https://exiftool.org (double-click installer on macOS/Windows,
or: brew install exiftool). Then re-run /setup.
```

---

## Check 2 — ExifTool minimum version

ExifTool 12.00 or later is required for reliable XMP namespace support.

Parse the version number from Check 1's output. If Check 1 failed, skip this
check and mark it **SKIPPED**.

- **PASS** — version ≥ 12.00.
- **FAIL** — version < 12.00.

FAIL action:
```
Upgrade ExifTool to 12.00 or later: https://exiftool.org. Then re-run /setup.
```

---

## Check 3 — editorialos.config present

The config file must exist at `exiftool/editorialos.config` relative to the
plugin root (the directory that contains `skills/`, `server/`, etc.).

- **PASS** — file exists and is non-empty.
- **FAIL** — file is missing or empty.

FAIL action:
```
The namespace config is missing. Re-download the plugin ZIP from
https://github.com/EditorialOS/photo-editor/releases and unzip it into this
directory, replacing any partial install. Then re-run /setup.
```

Do not attempt to regenerate the config from memory — the checked-in file is
the authoritative source. A missing config always means an incomplete download
or unzip.

---

## Check 4 — editorialos.config loads in ExifTool

Run:
```
exiftool -config exiftool/editorialos.config -ver
```

(Run from the plugin root so the relative path resolves correctly.)

- **PASS** — command exits 0 and prints a version string.
- **FAIL** — command exits non-zero, or stderr contains "Can't locate" /
  "syntax error" / "not defined".

If Check 1 or Check 3 failed, skip this check and mark it **SKIPPED**.

FAIL action: quote the first meaningful line of stderr verbatim, then say:
```
The config file is present but ExifTool rejected it. The file may be
corrupted or truncated. Re-download the plugin ZIP and replace
exiftool/editorialos.config, then re-run /setup.
```

---

## Check 5 — Python `mcp` package importable

Run:
```
python3 -c "import mcp; print(mcp.__version__)"
```

- **PASS** — exits 0 and prints a version string.
- **FAIL** — exits non-zero or prints an ImportError.

FAIL action:
```
Run: pip install -r server/requirements.txt
Then re-run /setup.
```

If `python3` is not found at all:
```
Python 3.9 or later is required. Install it from https://python.org, then run:
  pip install -r server/requirements.txt
Then re-run /setup.
```

---

## Check 6 — MCP server connectivity

Probe whether the `photo-editor` MCP server is reachable by calling any
read-only tool (e.g. `list_looks` with no arguments).

- **PASS** — tool call succeeds.
- **FAIL** — tool call errors or times out.

The most common cause of failure is that Claude Desktop launched without
`${CLAUDE_PLUGIN_ROOT}` resolving — this happens when the plugin is used from
an unzipped folder rather than a Cowork-managed install. Fix it automatically:

1. Resolve the absolute path to `server/photo_editor_mcp.py` on this machine:

   ```
   python3 -c "import os; print(os.path.realpath('server/photo_editor_mcp.py'))"
   ```

   If the returned path ends in `server/photo_editor_mcp.py` and exists on
   disk, use it. If not, stop here and tell the user to run `/setup` from
   inside the unzipped `photo-editor/` folder.

2. Open or create the Claude Desktop config file:
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

3. Add or overwrite the `photo-editor` entry under `mcpServers`:

   ```json
   "photo-editor": {
     "command": "python3",
     "args": ["/absolute/path/to/server/photo_editor_mcp.py"]
   }
   ```

4. Tell the user: "I've updated your Claude Desktop config with an absolute
   path that works from any directory. Quit and relaunch Claude Desktop, then
   run `/setup` again to confirm the server is connected." This one restart
   is the only step they need to do themselves.

If Check 5 failed (Python or `mcp` not available), skip this check and mark
it **SKIPPED**.

---

## Check 7 — work/ directory tree

The following directories must exist under the plugin root. Create any that
are missing — this is always safe:

```
work/
work/shoots/
work/archive/
```

For each directory:
- **PASS** — directory exists.
- **CREATED** — directory was missing; created now.

No FAIL state for this check. Directory creation is automatic and silent
unless it errors (e.g. a file named `work` already exists, which would be
unusual enough to surface verbatim).

---

## Summary format

After all checks, print:

```
Setup complete.

  ✓ ExifTool binary        (v{version})
  ✓ ExifTool version       (≥ 12.00)
  ✓ editorialos.config     (present)
  ✓ Namespace loads        (ExifTool accepts config)
  ✓ Python mcp package     (v{version})
  ✓ MCP server             (connected)
  ✓ work/ directories      (all present / created)

Everything looks good. Try:
  /ingest-shoot F26_DEMO   ← point it at work/shoots/F26_DEMO/shot_list.csv
```

If any check FAILED:
```
Setup found {N} issue(s):

  ✓ ExifTool binary        (v{version})
  ✗ ExifTool version       → Upgrade to 12.00+: https://exiftool.org
  ...

Fix the issue(s) above, then re-run /setup to confirm.
```

If a check was SKIPPED because a prerequisite failed, show it as:
```
  — Namespace loads        (skipped — ExifTool binary not found)
```

---

## Rules

- Run all seven checks unconditionally (except explicit SKIPPED conditions).
  A failure in Check 1 must not suppress Checks 3–7.
- Each failure produces exactly one action — a concrete command or URL,
  not a question.
- Do not guess at what might be wrong. Report what the check measured and
  what the fix is.
- The `work/` directories are always created if absent. Do not ask first.
