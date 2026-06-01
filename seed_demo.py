from pathlib import Path
import math
import random
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFilter

from config import COVERS_DIR, DISPLAY_DIR, ORIGINALS_DIR, ensure_runtime_files
from db import init_db, now_iso
from models import (
    collection_list,
    save_article,
    save_collection,
    save_photo,
)
from app import render_markdown


DEMO_PREFIX = "demo-"


def make_image(width, height, seed, display_name, cover_name, original_name):
    random.seed(seed)
    base = Image.new("RGB", (width, height), "#ece3df")
    pixels = base.load()
    for y in range(height):
        for x in range(width):
            drift = int(18 * math.sin((x + seed * 17) / 140) + 12 * math.cos((y + seed * 9) / 180))
            noise = random.randint(-5, 5)
            r = max(0, min(255, 236 + drift + noise))
            g = max(0, min(255, 226 + drift // 2 + noise))
            b = max(0, min(255, 222 + drift // 3 + noise))
            pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(base, "RGBA")
    for _ in range(8):
        x = random.randint(-width // 4, width)
        y = random.randint(-height // 4, height)
        w = random.randint(width // 8, width // 2)
        h = random.randint(height // 12, height // 3)
        color = random.choice([(255, 255, 255, 26), (180, 168, 160, 24), (210, 198, 190, 28)])
        draw.ellipse((x, y, x + w, y + h), fill=color)

    image = base.filter(ImageFilter.GaussianBlur(radius=1.1))
    image.save(ORIGINALS_DIR / original_name, "JPEG", quality=92)
    image.save(DISPLAY_DIR / display_name, "WEBP", quality=82)

    cover = image.copy()
    if cover.width > 2400:
        ratio = 2400 / cover.width
        cover = cover.resize((2400, int(cover.height * ratio)), Image.Resampling.LANCZOS)
    cover.save(COVERS_DIR / cover_name, "WEBP", quality=86)


def create_demo():
    ensure_runtime_files()
    init_db()

    if any(item["slug"].startswith(DEMO_PREFIX) for item in collection_list()):
        print("Demo content already exists.")
        return

    collections = [
        {
            "slug": "demo-river-light",
            "title": "River Light",
            "subtitle": "demo series",
            "description": "A demo photography series for checking the quiet rhythm of the Works pages.",
            "year": "2026",
            "location": "Shanghai",
            "is_featured": "1",
            "sort_order": "1",
        },
        {
            "slug": "demo-small-hours",
            "title": "Small Hours",
            "subtitle": "demo series",
            "description": "A second demo series with softer vertical images and more breathing space.",
            "year": "2025",
            "location": "Hangzhou",
            "is_featured": "1",
            "sort_order": "2",
        },
    ]

    for collection in collections:
        save_collection(collection)

    created = collection_list()
    by_slug = {item["slug"]: item for item in created}

    specs = [
        ("demo-river-light", 1500, 980),
        ("demo-river-light", 1200, 1600),
        ("demo-river-light", 1400, 1100),
        ("demo-small-hours", 1100, 1500),
        ("demo-small-hours", 1500, 1000),
        ("demo-small-hours", 1200, 1200),
    ]

    first_photo_id_by_collection = {}
    for index, (slug, width, height) in enumerate(specs, start=1):
        stem = f"{DEMO_PREFIX}{uuid4().hex}"
        original_name = f"{stem}.jpg"
        display_name = f"{stem}.webp"
        cover_name = f"{stem}-cover.webp"
        make_image(width, height, index, display_name, cover_name, original_name)
        collection = by_slug[slug]
        save_photo(
            {
                "collection_id": str(collection["id"]),
                "title": f"Demo image {index}",
                "description": "Generated placeholder for layout review.",
                "shot_date": f"2026-0{min(index, 9)}-01",
                "location": collection["location"],
                "sort_order": str(index),
                "is_featured": "1" if index in (1, 4) else "",
            },
            filenames={
                "filename": original_name,
                "display_filename": display_name,
                "cover_filename": cover_name,
            },
        )

    # Re-query photos through SQLite so collection cover IDs can be assigned.
    from db import get_db

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, collection_id FROM photos WHERE filename LIKE ? ORDER BY id ASC",
            (f"{DEMO_PREFIX}%",),
        ).fetchall()
        for row in rows:
            first_photo_id_by_collection.setdefault(row["collection_id"], row["id"])
        for collection_id, photo_id in first_photo_id_by_collection.items():
            conn.execute("UPDATE collections SET cover_photo_id = ? WHERE id = ?", (photo_id, collection_id))
        conn.commit()

    articles = [
        {
            "slug": "demo-essay-after-rain",
            "title": "After Rain",
            "category": "Essay",
            "summary": "A demo essay for checking literary text spacing.",
            "content_markdown": "The afternoon became quiet after the rain.\n\nThe street kept a thin layer of light, and every window looked briefly unfinished.\n\nI walked slowly, as if the city had lowered its voice.",
            "status": "published",
            "published_at": "2026-05-12",
        },
        {
            "slug": "demo-fiction-room",
            "title": "The Room at the End",
            "category": "Fiction",
            "summary": "A short fiction demo entry.",
            "content_markdown": "She kept the key in a blue envelope.\n\nNo one asked what it opened, which was perhaps why she never lost it.",
            "status": "published",
            "published_at": "2026-04-03",
        },
        {
            "slug": "demo-notes-window",
            "title": "Window Notes",
            "category": "Notes",
            "summary": "A fragment for checking the Notes category page.",
            "content_markdown": "Morning. Pale wall. A cup left too close to the edge.\n\nNothing happened, but the room changed anyway.",
            "status": "published",
            "published_at": "2026-03-18",
        },
    ]

    for article in articles:
        save_article(article, render_markdown(article["content_markdown"]))

    print("Demo content created.")


if __name__ == "__main__":
    create_demo()
