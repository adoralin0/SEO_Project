from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User

auth_bp = Blueprint("auth", __name__)


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
    return jsonify({"access_token": token})
