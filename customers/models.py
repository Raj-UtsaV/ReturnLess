"""Customer models - isolated from product data."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from shared.database import db, TimestampMixin


class Customer(db.Model, UserMixin, TimestampMixin):
    """Customer account - owns all customer-specific data."""
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(500))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Green Credits
    green_credits = db.Column(db.Integer, default=0)
    lifetime_credits = db.Column(db.Integer, default=0)

    # Body Measurements (for AI size prediction)
    height_cm = db.Column(db.Float)  # Height in centimeters
    weight_kg = db.Column(db.Float)  # Weight in kilograms
    body_type = db.Column(db.String(20))  # slim, regular, athletic, plus

    # Preferences (JSON)
    preferences = db.Column(db.JSON, default=dict)

    # Relationships
    addresses = db.relationship("Address", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer {self.email}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def credit_tier(self) -> dict:
        """Determine green credit tier."""
        credits = self.lifetime_credits
        if credits >= 3000:
            return {"name": "Green Hero", "color": "emerald", "min": 3000}
        elif credits >= 1500:
            return {"name": "Platinum", "color": "violet", "min": 1500}
        elif credits >= 500:
            return {"name": "Gold", "color": "amber", "min": 500}
        else:
            return {"name": "Silver", "color": "slate", "min": 0}

    def set_password(self, password: str):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize customer (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "green_credits": self.green_credits,
            "credit_tier": self.credit_tier,
            "avatar_url": self.avatar_url,
        }


class Address(db.Model, TimestampMixin):
    """Customer shipping/billing address."""
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    label = db.Column(db.String(50), default="Home")  # Home, Work, Other
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(300), nullable=False)
    address_line2 = db.Column(db.String(300))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default="India")
    is_default = db.Column(db.Boolean, default=False)
