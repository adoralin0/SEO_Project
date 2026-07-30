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


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, host="127.0.0.1")
