from config import COVERS_DIR, DISPLAY_DIR, ORIGINALS_DIR, ensure_runtime_files
from db import get_db, init_db


DEMO_PREFIX = "demo-"


def remove_file(directory, filename):
    if filename:
        path = directory / filename
        if path.exists():
            path.unlink()


def clear_demo():
    ensure_runtime_files()
    init_db()
    with get_db() as conn:
        photos = conn.execute(
            "SELECT filename, display_filename, cover_filename FROM photos WHERE filename LIKE ?",
            (f"{DEMO_PREFIX}%",),
        ).fetchall()
        for photo in photos:
            remove_file(ORIGINALS_DIR, photo["filename"])
            remove_file(DISPLAY_DIR, photo["display_filename"])
            remove_file(COVERS_DIR, photo["cover_filename"])

        demo_collection_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM collections WHERE slug LIKE ?",
                (f"{DEMO_PREFIX}%",),
            ).fetchall()
        ]
        for collection_id in demo_collection_ids:
            conn.execute("DELETE FROM photos WHERE collection_id = ?", (collection_id,))
        conn.execute("DELETE FROM collections WHERE slug LIKE ?", (f"{DEMO_PREFIX}%",))
        conn.execute("DELETE FROM articles WHERE slug LIKE ?", (f"{DEMO_PREFIX}%",))
        conn.commit()
    print("Demo content removed.")


if __name__ == "__main__":
    clear_demo()
