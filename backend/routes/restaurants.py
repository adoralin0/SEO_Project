from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Restaurant
from geocode import geocode_address, suggest_addresses

restaurants_bp = Blueprint("restaurants", __name__)


def _matches_query(restaurant, q: str) -> bool:
    if not q:
        return True
    haystack = f"{restaurant.name or ''} {restaurant.address or ''}".lower()
    return q in haystack


@restaurants_bp.get("/address-suggest")
@jwt_required()
def address_suggest():
    q = (request.args.get("q") or "").strip()
    return jsonify(suggest_addresses(q))


@restaurants_bp.get("/discover")
@jwt_required()
def discover_restaurants():
    q = (request.args.get("q") or "").strip().lower()
    results = [r.to_dict() for r in Restaurant.query.all() if _matches_query(r, q)]
    return jsonify(results)


@restaurants_bp.get("/")
@jwt_required()
def list_restaurants():
    q = (request.args.get("q") or "").strip().lower()
    owner_id = int(get_jwt_identity())
    restaurants = Restaurant.query.filter_by(owner_id=owner_id).all()
    results = [r.to_dict() for r in restaurants if _matches_query(r, q)]
    return jsonify(results)


@restaurants_bp.post("/")
@jwt_required()
def create_restaurant():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    address = (data.get("address") or "").strip()
    lat = data.get("lat")
    lng = data.get("lng")

    if not name:
        return jsonify({"error": "name required"}), 400
    if not address:
        return jsonify({"error": "address required"}), 400

    if lat is None or lng is None:
        lat, lng = geocode_address(address)
    else:
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            lat, lng = geocode_address(address)

    if lat is None or lng is None:
        return jsonify({
            "error": "Could not find that address. Try a fuller address (street, city, state).",
        }), 422

    r = Restaurant(
        name=name,
        address=address,
        lat=lat,
        lng=lng,
        owner_id=int(get_jwt_identity()),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201
