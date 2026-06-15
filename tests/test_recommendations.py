"""Tests for AI Size Recommendation - Phase 3."""
import pytest
from recommendations.models import SizePurchaseHistory, SizeRecommendation
from recommendations.services import SizeRecommendationService
from recommendations.ai_engine import SizeRecommendationEngine


class TestSizePurchaseHistoryModel:
    """Test SizePurchaseHistory model."""

    def test_create_purchase_history(self, db, sample_product, sample_customer, sample_category):
        """Test creating a purchase history record."""
        record = SizePurchaseHistory(
            customer_id=sample_customer.id,
            product_id=sample_product.id,
            category_id=sample_category.id,
            size_purchased="M",
            brand="TestBrand",
            kept=True,
        )
        db.session.add(record)
        db.session.commit()

        assert record.id is not None
        assert record.size_purchased == "M"
        assert record.kept is True

    def test_purchase_history_with_return(self, db, sample_product, sample_customer, sample_category):
        """Test recording a returned item."""
        record = SizePurchaseHistory(
            customer_id=sample_customer.id,
            product_id=sample_product.id,
            category_id=sample_category.id,
            size_purchased="L",
            brand="TestBrand",
            kept=False,
            return_reason="too_large",
        )
        db.session.add(record)
        db.session.commit()

        assert record.kept is False
        assert record.return_reason == "too_large"


class TestSizeRecommendationModel:
    """Test SizeRecommendation model."""

    def test_create_recommendation(self, db, sample_product, sample_customer):
        """Test creating a cached recommendation."""
        rec = SizeRecommendation(
            customer_id=sample_customer.id,
            product_id=sample_product.id,
            recommended_size="M",
            confidence=0.85,
            explanation="You purchased M 4 times and kept all.",
            factors={"purchase_history": 0.9, "return_patterns": 0.7},
        )
        db.session.add(rec)
        db.session.commit()

        assert rec.id is not None
        assert rec.recommended_size == "M"

    def test_recommendation_to_dict(self, db, sample_product, sample_customer):
        """Test serialization."""
        rec = SizeRecommendation(
            customer_id=sample_customer.id,
            product_id=sample_product.id,
            recommended_size="L",
            confidence=0.72,
            explanation="Test explanation.",
            factors={"purchase_history": 0.8},
        )
        db.session.add(rec)
        db.session.commit()

        data = rec.to_dict()
        assert data["recommended_size"] == "L"
        assert data["confidence"] == 0.72
        assert data["confidence_pct"] == 72
        assert "explanation" in data


class TestSizeRecommendationEngine:
    """Test the AI engine for size recommendations."""

    def setup_method(self):
        """Initialize engine."""
        self.engine = SizeRecommendationEngine()

    def test_recommend_with_history_exact_match(self):
        """Test recommendation with clear purchase history."""
        history = [
            {"size": "M", "kept": True, "brand": "Nike", "category": "Clothing"},
            {"size": "M", "kept": True, "brand": "Adidas", "category": "Clothing"},
            {"size": "M", "kept": True, "brand": "Nike", "category": "Clothing"},
            {"size": "L", "kept": False, "return_reason": "too_large", "brand": "Nike", "category": "Clothing"},
        ]

        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=history,
            product_reviews=[],
            brand="Nike",
        )

        assert result["recommended_size"] == "M"
        assert result["confidence"] > 0.5
        assert "explanation" in result
        assert len(result["explanation"]) > 0

    def test_recommend_with_no_history(self):
        """Test recommendation with no purchase history."""
        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=[],
            product_reviews=[],
        )

        assert result["recommended_size"] is not None
        assert result["confidence"] > 0
        assert "explanation" in result

    def test_recommend_with_reviews_runs_small(self):
        """Test that reviews mentioning 'runs small' affect recommendation."""
        reviews = [
            {"body": "Runs really small, had to size up", "size_purchased": "M", "rating": 3},
            {"body": "Very tight fit, too small for usual size", "size_purchased": "L", "rating": 3},
            {"body": "Recommend sizing up, runs small", "size_purchased": "M", "rating": 4},
        ]

        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=[],
            product_reviews=reviews,
        )

        # Should recommend larger sizes since product runs small
        assert result["recommended_size"] in ["L", "XL"]
        assert "small" in result["explanation"].lower() or "size" in result["explanation"].lower()

    def test_recommend_with_reviews_runs_large(self):
        """Test that reviews mentioning 'runs large' affect recommendation."""
        reviews = [
            {"body": "Way too large and loose, size down", "size_purchased": "M", "rating": 3},
            {"body": "Very oversized, had to size down", "size_purchased": "L", "rating": 3},
        ]

        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=[],
            product_reviews=reviews,
        )

        assert result["recommended_size"] in ["S", "M"]

    def test_recommend_penalizes_returned_sizes(self):
        """Test that returned sizes are penalized."""
        history = [
            {"size": "L", "kept": False, "return_reason": "too_large", "brand": "Nike", "category": "Clothing"},
            {"size": "M", "kept": True, "brand": "Nike", "category": "Clothing"},
            {"size": "M", "kept": True, "brand": "Adidas", "category": "Clothing"},
        ]

        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=history,
            product_reviews=[],
            brand="Nike",
        )

        # Should NOT recommend L (returned as too large)
        assert result["recommended_size"] != "L"
        assert result["recommended_size"] == "M"

    def test_recommend_brand_consistency(self):
        """Test brand-specific sizing is factored in."""
        history = [
            {"size": "L", "kept": True, "brand": "Nike", "category": "Clothing"},
            {"size": "L", "kept": True, "brand": "Nike", "category": "Clothing"},
            {"size": "M", "kept": True, "brand": "Adidas", "category": "Clothing"},
        ]

        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L", "XL"],
            purchase_history=history,
            product_reviews=[],
            brand="Nike",
        )

        # Nike-specific history says L, so should recommend L
        assert result["recommended_size"] == "L"

    def test_recommend_empty_sizes(self):
        """Test with no available sizes."""
        result = self.engine.recommend_size(
            available_sizes=[],
            purchase_history=[],
            product_reviews=[],
        )

        assert result["recommended_size"] is None
        assert result["confidence"] == 0

    def test_recommend_always_has_explanation(self):
        """Test that explanation is always provided."""
        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L"],
            purchase_history=[{"size": "M", "kept": True, "brand": "X", "category": "C"}],
            product_reviews=[],
        )

        assert "explanation" in result
        assert len(result["explanation"]) > 10

    def test_recommend_factors_included(self):
        """Test that factor breakdown is provided."""
        result = self.engine.recommend_size(
            available_sizes=["S", "M", "L"],
            purchase_history=[{"size": "M", "kept": True, "brand": "X", "category": "C"}],
            product_reviews=[],
        )

        assert "factors" in result
        assert isinstance(result["factors"], dict)

    def test_size_distance(self):
        """Test size distance calculation."""
        assert self.engine._size_distance("S", "S") == 0
        assert self.engine._size_distance("S", "M") == 1
        assert self.engine._size_distance("S", "XL") == 3
        assert self.engine._size_distance("30", "34") == 2


class TestSizeRecommendationService:
    """Test SizeRecommendationService business logic."""

    @pytest.fixture
    def clothing_product(self, db, sample_category):
        """Create a clothing product with sizes."""
        from products.models import Product
        product = Product(
            name="Test T-Shirt",
            slug="test-tshirt",
            description="A test shirt.",
            price=1999,
            category_id=sample_category.id,
            brand="Nike",
            sku="TST-SHIRT-001",
            stock_quantity=20,
            available_sizes=["S", "M", "L", "XL"],
        )
        db.session.add(product)
        db.session.commit()
        return product

    def test_record_purchase(self, app, db, clothing_product, sample_customer, sample_category):
        """Test recording a purchase."""
        with app.app_context():
            record = SizeRecommendationService.record_purchase(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
                category_id=sample_category.id,
                size_purchased="M",
                brand="Nike",
                kept=True,
            )

            assert record.id is not None
            assert record.size_purchased == "M"
            assert record.kept is True

    def test_get_recommendation_no_sizes(self, app, db, sample_product, sample_customer):
        """Test recommendation for product without sizes."""
        with app.app_context():
            result = SizeRecommendationService.get_recommendation(
                customer_id=sample_customer.id,
                product_id=sample_product.id,  # Standard product, no sizes
            )
            assert result is None

    def test_get_recommendation_with_history(self, app, db, clothing_product, sample_customer, sample_category):
        """Test recommendation with purchase history."""
        with app.app_context():
            # Add purchase history
            for _ in range(3):
                SizeRecommendationService.record_purchase(
                    customer_id=sample_customer.id,
                    product_id=clothing_product.id,
                    category_id=sample_category.id,
                    size_purchased="M",
                    brand="Nike",
                    kept=True,
                )

            result = SizeRecommendationService.get_recommendation(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
            )

            assert result is not None
            assert result["recommended_size"] == "M"
            assert result["confidence"] > 0
            assert "explanation" in result
            assert "confidence_pct" in result

    def test_recommendation_caching(self, app, db, clothing_product, sample_customer, sample_category):
        """Test that recommendations are cached."""
        with app.app_context():
            SizeRecommendationService.record_purchase(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
                category_id=sample_category.id,
                size_purchased="M",
                brand="Nike",
                kept=True,
            )

            # First call generates
            result1 = SizeRecommendationService.get_recommendation(
                sample_customer.id, clothing_product.id
            )

            # Verify it's cached
            cached = SizeRecommendation.query.filter_by(
                customer_id=sample_customer.id, product_id=clothing_product.id
            ).first()
            assert cached is not None

            # Second call uses cache
            result2 = SizeRecommendationService.get_recommendation(
                sample_customer.id, clothing_product.id
            )
            assert result1["recommended_size"] == result2["recommended_size"]

    def test_cache_invalidation_on_new_purchase(self, app, db, clothing_product, sample_customer, sample_category):
        """Test that new purchases invalidate the cache."""
        with app.app_context():
            SizeRecommendationService.record_purchase(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
                category_id=sample_category.id,
                size_purchased="M",
                brand="Nike",
                kept=True,
            )

            # Generate recommendation (creates cache)
            SizeRecommendationService.get_recommendation(
                sample_customer.id, clothing_product.id
            )

            # Record new purchase - should invalidate cache
            SizeRecommendationService.record_purchase(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
                category_id=sample_category.id,
                size_purchased="L",
                brand="Nike",
                kept=True,
            )

            # Cache should be cleared
            cached = SizeRecommendation.query.filter_by(
                customer_id=sample_customer.id
            ).first()
            assert cached is None

    def test_get_customer_size_profile_empty(self, app, db, sample_customer):
        """Test size profile with no history."""
        with app.app_context():
            profile = SizeRecommendationService.get_customer_size_profile(
                sample_customer.id
            )
            assert profile["has_history"] is False
            assert profile["total_purchases"] == 0

    def test_get_customer_size_profile_with_data(self, app, db, clothing_product, sample_customer, sample_category):
        """Test size profile with purchase data."""
        with app.app_context():
            for _ in range(3):
                SizeRecommendationService.record_purchase(
                    customer_id=sample_customer.id,
                    product_id=clothing_product.id,
                    category_id=sample_category.id,
                    size_purchased="M",
                    brand="Nike",
                    kept=True,
                )

            profile = SizeRecommendationService.get_customer_size_profile(
                sample_customer.id
            )
            assert profile["has_history"] is True
            assert profile["total_purchases"] == 3
            assert "Nike" in profile["brands"]


class TestRecommendationRoutes:
    """Test recommendation HTTP endpoints."""

    @pytest.fixture
    def clothing_product(self, db, sample_category):
        """Create a clothing product with sizes (needs clothing category)."""
        from products.models import Product, Category
        # Create clothing category
        clothing_cat = Category(name="Clothing", slug="clothing", icon="👕", description="Fashion")
        db.session.add(clothing_cat)
        db.session.flush()

        product = Product(
            name="Route Test Shirt",
            slug="route-test-shirt",
            description="A test shirt for routes.",
            price=1999,
            category_id=clothing_cat.id,
            brand="Nike",
            sku="TST-ROUTE-SHIRT",
            stock_quantity=20,
            available_sizes=["S", "M", "L", "XL"],
        )
        db.session.add(product)
        db.session.commit()
        return product

    def test_recommendation_requires_auth(self, client, clothing_product):
        """Test that recommendation endpoint requires login."""
        response = client.get(f"/recommendations/size/{clothing_product.id}")
        assert response.status_code == 302  # Redirect to login

    def test_recommendation_returns_json(self, client, clothing_product, sample_customer, sample_category, db):
        """Test JSON response for recommendation."""
        # Login
        client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        })

        # Add some history
        from recommendations.models import SizePurchaseHistory
        for _ in range(2):
            h = SizePurchaseHistory(
                customer_id=sample_customer.id,
                product_id=clothing_product.id,
                category_id=sample_category.id,
                size_purchased="M",
                brand="Nike",
                kept=True,
            )
            db.session.add(h)
        db.session.commit()

        response = client.get(f"/recommendations/api/size/{clothing_product.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert "recommended_size" in data
        assert "confidence" in data
        assert "explanation" in data

    def test_recommendation_htmx_partial(self, client, clothing_product, sample_customer, sample_category, db):
        """Test HTMX partial response."""
        client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        })

        from recommendations.models import SizePurchaseHistory
        h = SizePurchaseHistory(
            customer_id=sample_customer.id,
            product_id=clothing_product.id,
            category_id=sample_category.id,
            size_purchased="L",
            brand="Nike",
            kept=True,
        )
        db.session.add(h)
        db.session.commit()

        response = client.get(
            f"/recommendations/size/{clothing_product.id}",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b"AI Size Recommendation" in response.data

    def test_size_profile_endpoint(self, client, sample_customer):
        """Test size profile endpoint."""
        client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        })

        response = client.get("/recommendations/profile")
        assert response.status_code == 200
