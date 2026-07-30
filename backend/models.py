from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    image_url = db.Column(db.String(500), nullable=True)

    menu_items = db.relationship("MenuItem", backref="restaurant", cascade="all, delete-orphan")
    redemptions = db.relationship("Redemption", backref="restaurant", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "image": self.image_url,
            "owner_id": self.owner_id,
        }


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    points_cost = db.Column(db.Integer, nullable=False, default=50)

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "name": self.name,
            "points": self.points_cost,
        }


class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=True)
    item_name = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    customer_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "menu_item_id": self.menu_item_id,
            "item_name": self.item_name,
            "points": self.points,
            "customer_email": self.customer_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
