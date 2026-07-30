import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DB_PATH = INSTANCE_DIR / "loyable.db"


def load_env():
    """Load backend/.env (wins) then project-root .env."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(BASE_DIR / ".env", override=True)


load_env()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    # Absolute path so accounts always save to the same file
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret")

    # Auth0 — refreshed in create_app so .env edits apply on restart
    AUTH0_DOMAIN = ""
    AUTH0_CLIENT_ID = ""
    AUTH0_AUDIENCE = ""


def apply_auth0_config(app):
    load_env()
    app.config["AUTH0_DOMAIN"] = os.environ.get("AUTH0_DOMAIN", "").strip()
    app.config["AUTH0_CLIENT_ID"] = os.environ.get("AUTH0_CLIENT_ID", "").strip()
    app.config["AUTH0_AUDIENCE"] = os.environ.get("AUTH0_AUDIENCE", "").strip()
    app.config["AUTH0_CALLBACK_URL"] = (
        os.environ.get("AUTH0_CALLBACK_URL", "http://localhost:5000/login.html").strip()
        or "http://localhost:5000/login.html"
    )
