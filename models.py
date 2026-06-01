from db import get_db, now_iso


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def get_setting(key, default=""):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def all_settings():
    defaults = {
        "site_name": "龍梓洋｜Charles Long",
        "tagline": "摄影、文字与个人档案。",
        "about_text": "",
        "contact_email": "",
        "instagram": "",
        "xiaohongshu": "",
        "github": "",
    }
    with get_db() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    settings = defaults.copy()
    settings.update({row["key"]: row["value"] for row in rows})
    return settings


def collection_list(featured=None):
    sql = (
        "SELECT c.*, p.cover_filename, p.display_filename "
        "FROM collections c "
        "LEFT JOIN photos p ON p.id = c.cover_photo_id "
    )
    params = []
    if featured is not None:
        sql += "WHERE c.is_featured = ? "
        params.append(1 if featured else 0)
    sql += "ORDER BY c.sort_order ASC, c.year DESC, c.created_at DESC"
    with get_db() as conn:
        return rows_to_dicts(conn.execute(sql, params).fetchall())


def timeline_list():
    sql = (
        "SELECT t.*, p.cover_filename, p.display_filename "
        "FROM timelines t "
        "LEFT JOIN photos p ON p.id = t.cover_photo_id "
        "ORDER BY t.sort_order ASC, t.year DESC, t.created_at DESC"
    )
    with get_db() as conn:
        return rows_to_dicts(conn.execute(sql).fetchall())


def get_collection(collection_id):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone())


def get_timeline(timeline_id):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM timelines WHERE id = ?", (timeline_id,)).fetchone())


def get_collection_by_slug(slug):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM collections WHERE slug = ?", (slug,)).fetchone())


def get_timeline_by_slug(slug):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM timelines WHERE slug = ?", (slug,)).fetchone())


def save_collection(data, collection_id=None):
    timestamp = now_iso()
    values = {
        "slug": data.get("slug", "").strip(),
        "title": data.get("title", "").strip(),
        "subtitle": data.get("subtitle", "").strip(),
        "description": data.get("description", "").strip(),
        "year": data.get("year", "").strip(),
        "location": data.get("location", "").strip(),
        "cover_photo_id": data.get("cover_photo_id") or None,
        "is_featured": 1 if data.get("is_featured") else 0,
        "sort_order": int(data.get("sort_order") or 0),
        "updated_at": timestamp,
    }
    with get_db() as conn:
        if collection_id:
            assignments = ", ".join(f"{key} = ?" for key in values.keys())
            conn.execute(
                f"UPDATE collections SET {assignments} WHERE id = ?",
                [*values.values(), collection_id],
            )
        else:
            values["created_at"] = timestamp
            columns = ", ".join(values.keys())
            placeholders = ", ".join("?" for _ in values)
            conn.execute(
                f"INSERT INTO collections ({columns}) VALUES ({placeholders})",
                list(values.values()),
            )
        conn.commit()


def save_timeline(data, timeline_id=None):
    timestamp = now_iso()
    values = {
        "slug": data.get("slug", "").strip(),
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "year": data.get("year", "").strip(),
        "location": data.get("location", "").strip(),
        "cover_photo_id": data.get("cover_photo_id") or None,
        "sort_order": int(data.get("sort_order") or 0),
        "updated_at": timestamp,
    }
    with get_db() as conn:
        if timeline_id:
            assignments = ", ".join(f"{key} = ?" for key in values.keys())
            conn.execute(
                f"UPDATE timelines SET {assignments} WHERE id = ?",
                [*values.values(), timeline_id],
            )
        else:
            values["created_at"] = timestamp
            columns = ", ".join(values.keys())
            placeholders = ", ".join("?" for _ in values)
            conn.execute(
                f"INSERT INTO timelines ({columns}) VALUES ({placeholders})",
                list(values.values()),
            )
        conn.commit()


def delete_collection(collection_id):
    with get_db() as conn:
        conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        conn.execute("DELETE FROM photos WHERE collection_id = ?", (collection_id,))
        conn.commit()


def delete_timeline(timeline_id):
    with get_db() as conn:
        conn.execute("UPDATE photos SET timeline_id = NULL WHERE timeline_id = ?", (timeline_id,))
        conn.execute("DELETE FROM timelines WHERE id = ?", (timeline_id,))
        conn.commit()


def photo_list(collection_id=None, timeline_id=None, featured=None):
    sql = (
        "SELECT p.*, c.title AS collection_title, t.title AS timeline_title "
        "FROM photos p "
        "JOIN collections c ON c.id = p.collection_id "
        "LEFT JOIN timelines t ON t.id = p.timeline_id "
    )
    clauses = []
    params = []
    if collection_id:
        clauses.append("p.collection_id = ?")
        params.append(collection_id)
    if timeline_id:
        clauses.append("p.timeline_id = ?")
        params.append(timeline_id)
    if featured is not None:
        clauses.append("p.is_featured = ?")
        params.append(1 if featured else 0)
    if clauses:
        sql += "WHERE " + " AND ".join(clauses) + " "
    if featured is not None:
        sql += "ORDER BY p.featured_order ASC, p.sort_order ASC, p.shot_date DESC, p.created_at DESC"
    else:
        sql += "ORDER BY p.sort_order ASC, p.shot_date DESC, p.created_at DESC"
    with get_db() as conn:
        return rows_to_dicts(conn.execute(sql, params).fetchall())


def get_photo(photo_id):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone())


def save_photo(data, filenames=None, photo_id=None):
    timestamp = now_iso()
    values = {
        "collection_id": int(data.get("collection_id") or 0),
        "timeline_id": int(data.get("timeline_id")) if data.get("timeline_id") else None,
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "shot_date": data.get("shot_date", "").strip(),
        "location": data.get("location", "").strip(),
        "sort_order": int(data.get("sort_order") or 0),
        "is_featured": 1 if data.get("is_featured") else 0,
        "featured_order": int(data.get("featured_order") or 0),
        "updated_at": timestamp,
    }
    if filenames:
        values.update(filenames)
    with get_db() as conn:
        if photo_id:
            assignments = ", ".join(f"{key} = ?" for key in values.keys())
            conn.execute(f"UPDATE photos SET {assignments} WHERE id = ?", [*values.values(), photo_id])
            saved_id = photo_id
        else:
            values["created_at"] = timestamp
            columns = ", ".join(values.keys())
            placeholders = ", ".join("?" for _ in values)
            cursor = conn.execute(f"INSERT INTO photos ({columns}) VALUES ({placeholders})", list(values.values()))
            saved_id = cursor.lastrowid
        conn.commit()
        return saved_id


def max_photo_sort_order(collection_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) AS n FROM photos WHERE collection_id = ?",
            (collection_id,),
        ).fetchone()
        return row["n"] if row else 0


def save_home_slideshow(selected_ids, order_map):
    selected_ids = {int(photo_id) for photo_id in selected_ids if str(photo_id).strip()}
    with get_db() as conn:
        conn.execute("UPDATE photos SET is_featured = 0, featured_order = 0")
        for photo_id in selected_ids:
            conn.execute(
                "UPDATE photos SET is_featured = 1, featured_order = ? WHERE id = ?",
                (int(order_map.get(str(photo_id)) or 0), photo_id),
            )
        conn.commit()


def delete_photo(photo_id):
    with get_db() as conn:
        conn.execute("UPDATE collections SET cover_photo_id = NULL WHERE cover_photo_id = ?", (photo_id,))
        conn.execute("UPDATE timelines SET cover_photo_id = NULL WHERE cover_photo_id = ?", (photo_id,))
        conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()


def save_photo_batch(photo_updates):
    with get_db() as conn:
        for photo_id, data in photo_updates.items():
            conn.execute(
                "UPDATE photos SET title = ?, description = ?, timeline_id = ?, sort_order = ?, is_featured = ?, featured_order = ?, updated_at = ? WHERE id = ?",
                (
                    data.get("title", "").strip(),
                    data.get("description", "").strip(),
                    int(data.get("timeline_id")) if data.get("timeline_id") else None,
                    int(data.get("sort_order") or 0),
                    1 if data.get("is_featured") else 0,
                    int(data.get("featured_order") or 0),
                    now_iso(),
                    int(photo_id),
                ),
            )
        conn.commit()


def article_list(status=None, limit=None):
    sql = "SELECT * FROM articles "
    params = []
    if status:
        sql += "WHERE status = ? "
        params.append(status)
    sql += "ORDER BY published_at DESC, created_at DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    with get_db() as conn:
        return rows_to_dicts(conn.execute(sql, params).fetchall())


def get_article(article_id):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone())


def get_article_by_slug(slug):
    with get_db() as conn:
        return row_to_dict(conn.execute("SELECT * FROM articles WHERE slug = ? AND status = 'published'", (slug,)).fetchone())


def save_article(data, content_html, article_id=None):
    timestamp = now_iso()
    values = {
        "slug": data.get("slug", "").strip(),
        "title": data.get("title", "").strip(),
        "category": data.get("category", "Essay").strip(),
        "summary": data.get("summary", "").strip(),
        "content_markdown": data.get("content_markdown", "").strip(),
        "content_html": content_html,
        "cover_image": data.get("cover_image", "").strip(),
        "status": data.get("status", "draft").strip(),
        "published_at": data.get("published_at", "").strip(),
        "updated_at": timestamp,
    }
    with get_db() as conn:
        if article_id:
            assignments = ", ".join(f"{key} = ?" for key in values.keys())
            conn.execute(f"UPDATE articles SET {assignments} WHERE id = ?", [*values.values(), article_id])
        else:
            values["created_at"] = timestamp
            columns = ", ".join(values.keys())
            placeholders = ", ".join("?" for _ in values)
            conn.execute(f"INSERT INTO articles ({columns}) VALUES ({placeholders})", list(values.values()))
        conn.commit()


def delete_article(article_id):
    with get_db() as conn:
        conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        conn.commit()


def dashboard_counts():
    with get_db() as conn:
        return {
            "collections": conn.execute("SELECT COUNT(*) AS n FROM collections").fetchone()["n"],
            "timelines": conn.execute("SELECT COUNT(*) AS n FROM timelines").fetchone()["n"],
            "photos": conn.execute("SELECT COUNT(*) AS n FROM photos").fetchone()["n"],
            "published": conn.execute("SELECT COUNT(*) AS n FROM articles WHERE status = 'published'").fetchone()["n"],
            "drafts": conn.execute("SELECT COUNT(*) AS n FROM articles WHERE status = 'draft'").fetchone()["n"],
        }
