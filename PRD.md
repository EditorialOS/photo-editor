# PRD — Photo Editor v1.0

  **Status:** Shipped · v1.0.2 · [Changelog](CHANGELOG.md) · [Decision log](decision_log.md)
  **Owner:** Roger Gurbani

  ---

  ## Problem

  Every photo operation accumulates metadata debt. Six months after a shoot, a stray TIFF has no product, no rights window, no shoot context, and no way to answer "can we still use this?" The knowledge existed on shoot day — it just never got embedded where it survives: in the file itself. Manual metadata entry doesn't scale past a handful of images, and it's the first corner cut under deadline.

  ## Users

  - Photo desks and studio teams running recurring product or editorial shoots
  - Content ops teams who inherit image libraries with no embedded provenance
  - Any operation where usage rights have expiration dates and the file is the only artifact that travels

  ## What v1 does

  - Embeds XMP/IPTC metadata into images via ExifTool: products, rights, dates, shoot context — traceable at the file level
  - Ships a custom XMP namespace, checked into the repo, so fields are documented and machine-readable
  - **Intelligence at intake, determinism at embed:** the agent interprets messy human input at ingest; the embed step is deterministic code with no model in the write path
  - Flags every inferred value as `needs_review: true` rather than silently committing a guess
  - Preserves pristine originals — writes never destroy the source file
  - Runs two ways: as a Claude Code plugin (agent-assisted intake) or as a zero-dependency CLI via `runtime/runtime.py` on a schedule (deterministic batch processing)
  - Includes a sample fixture and a two-minute tryout path, plus an operator guide written for non-coders

  ## What v1 explicitly does NOT do

  - **Does not edit pixels.** No retouching, cropping, or conversion — metadata only.
  - **Does not replace a DAM.** It makes files self-describing so any DAM (or a bare folder) inherits the intelligence.
  - **Does not grant or clear rights.** It records the rights humans provide and surfaces expirations; it never adjudicates.
  - **Does not auto-approve inferred fields.** Anything the agent inferred stays flagged until a human confirms it.
  - **Does not require the agent to run.** The deterministic runtime processes batches with no model call at all.

  ## Success criteria

  - Every embedded field is verifiable in the file with standard tools (exiftool read-back matches what was written)
  - Zero destructive writes: original files bit-identical after processing <!-- RAJ: state how this is verified — backup diff, checksum, whatever the repo actually does. -->
  - 100% of model-inferred values carry the `needs_review` flag
  - A non-coder completes the two-minute tryout using only the operator guide <!-- RAJ: have one person do this cold and note the result. -->

  ## Roadmap

  <!-- RAJ: list actual v1.1 intent or delete this section. -->

  ## Decision log

  Fuller record in [decision_log.md](decision_log.md). Headlines:

  - **Intelligence at intake, determinism at embed** — the model never sits in the write path; when the model is wrong, it's wrong in a reviewable field, not in an embedded file
  - **File-level metadata over database records** — the file is the only artifact guaranteed to travel; embedded truth survives every system migration
  - **Review flags over silent inference** — a wrong guess that's flagged costs a glance; a wrong guess that's embedded costs an audit
  