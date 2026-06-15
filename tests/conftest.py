"""Pytest configuration and shared fixtures."""
import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from shared.database import db as _db
from products.models import Product, Category
from customers.models import Customer


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db(app):
    """Create a fresh database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_category(db):
    """Create a sample category."""
    category = Category(
        name="Electronics",
        slug="electronics",
        description="Electronic devices",
        icon="💻",
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def sample_product(db, sample_category):
    """Create a sample standard product."""
    product = Product(
        name="Test Smartphone",
        slug="test-smartphone",
        description="A test smartphone for testing purposes.",
        short_description="Test phone",
        price=29999,
        original_price=34999,
        category_id=sample_category.id,
        brand="TestBrand",
        sku="TST-PHONE-001",
        stock_quantity=10,
        product_type="standard",
        green_credits_earn=20,
        avg_rating=4.5,
        total_reviews=100,
        delivery_days_min=3,
        delivery_days_max=5,
        free_delivery=True,
        specifications={"Display": "6.5 inch", "RAM": "8GB"},
    )
    db.session.add(product)
    db.session.commit()
    return product


@pytest.fixture
def sample_refurbished_product(db, sample_category):
    """Create a sample refurbished product."""
    product = Product(
        name="Refurbished Laptop",
        slug="refurbished-laptop",
        description="A certified refurbished laptop.",
        short_description="Refurb laptop",
        price=49999,
        original_price=89999,
        category_id=sample_category.id,
        brand="TestBrand",
        sku="TST-LAPTOP-REFURB",
        stock_quantity=5,
        product_type="refurbished",
        green_credits_earn=50,
        avg_rating=4.6,
        total_reviews=50,
        grade="A",
        warranty_months=12,
        carbon_saved_kg=120.5,
        refurb_reason="Corporate lease return",
        inspection_notes="Excellent condition.",
        refurbished_by="ReturnLess Labs",
        specifications={"CPU": "i7", "RAM": "16GB"},
    )
    db.session.add(product)
    db.session.commit()
    return product


@pytest.fixture
def sample_customer(db):
    """Create a sample customer."""
    customer = Customer(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        green_credits=100,
        lifetime_credits=100,
    )
    customer.set_password("password123")
    db.session.add(customer)
    db.session.commit()
    return customer
