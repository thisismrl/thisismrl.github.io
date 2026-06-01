import sqlite3
from datetime import datetime

from config import DATABASE_PATH, ensure_runtime_files


SCHEMA = {
    "collections": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "slug": "TEXT UNIQUE NOT NULL",
        "title": "TEXT NOT NULL",
        "subtitle": "TEXT",
        "description": "TEXT",
        "year": "TEXT",
        "location": "TEXT",
        "cover_photo_id": "INTEGER",
        "is_featured": "INTEGER DEFAULT 0",
        "sort_order": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "timelines": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "slug": "TEXT UNIQUE NOT NULL",
        "title": "TEXT NOT NULL",
        "description": "TEXT",
        "year": "TEXT",
        "location": "TEXT",
        "cover_photo_id": "INTEGER",
        "sort_order": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "photos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "collection_id": "INTEGER NOT NULL",
        "timeline_id": "INTEGER",
        "filename": "TEXT NOT NULL",
        "display_filename": "TEXT",
        "cover_filename": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "shot_date": "TEXT",
        "location": "TEXT",
        "sort_order": "INTEGER DEFAULT 0",
        "is_featured": "INTEGER DEFAULT 0",
        "featured_order": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "articles": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "slug": "TEXT UNIQUE NOT NULL",
        "title": "TEXT NOT NULL",
        "category": "TEXT NOT NULL",
        "summary": "TEXT",
        "content_markdown": "TEXT",
        "content_html": "TEXT",
        "cover_image": "TEXT",
        "status": "TEXT DEFAULT 'draft'",
        "published_at": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "settings": {
        "key": "TEXT PRIMARY KEY",
        "value": "TEXT",
    },
}


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    ensure_runtime_files()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    ensure_runtime_files()
    with get_db() as conn:
        for table, columns in SCHEMA.items():
            column_sql = ", ".join(f"{name} {definition}" for name, definition in columns.items())
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({column_sql})")
            existing = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for name, definition in columns.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
        conn.commit()
