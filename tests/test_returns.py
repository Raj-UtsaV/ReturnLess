"""Tests for Returns - Phase 5."""
import pytest
from returns.models import ReturnRequest
from returns.services import ReturnService, CANCEL_SHIPPED_PENALTY, RETURN_STANDARD_PENALTY, RETURN_SERIAL_PENALTY
from checkout.services import CartService, OrderService
from checkout.models import Order


class TestReturnServiceCancel:
    """Test cancellation logic."""

    def _create_order(self, db, sample_product, sample_customer, status="confirmed"):
        """Helper to create an order and set its status."""
        CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
        order = OrderService.create_order(
            customer_id=sample_customer.id,
            shipping_name="Test", shipping_address="123 St",
            shipping_city="Delhi", shipping_state="Delhi",
            shipping_postal="110001", shipping_phone="9999999999",
        )
        order.status = status
        db.session.commit()
        return order

    def test_can_cancel_confirmed_order(self, app, db, sample_product, sample_customer):
        """Test that confirmed orders can be cancelled without penalty."""
        with app.app_context():
            order = self._create_order(db, sample_product, sample_customer, "confirmed")
            info = ReturnService.can_cancel(order)
            assert info["can_cancel"] is True
            assert info["penalty"] == 0

    def test_can_cancel_shipped_order_with_penalty(self, app, db, sample_product, sample_customer):
        """Test that shipped orders can be cancelled with penalty."""
        with app.app_context():
            order = self._create_order(db, sample_product, sample_customer, "shipped")
            info = ReturnService.can_cancel(order)
            assert info["can_cancel"] is True
            assert info["penalty"] == CANCEL_SHIPPED_PENALTY

    def test_cannot_cancel_delivered_order(self, app, db, sample_product, sample_customer):
        """Test that delivered orders cannot be cancelled."""
        with app.app_context():
            order = self._create_order(db, sample_product, sample_customer, "delivered")
            info = ReturnService.can_cancel(order)
            assert info["can_cancel"] is False

    def test_cancel_order_deducts_credits(self, app, db, sample_product, sample_customer):
        """Test cancellation deducts earned credits."""
        with app.app_context():
            initial_credits = sample_customer.green_credits
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )
            credits_earned = order.credits_earned

            result = ReturnService.cancel_order(order.id, sample_customer.id, "changed_mind")

            from customers.models import Customer
            customer = db.session.get(Customer, sample_customer.id)
            # Credits should be back to initial (earned ones removed)
            assert customer.green_credits == initial_credits
            assert result["success"] is True

    def test_cancel_shipped_order_extra_penalty(self, app, db, sample_product, sample_customer):
        """Test shipped cancellation applies extra penalty."""
        with app.app_context():
            initial_credits = sample_customer.green_credits
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )
            order.status = "shipped"
            db.session.commit()

            result = ReturnService.cancel_order(order.id, sample_customer.id, "changed_mind")

            from customers.models import Customer
            customer = db.session.get(Customer, sample_customer.id)
            # Should be initial - penalty (earned credits + shipped penalty)
            expected = initial_credits - CANCEL_SHIPPED_PENALTY
            assert customer.green_credits == max(0, expected)
            assert result["credits_deducted"] > 0


class TestReturnServiceReturn:
    """Test return logic."""

    def _create_delivered_order(self, db, sample_product, sample_customer):
        """Helper to create a delivered order."""
        CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
        order = OrderService.create_order(
            customer_id=sample_customer.id,
            shipping_name="Test", shipping_address="123 St",
            shipping_city="Delhi", shipping_state="Delhi",
            shipping_postal="110001", shipping_phone="9999999999",
        )
        order.status = "delivered"
        db.session.commit()
        return order

    def test_can_return_delivered_order(self, app, db, sample_product, sample_customer):
        """Test that delivered items can be returned."""
        with app.app_context():
            order = self._create_delivered_order(db, sample_product, sample_customer)
            item = order.items.first()
            info = ReturnService.can_return(order, item)
            assert info["can_return"] is True

    def test_cannot_return_non_delivered(self, app, db, sample_product, sample_customer):
        """Test that non-delivered items cannot be returned."""
        with app.app_context():
            CartService.add_to_cart(sample_customer.id, sample_product.id, 1)
            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )
            item = order.items.first()
            info = ReturnService.can_return(order, item)
            assert info["can_return"] is False

    def test_return_defective_no_penalty(self, app, db, sample_product, sample_customer):
        """Test defective returns have no penalty."""
        with app.app_context():
            penalty = ReturnService.calculate_return_penalty(sample_customer.id, "defective")
            assert penalty["penalty"] == 0
            assert penalty["is_defective"] is True

    def test_return_non_defective_standard_penalty(self, app, db, sample_product, sample_customer):
        """Test non-defective returns have standard penalty."""
        with app.app_context():
            penalty = ReturnService.calculate_return_penalty(sample_customer.id, "changed_mind")
            assert penalty["penalty"] == RETURN_STANDARD_PENALTY
            assert penalty["is_defective"] is False

    def test_return_wrong_item_no_penalty(self, app, db, sample_product, sample_customer):
        """Test wrong item returns have no penalty."""
        with app.app_context():
            penalty = ReturnService.calculate_return_penalty(sample_customer.id, "wrong_item")
            assert penalty["penalty"] == 0

    def test_return_request_created(self, app, db, sample_product, sample_customer):
        """Test return request is properly created."""
        with app.app_context():
            order = self._create_delivered_order(db, sample_product, sample_customer)
            item = order.items.first()
            result = ReturnService.request_return(
                order_id=order.id,
                order_item_id=item.id,
                customer_id=sample_customer.id,
                reason="changed_mind",
                reason_detail="Just didn't like it.",
            )

            assert result["success"] is True
            # credits_deducted = item_earned (20) + penalty (15) = 35
            assert result["credits_deducted"] == item.credits_earned + RETURN_STANDARD_PENALTY

            req = ReturnRequest.query.filter_by(order_item_id=item.id).first()
            assert req is not None
            assert req.request_type == "return"
            assert req.status == "approved"

    def test_return_defective_restores_credits(self, app, db, sample_product, sample_customer):
        """Test defective return reverses earned credits only (no extra penalty)."""
        with app.app_context():
            order = self._create_delivered_order(db, sample_product, sample_customer)

            from customers.models import Customer
            customer_before = db.session.get(Customer, sample_customer.id)
            credits_before = customer_before.green_credits

            item = order.items.first()
            item_credits = item.credits_earned
            result = ReturnService.request_return(
                order_id=order.id,
                order_item_id=item.id,
                customer_id=sample_customer.id,
                reason="defective",
            )

            # Defective: deducted = just the item's earned credits, no extra
            assert result["credits_deducted"] == item_credits
            customer_after = db.session.get(Customer, sample_customer.id)
            expected = credits_before - item_credits
            assert customer_after.green_credits == max(0, expected)

    def test_return_non_defective_extra_penalty(self, app, db, sample_product, sample_customer):
        """Test non-defective return deducts earned credits + extra penalty."""
        with app.app_context():
            order = self._create_delivered_order(db, sample_product, sample_customer)

            from customers.models import Customer
            customer_before = db.session.get(Customer, sample_customer.id)
            credits_before = customer_before.green_credits

            item = order.items.first()
            item_credits = item.credits_earned

            result = ReturnService.request_return(
                order_id=order.id,
                order_item_id=item.id,
                customer_id=sample_customer.id,
                reason="changed_mind",
            )

            # Total deducted = earned credits + penalty
            assert result["credits_deducted"] == item_credits + RETURN_STANDARD_PENALTY
            customer_after = db.session.get(Customer, sample_customer.id)
            expected = credits_before - item_credits - RETURN_STANDARD_PENALTY
            assert customer_after.green_credits == max(0, expected)

    def test_return_stock_restored(self, app, db, sample_product, sample_customer):
        """Test that returned items restore stock."""
        with app.app_context():
            from products.models import Product
            initial_stock = sample_product.stock_quantity

            CartService.add_to_cart(sample_customer.id, sample_product.id, 2)
            order = OrderService.create_order(
                customer_id=sample_customer.id,
                shipping_name="Test", shipping_address="123 St",
                shipping_city="Delhi", shipping_state="Delhi",
                shipping_postal="110001", shipping_phone="9999999999",
            )
            order.status = "delivered"
            db.session.commit()

            item = order.items.first()
            ReturnService.request_return(
                order_id=order.id,
                order_item_id=item.id,
                customer_id=sample_customer.id,
                reason="defective",
            )

            product = db.session.get(Product, sample_product.id)
            assert product.stock_quantity == initial_stock  # 2 deducted then 2 restored


class TestReturnRoutes:
    """Test return HTTP endpoints."""

    def _login_and_create_order(self, client, db, sample_product, sample_customer, status="confirmed"):
        """Helper to login and create order."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        client.post("/cart/add", data={"product_id": sample_product.id, "quantity": 1})
        client.post("/checkout", data={
            "shipping_name": "Test", "shipping_address": "123 St",
            "shipping_city": "Delhi", "shipping_state": "Delhi",
            "shipping_postal": "110001", "shipping_phone": "9999",
            "payment_method": "mock_card",
        })
        order = Order.query.filter_by(customer_id=sample_customer.id).first()
        if status != "confirmed":
            order.status = status
            db.session.commit()
        return order

    def test_cancel_page_loads(self, client, db, sample_product, sample_customer):
        """Test cancel page loads."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer)
        response = client.get(f"/returns/cancel/{order.id}")
        assert response.status_code == 200
        assert b"Cancel Order" in response.data

    def test_cancel_shipped_shows_warning(self, client, db, sample_product, sample_customer):
        """Test shipped order cancel shows penalty warning."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer, "shipped")
        response = client.get(f"/returns/cancel/{order.id}")
        assert response.status_code == 200
        assert b"already been shipped" in response.data

    def test_cancel_submit(self, client, db, sample_product, sample_customer):
        """Test submitting a cancellation."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer)
        response = client.post(f"/returns/cancel/{order.id}", data={
            "reason": "changed_mind",
            "reason_detail": "Found a better deal",
        }, follow_redirects=True)
        assert response.status_code == 200

        updated_order = db.session.get(Order, order.id)
        assert updated_order.status == "cancelled"

    def test_return_page_requires_delivered(self, client, db, sample_product, sample_customer):
        """Test return page redirects for non-delivered orders."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer)
        item = order.items.first()
        response = client.get(f"/returns/return/{order.id}/{item.id}", follow_redirects=True)
        assert response.status_code == 200  # Redirected with flash

    def test_return_page_loads_for_delivered(self, client, db, sample_product, sample_customer):
        """Test return page loads for delivered orders."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer, "delivered")
        item = order.items.first()
        response = client.get(f"/returns/return/{order.id}/{item.id}")
        assert response.status_code == 200
        assert b"Return Item" in response.data

    def test_return_submit(self, client, db, sample_product, sample_customer):
        """Test submitting a return."""
        order = self._login_and_create_order(client, db, sample_product, sample_customer, "delivered")
        item = order.items.first()
        response = client.post(f"/returns/return/{order.id}/{item.id}", data={
            "reason": "defective",
            "reason_detail": "Screen has dead pixels",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_return_history_page(self, client, db, sample_customer):
        """Test return history page."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.get("/returns/history")
        assert response.status_code == 200
