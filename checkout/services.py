"""Checkout service layer - cart management, order creation, validation."""
import uuid
from typing import Optional
from shared.database import db
from checkout.models import CartItem, Order, OrderItem


class CartService:
    """Service for shopping cart operations."""

    @staticmethod
    def add_to_cart(
        customer_id: int,
        product_id: int,
        quantity: int = 1,
        size: Optional[str] = None,
    ) -> CartItem:
        """
        Add item to cart or update quantity if already exists.

        Validates stock availability before adding.
        """
        from products.models import Product

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found")
        if not product.is_active:
            raise ValueError("Product is no longer available")
        if not product.in_stock:
            raise ValueError("Product is out of stock")

        # Validate size if product has sizes
        if product.available_sizes and size:
            if size not in product.available_sizes:
                raise ValueError(f"Size '{size}' is not available for this product")
        elif product.available_sizes and not size:
            raise ValueError("Please select a size")

        # Check if item already in cart
        existing = CartItem.query.filter_by(
            customer_id=customer_id,
            product_id=product_id,
            size=size,
        ).first()

        if existing:
            new_qty = existing.quantity + quantity
            if new_qty > product.stock_quantity:
                raise ValueError(f"Only {product.stock_quantity} available")
            existing.quantity = new_qty
            db.session.commit()
            return existing

        # Validate quantity against stock
        if quantity > product.stock_quantity:
            raise ValueError(f"Only {product.stock_quantity} available")

        item = CartItem(
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            size=size,
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update_quantity(cart_item_id: int, customer_id: int, quantity: int) -> Optional[CartItem]:
        """Update cart item quantity."""
        item = CartItem.query.filter_by(id=cart_item_id, customer_id=customer_id).first()
        if not item:
            return None

        if quantity <= 0:
            db.session.delete(item)
            db.session.commit()
            return None

        if quantity > item.product.stock_quantity:
            raise ValueError(f"Only {item.product.stock_quantity} available")

        item.quantity = quantity
        db.session.commit()
        return item

    @staticmethod
    def remove_from_cart(cart_item_id: int, customer_id: int) -> bool:
        """Remove item from cart."""
        item = CartItem.query.filter_by(id=cart_item_id, customer_id=customer_id).first()
        if not item:
            return False
        db.session.delete(item)
        db.session.commit()
        return True

    @staticmethod
    def get_cart(customer_id: int) -> dict:
        """Get full cart with totals."""
        items = CartItem.query.filter_by(customer_id=customer_id).all()

        subtotal = sum(item.subtotal for item in items)
        total_credits = sum(item.green_credits_total for item in items)
        item_count = sum(item.quantity for item in items)

        # Free delivery over ₹999
        delivery_fee = 0 if subtotal >= 999 else 49
        total = subtotal + delivery_fee

        return {
            "items": items,
            "item_count": item_count,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "total": total,
            "green_credits_earn": total_credits,
            "free_delivery_threshold": 999,
            "amount_to_free_delivery": max(0, 999 - subtotal),
        }

    @staticmethod
    def clear_cart(customer_id: int):
        """Remove all items from cart."""
        CartItem.query.filter_by(customer_id=customer_id).delete()
        db.session.commit()

    @staticmethod
    def get_cart_count(customer_id: int) -> int:
        """Get total number of items in cart."""
        items = CartItem.query.filter_by(customer_id=customer_id).all()
        return sum(item.quantity for item in items)


class OrderService:
    """Service for order management."""

    @staticmethod
    def create_order(
        customer_id: int,
        shipping_name: str,
        shipping_address: str,
        shipping_city: str,
        shipping_state: str,
        shipping_postal: str,
        shipping_phone: str,
        eco_shipping: bool = False,
        payment_method: str = "mock_card",
    ) -> Order:
        """
        Create an order from the customer's cart.

        Steps:
        1. Validate cart is not empty
        2. Validate stock for all items
        3. Create order + order items
        4. Deduct stock
        5. Award green credits
        6. Record size purchases (for AI recommendations)
        7. Clear cart
        """
        from products.models import Product
        from customers.models import Customer

        # Get cart
        cart = CartService.get_cart(customer_id)
        if not cart["items"]:
            raise ValueError("Your cart is empty")

        # Validate stock for all items
        for item in cart["items"]:
            product = db.session.get(Product, item.product_id)
            if not product or product.stock_quantity < item.quantity:
                raise ValueError(f"'{item.product.name}' is no longer available in the requested quantity")

        # Generate order number
        order_number = f"RL-{uuid.uuid4().hex[:8].upper()}"

        # Calculate totals
        subtotal = cart["subtotal"]
        delivery_fee = cart["delivery_fee"]
        if eco_shipping:
            delivery_fee = 0  # Eco shipping is free (slower)

        total = subtotal + delivery_fee

        # Calculate credits
        credits_earned = cart["green_credits_earn"]
        if eco_shipping:
            credits_earned += 10  # +10 for eco shipping

        # Estimate delivery
        max_delivery = max(item.product.delivery_days_max for item in cart["items"])
        min_delivery = min(item.product.delivery_days_min for item in cart["items"])
        if eco_shipping:
            max_delivery += 3
            min_delivery += 2

        # Create order
        order = Order(
            customer_id=customer_id,
            order_number=order_number,
            status="confirmed",
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            credits_earned=credits_earned,
            eco_shipping=eco_shipping,
            shipping_name=shipping_name,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_postal=shipping_postal,
            shipping_phone=shipping_phone,
            payment_method=payment_method,
            payment_status="paid",
            estimated_delivery_min=min_delivery,
            estimated_delivery_max=max_delivery,
        )
        db.session.add(order)
        db.session.flush()

        # Create order items + deduct stock
        for cart_item in cart["items"]:
            product = db.session.get(Product, cart_item.product_id)

            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price_at_purchase=product.price,
                size=cart_item.size,
                product_name=product.name,
                product_thumbnail=product.thumbnail,
                product_type=product.product_type,
                credits_earned=cart_item.green_credits_total,
            )
            db.session.add(order_item)

            # Deduct stock
            product.stock_quantity -= cart_item.quantity

            # Record size purchase for AI recommendations
            if cart_item.size and product.category_id:
                from recommendations.services import SizeRecommendationService
                SizeRecommendationService.record_purchase(
                    customer_id=customer_id,
                    product_id=cart_item.product_id,
                    category_id=product.category_id,
                    size_purchased=cart_item.size,
                    brand=product.brand,
                    kept=True,  # Assumed kept until return
                )

        # Award green credits
        customer = db.session.get(Customer, customer_id)
        customer.green_credits += credits_earned
        customer.lifetime_credits += credits_earned

        # Clear cart
        CartService.clear_cart(customer_id)

        db.session.commit()
        return order

    @staticmethod
    def get_order(order_id: int, customer_id: int) -> Optional[Order]:
        """Get order by ID (scoped to customer)."""
        return Order.query.filter_by(id=order_id, customer_id=customer_id).first()

    @staticmethod
    def get_order_by_number(order_number: str, customer_id: int) -> Optional[Order]:
        """Get order by order number (scoped to customer)."""
        return Order.query.filter_by(order_number=order_number, customer_id=customer_id).first()

    @staticmethod
    def get_customer_orders(customer_id: int, page: int = 1, per_page: int = 10) -> dict:
        """Get paginated orders for a customer."""
        pagination = (
            Order.query
            .filter_by(customer_id=customer_id)
            .order_by(Order.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }

    @staticmethod
    def cancel_order(order_id: int, customer_id: int) -> Optional[Order]:
        """Cancel an order (only if still confirmed/pending)."""
        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            return None

        if order.status not in ("pending", "confirmed"):
            raise ValueError("Order cannot be cancelled in current status")

        # Restore stock
        for item in order.items:
            product = db.session.get(item.product.__class__, item.product_id)
            if product:
                product.stock_quantity += item.quantity

        # Deduct credits
        from customers.models import Customer
        customer = db.session.get(Customer, customer_id)
        customer.green_credits = max(0, customer.green_credits - order.credits_earned)

        order.status = "cancelled"
        order.payment_status = "refunded"
        db.session.commit()
        return order
