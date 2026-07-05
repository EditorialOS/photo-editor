#!/usr/bin/env python3
"""
Photo Editor — deterministic runtime (no agent required)

The CLI fallback and cron layer. Every operation here is deterministic:
CSV in, look files out, metadata embedded exactly as specified. The AI
teammate (via Cowork) uses the same folders, the same look files, and the
same ExifTool config — this runtime is what runs when no agent is present.

Usage:
    python3 runtime/runtime.py ingest-shoot  SHOOT_ID path/to/shot_list.csv
    python3 runtime/runtime.py tag-shoot     SHOOT_ID
    python3 runtime/runtime.py tag-look      LOOK_ID
    python3 runtime/runtime.py audit-shoot   SHOOT_ID
    python3 runtime/runtime.py archive-shoot SHOOT_ID
    python3 runtime/runtime.py find-image    TRACKING_ID
    python3 runtime/runtime.py find-product  SKU
    python3 runtime/runtime.py watch-once

No third-party dependencies. Requires ExifTool on PATH (or EXIFTOOL_PATH).
"""

import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_tools as mt

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
WORK = PLUGIN_ROOT / "work"
SHOOTS = WORK / "shoots"
ARCHIVE = WORK / "archive"
LOGBOOK = PLUGIN_ROOT / "logbook.md"
DECISION_LOG = PLUGIN_ROOT / "decision_log.md"
WATCH_LOCK = WORK / ".watch.lock"

# Products may carry any extra columns; these are the core recognized ones.
CORE_PRODUCT_FIELDS = ["sku", "description", "type", "rights", "available_date"]
LOOK_SCALARS = ["look_id", "shoot", "date", "priority", "theme", "status",
                "images_tagged", "rights", "needs_review", "notes"]


# ── Look file format (frontmatter, controlled schema) ───────────────

def write_look_file(path: Path, look: dict):
    """Serialize a look dict to our controlled frontmatter format."""
    lines = ["---"]
    for key in LOOK_SCALARS:
        if key in look and look[key] not in (None, ""):
            lines.append(f"{key}: {look[key]}")
    lines.append("products:")
    for p in look.get("products", []):
        first = True
        for k, v in p.items():
            if v in (None, ""):
                continue
            prefix = "  - " if first else "    "
            lines.append(f"{prefix}{k}: {v}")
            first = False
    lines.append("---")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_look_file(path: Path) -> dict:
    """Parse our controlled frontmatter format back into a dict."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise ValueError(f"No frontmatter in {path}")
    look = {"products": []}
    current_product = None
    in_products = False
    for raw in m.group(1).splitlines():
        if not raw.strip():
            continue
        if raw.strip() == "products:":
            in_products = True
            continue
        if in_products and (raw.startswith("  - ") or raw.startswith("    ")):
            content = raw.strip()
            if raw.startswith("  - "):
                current_product = {}
                look["products"].append(current_product)
                content = content[2:]
            k, _, v = content.partition(":")
            if current_product is not None:
                current_product[k.strip()] = v.strip()
            continue
        in_products = False
        k, _, v = raw.partition(":")
        look[k.strip()] = v.strip()
    if "images_tagged" in look:
        try:
            look["images_tagged"] = int(look["images_tagged"])
        except ValueError:
            look["images_tagged"] = 0
    return look


def looks_dir(shoot_id: str) -> Path:
    return SHOOTS / shoot_id / "looks"


def images_dir(shoot_id: str) -> Path:
    return SHOOTS / shoot_id / "images"


def all_looks(shoot_id: str):
    d = looks_dir(shoot_id)
    if not d.is_dir():
        return []
    return [read_look_file(p) for p in sorted(d.glob("*.md"))]


def log(line: str, decision: bool = False):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    target = DECISION_LOG if decision else LOGBOOK
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {line}\n")


# ── Commands ────────────────────────────────────────────────────────

def cmd_ingest(shoot_id: str, csv_path: str):
    """Deterministic CSV ingest. One look file per look_id; rows sharing a
    look_id become multiple products in one look. Unknown columns are
    preserved into the product records (they travel into productData).

    Exits with an error if any look files from this CSV already exist —
    use the agent-operated flow to re-ingest with confirmation, or delete
    the existing look files manually before re-running."""
    src = Path(csv_path)
    if not src.is_file():
        sys.exit(f"Shoot list not found: {csv_path}")

    (looks_dir(shoot_id)).mkdir(parents=True, exist_ok=True)
    (images_dir(shoot_id)).mkdir(parents=True, exist_ok=True)

    looks: dict[str, dict] = {}
    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            look_id = row.get("look_id", "")
            if not look_id:
                print(f"  skipped row with no look_id: {row}")
                continue
            look = looks.setdefault(look_id, {
                "look_id": look_id,
                "shoot": row.get("shoot", shoot_id),
                "date": row.get("date", ""),
                "priority": row.get("priority", "medium"),
                "theme": row.get("theme", ""),
                "status": "untagged",
                "images_tagged": 0,
                "notes": row.get("notes", ""),
                "products": [],
            })
            product = {}
            for k in CORE_PRODUCT_FIELDS:
                if row.get(k):
                    product[k] = row[k]
            # Preserve every extra column — granular info travels with the product
            consumed = set(CORE_PRODUCT_FIELDS) | {"look_id", "shoot", "date",
                                                   "priority", "theme", "notes"}
            for k, v in row.items():
                if k not in consumed and v:
                    product[k] = v
            if product.get("sku"):
                look["products"].append(product)

    # Conflict check: refuse to silently overwrite existing look files.
    ld = looks_dir(shoot_id)
    conflicts = [lid for lid in looks if (ld / f"{lid}.md").exists()]
    if conflicts:
        sys.exit(
            f"Conflict: {len(conflicts)} look file(s) already exist for shoot "
            f"'{shoot_id}': {', '.join(conflicts)}.\n"
            "Delete the existing look files before re-ingesting, or use the "
            "agent (/ingest-shoot) which shows a proposal and confirms before writing."
        )

    created = 0
    with_images = 0
    for look_id, look in looks.items():
        write_look_file(ld / f"{look_id}.md", look)
        created += 1
        if (images_dir(shoot_id) / look_id).is_dir():
            with_images += 1

    log(f"INGEST {shoot_id}: {created} look files created from {src.name}. "
        f"{with_images} with matching image folders.")
    print(f"Ingested {shoot_id}: {created} look(s), {with_images} with image folders ready.")


def tag_one_look(shoot_id: str, look: dict) -> int:
    look_id = look["look_id"]
    folder = images_dir(shoot_id) / look_id
    if not folder.is_dir():
        return 0
    images = mt.list_images(folder)
    if not images:
        return 0

    tagged = 0
    for seq, img in enumerate(images, start=1):
        result = mt.embed_look_data(
            path=img, look_id=look_id, shoot_id=shoot_id, image_seq=seq,
            products=look.get("products", []),
            rights=look.get("rights") or effective_rights(look),
            theme=look.get("theme", ""), notes=look.get("notes", ""),
        )
        tagged += 1
        # Verify the write landed
        meta = mt.read_metadata(img)
        if meta.get("XMP:LookId") != look_id and meta.get("XMP-editorialOS:LookId") != look_id \
           and not any(str(v) == look_id for k, v in meta.items() if "LookId" in k):
            log(f"INTEGRITY_FAIL {result['tracking_id']}: embedded lookId not "
                f"read back from {img}", decision=True)

    look["status"] = "tagged"
    look["images_tagged"] = tagged
    write_look_file(looks_dir(shoot_id) / f"{look_id}.md", look)
    ids = f"{look_id}_001..{look_id}_{tagged:03d}" if tagged > 1 else f"{look_id}_001"
    log(f"TAG {look_id}: {tagged} images embedded ({ids}).")
    return tagged


def effective_rights(look: dict) -> str:
    """Most restrictive product rights wins. editorial < commercial < all."""
    order = {"editorial": 0, "commercial": 1, "all": 2}
    rights = [p.get("rights", "editorial") for p in look.get("products", [])]
    rights = [r for r in rights if r in order] or ["editorial"]
    return min(rights, key=lambda r: order[r])


def cmd_tag_shoot(shoot_id: str):
    total_looks = total_images = 0
    for look in all_looks(shoot_id):
        if look.get("status") != "untagged":
            continue
        n = tag_one_look(shoot_id, look)
        if n:
            total_looks += 1
            total_images += n
    print(f"Tagged {shoot_id}: {total_looks} look(s), {total_images} image(s).")


def cmd_tag_look(look_id: str):
    for shoot_dir in sorted(SHOOTS.iterdir()) if SHOOTS.is_dir() else []:
        lf = shoot_dir / "looks" / f"{look_id}.md"
        if lf.is_file():
            look = read_look_file(lf)
            n = tag_one_look(shoot_dir.name, look)
            print(f"Tagged {look_id}: {n} image(s).")
            return
    sys.exit(f"Look not found: {look_id}")


def cmd_audit(shoot_id: str):
    looks = all_looks(shoot_id)
    look_ids = {l["look_id"] for l in looks}
    flags = 0

    # Orphans: images outside any look folder, or in unmatched folders
    img_root = images_dir(shoot_id)
    if img_root.is_dir():
        for img in mt.list_images(img_root):
            rel = Path(img).relative_to(img_root)
            top = rel.parts[0] if len(rel.parts) > 1 else None
            if top is None or top not in look_ids:
                fp = mt.compute_fingerprint(img)
                log(f"ORPHAN {img}: no matching look. MD5 {fp['file_md5']}, "
                    f"{fp['image_size']}. Assign to a look or discard.", decision=True)
                flags += 1

    # Missing images / needs_review / rights checks / expirations
    today = date.today()
    for look in looks:
        lid = look["look_id"]
        if look.get("status") == "untagged" and not (img_root / lid).is_dir():
            log(f"MISSING_IMAGES {lid}: look file exists, no image folder.", decision=True)
            flags += 1
        if str(look.get("needs_review", "")).lower() == "true":
            log(f"NEEDS_REVIEW {lid}: contains inferred fields awaiting human "
                f"confirmation. Review the look file.", decision=True)
            flags += 1
        rights_set = {p.get("rights") for p in look.get("products", []) if p.get("rights")}
        if len(rights_set) > 1:
            log(f"MIXED_RIGHTS {lid}: {sorted(rights_set)} — most restrictive "
                f"({effective_rights(look)}) applies to the image.", decision=True)
            flags += 1
        for p in look.get("products", []):
            if p.get("type") == "rental" and not p.get("available_date"):
                log(f"RENTAL_NO_DATE {lid}: SKU {p.get('sku')} is rental with no "
                    f"available_date.", decision=True)
                flags += 1
            ad = p.get("available_date", "")
            if ad:
                try:
                    d = datetime.strptime(ad, "%Y-%m-%d").date()
                    if d < today:
                        level = "RENTAL_EXPIRED"
                    elif d <= today + timedelta(days=30):
                        level = "RENTAL_URGENT"
                    elif d <= today + timedelta(days=90):
                        level = "RENTAL_WARNING"
                    else:
                        level = None
                    if level:
                        log(f"{level} {lid}: SKU {p.get('sku')} available_date {ad}.",
                            decision=True)
                        flags += 1
                except ValueError:
                    pass
        if look.get("status") == "tagged" and flags == 0:
            look["status"] = "audited"
            write_look_file(looks_dir(shoot_id) / f"{lid}.md", look)

    log(f"AUDIT {shoot_id}: {len(looks)} looks checked, {flags} flags.")
    print(f"Audit {shoot_id}: {len(looks)} look(s) checked, {flags} flag(s). "
          f"{'See decision_log.md.' if flags else 'Clean.'}")


def cmd_archive(shoot_id: str):
    looks = all_looks(shoot_id)
    untagged = [l["look_id"] for l in looks if l.get("status") == "untagged"]
    if untagged:
        sys.exit(f"Refusing to archive: {len(untagged)} untagged look(s): "
                 f"{', '.join(untagged)}")
    for look in looks:
        look["status"] = "archived"
        write_look_file(looks_dir(shoot_id) / f"{look['look_id']}.md", look)
    dest = ARCHIVE / shoot_id
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    shutil.move(str(SHOOTS / shoot_id), str(dest))
    log(f"ARCHIVE {shoot_id}: closed, {len(looks)} looks. Moved to {dest}.")
    print(f"Archived {shoot_id} → {dest}")


def cmd_find_image(tracking_id: str):
    m = re.match(r"(.+)_(\d{3})$", tracking_id)
    if not m:
        sys.exit(f"Tracking ID format not recognized: {tracking_id}")
    look_id, seq = m.group(1), int(m.group(2))
    for base in [SHOOTS, ARCHIVE]:
        if not base.is_dir():
            continue
        for shoot_dir in sorted(base.iterdir()):
            folder = shoot_dir / "images" / look_id
            if folder.is_dir():
                images = mt.list_images(folder)
                if seq <= len(images):
                    img = images[seq - 1]
                    meta = mt.read_metadata(img)
                    print(f"Found: {img}")
                    for k in sorted(meta):
                        if "editorialOS" in k or k.startswith("XMP:") and any(
                                t in k for t in ["Identifier", "Rights", "Subject"]):
                            print(f"  {k}: {meta[k]}")
                    return
    sys.exit(f"No image found for {tracking_id}")


def cmd_find_product(sku: str):
    hits = 0
    for base in [SHOOTS, ARCHIVE]:
        if not base.is_dir():
            continue
        for shoot_dir in sorted(base.iterdir()):
            ld = shoot_dir / "looks"
            if not ld.is_dir():
                continue
            for lf in sorted(ld.glob("*.md")):
                look = read_look_file(lf)
                if any(p.get("sku") == sku for p in look.get("products", [])):
                    hits += 1
                    print(f"{look['look_id']} — shoot {look.get('shoot')}, "
                          f"theme '{look.get('theme','')}', status {look.get('status')}, "
                          f"rights {effective_rights(look)}, "
                          f"{look.get('images_tagged',0)} image(s)")
    if not hits:
        print(f"No looks contain SKU {sku}.")


def cmd_watch_once():
    """One pass of the overnight watcher: tag anything taggable, audit shoots
    that changed. Schedule via cron for autonomous operation.

    Uses a PID-based lock file (work/.watch.lock) to prevent two overlapping
    cron invocations from tagging the same looks concurrently."""
    WORK.mkdir(parents=True, exist_ok=True)

    # Acquire lock — check for a running prior instance
    if WATCH_LOCK.exists():
        try:
            lock_data = json.loads(WATCH_LOCK.read_text(encoding="utf-8"))
            prior_pid = lock_data.get("pid")
            # Check if the PID is still alive (POSIX: signal 0 = existence check)
            try:
                os.kill(prior_pid, 0)
                # PID exists — another watch-once is running
                print(f"watch-once already running (PID {prior_pid}). Skipping.")
                return
            except (ProcessLookupError, TypeError):
                # PID is gone — stale lock, safe to overwrite
                pass
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt or unreadable lock — overwrite it

    lock_info = json.dumps({"pid": os.getpid(),
                            "started": datetime.now().isoformat()})
    WATCH_LOCK.write_text(lock_info, encoding="utf-8")

    try:
        if not SHOOTS.is_dir():
            print("No shoots.")
            return
        for shoot_dir in sorted(SHOOTS.iterdir()):
            shoot_id = shoot_dir.name
            changed = 0
            for look in all_looks(shoot_id):
                if look.get("status") == "untagged":
                    changed += tag_one_look(shoot_id, look)
            if changed:
                cmd_audit(shoot_id)
        log("WATCH: pass complete.")
        print("Watch pass complete.")
    finally:
        try:
            WATCH_LOCK.unlink()
        except OSError:
            pass


# ── Entry ───────────────────────────────────────────────────────────

COMMANDS = {
    "ingest-shoot": (cmd_ingest, 2),
    "tag-shoot": (cmd_tag_shoot, 1),
    "tag-look": (cmd_tag_look, 1),
    "audit-shoot": (cmd_audit, 1),
    "archive-shoot": (cmd_archive, 1),
    "find-image": (cmd_find_image, 1),
    "find-product": (cmd_find_product, 1),
    "watch-once": (cmd_watch_once, 0),
}

if __name__ == "__main__":
    argv = list(sys.argv[1:])
    if argv:
        argv[0] = argv[0].lstrip("/")  # accept both `tag-shoot` and `/tag-shoot`
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    fn, nargs = COMMANDS[argv[0]]
    if len(argv) - 1 < nargs:
        sys.exit(f"{argv[0]} requires {nargs} argument(s). See --help.")
    fn(*argv[1:1 + nargs])
