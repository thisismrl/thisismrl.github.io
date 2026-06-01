from pathlib import Path
import secrets


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = BASE_DIR / "uploads"
ORIGINALS_DIR = UPLOAD_DIR / "originals"
DISPLAY_DIR = UPLOAD_DIR / "display"
COVERS_DIR = UPLOAD_DIR / "covers"
DOCS_DIR = BASE_DIR / "docs"
DATABASE_PATH = INSTANCE_DIR / "site.db"
SECRET_KEY_PATH = INSTANCE_DIR / "secret_key.txt"
ADMIN_PASSWORD_PATH = INSTANCE_DIR / "admin_password.txt"


def ensure_runtime_files():
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    DISPLAY_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.write_text(secrets.token_hex(32), encoding="utf-8")

    if not ADMIN_PASSWORD_PATH.exists():
        ADMIN_PASSWORD_PATH.write_text("change-this-password", encoding="utf-8")


def read_secret_key():
    ensure_runtime_files()
    return SECRET_KEY_PATH.read_text(encoding="utf-8").strip()


def read_admin_password():
    ensure_runtime_files()
    return ADMIN_PASSWORD_PATH.read_text(encoding="utf-8").strip()
