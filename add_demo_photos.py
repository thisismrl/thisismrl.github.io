from uuid import uuid4

from config import ensure_runtime_files
from db import get_db, init_db
from models import save_photo
from seed_demo import DEMO_PREFIX, make_image


def add_demo_photos():
    ensure_runtime_files()
    init_db()
    with get_db() as conn:
        collection = conn.execute(
            "SELECT id, location FROM collections WHERE slug = ?",
            ("demo-river-light",),
        ).fetchone()
        if not collection:
            print("demo-river-light not found. Run seed_demo.py first.")
            return
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM photos WHERE collection_id = ?",
            (collection["id"],),
        ).fetchone()["n"]
        if count >= 8:
            print("Demo series already has enough photos.")
            return

    specs = [
        (1600, 1060),
        (1120, 1680),
        (1500, 1200),
        (980, 1480),
        (1700, 980),
    ]
    start = count + 1
    for offset, (width, height) in enumerate(specs, start=0):
        index = start + offset
        stem = f"{DEMO_PREFIX}{uuid4().hex}"
        original_name = f"{stem}.jpg"
        display_name = f"{stem}.webp"
        cover_name = f"{stem}-cover.webp"
        make_image(width, height, 40 + index, display_name, cover_name, original_name)
        save_photo(
            {
                "collection_id": str(collection["id"]),
                "title": f"Demo image {index}",
                "description": "Additional generated placeholder for sequence review.",
                "shot_date": f"2026-06-{min(index, 28):02d}",
                "location": collection["location"],
                "sort_order": str(index),
                "is_featured": "",
            },
            filenames={
                "filename": original_name,
                "display_filename": display_name,
                "cover_filename": cover_name,
            },
        )
    print("Additional demo photos added.")


if __name__ == "__main__":
    add_demo_photos()
