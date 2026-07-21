from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Reward, Restaurant

rewards_bp = Blueprint("rewards", __name__)

@rewards_bp.get("/")
@jwt_required()
def list_rewards():
    owner_id = int(get_jwt_identity())
    rewards = (
        Reward.query.join(Restaurant, Reward.restaurant_id == Restaurant.id)
        .filter(Restaurant.owner_id == owner_id)
        .all()
    )
    return jsonify([
        {
            "id": r.id,
            "restaurant_id": r.restaurant_id,
            "title": r.title,
            "description": r.description,
            "points_required": r.points_required,
        }
        for r in rewards
    ])

@rewards_bp.post("/")
@jwt_required()
def create_reward():
    owner_id = int(get_jwt_identity())
    data = request.get_json() or {}
    restaurant_id = data.get("restaurant_id")
    title = data.get("title")
    if not restaurant_id or not title:
        return jsonify({"error": "restaurant_id and title required"}), 400
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=owner_id).first()
    if not restaurant:
        return jsonify({"error": "restaurant not found"}), 404
    reward = Reward(
        restaurant_id=restaurant_id,
        title=title,
        description=data.get("description"),
        points_required=data.get("points_required", 0),
    )
    db.session.add(reward)
    db.session.commit()
    return jsonify({
        "id": reward.id,
        "restaurant_id": reward.restaurant_id,
        "title": reward.title,
        "description": reward.description,
        "points_required": reward.points_required,
    }), 201
