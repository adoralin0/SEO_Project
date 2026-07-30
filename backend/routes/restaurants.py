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


@restaurants_bp.post("/geocode")
@jwt_required()
def geocode():
    data = request.get_json() or {}
    address = (data.get("address") or request.args.get("q") or "").strip()
    if not address:
        return jsonify({"error": "address required"}), 400

    from geocode import _census_geocode, _query_variants

    matched_label = address
    lat = lng = None
    for query in _query_variants(address):
        lat, lng, matched = _census_geocode(query)
        if lat is not None:
            matched_label = matched or query
            break
    if lat is None:
        lat, lng = geocode_address(address)

    if lat is None or lng is None:
        return jsonify({
            "error": "Could not find that address. Check the spelling, or place the pin manually on the map.",
            "lat": None,
            "lng": None,
        }), 404
    return jsonify({"address": matched_label, "lat": lat, "lng": lng})


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
    address = (data.get("address") or "").strip() or None
    lat = data.get("lat")
    lng = data.get("lng")

    if not name:
        return jsonify({"error": "name required"}), 400

    if address and (lat is None or lng is None):
        lat, lng = geocode_address(address)
    elif lat is not None and lng is not None:
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid map location"}), 400

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


@restaurants_bp.delete("/<int:restaurant_id>")
@jwt_required()
def delete_restaurant(restaurant_id):
    owner_id = int(get_jwt_identity())
    r = Restaurant.query.filter_by(id=restaurant_id, owner_id=owner_id).first()
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
