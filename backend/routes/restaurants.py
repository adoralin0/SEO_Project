from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Restaurant, MenuItem, Redemption, User
from geocode import geocode_address, suggest_addresses

restaurants_bp = Blueprint("restaurants", __name__)


def _matches_query(restaurant, q: str) -> bool:
    if not q:
        return True
    haystack = f"{restaurant.name or ''} {restaurant.address or ''}".lower()
    return q in haystack


def _current_user():
    uid = int(get_jwt_identity())
    return User.query.get(uid)


def _owned_restaurant(restaurant_id: int):
    owner_id = int(get_jwt_identity())
    return Restaurant.query.filter_by(id=restaurant_id, owner_id=owner_id).first()


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
    """Only restaurants created by an owner (not demo/unowned rows)."""
    q = (request.args.get("q") or "").strip().lower()
    restaurants = Restaurant.query.filter(Restaurant.owner_id.isnot(None)).all()
    results = [r.to_dict() for r in restaurants if _matches_query(r, q)]
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
    image = (data.get("image") or "").strip() or None

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
        image_url=image,
        owner_id=int(get_jwt_identity()),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@restaurants_bp.delete("/<int:restaurant_id>")
@jwt_required()
def delete_restaurant(restaurant_id):
    r = _owned_restaurant(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200


@restaurants_bp.get("/menu")
@jwt_required()
def menu_by_name():
    """Customer: load menu for a restaurant by id (preferred) or name."""
    restaurant_id = request.args.get("id", type=int)
    name = (request.args.get("name") or "").strip()

    r = None
    if restaurant_id:
        r = Restaurant.query.get(restaurant_id)
    if not r and name:
        # Prefer owner-created restaurants when names collide with old demos
        r = (
            Restaurant.query.filter(
                db.func.lower(Restaurant.name) == name.lower(),
                Restaurant.owner_id.isnot(None),
            ).first()
            or Restaurant.query.filter(
                db.func.lower(Restaurant.name) == name.lower()
            ).first()
        )
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    items = MenuItem.query.filter_by(restaurant_id=r.id).order_by(MenuItem.points_cost).all()
    return jsonify({"restaurant": r.to_dict(), "items": [i.to_dict() for i in items]})


@restaurants_bp.get("/<int:restaurant_id>/menu")
@jwt_required()
def list_menu(restaurant_id):
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    items = MenuItem.query.filter_by(restaurant_id=r.id).order_by(MenuItem.points_cost).all()
    return jsonify([i.to_dict() for i in items])


@restaurants_bp.post("/<int:restaurant_id>/menu")
@jwt_required()
def add_menu_item(restaurant_id):
    r = _owned_restaurant(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    try:
        points = int(data.get("points"))
    except (TypeError, ValueError):
        points = 0
    if not name:
        return jsonify({"error": "name required"}), 400
    if points < 1:
        return jsonify({"error": "points must be a positive integer"}), 400
    item = MenuItem(restaurant_id=r.id, name=name, points_cost=points)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@restaurants_bp.delete("/<int:restaurant_id>/menu/<int:item_id>")
@jwt_required()
def delete_menu_item(restaurant_id, item_id):
    r = _owned_restaurant(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=r.id).first()
    if not item:
        return jsonify({"error": "Menu item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200


@restaurants_bp.post("/<int:restaurant_id>/redeem")
@jwt_required()
def redeem_item(restaurant_id):
    """Customer spends points on a menu item; logged for the restaurant dashboard."""
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    data = request.get_json() or {}
    item_id = data.get("menu_item_id")
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=r.id).first()
    if not item:
        return jsonify({"error": "Menu item not found"}), 404

    user = _current_user()
    email = user.email if user else None
    redemption = Redemption(
        restaurant_id=r.id,
        menu_item_id=item.id,
        item_name=item.name,
        points=item.points_cost,
        customer_email=email,
    )
    db.session.add(redemption)
    db.session.commit()
    return jsonify(redemption.to_dict()), 201


@restaurants_bp.get("/<int:restaurant_id>/redemptions")
@jwt_required()
def list_redemptions(restaurant_id):
    from datetime import datetime, timedelta, timezone

    r = _owned_restaurant(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404
    rows = (
        Redemption.query.filter_by(restaurant_id=r.id)
        .order_by(Redemption.id.desc())
        .limit(200)
        .all()
    )

    # Per-item: total redemptions + unique customers
    redeem_counts = {}
    people = {}
    for row in Redemption.query.filter_by(restaurant_id=r.id).all():
        redeem_counts[row.item_name] = redeem_counts.get(row.item_name, 0) + 1
        key = (row.customer_email or "").strip().lower() or f"anon-{row.id}"
        people.setdefault(row.item_name, set()).add(key)

    popular = sorted(
        [
            {
                "name": name,
                "count": redeem_counts[name],
                "people": len(people[name]),
            }
            for name in redeem_counts
        ],
        key=lambda x: (-x["people"], -x["count"]),
    )

    # Last 7 days of redemption activity (for the bar chart)
    today = datetime.now(timezone.utc).date()
    day_buckets = {(today - timedelta(days=i)).isoformat(): 0 for i in range(6, -1, -1)}
    for row in Redemption.query.filter_by(restaurant_id=r.id).all():
        if not row.created_at:
            continue
        d = row.created_at.date().isoformat()
        if d in day_buckets:
            day_buckets[d] += 1

    by_day = [
        {
            "date": day,
            "label": datetime.fromisoformat(day).strftime("%a"),
            "value": count,
        }
        for day, count in day_buckets.items()
    ]

    return jsonify(
        {
            "redemptions": [row.to_dict() for row in rows],
            "popular": popular,
            "by_day": by_day,
        }
    )
