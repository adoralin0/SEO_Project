# ============================================================================
# WARNING: Running this script DELETES ALL EXISTING DATA in the database.
# It drops every table, recreates them, and seeds a single demo record set.
# Only run this when you want a clean, predictable state (e.g. before a demo).
# ============================================================================

from app import create_app
from models import db, User, Restaurant, Reward


def reset_and_seed():
    app = create_app()
    with app.app_context():
        # Completely wipe and rebuild the schema.
        db.drop_all()
        db.create_all()

        # Seed one demo user.
        demo_user = User(email="demo@demo.com")
        demo_user.set_password("demo1234")
        db.session.add(demo_user)
        db.session.flush()  # assign demo_user.id before creating the restaurant

        # Seed one restaurant owned by the demo user.
        restaurant = Restaurant(name="Blue Fig Cafe", owner_id=demo_user.id)
        db.session.add(restaurant)
        db.session.flush()  # assign restaurant.id before creating the reward

        # Seed one reward for that restaurant.
        reward = Reward(
            restaurant_id=restaurant.id,
            title="Free coffee",
            description="Free coffee after 10 visits",
            points_required=10,
        )
        db.session.add(reward)

        db.session.commit()

        print("Database reset complete. Seeded 1 user, 1 restaurant, 1 reward.")
        print("Demo login -> email: demo@demo.com | password: demo1234")


if __name__ == "__main__":
    reset_and_seed()
