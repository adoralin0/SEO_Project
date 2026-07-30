from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config, apply_auth0_config
from models import db
from routes.auth import auth_bp
from routes.restaurants import restaurants_bp

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    apply_auth0_config(app)
    CORS(app)
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(restaurants_bp, url_prefix="/api/restaurants")

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND, "login.html")

    @app.get("/<path:path>")
    def frontend(path):
        return send_from_directory(FRONTEND, path)

    with app.app_context():
        db.create_all()
        _ensure_restaurant_location_columns()
        _ensure_restaurant_image_column()
        _seed_missing_menus()
        _reassign_demo_redemptions()

    return app


def _ensure_restaurant_location_columns():
    """Add address/lat/lng columns on existing SQLite DBs."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "restaurant" not in inspector.get_table_names():
        return

    with db.engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(restaurant)")).fetchall()
        cols = {row[1] for row in rows}
        alterations = []
        if "address" not in cols:
            alterations.append("ALTER TABLE restaurant ADD COLUMN address VARCHAR(255)")
        if "lat" not in cols:
            alterations.append("ALTER TABLE restaurant ADD COLUMN lat FLOAT")
        if "lng" not in cols:
            alterations.append("ALTER TABLE restaurant ADD COLUMN lng FLOAT")
        for stmt in alterations:
            conn.execute(text(stmt))
        if alterations:
            conn.commit()


def _ensure_restaurant_image_column():
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "restaurant" not in inspector.get_table_names():
        return
    with db.engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(restaurant)")).fetchall()
        cols = {row[1] for row in rows}
        if "image_url" not in cols:
            conn.execute(text("ALTER TABLE restaurant ADD COLUMN image_url VARCHAR(500)"))
            conn.commit()


def _seed_missing_menus():
    from models import Restaurant
    from menu_seed import seed_default_menu

    for r in Restaurant.query.filter(Restaurant.owner_id.isnot(None)).all():
        seed_default_menu(r)


def _reassign_demo_redemptions():
    """Move redemptions off unowned demo duplicates onto the owned restaurant."""
    from models import Restaurant, Redemption

    owned = {
        (r.name or "").strip().lower(): r
        for r in Restaurant.query.filter(Restaurant.owner_id.isnot(None)).all()
    }
    changed = False
    for demo in Restaurant.query.filter(Restaurant.owner_id.is_(None)).all():
        key = (demo.name or "").strip().lower()
        target = owned.get(key)
        if not target:
            continue
        for row in Redemption.query.filter_by(restaurant_id=demo.id).all():
            row.restaurant_id = target.id
            # Keep item name; menu_item_id may point at demo menu — clear to avoid FK confusion
            row.menu_item_id = None
            changed = True
    if changed:
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, host="127.0.0.1")
