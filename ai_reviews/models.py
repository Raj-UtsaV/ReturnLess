"""Review models - customer reviews with AI analysis."""
from shared.database import db, TimestampMixin


class Review(db.Model, TimestampMixin):
    """Customer product review."""
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    # Review content
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # Purchase context
    verified_purchase = db.Column(db.Boolean, default=False)
    size_purchased = db.Column(db.String(20))  # For clothing/shoes

    # Helpfulness voting
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)

    # AI-generated analysis (populated by AI service)
    sentiment_score = db.Column(db.Float)  # -1.0 to 1.0
    sentiment_label = db.Column(db.String(20))  # positive, negative, neutral
    topics = db.Column(db.JSON, default=list)  # extracted topics/aspects
    ai_processed = db.Column(db.Boolean, default=False)

    # Relationships
    product = db.relationship("Product", backref=db.backref("reviews", lazy="dynamic"))
    customer = db.relationship("Customer", backref=db.backref("reviews", lazy="dynamic"))

    def __repr__(self):
        return f"<Review {self.id} - {self.rating}★ by customer {self.customer_id}>"

    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio."""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return self.helpful_count / total

    def to_dict(self) -> dict:
        """Serialize review to dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "verified_purchase": self.verified_purchase,
            "size_purchased": self.size_purchased,
            "helpful_count": self.helpful_count,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "topics": self.topics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReviewSummary(db.Model, TimestampMixin):
    """AI-generated review summary for a product."""
    __tablename__ = "review_summaries"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True)

    # AI Summary content
    summary_text = db.Column(db.Text, nullable=False)
    pros = db.Column(db.JSON, default=list)  # List of positive aspects
    cons = db.Column(db.JSON, default=list)  # List of negative aspects
    common_topics = db.Column(db.JSON, default=list)  # Most discussed topics

    # Sentiment distribution
    positive_pct = db.Column(db.Float, default=0)
    neutral_pct = db.Column(db.Float, default=0)
    negative_pct = db.Column(db.Float, default=0)

    # Rating distribution
    rating_distribution = db.Column(db.JSON, default=dict)  # {1: count, 2: count, ...}

    # Size fit analysis (for clothing)
    size_fit = db.Column(db.JSON, default=dict)  # {runs_small: %, true_to_size: %, runs_large: %}

    # Metadata
    total_reviews_analyzed = db.Column(db.Integer, default=0)
    confidence_score = db.Column(db.Float)  # 0-1, confidence in summary

    # AI explanation
    explanation = db.Column(db.Text)  # Why the AI reached these conclusions

    # Relationship
    product = db.relationship("Product", backref=db.backref("review_summary", uselist=False))

    def __repr__(self):
        return f"<ReviewSummary product={self.product_id}>"

    def to_dict(self) -> dict:
        """Serialize review summary."""
        return {
            "product_id": self.product_id,
            "summary_text": self.summary_text,
            "pros": self.pros,
            "cons": self.cons,
            "common_topics": self.common_topics,
            "positive_pct": self.positive_pct,
            "neutral_pct": self.neutral_pct,
            "negative_pct": self.negative_pct,
            "rating_distribution": self.rating_distribution,
            "size_fit": self.size_fit,
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "confidence_score": self.confidence_score,
            "explanation": self.explanation,
        }
