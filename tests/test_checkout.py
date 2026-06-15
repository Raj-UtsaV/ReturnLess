"""Tests for Checkout - Phase 4."""
import pytest
from checkout.models import CartItem, Order, OrderItem
from checkout.services import CartService, OrderService


class TestCartService:
    """Test cart operations."""

    def test_add_to_cart(self, app, db, sample_product, sample_customer):
        """Test adding item to cart."""
        with app.app_context():
            item = CartService.add_to_cart(
                customer_id=sample_customer.id,
                product_id=sample_product.id,
                quantity=1,
            )
            assert item.id is not None
            assert item.quantity == 1
            assert item.product_id == sample_product.id

    def test_add_to_cart_increments_quantity(self, app, db, sample_product, sample_customer):
        """Test adding same item again increments quantity."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            item = CartService.add_to_cart(sample_customer.id, sample_product.id, 2)
            assert item.quantity == 3

    def test_add_to_cart_validates_stock(self, app, db, sample_product, sample_customer):
        """Test stock validation."""
        with app.app_context():
            sample_product.stock_quantity = 2
            db.session.commit()

            with pytest.raises(ValueError, match="Only 2 available"):
                CartService.add_to_cart(sample_customer.id, sample_product.id, 5)

    def test_add_to_cart_validates_size_required(self, app, db, sample_category, sample_customer):
        """Test size validation for clothing."""
        from products.models import Product
        with app.app_context():
            product = Product(
                name="Sized Product", slug="sized-product",
                description="Test", price=999,
                category_id=sample_category.id, brand="Test",
                sku="TST-SIZED", stock_quantity=10,
                available_sizes=["S", "M", "L"],
            )
            db.session.add(product)
            db.session.commit()

            with pytest.raises(ValueError, match="Please select a size"):
                CartService.add_to_cart(sample_customer.id, product.id, 1)

    def test_add_to_cart_validates_size_value(self, app, db, sample_category, sample_customer):
        """Test invalid size rejected."""
        from products.models import Product
        with app.app_context():
            product = Product(
                name="Sized Product 2", slug="sized-product-2",
                description="Test", price=999,
                category_id=sample_category.id, brand="Test",
                sku="TST-SIZED2", stock_quantity=10,
                available_sizes=["S", "M", "L"],
            )
            db.session.add(product)
            db.session.commit()

            with pytest.raises(ValueError, match="not available"):
                CartService.add_to_cart(sample_customer.id, product.id, 1, size="XXL")

    def test_update_quantity(self, app, db, sample_product, sample_customer):
        """Test updating cart item quantity."""
        with app.app_context():
            item = CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            updated = CartService.update_quantity(item.id, sample_customer.id, 3)
            assert updated.quantity == 3

    def test_update_quantity_to_zero_removes(self, app, db, sample_product, sample_customer):
        """Test setting quantity to 0 removes item."""
        with app.app_context():
            item = CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            result = CartService.update_quantity(item.id, sample_customer.id, 0)
            assert result is None
            assert CartItem.query.get(item.id) is None

    def test_remove_from_cart(self, app, db, sample_product, sample_customer):
        """Test removing item from cart."""
        with app.app_context():
            item = CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            result = CartService.remove_from_cart(item.id, sample_customer.id)
            assert result is True

    def test_get_cart(self, app, db, sample_product, sample_customer):
        """Test getting full cart with totals."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 2)
            cart = CartService.get_cart(sample_customer.id)

            assert cart["item_count"] == 2
            assert cart["subtotal"] == sample_product.price * 2
            assert "total" in cart
            assert "green_credits_earn" in cart

    def test_get_cart_free_delivery(self, app, db, sample_product, sample_customer):
        """Test free delivery threshold."""
        with app.app_context():
            # Product price is 29999, well over 999 threshold
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            cart = CartService.get_cart(sample_customer.id)
            assert cart["delivery_fee"] == 0

    def test_clear_cart(self, app, db, sample_product, sample_customer):
        """Test clearing all cart items."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 2)
            CartService.clear_cart(sample_customer.id)
            cart = CartService.get_cart(sample_customer.id)
            assert cart["item_count"] == 0

    def test_get_cart_count(self, app, db, sample_product, sample_customer):
        """Test cart count."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 3)
            count = CartService.get_cart_count(sample_customer.id)
            assert count == 3


class TestOrderService:
    """Test order creation and management."""

    def test_create_order(self, app, db, sample_product, sample_customer):
        """Test order creation from cart."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)

            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test User",
                shipping_address="123 Test St",
                shipping_city="Mumbai",
                shipping_state="Maharashtra",
                shipping_postal="400001",
                shipping_phone="+91 9876543210",
            )

            assert order.id is not None
            assert order.order_number.startswith("RL-")
            assert order.status == "confirmed"
            assert order.total > 0
            assert order.credits_earned > 0

    def test_create_order_awards_credits(self, app, db, sample_product, sample_customer):
        """Test that order awards green credits."""
        with app.app_context():
            initial_credits = sample_customer.green_credits
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)

            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )

            from customers.models import Customer
            customer = db.session.get(Customer, sample_customer.id)
            assert customer.green_credits == initial_credits + order.credits_earned

    def test_create_order_deducts_stock(self, app, db, sample_product, sample_customer):
        """Test that order deducts product stock."""
        with app.app_context():
            initial_stock = sample_product.stock_quantity
            CartService.add_to_cart(sample_customer.id, sample_product.id, 2)

            OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )

            from products.models import Product
            product = db.session.get(Product, sample_product.id)
            assert product.stock_quantity == initial_stock - 2

    def test_create_order_clears_cart(self, app, db, sample_product, sample_customer):
        """Test that order clears the cart."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)

            OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )

            cart = CartService.get_cart(sample_customer.id)
            assert cart["item_count"] == 0

    def test_create_order_empty_cart_fails(self, app, db, sample_customer):
        """Test order creation fails with empty cart."""
        with app.app_context():
            with pytest.raises(ValueError, match="cart is empty"):
                OrderService.create_order(
                    customer_id=sample_customer.id,
                    shipping_name="Test", shipping_address="123 St",
                    shipping_city="Delhi", shipping_state="Delhi",
                    shipping_postal="110001", shipping_phone="9999999999",
                )

    def test_create_order_eco_shipping(self, app, db, sample_product, sample_customer):
        """Test eco shipping adds bonus credits."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)

            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
                eco_shipping=True,
            )

            assert order.eco_shipping is True
            assert order.delivery_fee == 0
            # +10 eco bonus included
            assert order.credits_earned == sample_product.green_credits_earn + 10

    def test_get_customer_orders(self, app, db, sample_product, sample_customer):
        """Test getting customer orders."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )

            orders = OrderService.get_customer_orders(sample_customer.id)
            assert orders["total"] == 1

    def test_cancel_order(self, app, db, sample_product, sample_customer):
        """Test order cancellation restores stock and deducts credits."""
        with app.app_context():
            initial_stock = sample_product.stock_quantity
            initial_credits = sample_customer.green_credits

            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )

            cancelled = OrderService.cancel_order(order.id, sample_customer.id)
            assert cancelled.status == "cancelled"

            from products.models import Product
            from customers.models import Customer
            product = db.session.get(Product, sample_product.id)
            customer = db.session.get(Customer, sample_customer.id)
            assert product.stock_quantity == initial_stock
            assert customer.green_credits == initial_credits


class TestCheckoutRoutes:
    """Test checkout HTTP endpoints."""

    def test_cart_page_requires_auth(self, client):
        """Test cart page requires login."""
        response = client.get("/cart")
        assert response.status_code == 302

    def test_cart_page_loads(self, client, sample_customer):
        """Test cart page loads when authenticated."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.get("/cart")
        assert response.status_code == 200

    def test_add_to_cart_route(self, client, sample_product, sample_customer):
        """Test add to cart via POST."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.post("/cart/add", data={
            "product_id": sample_product.id,
            "quantity": 1,
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_checkout_page_loads(self, client, sample_product, sample_customer):
        """Test checkout page with items in cart."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        client.post("/cart/add", data={"product_id": sample_product.id, "quantity": 1})
        response = client.get("/checkout")
        assert response.status_code == 200
        assert b"Checkout" in response.data

    def test_checkout_empty_cart_redirects(self, client, sample_customer):
        """Test checkout with empty cart redirects."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.get("/checkout", follow_redirects=True)
        assert response.status_code == 200

    def test_place_order(self, client, sample_product, sample_customer):
        """Test placing an order."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        client.post("/cart/add", data={"product_id": sample_product.id, "quantity": 1})

        response = client.post("/checkout", data={
            "shipping_name": "Test User",
            "shipping_address": "123 Test Street",
            "shipping_city": "Mumbai",
            "shipping_state": "Maharashtra",
            "shipping_postal": "400001",
            "shipping_phone": "9876543210",
            "payment_method": "mock_card",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Order Confirmed" in response.data

    def test_order_history_page(self, client, sample_customer):
        """Test order history page."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.get("/orders")
        assert response.status_code == 200

    def test_api_cart(self, client, sample_product, sample_customer):
        """Test cart API endpoint."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        client.post("/cart/add", data={"product_id": sample_product.id, "quantity": 1})

        response = client.get("/api/cart")
        assert response.status_code == 200
        data = response.get_json()
        assert data["item_count"] == 1
        assert "subtotal" in data
