"""Product models - standard and refurbished products."""
from shared.database import db, TimestampMixin


class Category(db.Model, TimestampMixin):
    """Product category."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Emoji or icon class
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    # Relationships
    parent = db.relationship("Category", remote_side=[id], backref="subcategories")
    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model, TimestampMixin):
    """Base product model supporting standard and refurbished items."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(350), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(500))

    # Pricing
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)  # For showing discounts
    currency = db.Column(db.String(3), default="INR")

    # Categorization
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    brand = db.Column(db.String(100), index=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)

    # Inventory
    stock_quantity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Product type: 'standard' or 'refurbished'
    product_type = db.Column(db.String(20), default="standard", index=True)

    # Images (JSON array of paths)
    images = db.Column(db.JSON, default=list)
    thumbnail = db.Column(db.String(500))

    # Specifications (JSON object)
    specifications = db.Column(db.JSON, default=dict)

    # Delivery
    delivery_days_min = db.Column(db.Integer, default=3)
    delivery_days_max = db.Column(db.Integer, default=7)
    free_delivery = db.Column(db.Boolean, default=False)

    # Sustainability
    carbon_footprint_kg = db.Column(db.Float, default=0)
    eco_friendly = db.Column(db.Boolean, default=False)

    # Green Credits earned on purchase
    green_credits_earn = db.Column(db.Integer, default=20)

    # Ratings (aggregated)
    avg_rating = db.Column(db.Float, default=0)
    total_reviews = db.Column(db.Integer, default=0)

    # Size/Clothing specific
    available_sizes = db.Column(db.JSON, default=list)  # ["S", "M", "L", "XL"]
    color = db.Column(db.String(50))

    # Refurbished-specific fields (only populated for product_type='refurbished')
    grade = db.Column(db.String(20))  # A, B, C, D
    warranty_months = db.Column(db.Integer)
    carbon_saved_kg = db.Column(db.Float)
    refurb_reason = db.Column(db.String(200))
    inspection_notes = db.Column(db.Text)
    refurbished_by = db.Column(db.String(100))

    # Relationships
    images_list = db.relationship("ProductImage", backref="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product {self.name[:50]}>"

    @property
    def is_refurbished(self) -> bool:
        return self.product_type == "refurbished"

    @property
    def savings(self) -> dict:
        """Calculate savings compared to original price."""
        if not self.original_price or self.original_price <= self.price:
            return {"amount": 0, "percentage": 0}
        amount = self.original_price - self.price
        percentage = (amount / self.original_price) * 100
        return {"amount": round(amount, 2), "percentage": round(percentage, 1)}

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def delivery_estimate(self) -> str:
        if self.delivery_days_min == self.delivery_days_max:
            return f"{self.delivery_days_min} days"
        return f"{self.delivery_days_min}-{self.delivery_days_max} days"

    def to_dict(self) -> dict:
        """Serialize product to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "price": self.price,
            "original_price": self.original_price,
            "brand": self.brand,
            "category": self.category.name if self.category else None,
            "product_type": self.product_type,
            "in_stock": self.in_stock,
            "thumbnail": self.thumbnail,
            "avg_rating": self.avg_rating,
            "total_reviews": self.total_reviews,
            "green_credits_earn": self.green_credits_earn,
            "savings": self.savings,
            "delivery_estimate": self.delivery_estimate,
        }
        if self.is_refurbished:
            data.update({
                "grade": self.grade,
                "warranty_months": self.warranty_months,
                "carbon_saved_kg": self.carbon_saved_kg,
                "refurb_reason": self.refurb_reason,
            })
        return data


class ProductImage(db.Model, TimestampMixin):
    """Product images with ordering."""
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
