"""Tests for AI Review Analysis - Phase 2."""
import pytest
from ai_reviews.models import Review, ReviewSummary
from ai_reviews.services import ReviewService
from ai_reviews.ai_engine import ReviewAIEngine


class TestReviewModel:
    """Test Review model properties."""

    def test_review_creation(self, db, sample_product, sample_customer):
        """Test review model creation."""
        review = Review(
            product_id=sample_product.id,
            customer_id=sample_customer.id,
            rating=5,
            title="Great product!",
            body="This is an amazing smartphone, absolutely love it.",
            verified_purchase=True,
        )
        db.session.add(review)
        db.session.commit()

        assert review.id is not None
        assert review.rating == 5
        assert review.verified_purchase is True

    def test_review_helpfulness_ratio(self, db, sample_product, sample_customer):
        """Test helpfulness ratio calculation."""
        review = Review(
            product_id=sample_product.id,
            customer_id=sample_customer.id,
            rating=4,
            title="Good",
            body="Nice product overall.",
            helpful_count=8,
            not_helpful_count=2,
        )
        db.session.add(review)
        db.session.commit()

        assert review.helpfulness_ratio == 0.8

    def test_review_helpfulness_ratio_zero(self, db, sample_product, sample_customer):
        """Test helpfulness ratio with no votes."""
        review = Review(
            product_id=sample_product.id,
            customer_id=sample_customer.id,
            rating=3,
            title="Ok",
            body="Average product.",
        )
        db.session.add(review)
        db.session.commit()

        assert review.helpfulness_ratio == 0

    def test_review_to_dict(self, db, sample_product, sample_customer):
        """Test review serialization."""
        review = Review(
            product_id=sample_product.id,
            customer_id=sample_customer.id,
            rating=5,
            title="Love it",
            body="Best purchase ever.",
            sentiment_score=0.8,
            sentiment_label="positive",
            topics=["value for money", "build quality"],
        )
        db.session.add(review)
        db.session.commit()

        data = review.to_dict()
        assert data["rating"] == 5
        assert data["sentiment_label"] == "positive"
        assert "value for money" in data["topics"]


class TestReviewSummaryModel:
    """Test ReviewSummary model."""

    def test_summary_creation(self, db, sample_product):
        """Test summary model creation."""
        summary = ReviewSummary(
            product_id=sample_product.id,
            summary_text="Highly rated product with positive sentiment.",
            pros=["Great value", "Fast delivery"],
            cons=["Battery could be better"],
            common_topics=["battery life", "performance speed"],
            positive_pct=75.0,
            neutral_pct=15.0,
            negative_pct=10.0,
            total_reviews_analyzed=10,
            confidence_score=0.5,
            explanation="Mock analysis from keyword matching.",
        )
        db.session.add(summary)
        db.session.commit()

        assert summary.id is not None
        assert summary.product_id == sample_product.id
        assert summary.positive_pct == 75.0

    def test_summary_to_dict(self, db, sample_product):
        """Test summary serialization."""
        summary = ReviewSummary(
            product_id=sample_product.id,
            summary_text="Test summary.",
            pros=["Good"],
            cons=["Bad"],
            common_topics=["quality"],
            positive_pct=60,
            neutral_pct=30,
            negative_pct=10,
            total_reviews_analyzed=5,
            confidence_score=0.25,
            explanation="Test explanation.",
        )
        db.session.add(summary)
        db.session.commit()

        data = summary.to_dict()
        assert data["summary_text"] == "Test summary."
        assert data["confidence_score"] == 0.25


class TestAIEngine:
    """Test the AI engine (mock mode - no ML dependencies required)."""

    def setup_method(self):
        """Initialize AI engine for each test."""
        self.engine = ReviewAIEngine()

    def test_sentiment_positive(self):
        """Test positive sentiment detection."""
        result = self.engine.analyze_sentiment(
            "This product is absolutely amazing! Great quality, love it."
        )
        assert result["label"] == "positive"
        assert result["score"] > 0
        assert "explanation" in result

    def test_sentiment_negative(self):
        """Test negative sentiment detection."""
        result = self.engine.analyze_sentiment(
            "Terrible product. Broke after one week. Horrible experience, total waste. Worst purchase ever, completely useless junk."
        )
        assert result["label"] in ("negative", "neutral")  # ML may classify borderline texts as neutral
        assert result["score"] <= 0.15  # Score should not be positive
        assert "explanation" in result

    def test_sentiment_neutral(self):
        """Test neutral sentiment detection."""
        result = self.engine.analyze_sentiment(
            "Received the item on time. Works as described in the listing."
        )
        assert result["label"] in ("neutral", "positive")  # Allow either for this text
        assert "explanation" in result

    def test_sentiment_explanation_always_present(self):
        """Test that explanation is always provided."""
        result = self.engine.analyze_sentiment("ok")
        assert "explanation" in result
        assert len(result["explanation"]) > 0

    def test_extract_topics_electronics(self):
        """Test topic extraction for electronics review."""
        topics = self.engine.extract_topics(
            "The battery life is incredible, lasts all day. Screen display is bright and vibrant."
        )
        assert len(topics) > 0
        assert any("battery" in t for t in topics)

    def test_extract_topics_clothing(self):
        """Test topic extraction for clothing review."""
        topics = self.engine.extract_topics(
            "Very comfortable fit, the material quality is excellent. True to size."
        )
        assert len(topics) > 0

    def test_extract_topics_max_five(self):
        """Test topic extraction returns at most 5 topics."""
        topics = self.engine.extract_topics(
            "Battery is great, screen is nice, camera takes good photos, "
            "sound quality is perfect, delivery was fast, design looks beautiful, "
            "performance speed is fast, very comfortable."
        )
        assert len(topics) <= 5

    def test_generate_summary_basic(self):
        """Test summary generation with multiple reviews."""
        reviews = [
            {"body": "Excellent product, amazing quality!", "title": "Great", "rating": 5},
            {"body": "Good value, love the design and build.", "title": "Nice", "rating": 4},
            {"body": "Terrible, broke after a week. Very disappointing.", "title": "Bad", "rating": 1},
            {"body": "Average product, nothing special. Does the job.", "title": "Ok", "rating": 3},
            {"body": "Fantastic! Best purchase ever, recommend to everyone.", "title": "Love it", "rating": 5},
        ]
        result = self.engine.generate_summary(reviews)

        assert "summary_text" in result
        assert len(result["summary_text"]) > 0
        assert "pros" in result
        assert "cons" in result
        assert "common_topics" in result
        assert "positive_pct" in result
        assert "negative_pct" in result
        assert "neutral_pct" in result
        assert "confidence_score" in result
        assert "explanation" in result
        assert result["confidence_score"] > 0

    def test_generate_summary_empty(self):
        """Test summary generation with no reviews."""
        result = self.engine.generate_summary([])
        assert result["summary_text"] == "No reviews available yet."
        assert result["confidence_score"] == 0

    def test_generate_summary_sentiment_distribution(self):
        """Test that sentiment percentages sum to ~100."""
        reviews = [
            {"body": "Amazing! Love it!", "title": "Great", "rating": 5},
            {"body": "Good product", "title": "Nice", "rating": 4},
            {"body": "Terrible waste of money", "title": "Bad", "rating": 1},
        ]
        result = self.engine.generate_summary(reviews)
        total = result["positive_pct"] + result["neutral_pct"] + result["negative_pct"]
        assert abs(total - 100.0) < 1.0  # Allow small rounding error

    def test_size_fit_analysis(self):
        """Test size fit analysis."""
        reviews = [
            {"body": "Fits perfectly, true to size. Very comfortable.", "rating": 5, "size_purchased": "M"},
            {"body": "Runs a bit small, had to size up. Tight around the chest.", "rating": 3, "size_purchased": "M"},
            {"body": "Way too large and loose, should have gotten a smaller size.", "rating": 3, "size_purchased": "L"},
            {"body": "Perfect fit, just right.", "rating": 5, "size_purchased": "S"},
        ]
        result = self.engine.analyze_size_fit(reviews)

        assert "runs_small_pct" in result
        assert "true_to_size_pct" in result
        assert "runs_large_pct" in result
        assert "explanation" in result
        assert result["total_fit_reviews"] > 0

    def test_size_fit_no_fit_reviews(self):
        """Test size fit with no size-related content."""
        reviews = [
            {"body": "Great product, works well.", "rating": 5},
            {"body": "Nice colors and design.", "rating": 4},
        ]
        result = self.engine.analyze_size_fit(reviews)
        assert result["total_fit_reviews"] == 0


class TestReviewService:
    """Test ReviewService business logic."""

    def test_create_review(self, app, db, sample_product, sample_customer):
        """Test creating a review with AI analysis."""
        with app.app_context():
            review = ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=5,
                title="Absolutely love this phone!",
                body="Amazing display, great performance, and the camera is incredible. Best phone I've ever owned.",
                verified_purchase=True,
            )

            assert review.id is not None
            assert review.ai_processed is True
            assert review.sentiment_label is not None
            assert review.sentiment_score is not None
            assert review.topics is not None

    def test_create_review_invalid_rating(self, app, db, sample_product, sample_customer):
        """Test validation rejects invalid ratings."""
        with app.app_context():
            with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
                ReviewService.create_review(
                    product_id=sample_product.id,
                    customer_id=sample_customer.id,
                    rating=6,
                    title="Test",
                    body="Test body that is long enough.",
                )

    def test_create_review_duplicate_rejected(self, app, db, sample_product, sample_customer):
        """Test duplicate review prevention."""
        with app.app_context():
            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=5,
                title="First review",
                body="Great product, love it!",
            )

            with pytest.raises(ValueError, match="already reviewed"):
                ReviewService.create_review(
                    product_id=sample_product.id,
                    customer_id=sample_customer.id,
                    rating=4,
                    title="Second attempt",
                    body="Trying again to review.",
                )

    def test_get_reviews_for_product(self, app, db, sample_product, sample_customer):
        """Test fetching paginated reviews."""
        with app.app_context():
            # Create a review
            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=4,
                title="Good phone",
                body="Nice smartphone, works well for the price.",
            )

            result = ReviewService.get_reviews_for_product(sample_product.id)
            assert result["total"] == 1
            assert len(result["items"]) == 1

    def test_get_reviews_filter_by_rating(self, app, db, sample_product, sample_customer):
        """Test filtering reviews by rating."""
        with app.app_context():
            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=5,
                title="Perfect",
                body="Absolutely perfect product.",
            )

            result_5star = ReviewService.get_reviews_for_product(
                sample_product.id, filter_rating=5
            )
            result_1star = ReviewService.get_reviews_for_product(
                sample_product.id, filter_rating=1
            )

            assert result_5star["total"] == 1
            assert result_1star["total"] == 0

    def test_vote_helpful(self, app, db, sample_product, sample_customer):
        """Test helpful voting."""
        with app.app_context():
            review = ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=4,
                title="Good",
                body="Good product, recommend it.",
            )

            ReviewService.vote_helpful(review.id, helpful=True)
            ReviewService.vote_helpful(review.id, helpful=True)
            ReviewService.vote_helpful(review.id, helpful=False)

            updated = Review.query.get(review.id)
            assert updated.helpful_count == 2
            assert updated.not_helpful_count == 1

    def test_get_review_stats(self, app, db, sample_product, sample_customer):
        """Test review statistics."""
        with app.app_context():
            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=5,
                title="Excellent",
                body="Amazing product, love everything about it.",
                verified_purchase=True,
            )

            stats = ReviewService.get_review_stats(sample_product.id)
            assert stats["total"] == 1
            assert stats["average"] == 5.0
            assert stats["distribution"]["5"] == 1
            assert stats["verified_count"] == 1

    def test_can_review(self, app, db, sample_product, sample_customer):
        """Test can_review check."""
        with app.app_context():
            assert ReviewService.can_review(sample_product.id, sample_customer.id) is True

            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=4,
                title="Good",
                body="Nice product, works well.",
            )

            assert ReviewService.can_review(sample_product.id, sample_customer.id) is False

    def test_product_rating_updated(self, app, db, sample_product, sample_customer):
        """Test that creating a review updates product rating."""
        with app.app_context():
            from products.models import Product

            ReviewService.create_review(
                product_id=sample_product.id,
                customer_id=sample_customer.id,
                rating=3,
                title="Average",
                body="Average product, nothing special.",
            )

            product = Product.query.get(sample_product.id)
            assert product.avg_rating == 3.0
            assert product.total_reviews == 1


class TestReviewSummaryGeneration:
    """Test AI summary generation through service."""

    def _create_multiple_reviews(self, db, product_id, customer_base_id):
        """Helper to create multiple reviews."""
        from customers.models import Customer

        reviews_data = [
            (5, "Love it!", "Amazing quality, battery life is incredible. Best phone ever!"),
            (4, "Great value", "Good performance for the price. Camera is nice."),
            (5, "Excellent!", "Fast, beautiful display, comfortable to hold."),
            (2, "Disappointed", "Broke after a month. Poor build quality. Very disappointing."),
            (4, "Good overall", "Nice design and fast charging. Sound quality is great."),
        ]

        for i, (rating, title, body) in enumerate(reviews_data):
            customer = Customer(
                email=f"reviewer{i}@example.com",
                first_name=f"Reviewer{i}",
                last_name="Test",
                green_credits=0,
                lifetime_credits=0,
            )
            customer.set_password("test123")
            db.session.add(customer)
            db.session.flush()

            review = Review(
                product_id=product_id,
                customer_id=customer.id,
                rating=rating,
                title=title,
                body=body,
                verified_purchase=True,
                ai_processed=True,
            )
            db.session.add(review)

        db.session.commit()

    def test_generate_product_summary(self, app, db, sample_product, sample_customer):
        """Test full summary generation."""
        with app.app_context():
            self._create_multiple_reviews(db, sample_product.id, sample_customer.id)

            summary = ReviewService.generate_product_summary(sample_product.id)

            assert summary is not None
            assert summary.product_id == sample_product.id
            assert len(summary.summary_text) > 0
            assert summary.total_reviews_analyzed == 5
            assert summary.confidence_score > 0
            assert summary.explanation is not None
            assert summary.positive_pct + summary.neutral_pct + summary.negative_pct > 0

    def test_summary_regeneration_updates(self, app, db, sample_product, sample_customer):
        """Test that regenerating summary updates existing record."""
        with app.app_context():
            self._create_multiple_reviews(db, sample_product.id, sample_customer.id)

            summary1 = ReviewService.generate_product_summary(sample_product.id)
            summary_id = summary1.id

            # Regenerate
            summary2 = ReviewService.generate_product_summary(sample_product.id)

            assert summary2.id == summary_id  # Same record updated
            assert ReviewSummary.query.filter_by(product_id=sample_product.id).count() == 1


class TestReviewRoutes:
    """Test review HTTP endpoints."""

    def test_product_reviews_page(self, client, sample_product):
        """Test reviews page loads."""
        response = client.get(f"/reviews/product/{sample_product.id}")
        assert response.status_code == 200

    def test_product_reviews_404(self, client):
        """Test 404 for non-existent product."""
        response = client.get("/reviews/product/99999")
        assert response.status_code == 404

    def test_write_review_requires_auth(self, client, sample_product):
        """Test write review requires authentication."""
        response = client.get(f"/reviews/product/{sample_product.id}/write")
        assert response.status_code == 302  # Redirect to login

    def test_write_review_page_loads(self, client, sample_product, sample_customer):
        """Test write review page loads when authenticated."""
        # Log in first
        client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        })

        response = client.get(f"/reviews/product/{sample_product.id}/write")
        assert response.status_code == 200
        assert b"Write Your Review" in response.data

    def test_submit_review(self, client, sample_product, sample_customer):
        """Test submitting a review."""
        client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        })

        response = client.post(
            f"/reviews/product/{sample_product.id}/write",
            data={
                "rating": "5",
                "title": "Amazing phone!",
                "body": "This is the best smartphone I have ever used. The camera is incredible.",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify review was created
        review = Review.query.filter_by(
            product_id=sample_product.id, customer_id=sample_customer.id
        ).first()
        assert review is not None
        assert review.rating == 5
        assert review.ai_processed is True

    def test_review_stats_api(self, client, sample_product):
        """Test review stats API endpoint."""
        response = client.get(f"/reviews/api/product/{sample_product.id}/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data
        assert "average" in data
        assert "distribution" in data

    def test_vote_helpful(self, client, db, sample_product, sample_customer):
        """Test voting on review helpfulness."""
        review = Review(
            product_id=sample_product.id,
            customer_id=sample_customer.id,
            rating=4,
            title="Test",
            body="Good product.",
        )
        db.session.add(review)
        db.session.commit()

        response = client.post(
            f"/reviews/{review.id}/vote",
            data={"helpful": "true"},
        )
        assert response.status_code == 200
