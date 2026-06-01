from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

from config import COVERS_DIR, DISPLAY_DIR, ORIGINALS_DIR


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def allowed_image(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage):
    original_name = secure_filename(file_storage.filename or "")
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported image format.")

    stem = f"{uuid4().hex}"
    original_filename = f"{stem}{suffix}"
    display_filename = f"{stem}.webp"
    cover_filename = f"{stem}-cover.webp"

    original_path = ORIGINALS_DIR / original_filename
    file_storage.save(original_path)

    with Image.open(original_path) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")
        _save_webp(image, DISPLAY_DIR / display_filename, max_width=1800, quality=82)
        _save_webp(image, COVERS_DIR / cover_filename, max_width=2400, quality=86)

    return {
        "filename": original_filename,
        "display_filename": display_filename,
        "cover_filename": cover_filename,
    }


def _save_webp(image, path, max_width, quality):
    output = image.copy()
    if output.width > max_width:
        ratio = max_width / output.width
        height = int(output.height * ratio)
        output = output.resize((max_width, height), Image.Resampling.LANCZOS)
    output.save(path, "WEBP", quality=quality, method=6)
