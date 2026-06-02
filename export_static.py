from pathlib import Path
import shutil

from config import BASE_DIR, DOCS_DIR
from models import article_list, collection_list, timeline_list


def write_response(client, route, output_path):
    response = client.get(route)
    if response.status_code != 200:
        raise RuntimeError(f"{route} returned HTTP {response.status_code}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.data)


def copy_if_exists(source, destination):
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def export_site(flask_app=None):
    if flask_app is None:
        from app import app as flask_app

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    routes = [
        ("/", DOCS_DIR / "index.html"),
        ("/news/", DOCS_DIR / "news" / "index.html"),
        ("/works/", DOCS_DIR / "works" / "index.html"),
        ("/texts/", DOCS_DIR / "texts" / "index.html"),
        ("/texts/essay/", DOCS_DIR / "texts" / "essay" / "index.html"),
        ("/texts/fiction/", DOCS_DIR / "texts" / "fiction" / "index.html"),
        ("/texts/notes/", DOCS_DIR / "texts" / "notes" / "index.html"),
        ("/archive/", DOCS_DIR / "archive" / "index.html"),
        ("/about/", DOCS_DIR / "about" / "index.html"),
    ]

    for collection in collection_list(show_in_series=True):
        routes.append((
            f"/works/{collection['slug']}/",
            DOCS_DIR / "works" / collection["slug"] / "index.html",
        ))

    for timeline in timeline_list():
        routes.append((
            f"/works/timeline/{timeline['slug']}/",
            DOCS_DIR / "works" / "timeline" / timeline["slug"] / "index.html",
        ))

    for article in article_list(status="published"):
        routes.append((
            f"/texts/{article['slug']}/",
            DOCS_DIR / "texts" / article["slug"] / "index.html",
        ))

    with flask_app.test_client() as client:
        for route, output_path in routes:
            write_response(client, route, output_path)

    copy_if_exists(BASE_DIR / "static", DOCS_DIR / "static")
    copy_if_exists(BASE_DIR / "uploads" / "display", DOCS_DIR / "uploads" / "display")
    copy_if_exists(BASE_DIR / "uploads" / "covers", DOCS_DIR / "uploads" / "covers")

    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
    copy_if_exists(BASE_DIR / "CNAME", DOCS_DIR / "CNAME")

    return len(routes)


if __name__ == "__main__":
    pages = export_site()
    print(f"Exported {pages} pages to {DOCS_DIR}")
