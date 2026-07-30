import secrets

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token

from auth0_verify import Auth0Error, auth0_configured, verify_auth0_id_token
from models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/auth0-config")
def auth0_config():
    """Public SPA settings for Auth0 (no secrets)."""
    domain = current_app.config.get("AUTH0_DOMAIN") or ""
    client_id = current_app.config.get("AUTH0_CLIENT_ID") or ""
    audience = current_app.config.get("AUTH0_AUDIENCE") or ""
    callback_url = (
        current_app.config.get("AUTH0_CALLBACK_URL")
        or "http://localhost:5000/login.html"
    )
    return jsonify(
        {
            "configured": bool(domain and client_id),
            "domain": domain,
            "clientId": client_id,
            "audience": audience,
            "callbackUrl": callback_url,
        }
    )


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists. Try logging in."}), 409
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "registered"}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found. Tap Sign up to create one."}), 401
    if not user.check_password(password):
        return jsonify({"error": "Wrong password. Try again."}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "email": user.email})


@auth_bp.post("/auth0")
def auth0_login():
    """Exchange a verified Auth0 ID token for a Loyable API JWT."""
    if not auth0_configured():
        return jsonify({"error": "Auth0 is not configured. Set AUTH0_DOMAIN and AUTH0_CLIENT_ID."}), 503

    data = request.get_json() or {}
    id_token = (data.get("id_token") or "").strip()
    if not id_token:
        return jsonify({"error": "id_token required"}), 400

    try:
        claims = verify_auth0_id_token(id_token)
    except Auth0Error as exc:
        return jsonify({"error": str(exc)}), 401

    email = (claims.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        # Unusable local password — this account signs in via Auth0/Google
        user.set_password(secrets.token_urlsafe(48))
        db.session.add(user)
        db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "email": user.email})
