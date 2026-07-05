"""
Photo Editor — metadata_tools
Stdlib-only ExifTool wrapper for the deterministic CLI (runtime.py).
Mirrors the MCP server's behavior: same namespace config, same backup
policy, same fields. No third-party dependencies.
"""

import os
import json
import hashlib
import shutil
import subprocess
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".psd", ".dng", ".cr2", ".nef", ".arw"}

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
EXIFTOOL_CONFIG = PLUGIN_ROOT / "exiftool" / "editorialos.config"


def exiftool_bin() -> str:
    return os.environ.get("EXIFTOOL_PATH") or shutil.which("exiftool") or "exiftool"


def run_exiftool(args, use_config=False) -> str:
    cmd = [exiftool_bin()]
    if use_config:
        cmd += ["-config", str(EXIFTOOL_CONFIG)]
    cmd += args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 and result.stderr.strip() and not result.stdout.strip():
        raise RuntimeError(f"ExifTool error: {result.stderr.strip()}")
    return result.stdout.strip()


def is_image(path) -> bool:
    p = Path(path)
    return p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.endswith("_original")


def has_backup(path) -> bool:
    return os.path.isfile(str(path) + "_original")


def list_images(folder, recursive=True):
    folder = str(folder)
    images = []
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if is_image(fpath):
                    images.append(fpath)
    else:
        for fname in sorted(os.listdir(folder)):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath) and is_image(fpath):
                images.append(fpath)
    return images


def read_metadata(path) -> dict:
    raw = run_exiftool(["-json", "-G", "-n", str(path)], use_config=True)
    data = json.loads(raw)
    return data[0] if data else {}


def compute_fingerprint(path) -> dict:
    file_hash = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            file_hash.update(chunk)
    try:
        size = run_exiftool(["-s3", "-ImageSize", str(path)])
    except Exception:
        size = "unknown"
    return {"file_md5": file_hash.hexdigest(), "image_size": size,
            "file_size": os.path.getsize(path), "path": str(path)}


def embed_look_data(path, look_id, shoot_id, image_seq, products, rights, theme="", notes="") -> dict:
    """Embed full look data into one image. First tag preserves _original."""
    path = str(path)
    tracking_id = f"{look_id}_{image_seq:03d}"
    sku_list = [p["sku"] for p in products]
    descriptions = [p.get("description", "") for p in products if p.get("description")]
    product_types = sorted({p.get("type", "unknown") for p in products})
    available_dates = [p.get("available_date", "") for p in products if p.get("available_date")]

    rights_detail = f"{rights} use"
    if product_types:
        rights_detail += f" | {', '.join(product_types)}"

    args = []
    backup_created = not has_backup(path)
    if not backup_created:
        args.append("-overwrite_original")

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

    args.append(f"-XMP-editorialOS:lookId={look_id}")
    args.append(f"-XMP-editorialOS:shootId={shoot_id}")
    args.append(f"-XMP-editorialOS:trackingId={tracking_id}")
    args.append(f"-XMP-editorialOS:skus={','.join(sku_list)}")
    args.append(f"-XMP-editorialOS:productTypes={','.join(product_types)}")
    args.append(f"-XMP-editorialOS:rights={rights}")
    if theme:
        args.append(f"-XMP-editorialOS:theme={theme}")
    if available_dates:
        args.append(f"-XMP-editorialOS:availableDates={','.join(available_dates)}")
    if notes:
        args.append(f"-XMP-editorialOS:notes={notes}")
    args.append(f"-XMP-editorialOS:productData={json.dumps(products, ensure_ascii=False)}")

    args.append(path)
    run_exiftool(args, use_config=True)

    return {"tracking_id": tracking_id, "skus": sku_list,
            "rights": rights_detail, "backup_created": backup_created}
