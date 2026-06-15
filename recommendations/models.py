"""Size recommendation models - purchase history and size preferences."""
from shared.database import db, TimestampMixin


class SizePurchaseHistory(db.Model, TimestampMixin):
    """Tracks customer size purchases and outcomes (kept/returned)."""
    __tablename__ = "size_purchase_history"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    # Size details
    size_purchased = db.Column(db.String(20), nullable=False)
    brand = db.Column(db.String(100))

    # Outcome
    kept = db.Column(db.Boolean, default=True)  # True = kept, False = returned
    return_reason = db.Column(db.String(100))  # "too_small", "too_large", "other"

    # Relationships
    customer = db.relationship("Customer", backref=db.backref("size_history", lazy="dynamic"))
    product = db.relationship("Product", backref=db.backref("size_purchases", lazy="dynamic"))

    def __repr__(self):
        return f"<SizePurchase customer={self.customer_id} size={self.size_purchased} kept={self.kept}>"


class SizeRecommendation(db.Model, TimestampMixin):
    """Cached AI size recommendations per customer-product pair."""
    __tablename__ = "size_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    # Recommendation
    recommended_size = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)  # 0-1

    # AI explanation (architecture rule: all AI decisions include explanations)
    explanation = db.Column(db.Text, nullable=False)

    # Factors used
    factors = db.Column(db.JSON, default=dict)
    # Example: {"purchase_history": 0.4, "review_analysis": 0.3, "brand_adjustment": 0.2, "category_fit": 0.1}

    # Relationships
    customer = db.relationship("Customer", backref=db.backref("size_recommendations", lazy="dynamic"))
    product = db.relationship("Product", backref=db.backref("size_recommendations", lazy="dynamic"))

    def __repr__(self):
        return f"<SizeRec customer={self.customer_id} product={self.product_id} size={self.recommended_size}>"

    def to_dict(self) -> dict:
        """Serialize recommendation."""
        return {
            "recommended_size": self.recommended_size,
            "confidence": self.confidence,
            "confidence_pct": round(self.confidence * 100),
            "explanation": self.explanation,
            "factors": self.factors,
        }
