"""Tests for product catalog - Phase 1."""
import pytest


class TestProductModel:
    """Test Product model properties and methods."""

    def test_product_creation(self, sample_product):
        """Test that a product is created correctly."""
        assert sample_product.id is not None
        assert sample_product.name == "Test Smartphone"
        assert sample_product.price == 29999
        assert sample_product.product_type == "standard"

    def test_product_is_refurbished_flag(self, sample_product, sample_refurbished_product):
        """Test is_refurbished property."""
        assert sample_product.is_refurbished is False
        assert sample_refurbished_product.is_refurbished is True

    def test_product_savings_calculation(self, sample_product):
        """Test savings calculation."""
        savings = sample_product.savings
        assert savings["amount"] == 5000.0
        assert savings["percentage"] == 14.3

    def test_product_savings_no_discount(self, db, sample_category):
        """Test savings when no original price."""
        from products.models import Product
        product = Product(
            name="No Discount",
            slug="no-discount",
            description="Test",
            price=1000,
            original_price=None,
            category_id=sample_category.id,
            brand="Test",
            sku="TST-ND",
            stock_quantity=1,
        )
        db.session.add(product)
        db.session.commit()
        assert product.savings == {"amount": 0, "percentage": 0}

    def test_product_in_stock(self, sample_product):
        """Test in_stock property."""
        assert sample_product.in_stock is True
        sample_product.stock_quantity = 0
        assert sample_product.in_stock is False

    def test_product_delivery_estimate(self, sample_product):
        """Test delivery estimate string."""
        assert sample_product.delivery_estimate == "3-5 days"

    def test_refurbished_product_fields(self, sample_refurbished_product):
        """Test refurbished-specific fields."""
        assert sample_refurbished_product.grade == "A"
        assert sample_refurbished_product.warranty_months == 12
        assert sample_refurbished_product.carbon_saved_kg == 120.5
        assert sample_refurbished_product.refurb_reason == "Corporate lease return"

    def test_product_to_dict(self, sample_product):
        """Test product serialization."""
        data = sample_product.to_dict()
        assert data["id"] == sample_product.id
        assert data["name"] == "Test Smartphone"
        assert data["product_type"] == "standard"
        assert "grade" not in data

    def test_refurbished_product_to_dict(self, sample_refurbished_product):
        """Test refurbished product serialization includes extra fields."""
        data = sample_refurbished_product.to_dict()
        assert data["product_type"] == "refurbished"
        assert data["grade"] == "A"
        assert data["warranty_months"] == 12
        assert data["carbon_saved_kg"] == 120.5


class TestProductService:
    """Test ProductService business logic."""

    def test_get_product_by_slug(self, app, sample_product):
        """Test fetching product by slug."""
        from products.services import ProductService
        with app.app_context():
            product = ProductService.get_product_by_slug("test-smartphone")
            assert product is not None
            assert product.name == "Test Smartphone"

    def test_get_product_by_slug_not_found(self, app, db):
        """Test fetching non-existent product."""
        from products.services import ProductService
        with app.app_context():
            product = ProductService.get_product_by_slug("does-not-exist")
            assert product is None

    def test_get_catalog_returns_dict(self, app, sample_product):
        """Test catalog returns proper pagination dict."""
        from products.services import ProductService
        with app.app_context():
            result = ProductService.get_catalog()
            assert "items" in result
            assert "total" in result
            assert "page" in result
            assert "pages" in result
            assert result["total"] >= 1

    def test_get_catalog_filter_by_type(self, app, sample_product, sample_refurbished_product):
        """Test filtering by product type."""
        from products.services import ProductService
        with app.app_context():
            standard = ProductService.get_catalog(product_type="standard")
            refurbished = ProductService.get_catalog(product_type="refurbished")
            assert all(p.product_type == "standard" for p in standard["items"])
            assert all(p.product_type == "refurbished" for p in refurbished["items"])

    def test_get_catalog_search(self, app, sample_product):
        """Test search functionality."""
        from products.services import ProductService
        with app.app_context():
            result = ProductService.get_catalog(search="Smartphone")
            assert result["total"] >= 1
            assert any("Smartphone" in p.name for p in result["items"])

    def test_get_catalog_filter_by_brand(self, app, sample_product):
        """Test filtering by brand."""
        from products.services import ProductService
        with app.app_context():
            result = ProductService.get_catalog(brand="TestBrand")
            assert result["total"] >= 1

    def test_get_catalog_price_range(self, app, sample_product, sample_refurbished_product):
        """Test price range filtering."""
        from products.services import ProductService
        with app.app_context():
            result = ProductService.get_catalog(min_price=40000, max_price=60000)
            assert all(40000 <= p.price <= 60000 for p in result["items"])

    def test_get_featured_products(self, app, sample_product):
        """Test featured products query."""
        from products.services import ProductService
        with app.app_context():
            featured = ProductService.get_featured_products()
            assert len(featured) >= 1

    def test_get_all_brands(self, app, sample_product):
        """Test brands retrieval."""
        from products.services import ProductService
        with app.app_context():
            brands = ProductService.get_all_brands()
            assert "TestBrand" in brands

    def test_get_price_range(self, app, sample_product, sample_refurbished_product):
        """Test price range calculation."""
        from products.services import ProductService
        with app.app_context():
            price_range = ProductService.get_price_range()
            assert price_range["min"] <= 29999
            assert price_range["max"] >= 49999


class TestProductRoutes:
    """Test product HTTP endpoints."""

    def test_catalog_page_loads(self, client):
        """Test catalog page returns 200."""
        response = client.get("/products/")
        assert response.status_code == 200

    def test_catalog_page_content(self, client, sample_product):
        """Test catalog page contains product."""
        response = client.get("/products/")
        assert b"Test Smartphone" in response.data

    def test_product_detail_page(self, client, sample_product):
        """Test product detail page loads."""
        response = client.get("/products/test-smartphone")
        assert response.status_code == 200
        assert b"Test Smartphone" in response.data

    def test_product_detail_404(self, client):
        """Test 404 for non-existent product."""
        response = client.get("/products/does-not-exist")
        assert response.status_code == 404

    def test_product_search_api(self, client, sample_product):
        """Test search API endpoint."""
        response = client.get("/products/api/search?q=Smart")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_product_search_api_short_query(self, client):
        """Test search API rejects short queries."""
        response = client.get("/products/api/search?q=S")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []


class TestCategoryModel:
    """Test Category model."""

    def test_category_creation(self, sample_category):
        """Test category is created."""
        assert sample_category.id is not None
        assert sample_category.name == "Electronics"
        assert sample_category.slug == "electronics"


class TestCustomerModel:
    """Test Customer model."""

    def test_customer_creation(self, sample_customer):
        """Test customer creation."""
        assert sample_customer.id is not None
        assert sample_customer.email == "test@example.com"

    def test_customer_password(self, sample_customer):
        """Test password hashing."""
        assert sample_customer.check_password("password123") is True
        assert sample_customer.check_password("wrongpass") is False

    def test_customer_full_name(self, sample_customer):
        """Test full_name property."""
        assert sample_customer.full_name == "Test User"

    def test_customer_credit_tier_silver(self, sample_customer):
        """Test silver tier."""
        sample_customer.lifetime_credits = 100
        assert sample_customer.credit_tier["name"] == "Silver"

    def test_customer_credit_tier_gold(self, sample_customer):
        """Test gold tier."""
        sample_customer.lifetime_credits = 500
        assert sample_customer.credit_tier["name"] == "Gold"

    def test_customer_credit_tier_platinum(self, sample_customer):
        """Test platinum tier."""
        sample_customer.lifetime_credits = 1500
        assert sample_customer.credit_tier["name"] == "Platinum"

    def test_customer_credit_tier_green_hero(self, sample_customer):
        """Test green hero tier."""
        sample_customer.lifetime_credits = 3000
        assert sample_customer.credit_tier["name"] == "Green Hero"


class TestCustomerRoutes:
    """Test customer auth routes."""

    def test_login_page_loads(self, client):
        """Test login page renders."""
        response = client.get("/account/login")
        assert response.status_code == 200
        assert b"Sign In" in response.data or b"Welcome Back" in response.data

    def test_register_page_loads(self, client):
        """Test register page renders."""
        response = client.get("/account/register")
        assert response.status_code == 200
        assert b"Join ReturnLess" in response.data

    def test_register_new_customer(self, client, db):
        """Test customer registration."""
        response = client.post("/account/register", data={
            "email": "new@example.com",
            "password": "secret123",
            "first_name": "New",
            "last_name": "User",
        }, follow_redirects=True)
        assert response.status_code == 200

        from customers.models import Customer
        customer = Customer.query.filter_by(email="new@example.com").first()
        assert customer is not None
        assert customer.first_name == "New"

    def test_login_valid_credentials(self, client, sample_customer):
        """Test login with valid credentials."""
        response = client.post("/account/login", data={
            "email": "test@example.com",
            "password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_invalid_credentials(self, client, sample_customer):
        """Test login with invalid credentials."""
        response = client.post("/account/login", data={
            "email": "test@example.com",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Invalid" in response.data


class TestHomePage:
    """Test main index page."""

    def test_homepage_loads(self, client):
        """Test homepage returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_homepage_contains_branding(self, client):
        """Test homepage has brand elements."""
        response = client.get("/")
        assert b"ReturnLess" in response.data
