from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Restaurant

restaurants_bp = Blueprint("restaurants", __name__)


@restaurants_bp.get("/discover")
@jwt_required()
def discover_restaurants():
    q = (request.args.get("q") or "").strip().lower()
    results = []

    for r in Restaurant.query.all():
        if not q or q in r.name.lower():
            results.append({
                "id": r.id,
                "name": r.name,
                "address": None,
                "lat": None,
                "lng": None,
                "cuisine": None,
            })

    return jsonify(results)


@restaurants_bp.get("/")
@jwt_required()
def list_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([{"id": r.id, "name": r.name} for r in restaurants])


@restaurants_bp.post("/")
@jwt_required()
def create_restaurant():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    r = Restaurant(name=name, owner_id=int(get_jwt_identity()))
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id, "name": r.name}), 201
