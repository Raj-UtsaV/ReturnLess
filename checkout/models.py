"""Checkout models - cart, orders, order items."""
from shared.database import db, TimestampMixin


class CartItem(db.Model, TimestampMixin):
    """Shopping cart item."""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    size = db.Column(db.String(20))  # Selected size (for clothing)

    # Relationships
    customer = db.relationship("Customer", backref=db.backref("cart_items", lazy="dynamic"))
    product = db.relationship("Product")

    def __repr__(self):
        return f"<CartItem customer={self.customer_id} product={self.product_id} qty={self.quantity}>"

    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity

    @property
    def green_credits_total(self) -> int:
        return self.product.green_credits_earn * self.quantity

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name,
            "product_thumbnail": self.product.thumbnail,
            "price": self.product.price,
            "quantity": self.quantity,
            "size": self.size,
            "subtotal": self.subtotal,
            "green_credits": self.green_credits_total,
        }


class Order(db.Model, TimestampMixin):
    """Customer order."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Status: pending, confirmed, shipped, delivered, cancelled
    status = db.Column(db.String(20), default="confirmed", index=True)

    # Pricing
    subtotal = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)

    # Green credits
    credits_earned = db.Column(db.Integer, default=0)
    eco_shipping = db.Column(db.Boolean, default=False)

    # Shipping address (snapshot at time of order)
    shipping_name = db.Column(db.String(200))
    shipping_address = db.Column(db.Text)
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_postal = db.Column(db.String(20))
    shipping_phone = db.Column(db.String(20))

    # Payment (mock)
    payment_method = db.Column(db.String(50), default="mock_card")
    payment_status = db.Column(db.String(20), default="paid")

    # Delivery estimate
    estimated_delivery_min = db.Column(db.Integer)
    estimated_delivery_max = db.Column(db.Integer)

    # Relationships
    customer = db.relationship("Customer", backref=db.backref("orders", lazy="dynamic"))
    items = db.relationship("OrderItem", backref="order", lazy="dynamic")

    def __repr__(self):
        return f"<Order {self.order_number} status={self.status}>"

    @property
    def item_count(self) -> int:
        return self.items.count()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "status": self.status,
            "subtotal": self.subtotal,
            "delivery_fee": self.delivery_fee,
            "total": self.total,
            "credits_earned": self.credits_earned,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrderItem(db.Model, TimestampMixin):
    """Individual item in an order."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)  # Snapshot of price
    size = db.Column(db.String(20))

    # Product snapshot (in case product changes later)
    product_name = db.Column(db.String(300), nullable=False)
    product_thumbnail = db.Column(db.String(500))
    product_type = db.Column(db.String(20))

    # Green credits for this item
    credits_earned = db.Column(db.Integer, default=0)

    # Relationships
    product = db.relationship("Product")

    @property
    def subtotal(self) -> float:
        return self.price_at_purchase * self.quantity
