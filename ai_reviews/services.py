"""Review service layer - business logic for reviews and AI analysis."""
from typing import Optional
from sqlalchemy import desc, func
from shared.database import db
from ai_reviews.models import Review, ReviewSummary
from ai_reviews.ai_engine import ReviewAIEngine


class ReviewService:
    """Service for review CRUD operations and AI analysis."""

    _ai_engine = None

    @classmethod
    def _get_ai_engine(cls) -> ReviewAIEngine:
        """Lazy-load AI engine (singleton)."""
        if cls._ai_engine is None:
            cls._ai_engine = ReviewAIEngine()
        return cls._ai_engine

    @staticmethod
    def create_review(
        product_id: int,
        customer_id: int,
        rating: int,
        title: str,
        body: str,
        verified_purchase: bool = False,
        size_purchased: Optional[str] = None,
    ) -> Review:
        """
        Create a new review and trigger AI analysis.

        Args:
            product_id: Product being reviewed
            customer_id: Customer writing the review
            rating: 1-5 star rating
            title: Review title
            body: Review body text
            verified_purchase: Whether customer actually bought the product
            size_purchased: Size purchased (for clothing)

        Returns:
            Created Review instance with AI analysis populated
        """
        # Validate rating
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Check for duplicate review
        existing = Review.query.filter_by(
            product_id=product_id, customer_id=customer_id
        ).first()
        if existing:
            raise ValueError("You have already reviewed this product")

        review = Review(
            product_id=product_id,
            customer_id=customer_id,
            rating=rating,
            title=title,
            body=body,
            verified_purchase=verified_purchase,
            size_purchased=size_purchased,
        )

        # Run AI analysis on the review
        ai_engine = ReviewService._get_ai_engine()
        sentiment = ai_engine.analyze_sentiment(body)
        topics = ai_engine.extract_topics(body)

        review.sentiment_score = sentiment["score"]
        review.sentiment_label = sentiment["label"]
        review.topics = topics
        review.ai_processed = True

        db.session.add(review)
        db.session.commit()

        # Update product average rating
        ReviewService._update_product_rating(product_id)

        # Regenerate summary if enough reviews
        review_count = Review.query.filter_by(product_id=product_id).count()
        if review_count >= 3:
            ReviewService.generate_product_summary(product_id)

        return review

    @staticmethod
    def get_reviews_for_product(
        product_id: int,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "newest",
        filter_rating: Optional[int] = None,
    ) -> dict:
        """
        Get paginated reviews for a product.

        Args:
            product_id: Product ID
            page: Page number
            per_page: Reviews per page
            sort_by: Sort order (newest, oldest, highest, lowest, helpful)
            filter_rating: Filter by specific star rating

        Returns:
            Dict with items, pagination info
        """
        query = Review.query.filter_by(product_id=product_id)

        if filter_rating and 1 <= filter_rating <= 5:
            query = query.filter_by(rating=filter_rating)

        # Sorting
        sort_options = {
            "newest": desc(Review.created_at),
            "oldest": Review.created_at,
            "highest": desc(Review.rating),
            "lowest": Review.rating,
            "helpful": desc(Review.helpful_count),
        }
        order = sort_options.get(sort_by, desc(Review.created_at))
        query = query.order_by(order)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }

    @staticmethod
    def get_product_summary(product_id: int) -> Optional[ReviewSummary]:
        """Get the AI-generated summary for a product."""
        return ReviewSummary.query.filter_by(product_id=product_id).first()

    @staticmethod
    def generate_product_summary(product_id: int) -> Optional[ReviewSummary]:
        """
        Generate or regenerate AI summary for a product.

        Analyzes all reviews and produces:
        - Summary text
        - Pros and cons
        - Sentiment distribution
        - Common topics
        - Size fit analysis (if applicable)
        """
        reviews = Review.query.filter_by(product_id=product_id).all()
        if not reviews:
            return None

        ai_engine = ReviewService._get_ai_engine()

        # Prepare review data for AI engine
        review_data = [
            {
                "body": r.body,
                "title": r.title,
                "rating": r.rating,
                "size_purchased": r.size_purchased,
            }
            for r in reviews
        ]

        # Generate summary
        summary_result = ai_engine.generate_summary(review_data)

        # Analyze size fit if reviews mention sizes
        size_reviews = [r for r in review_data if r.get("size_purchased")]
        size_fit = {}
        if size_reviews:
            size_fit = ai_engine.analyze_size_fit(review_data)

        # Calculate rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[str(i)] = sum(1 for r in reviews if r.rating == i)

        # Upsert summary
        existing = ReviewSummary.query.filter_by(product_id=product_id).first()
        if existing:
            summary = existing
        else:
            summary = ReviewSummary(product_id=product_id)
            db.session.add(summary)

        summary.summary_text = summary_result["summary_text"]
        summary.pros = summary_result["pros"]
        summary.cons = summary_result["cons"]
        summary.common_topics = summary_result["common_topics"]
        summary.positive_pct = summary_result["positive_pct"]
        summary.neutral_pct = summary_result["neutral_pct"]
        summary.negative_pct = summary_result["negative_pct"]
        summary.rating_distribution = rating_dist
        summary.size_fit = size_fit
        summary.total_reviews_analyzed = len(reviews)
        summary.confidence_score = summary_result["confidence_score"]
        summary.explanation = summary_result["explanation"]

        db.session.commit()
        return summary

    @staticmethod
    def vote_helpful(review_id: int, helpful: bool) -> Optional[Review]:
        """Record a helpfulness vote on a review."""
        review = db.session.get(Review, review_id)
        if not review:
            return None

        if helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1

        db.session.commit()
        return review

    @staticmethod
    def get_review_stats(product_id: int) -> dict:
        """Get aggregate review statistics for a product."""
        reviews = Review.query.filter_by(product_id=product_id)

        total = reviews.count()
        if total == 0:
            return {
                "total": 0,
                "average": 0,
                "distribution": {str(i): 0 for i in range(1, 6)},
                "verified_count": 0,
            }

        avg = db.session.query(func.avg(Review.rating)).filter_by(
            product_id=product_id
        ).scalar() or 0

        distribution = {}
        for i in range(1, 6):
            count = reviews.filter_by(rating=i).count()
            distribution[str(i)] = count

        verified_count = reviews.filter_by(verified_purchase=True).count()

        return {
            "total": total,
            "average": round(float(avg), 1),
            "distribution": distribution,
            "verified_count": verified_count,
        }

    @staticmethod
    def _update_product_rating(product_id: int):
        """Update product's cached average rating and review count."""
        from products.models import Product

        stats = ReviewService.get_review_stats(product_id)
        product = db.session.get(Product, product_id)
        if product:
            product.avg_rating = stats["average"]
            product.total_reviews = stats["total"]
            db.session.commit()

    @staticmethod
    def get_customer_reviews(customer_id: int) -> list:
        """Get all reviews by a customer."""
        return Review.query.filter_by(customer_id=customer_id).order_by(
            desc(Review.created_at)
        ).all()

    @staticmethod
    def can_review(product_id: int, customer_id: int) -> bool:
        """Check if a customer can review a product (no duplicate reviews)."""
        existing = Review.query.filter_by(
            product_id=product_id, customer_id=customer_id
        ).first()
        return existing is None
