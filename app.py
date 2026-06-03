import os
import re
from datetime import datetime
from pathlib import Path

import markdown
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from config import (
    BASE_DIR,
    COVERS_DIR,
    DISPLAY_DIR,
    ORIGINALS_DIR,
    read_admin_password,
    read_secret_key,
)
from db import get_db, init_db
from image_utils import save_uploaded_image
from models import (
    all_settings,
    article_list,
    collection_list,
    dashboard_counts,
    delete_article,
    delete_collection,
    delete_photo,
    get_article,
    get_article_by_slug,
    get_collection,
    get_collection_by_slug,
    get_photo,
    max_photo_sort_order,
    photo_list,
    save_article,
    save_collection,
    save_collection_order,
    save_home_slideshow,
    save_photo,
    save_photo_batch,
    set_setting,
)


app = Flask(__name__)
app.secret_key = read_secret_key()
init_db()

TEXT_CATEGORIES = ["Fiction", "Essay", "Notes", "Poem"]


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or datetime.now().strftime("%Y%m%d%H%M%S")


def render_markdown(text):
    return markdown.markdown(
        text or "",
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )


def render_article_markdown(text, category):
    extensions = ["extra", "sane_lists", "smarty"]
    if category == "Poem":
        extensions.append("nl2br")
    return markdown.markdown(text or "", extensions=extensions, output_format="html5")


def text_excerpt(text, length=120):
    plain = re.sub(r"[#>*_`~\-\[\]\(\)]", "", text or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= length:
        return plain
    return plain[:length].rstrip() + "..."


def normalize_article_data(form):
    data = form.to_dict()
    category = data.get("category", "Fiction").strip() or "Fiction"
    data["category"] = category
    data["status"] = data.get("status", "draft").strip() or "draft"
    data["content_markdown"] = data.get("content_markdown", "").strip()

    if not data.get("published_at") and data["status"] == "published":
        data["published_at"] = datetime.now().strftime("%Y-%m-%d")

    if category in {"Essay", "Notes", "Poem"}:
        data["cover_image"] = ""
        if not data.get("summary"):
            data["summary"] = text_excerpt(data["content_markdown"], 160)
        if not data.get("title"):
            date_label = data.get("published_at") or datetime.now().strftime("%Y-%m-%d")
            fallback_prefix = {"Essay": "Essay", "Notes": "Note", "Poem": "Poem"}.get(category, "Text")
            data["title"] = f"{fallback_prefix} {date_label}"
    elif not data.get("summary"):
        data["summary"] = text_excerpt(data["content_markdown"], 140)

    if not data.get("slug"):
        data["slug"] = slugify(data.get("title", ""))

    return data


def apply_article_cover_upload(data, files):
    if data.get("category") in {"Essay", "Notes", "Poem"}:
        data["cover_image"] = ""
        return data

    if data.get("clear_cover"):
        data["cover_image"] = ""

    cover_file = files.get("cover_upload")
    if cover_file and cover_file.filename:
        image_data = save_uploaded_image(cover_file)
        data["cover_image"] = f"/uploads/covers/{image_data['cover_filename']}"

    return data


def login_required(view):
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def remove_photo_files(photo):
    for directory, key in (
        (ORIGINALS_DIR, "filename"),
        (DISPLAY_DIR, "display_filename"),
        (COVERS_DIR, "cover_filename"),
    ):
        filename = photo.get(key)
        if filename:
            path = directory / filename
            if path.exists():
                path.unlink()


@app.context_processor
def inject_globals():
    return {"site_settings": all_settings(), "current_year": datetime.now().year}


@app.route("/uploads/display/<path:filename>")
def uploaded_display(filename):
    return send_from_directory(DISPLAY_DIR, filename)


@app.route("/uploads/covers/<path:filename>")
def uploaded_cover(filename):
    return send_from_directory(COVERS_DIR, filename)


@app.route("/")
def home():
    featured_collections = collection_list(featured=True)
    featured_photos = photo_list(featured=True)
    hero_photos = featured_photos[:8]
    if not hero_photos:
        for collection in featured_collections:
            cover_name = collection.get("cover_filename") or collection.get("display_filename")
            if cover_name:
                hero_photos.append({
                    "display_filename": cover_name,
                    "title": collection.get("title"),
                })
    return render_template(
        "home.html",
        hero_photos=hero_photos,
    )


@app.route("/news/")
def news():
    items = []
    for collection in collection_list():
        date = collection.get("updated_at") or collection.get("created_at") or collection.get("year") or ""
        image = ""
        if collection.get("cover_filename"):
            image = f"/uploads/covers/{collection['cover_filename']}"
        elif collection.get("display_filename"):
            image = f"/uploads/display/{collection['display_filename']}"
        items.append({
            "date": date,
            "kind": "Work",
            "title": collection["title"],
            "summary": collection.get("description") or "",
            "meta": collection.get("year") or "",
            "image": image,
            "url": url_for("work_detail", slug=collection["slug"]),
        })

    for article in article_list(status="published"):
        if article["category"] not in TEXT_CATEGORIES:
            continue
        date = article.get("published_at") or article.get("updated_at") or article.get("created_at") or ""
        items.append({
            "date": date,
            "kind": article["category"],
            "title": article["title"],
            "summary": article.get("summary") or "",
            "meta": date[:10],
            "image": article.get("cover_image") or "",
            "url": url_for("text_detail", slug=article["slug"]),
        })

    items.sort(key=lambda item: item["date"] or "", reverse=True)
    return render_template("news.html", items=items)


@app.route("/works/")
def works():
    return render_template(
        "works.html",
        collections=collection_list(show_in_series=True),
        travel_collections=collection_list(show_in_series=False),
    )


@app.route("/works/<slug>/")
def work_detail(slug):
    collection = get_collection_by_slug(slug)
    if not collection:
        abort(404)
    photos = photo_list(collection_id=collection["id"])
    return render_template(
        "work_detail.html",
        collection=collection,
        photos=photos,
        collections=collection_list(show_in_series=True),
        travel_collections=collection_list(show_in_series=False),
        active_mode="series",
    )


@app.route("/texts/")
def texts():
    articles = article_list(status="published")
    categories = TEXT_CATEGORIES
    grouped = {category: [a for a in articles if a["category"] == category] for category in categories}
    return render_template("texts.html", articles=articles, grouped=grouped, categories=categories, active_category="Fiction")


@app.route("/texts/fiction/")
@app.route("/texts/essay/")
@app.route("/texts/notes/")
@app.route("/texts/poem/")
def text_category():
    category_map = {
        "fiction": "Fiction",
        "essay": "Essay",
        "notes": "Notes",
        "poem": "Poem",
    }
    slug = request.path.strip("/").split("/")[-1]
    category = category_map.get(slug)
    if not category:
        abort(404)
    articles = article_list(status="published")
    categories = TEXT_CATEGORIES
    grouped = {item: [a for a in articles if a["category"] == item] for item in categories}
    return render_template("texts.html", articles=articles, grouped=grouped, categories=categories, active_category=category)


@app.route("/texts/<slug>/")
def text_detail(slug):
    article = get_article_by_slug(slug)
    if not article:
        abort(404)
    return render_template("text_detail.html", article=article)


@app.route("/archive/")
def archive():
    items = []
    for collection in collection_list():
        year = collection.get("year") or "Undated"
        items.append({
            "year": year,
            "kind": "Work",
            "title": collection["title"],
            "meta": collection.get("location") or "",
            "url": url_for("work_detail", slug=collection["slug"]),
        })
    for article in article_list(status="published"):
        if article["category"] not in TEXT_CATEGORIES:
            continue
        date = article.get("published_at") or article.get("created_at") or ""
        year = date[:4] if date else "Undated"
        items.append({
            "year": year,
            "kind": article["category"],
            "title": article["title"],
            "meta": date[:10],
            "url": url_for("text_detail", slug=article["slug"]),
        })
    items.sort(key=lambda item: item["year"], reverse=True)
    grouped = {}
    for item in items:
        grouped.setdefault(item["year"], []).append(item)
    return render_template("archive.html", grouped=grouped)


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/contact/")
def contact():
    return redirect(url_for("about"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password", "") == read_admin_password():
            session["admin_logged_in"] = True
            flash("已登录。", "success")
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("密码不正确。", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("已退出。", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin/")
@login_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        counts=dashboard_counts(),
        recent_collections=collection_list()[:5],
        recent_articles=article_list(limit=5),
    )


@app.route("/admin/collections")
@login_required
def admin_collections():
    return render_template(
        "admin/collections.html",
        travel_collections=collection_list(show_in_series=False),
        standalone_collections=collection_list(show_in_series=True),
    )


@app.route("/admin/collections/reorder", methods=["POST"])
@login_required
def admin_collections_reorder():
    collection_ids = request.form.getlist("collection_ids")
    label = request.form.get("order_label") or "作品集"
    if not collection_ids:
        flash("没有收到需要排序的作品集。", "error")
        return redirect(url_for("admin_collections"))
    save_collection_order(collection_ids)
    flash(f"{label}顺序已保存。", "success")
    return redirect(url_for("admin_collections"))


@app.route("/admin/collections/new", methods=["GET", "POST"])
@login_required
def admin_collection_new():
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("slug"):
            data["slug"] = slugify(data.get("title", ""))
        data["show_in_series"] = "" if request.form.get("in_travel_feature") else "1"
        try:
            save_collection(data)
            flash("作品集已创建。", "success")
            return redirect(url_for("admin_collections"))
        except Exception as exc:
            flash(f"无法保存作品集：{exc}", "error")
    return render_template("admin/collection_edit.html", collection={}, photos=[], is_new=True)


@app.route("/admin/collections/<int:collection_id>/edit", methods=["GET", "POST"])
@login_required
def admin_collection_edit(collection_id):
    collection = get_collection(collection_id)
    if not collection:
        abort(404)
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("slug"):
            data["slug"] = slugify(data.get("title", ""))
        data["show_in_series"] = "" if request.form.get("in_travel_feature") else "1"
        try:
            save_collection(data, collection_id=collection_id)
            flash("作品集已更新。", "success")
            return redirect(url_for("admin_collections"))
        except Exception as exc:
            flash(f"无法保存作品集：{exc}", "error")
    return render_template(
        "admin/collection_edit.html",
        collection=collection,
        photos=photo_list(collection_id=collection_id),
        is_new=False,
    )


@app.route("/admin/collections/<int:collection_id>/photos", methods=["POST"])
@login_required
def admin_collection_photos(collection_id):
    collection = get_collection(collection_id)
    if not collection:
        abort(404)
    action = request.form.get("action")
    selected_ids = request.form.getlist("selected_photo")
    photos = photo_list(collection_id=collection_id)
    photo_by_id = {str(photo["id"]): photo for photo in photos}

    if action == "delete":
        for photo_id in selected_ids:
            photo = photo_by_id.get(str(photo_id))
            if photo:
                remove_photo_files(photo)
                delete_photo(photo_id)
        flash(f"已删除 {len(selected_ids)} 张照片。", "success")
        return redirect(url_for("admin_collection_edit", collection_id=collection_id))

    if not any(key.startswith("title_") for key in request.form.keys()):
        flash("没有收到照片更新内容。", "error")
        return redirect(url_for("admin_collection_edit", collection_id=collection_id))

    updates = {}
    for photo in photos:
        photo_id = str(photo["id"])
        updates[photo_id] = {
            "title": request.form.get(f"title_{photo_id}", ""),
            "description": request.form.get(f"description_{photo_id}", ""),
            "sort_order": request.form.get(f"sort_order_{photo_id}", "0"),
            "featured_order": request.form.get(f"featured_order_{photo_id}", "0"),
            "is_featured": request.form.get(f"is_featured_{photo_id}"),
        }
    save_photo_batch(updates)
    cover_photo_id = request.form.get("cover_photo_id")
    with get_db() as conn:
        conn.execute(
            "UPDATE collections SET cover_photo_id = ?, updated_at = ? WHERE id = ?",
            (cover_photo_id or None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), collection_id),
        )
        conn.commit()
    flash("照片信息已保存。", "success")
    return redirect(url_for("admin_collection_edit", collection_id=collection_id))


@app.route("/admin/collections/<int:collection_id>/delete", methods=["POST"])
@login_required
def admin_collection_delete(collection_id):
    for photo in photo_list(collection_id=collection_id):
        remove_photo_files(photo)
    delete_collection(collection_id)
    flash("作品集已删除。", "success")
    return redirect(url_for("admin_collections"))


@app.route("/admin/photos")
@login_required
def admin_photos():
    return render_template("admin/photos.html", photos=photo_list())


@app.route("/admin/home-slideshow", methods=["GET", "POST"])
@login_required
def admin_home_slideshow():
    if request.method == "POST":
        selected_ids = request.form.getlist("selected_photo")
        order_map = {
            key.replace("featured_order_", ""): value
            for key, value in request.form.items()
            if key.startswith("featured_order_")
        }
        save_home_slideshow(selected_ids, order_map)
        flash("首页轮播已更新。", "success")
        return redirect(url_for("admin_home_slideshow"))
    return render_template("admin/home_slideshow.html", photos=photo_list())


@app.route("/admin/photos/upload", methods=["GET", "POST"])
@login_required
def admin_photo_upload():
    collections = collection_list()
    preselected_collection_id = request.args.get("collection_id", "")
    if request.method == "POST":
        file_storages = [file for file in request.files.getlist("images") if file and file.filename]
        if not file_storages:
            legacy_file = request.files.get("image")
            file_storages = [legacy_file] if legacy_file and legacy_file.filename else []
        if not file_storages:
            flash("请选择一张或多张照片。", "error")
            return redirect(url_for("admin_photo_upload"))
        try:
            data = request.form.to_dict()
            collection_id = int(data.get("collection_id") or 0)
            base_sort = max_photo_sort_order(collection_id)
            uploaded_ids = []
            for offset, file_storage in enumerate(file_storages, start=1):
                filenames = save_uploaded_image(file_storage)
                photo_data = data.copy()
                photo_data["sort_order"] = str(base_sort + offset)
                photo_data["is_featured"] = request.form.get("is_featured") if offset == 1 else ""
                uploaded_ids.append(save_photo(photo_data, filenames=filenames))
            if request.form.get("use_as_cover") and uploaded_ids:
                with get_db() as conn:
                    conn.execute(
                        "UPDATE collections SET cover_photo_id = ?, updated_at = ? WHERE id = ?",
                        (uploaded_ids[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), collection_id),
                    )
                    conn.commit()
            flash(f"已上传 {len(uploaded_ids)} 张照片。", "success")
            return redirect(url_for("admin_collection_edit", collection_id=collection_id))
        except Exception as exc:
            flash(f"无法上传照片：{exc}", "error")
    return render_template(
        "admin/photo_upload.html",
        collections=collections,
        preselected_collection_id=preselected_collection_id,
    )


@app.route("/admin/photos/<int:photo_id>/edit", methods=["GET", "POST"])
@login_required
def admin_photo_edit(photo_id):
    photo = get_photo(photo_id)
    if not photo:
        abort(404)
    if request.method == "POST":
        data = request.form.to_dict()
        data["is_featured"] = request.form.get("is_featured")
        save_photo(data, photo_id=photo_id)
        flash("照片已更新。", "success")
        return redirect(url_for("admin_photos"))
    return render_template("admin/photo_edit.html", photo=photo, collections=collection_list())


@app.route("/admin/photos/<int:photo_id>/delete", methods=["POST"])
@login_required
def admin_photo_delete(photo_id):
    photo = get_photo(photo_id)
    if photo:
        remove_photo_files(photo)
        delete_photo(photo_id)
    flash("照片已删除。", "success")
    return redirect(url_for("admin_photos"))


@app.route("/admin/articles")
@login_required
def admin_articles():
    return render_template("admin/articles.html", articles=article_list())


@app.route("/admin/articles/new", methods=["GET", "POST"])
@login_required
def admin_article_new():
    if request.method == "POST":
        data = normalize_article_data(request.form)
        try:
            data = apply_article_cover_upload(data, request.files)
            save_article(data, render_article_markdown(data.get("content_markdown", ""), data.get("category")))
            flash("文字已创建。", "success")
            return redirect(url_for("admin_articles"))
        except Exception as exc:
            flash(f"无法保存文字：{exc}", "error")
    return render_template("admin/article_edit.html", article={}, is_new=True)


@app.route("/admin/articles/<int:article_id>/edit", methods=["GET", "POST"])
@login_required
def admin_article_edit(article_id):
    article = get_article(article_id)
    if not article:
        abort(404)
    if request.method == "POST":
        data = normalize_article_data(request.form)
        try:
            data = apply_article_cover_upload(data, request.files)
            save_article(
                data,
                render_article_markdown(data.get("content_markdown", ""), data.get("category")),
                article_id=article_id,
            )
            flash("文字已更新。", "success")
            return redirect(url_for("admin_articles"))
        except Exception as exc:
            flash(f"无法保存文字：{exc}", "error")
    return render_template("admin/article_edit.html", article=article, is_new=False)


@app.route("/admin/articles/<int:article_id>/delete", methods=["POST"])
@login_required
def admin_article_delete(article_id):
    delete_article(article_id)
    flash("文字已删除。", "success")
    return redirect(url_for("admin_articles"))


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    keys = ["site_name", "tagline", "about_text", "contact_email", "instagram", "xiaohongshu", "github"]
    if request.method == "POST":
        for key in keys:
            set_setting(key, request.form.get(key, "").strip())
        flash("设置已保存。", "success")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html", settings=all_settings())


@app.route("/admin/export", methods=["GET", "POST"])
@login_required
def admin_export():
    result = None
    if request.method == "POST":
        try:
            from export_static import export_site

            exported = export_site(app)
            result = f"导出完成，已写入 {exported} 个页面到 docs/。"
            flash(result, "success")
        except Exception as exc:
            result = f"导出失败：{exc}"
            flash(result, "error")
    return render_template("admin/export.html", result=result)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5050")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
