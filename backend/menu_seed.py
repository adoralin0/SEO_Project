"""Default reward-menu helpers (3 foods, costs vary by restaurant)."""

from models import MenuItem, db

# Three foods; point costs are offset per restaurant so each spot differs
BASE_ITEMS = (
    ("Truffle Fries", 45),
    ("Smash Burger", 80),
    ("Matcha Soft Serve", 35),
)


def point_costs_for_restaurant(restaurant_id: int):
    """Return three (name, points) pairs unique-ish to this restaurant id."""
    offset = (int(restaurant_id) * 13) % 40
    return [
        (BASE_ITEMS[0][0], BASE_ITEMS[0][1] + offset),
        (BASE_ITEMS[1][0], BASE_ITEMS[1][1] + (offset // 2) + 10),
        (BASE_ITEMS[2][0], BASE_ITEMS[2][1] + (offset % 15) + 5),
    ]


def seed_default_menu(restaurant):
    """Add the three default items if this restaurant has no menu yet."""
    if MenuItem.query.filter_by(restaurant_id=restaurant.id).count():
        return
    for name, points in point_costs_for_restaurant(restaurant.id):
        db.session.add(
            MenuItem(restaurant_id=restaurant.id, name=name, points_cost=int(points))
        )
    db.session.commit()
