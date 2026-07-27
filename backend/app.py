from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes.auth import auth_bp
from routes.restaurants import restaurants_bp

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
