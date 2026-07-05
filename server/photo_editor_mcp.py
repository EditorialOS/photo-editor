"""
Photo Editor MCP Server
Wraps ExifTool for deterministic image metadata operations.

Tools:
  read_metadata(path)          → dict of all metadata
  write_xmp(path, ...)         → write XMP fields (standard or editorialOS namespace)
  embed_look_data(path, look)  → embed full look data in one call (the main tool)
  compute_fingerprint(path)    → file MD5 + dimensions for dedup and orphan matching
  list_images(folder)          → list image paths recursively (skips _original backups)

Design notes:
  - The editorialOS XMP namespace is defined once in exiftool/editorialos.config
    (checked into the repo). It is never regenerated at runtime.
  - First tag of an image preserves an ExifTool `_original` backup ("zero data
    loss"). Re-tags overwrite in place — one backup per image, the pristine
    untagged file, not a stack.
  - This server makes no creative judgments. It reads, writes, and reports.

Requires: ExifTool installed on the host (https://exiftool.org)
"""

import os
import json
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# ── Server ──────────────────────────────────────────────────────────

mcp = FastMCP("photo-editor")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".psd", ".dng", ".cr2", ".nef", ".arw"}

# Persistent namespace config, shipped with the plugin
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
EXIFTOOL_CONFIG = PLUGIN_ROOT / "exiftool" / "editorialos.config"

# Standard namespaces ExifTool knows without our config
STANDARD_NAMESPACES = {"dc", "xmp", "xmprights", "photoshop", "iptc4xmpcore", "iptc"}

# Rights precedence: lower index = more restrictive
_RIGHTS_ORDER = {"editorial": 0, "commercial": 1, "all": 2}


# ── Helpers ─────────────────────────────────────────────────────────

def _exiftool_bin() -> str:
    """Locate exiftool, honoring EXIFTOOL_PATH for non-standard installs."""
    return os.environ.get("EXIFTOOL_PATH") or shutil.which("exiftool") or "exiftool"


def _run_exiftool(args: list[str], use_config: bool = False) -> str:
    """Run exiftool as a subprocess and return stdout."""
    cmd = [_exiftool_bin()]
    if use_config:
        if not EXIFTOOL_CONFIG.is_file():
            raise RuntimeError(
                f"Namespace config not found at {EXIFTOOL_CONFIG}. "
                "The plugin install may be incomplete — run /setup."
            )
        cmd += ["-config", str(EXIFTOOL_CONFIG)]
    cmd += args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 and result.stderr.strip():
        # ExifTool writes warnings to stderr but still succeeds for many ops.
        # Only raise if there's no stdout at all.
        if not result.stdout.strip():
            raise RuntimeError(f"ExifTool error: {result.stderr.strip()}")
    return result.stdout.strip()


def _is_image(path: str) -> bool:
    p = Path(path)
    return p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.endswith("_original")


def _has_backup(path: str) -> bool:
    """True if ExifTool's `_original` backup already exists for this file."""
    return os.path.isfile(path + "_original")


def _effective_rights(products: list[dict], caller_rights: str) -> tuple[str, bool]:
    """Return the most restrictive rights value across all products.

    If products carry per-product rights that differ from each other or from
    the caller-supplied value, the most restrictive wins and rights_resolved
    is True. This mirrors the CLI runtime's effective_rights() logic so the
    MCP server is safe to call even when the agent passes an unresolved value.

    Returns (resolved_rights, was_resolved) where was_resolved is True when
    the caller value was overridden by a stricter per-product right.
    """
    product_rights = [p.get("rights", "") for p in products if p.get("rights")]
    known = [r for r in product_rights if r in _RIGHTS_ORDER]
    if not known:
        return caller_rights, False
    most_restrictive = min(known, key=lambda r: _RIGHTS_ORDER[r])
    caller_known = caller_rights if caller_rights in _RIGHTS_ORDER else None
    if caller_known is None:
        return most_restrictive, True
    effective = min([caller_known, most_restrictive], key=lambda r: _RIGHTS_ORDER[r])
    return effective, (effective != caller_rights)


# ── Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def read_metadata(path: str) -> dict[str, Any]:
    """
    Read all metadata from an image file.
    Returns a dict of tag → value for EXIF, IPTC, XMP (including the
    editorialOS namespace), and file-level metadata.

    Args:
        path: Absolute path to the image file
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not _is_image(path):
        raise ValueError(f"Not a recognized image file: {path}")

    raw = _run_exiftool(["-json", "-G", "-n", path], use_config=True)
    data = json.loads(raw)
    return data[0] if data else {}


@mcp.tool()
def write_xmp(path: str, namespace: str, fields: dict[str, str]) -> dict[str, Any]:
    """
    Write XMP fields to an image file.

    Supported namespaces: the standard set (dc, xmp, xmpRights, photoshop,
    Iptc4xmpCore, iptc) and the plugin's own 'editorialOS' namespace.
    Arbitrary custom namespaces are NOT supported — ExifTool requires each
    custom tag to be pre-declared in a config file, and only editorialOS
    is declared. For editorialOS, valid fields are: lookId, shootId,
    trackingId, skus, productTypes, rights, theme, availableDates,
    productData, notes.

    Preserves an ExifTool `_original` backup on the first write to a file.

    Args:
        path: Absolute path to the image file
        namespace: XMP namespace prefix ('dc', 'editorialOS', ...)
        fields: Dict of field_name → value to write
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not fields:
        raise ValueError("No fields provided")

    ns_lower = namespace.lower()
    is_custom = ns_lower == "editorialos"
    if not is_custom and ns_lower not in STANDARD_NAMESPACES:
        raise ValueError(
            f"Unsupported namespace '{namespace}'. Use a standard namespace "
            f"({', '.join(sorted(STANDARD_NAMESPACES))}) or 'editorialOS'."
        )

    args = []
    # First write keeps the untagged original; re-writes don't stack backups.
    backup_will_be_created = not _has_backup(path)
    if not backup_will_be_created:
        args.append("-overwrite_original")

    ns_tag = "editorialOS" if is_custom else namespace
    for field, value in fields.items():
        args.append(f"-XMP-{ns_tag}:{field}={value}")

    args.append(path)
    output = _run_exiftool(args, use_config=is_custom)

    return {
        "status": "ok",
        "fields_written": len(fields),
        "backup_created": backup_will_be_created,
        "output": output,
    }


@mcp.tool()
def embed_look_data(
    path: str,
    look_id: str,
    shoot_id: str,
    image_seq: int,
    products: list[dict],
    rights: str,
    theme: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """
    Embed full look data into an image in one call.
    Sets standard XMP/IPTC fields plus the custom editorialOS namespace,
    including a full productData JSON payload so granular product info
    travels inside the file.

    The first tag of an image preserves an ExifTool `_original` backup
    (the pristine untagged file). Re-tags overwrite in place.

    Mixed-rights resolution: if products carry per-product rights values
    that are more restrictive than the caller-supplied `rights`, the most
    restrictive value is used automatically. The return dict includes
    `rights_resolved: true` when this override occurs so the agent can log it.
    Rights precedence: editorial (most restrictive) < commercial < all.

    This is the main tool for the tag_look skill. One call per image.

    Args:
        path: Absolute path to the image file
        look_id: The look identifier (e.g., AV_NG_F26_LOC_SUIT_1)
        shoot_id: The shoot identifier (e.g., F26_LOC)
        image_seq: Sequence number within the look (1, 2, 3...)
        products: List of product dicts. Required key: sku. Recognized keys:
            description, type, rights, available_date. Any additional keys
            are preserved in the embedded productData JSON.
        rights: Rights summary string (e.g., 'editorial', 'commercial', 'all').
            Per-product rights in the products list may tighten this further.
        theme: Optional theme/occasion (e.g., 'Wedding Party')
        notes: Optional notes
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not _is_image(path):
        raise ValueError(f"Not a recognized image file: {path}")

    # Resolve mixed rights — most restrictive product right wins
    effective_rights, rights_resolved = _effective_rights(products, rights)

    tracking_id = f"{look_id}_{image_seq:03d}"
    sku_list = [p["sku"] for p in products]
    descriptions = [p.get("description", "") for p in products if p.get("description")]

    rights_detail = f"{effective_rights} use"
    product_types = sorted({p.get("type", "unknown") for p in products})
    if product_types:
        rights_detail += f" | {', '.join(product_types)}"

    available_dates = [p.get("available_date", "") for p in products if p.get("available_date")]

    args = []
    backup_will_be_created = not _has_backup(path)
    if not backup_will_be_created:
        args.append("-overwrite_original")

    # ── Standard XMP/IPTC fields (readable by Bridge, Lightroom, any DAM) ──
    args.append(f"-XMP-dc:Identifier={tracking_id}")
    if descriptions:
        args.append(f"-XMP-dc:Description={'; '.join(descriptions)}")
    args.append(f"-XMP-dc:Rights={rights_detail}")
    for sku in sku_list:
        args.append(f"-XMP-dc:Subject+={sku}")
        args.append(f"-IPTC:Keywords+={sku}")
    if theme:
        args.append(f"-XMP-dc:Subject+={theme}")
        args.append(f"-IPTC:Keywords+={theme}")

    # ── Custom editorialOS namespace (defined in exiftool/editorialos.config) ──
    args.append(f"-XMP-editorialOS:lookId={look_id}")
    args.append(f"-XMP-editorialOS:shootId={shoot_id}")
    args.append(f"-XMP-editorialOS:trackingId={tracking_id}")
    args.append(f"-XMP-editorialOS:skus={','.join(sku_list)}")
    args.append(f"-XMP-editorialOS:productTypes={','.join(product_types)}")
    args.append(f"-XMP-editorialOS:rights={effective_rights}")
    if theme:
        args.append(f"-XMP-editorialOS:theme={theme}")
    if available_dates:
        args.append(f"-XMP-editorialOS:availableDates={','.join(available_dates)}")
    if notes:
        args.append(f"-XMP-editorialOS:notes={notes}")
    # Full product payload — granular spreadsheet columns travel in the file
    args.append(f"-XMP-editorialOS:productData={json.dumps(products, ensure_ascii=False)}")

    args.append(path)
    output = _run_exiftool(args, use_config=True)

    return {
        "status": "ok",
        "tracking_id": tracking_id,
        "shoot_id": shoot_id,
        "skus_embedded": sku_list,
        "rights": rights_detail,
        "rights_resolved": rights_resolved,
        "backup_created": backup_will_be_created,
        "output": output,
    }


@mcp.tool()
def compute_fingerprint(path: str) -> dict[str, Any]:
    """
    Compute an identity fingerprint of an image for dedup and orphan matching:
    file-level MD5 plus pixel dimensions.

    NOTE: This is exact-file matching, not perceptual hashing. A resized,
    re-exported, or re-compressed copy will NOT match. It reliably identifies
    byte-identical duplicates and pairs an orphan with its exact source.
    (Perceptual hashing is a planned v2 feature.)

    Args:
        path: Absolute path to the image file
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    file_hash = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            file_hash.update(chunk)

    try:
        raw_size = _run_exiftool(["-s3", "-ImageSize", path])
    except Exception:
        raw_size = "unknown"

    return {
        "file_md5": file_hash.hexdigest(),
        "image_size": raw_size,
        "file_size": os.path.getsize(path),
        "path": path,
        "method": "file_md5+dimensions (exact match only)",
    }


@mcp.tool()
def list_images(folder: str, recursive: bool = True) -> list[dict[str, Any]]:
    """
    List all recognized image files in a folder.
    Skips ExifTool `_original` backup files — they are pristine pre-tag
    copies, not shoot images, and must never be tagged or counted.

    Args:
        folder: Absolute path to the folder to scan
        recursive: Whether to scan subdirectories (default: True)
    """
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Directory not found: {folder}")

    def entry(fpath: str, base: str) -> dict[str, Any]:
        return {
            "path": fpath,
            "filename": os.path.basename(fpath),
            "extension": Path(fpath).suffix.lower(),
            "size_bytes": os.path.getsize(fpath),
            "relative_path": os.path.relpath(fpath, base),
        }

    images = []
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if _is_image(fpath):
                    images.append(entry(fpath, folder))
    else:
        for fname in sorted(os.listdir(folder)):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath) and _is_image(fpath):
                images.append(entry(fpath, folder))

    return images


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
