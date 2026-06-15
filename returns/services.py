"""Return service layer - cancellation and return logic with credit adjustments.

Credit Penalty Rules:
- Cancel (pending/confirmed): Reverse earned credits only (no extra penalty)
- Cancel (shipped): Reverse earned credits + 10 extra penalty
- Return (defective/wrong item): Reverse earned credits only (no extra penalty)
- Return (non-defective, customer's fault): Reverse earned credits + 15 extra penalty
- Return (serial returner 3+/30 days): Reverse earned credits + 30 extra penalty

The "earned credits" = what that specific product gave on purchase (20 for standard, 50 for refurbished).
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
from shared.database import db
from returns.models import ReturnRequest
from checkout.models import Order, OrderItem


# Extra penalty ON TOP of reversing earned credits
CANCEL_SHIPPED_PENALTY = 10   # Extra for cancelling after shipment
RETURN_STANDARD_PENALTY = 15  # Extra for returning without valid defect
RETURN_SERIAL_PENALTY = 30    # Extra for frequent returners (3+ in 30 days)


class ReturnService:
    """Service for return and cancellation operations."""

    # Valid reasons
    CANCEL_REASONS = {
        "changed_mind": "Changed my mind",
        "ordered_wrong": "Ordered wrong item",
        "found_cheaper": "Found cheaper elsewhere",
        "delivery_too_slow": "Delivery taking too long",
        "other": "Other reason",
    }

    RETURN_REASONS = {
        "defective": "Product is defective/damaged",
        "wrong_item": "Received wrong item",
        "not_as_described": "Not as described",
        "size_issue": "Size doesn't fit",
        "changed_mind": "Changed my mind",
        "other": "Other reason",
    }

    # Defective reasons (no penalty)
    DEFECTIVE_REASONS = {"defective", "wrong_item", "not_as_described"}

    @staticmethod
    def can_cancel(order: Order) -> dict:
        """
        Check if an order can be cancelled and what penalties apply.

        Returns:
            dict with: can_cancel, penalty, explanation
        """
        if order.status == "cancelled":
            return {"can_cancel": False, "penalty": 0, "explanation": "Order is already cancelled."}

        if order.status == "delivered":
            return {"can_cancel": False, "penalty": 0, "explanation": "Order has been delivered. Use return instead."}

        # Check if customer has credits (must have > 0 to process)
        from customers.models import Customer
        customer = db.session.get(Customer, order.customer_id)
        if customer and customer.green_credits <= 0:
            return {
                "can_cancel": False,
                "penalty": 0,
                "explanation": (
                    "Your Green Credit balance is too low to process this cancellation. "
                    "Please contact customer support at support@returnless.ai for further assistance."
                ),
            }

        if order.status in ("pending", "confirmed"):
            return {
                "can_cancel": True,
                "penalty": 0,
                "explanation": "Cancel without penalty. Full refund will be processed.",
            }

        if order.status == "shipped":
            return {
                "can_cancel": True,
                "penalty": CANCEL_SHIPPED_PENALTY,
                "explanation": (
                    f"Order has already been shipped. Cancellation will reverse your earned credits "
                    f"plus an additional {CANCEL_SHIPPED_PENALTY} credits penalty for in-transit cancellation."
                ),
            }

        return {"can_cancel": False, "penalty": 0, "explanation": "Order cannot be cancelled in current status."}

    @staticmethod
    def can_return(order: Order, order_item: OrderItem) -> dict:
        """
        Check if an order item can be returned.

        Returns:
            dict with: can_return, explanation
        """
        if order.status != "delivered":
            return {"can_return": False, "explanation": "Order has not been delivered yet. Use cancel instead."}

        # Check if customer has credits (must have > 0 to process)
        from customers.models import Customer
        customer = db.session.get(Customer, order.customer_id)
        if customer and customer.green_credits <= 0:
            return {
                "can_return": False,
                "explanation": (
                    "Your Green Credit balance is too low to process this return. "
                    "Please contact customer support at support@returnless.ai for further assistance."
                ),
            }

        # Check if already returned
        existing = ReturnRequest.query.filter(
            ReturnRequest.order_item_id == order_item.id,
            ReturnRequest.status.in_(["pending", "approved", "completed"])
        ).first()

        if existing:
            return {"can_return": False, "explanation": "A return has already been requested for this item."}

        # Check return window (14 days)
        if order.created_at:
            # Handle both naive and aware datetimes
            now = datetime.now(timezone.utc)
            created = order.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_since = (now - created).days
            if days_since > 14:
                return {"can_return": False, "explanation": "Return window (14 days) has expired."}

        return {"can_return": True, "explanation": "Item is eligible for return."}

    @staticmethod
    def calculate_return_penalty(customer_id: int, reason: str) -> dict:
        """
        Calculate credit penalty for a return.

        Rules:
        - Defective/wrong item: No penalty
        - Non-defective: -15 credits
        - Serial returner (3+ returns in 30 days): -30 credits
        """
        is_defective = reason in ReturnService.DEFECTIVE_REASONS

        if is_defective:
            return {
                "penalty": 0,
                "is_serial": False,
                "is_defective": True,
                "explanation": "Earned credits will be reversed. If verified as a genuine defect after inspection, the penalty will be refunded to your account.",
            }

        # Check if serial returner
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_returns = ReturnRequest.query.filter(
            ReturnRequest.customer_id == customer_id,
            ReturnRequest.request_type == "return",
            ReturnRequest.created_at >= thirty_days_ago,
            ReturnRequest.status.in_(["approved", "completed"]),
        ).count()

        is_serial = recent_returns >= 3

        if is_serial:
            return {
                "penalty": RETURN_SERIAL_PENALTY,
                "is_serial": True,
                "is_defective": False,
                "explanation": (
                    f"Serial returner penalty: earned credits will be reversed + {RETURN_SERIAL_PENALTY} extra credits deducted. "
                    f"You've made {recent_returns} returns in the last 30 days. "
                    f"Consider using AI size recommendations to reduce returns."
                ),
            }

        return {
            "penalty": RETURN_STANDARD_PENALTY,
            "is_serial": False,
            "is_defective": False,
            "explanation": (
                f"Earned credits from this purchase will be reversed + {RETURN_STANDARD_PENALTY} extra credits penalty. "
                f"Returns without a valid defect incur an additional penalty for carelessness."
            ),
        }

    @staticmethod
    def cancel_order(
        order_id: int,
        customer_id: int,
        reason: str = "changed_mind",
        reason_detail: Optional[str] = None,
    ) -> dict:
        """
        Cancel an order with appropriate credit adjustments.

        Returns:
            dict with: success, return_request, message, credits_deducted
        """
        from customers.models import Customer
        from products.models import Product

        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            raise ValueError("Order not found")

        cancel_info = ReturnService.can_cancel(order)
        if not cancel_info["can_cancel"]:
            raise ValueError(cancel_info["explanation"])

        penalty = cancel_info["penalty"]
        customer = db.session.get(Customer, customer_id)

        # Create return request for each item
        for item in order.items:
            item_credits = item.credits_earned
            total_item_deduction = item_credits + penalty
            return_req = ReturnRequest(
                order_id=order.id,
                order_item_id=item.id,
                customer_id=customer_id,
                request_type="cancel",
                status="completed",
                reason=reason,
                reason_detail=reason_detail,
                is_defective=False,
                credits_deducted=total_item_deduction,
                credit_explanation=(
                    f"Reversed {item_credits} earned credits"
                    + (f" + {penalty} extra penalty (shipped cancellation)" if penalty > 0 else " (cancelled before shipping)")
                ),
                refund_amount=item.subtotal,
                refund_status="processed",
            )
            db.session.add(return_req)

            # Restore stock
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock_quantity += item.quantity

        # Deduct original credits earned + penalty
        total_deduction = order.credits_earned + penalty
        customer.green_credits = max(0, customer.green_credits - total_deduction)
        customer.lifetime_credits = max(0, customer.lifetime_credits - order.credits_earned)

        # Update order status
        order.status = "cancelled"
        order.payment_status = "refunded"

        db.session.commit()

        # Route each cancelled item to a warehouse (admin visibility)
        try:
            from routing.services import RoutingService
            for item in order.items:
                ret_req = ReturnRequest.query.filter_by(
                    order_id=order.id, order_item_id=item.id
                ).first()
                if ret_req:
                    RoutingService.route_return(
                        return_request_id=ret_req.id,
                        customer_state=order.shipping_state or "Maharashtra",
                    )
        except Exception:
            pass  # Don't block cancel if routing fails

        message = "Order cancelled successfully. Full refund will be processed in 3-5 business days."
        if penalty > 0:
            message += f" Your {order.credits_earned} earned credits were reversed + {penalty} extra penalty for in-transit cancellation."
        else:
            message += f" Your {order.credits_earned} earned credits from this order have been reversed."

        return {
            "success": True,
            "message": message,
            "credits_deducted": total_deduction,
            "refund_amount": order.total,
        }

    @staticmethod
    def request_return(
        order_id: int,
        order_item_id: int,
        customer_id: int,
        reason: str,
        reason_detail: Optional[str] = None,
    ) -> dict:
        """
        Request a return for a delivered order item.

        Returns:
            dict with: success, return_request, message, credits_deducted, refund_amount
        """
        from customers.models import Customer
        from products.models import Product

        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            raise ValueError("Order not found")

        order_item = db.session.get(OrderItem, order_item_id)
        if not order_item or order_item.order_id != order.id:
            raise ValueError("Order item not found")

        return_check = ReturnService.can_return(order, order_item)
        if not return_check["can_return"]:
            raise ValueError(return_check["explanation"])

        # Calculate penalty
        penalty_info = ReturnService.calculate_return_penalty(customer_id, reason)
        penalty = penalty_info["penalty"]
        is_defective = penalty_info["is_defective"]

        customer = db.session.get(Customer, customer_id)

        # Create return request
        return_req = ReturnRequest(
            order_id=order.id,
            order_item_id=order_item_id,
            customer_id=customer_id,
            request_type="return",
            status="approved",  # Auto-approve for now
            reason=reason,
            reason_detail=reason_detail,
            is_defective=is_defective,
            credits_deducted=0,  # Updated below after calculation
            credit_explanation=penalty_info["explanation"],
            refund_amount=order_item.subtotal,
            refund_status="processed",
        )
        db.session.add(return_req)

        # Credit adjustments
        item_credits = order_item.credits_earned
        if is_defective:
            # Defective: reverse earned credits only (no extra penalty)
            total_deduction = item_credits
            customer.green_credits = max(0, customer.green_credits - item_credits)
            customer.lifetime_credits = max(0, customer.lifetime_credits - item_credits)
            return_req.credits_deducted = total_deduction
            return_req.credit_explanation = f"Reversed {item_credits} earned credits. If verified as defective, penalty will be refunded after inspection."
        else:
            # Non-defective: reverse earned credits + extra penalty
            total_deduction = item_credits + penalty
            customer.green_credits = max(0, customer.green_credits - total_deduction)
            customer.lifetime_credits = max(0, customer.lifetime_credits - item_credits)
            return_req.credits_deducted = total_deduction
            return_req.credit_explanation = f"Reversed {item_credits} earned credits + {penalty} extra penalty (product was fine, customer carelessness)."

        # Restore stock
        product = db.session.get(Product, order_item.product_id)
        if product:
            product.stock_quantity += order_item.quantity

        # Record size return for AI (if applicable)
        if order_item.size and reason == "size_issue":
            from recommendations.services import SizeRecommendationService
            SizeRecommendationService.record_purchase(
                customer_id=customer_id,
                product_id=order_item.product_id,
                category_id=product.category_id if product else 1,
                size_purchased=order_item.size,
                brand=product.brand if product else None,
                kept=False,
                return_reason="too_small" if "small" in (reason_detail or "").lower() else "too_large",
            )

        db.session.commit()

        # Check if all items in order are now returned — if so, mark order as "returned"
        all_items_returned = all(
            ReturnRequest.query.filter(
                ReturnRequest.order_item_id == item.id,
                ReturnRequest.status.in_(["approved", "completed"])
            ).first() is not None
            for item in order.items
        )
        if all_items_returned:
            order.status = "returned"
            db.session.commit()

        # Auto-route to warehouse (invisible to customer)
        try:
            from routing.services import RoutingService
            RoutingService.route_return(
                return_request_id=return_req.id,
                customer_state=order.shipping_state or "Maharashtra",
            )
        except Exception:
            pass  # Don't block return if routing fails

        # Auto-grade the returned product
        try:
            from grading.services import GradingService
            GradingService.auto_inspect_from_return(return_req.id)
        except Exception:
            pass  # Don't block return if grading fails

        message = "Return approved. Refund will be processed in 3-5 business days."
        if is_defective:
            message += f" {item_credits} earned credits reversed (no extra penalty for defective item)."
        elif penalty > 0:
            message += f" {item_credits} earned credits reversed + {penalty} extra penalty for non-defective return."

        return {
            "success": True,
            "return_request": return_req,
            "message": message,
            "credits_deducted": penalty + item_credits if not is_defective else item_credits,
            "refund_amount": order_item.subtotal,
        }

    @staticmethod
    def get_customer_returns(customer_id: int, page: int = 1, per_page: int = 10) -> dict:
        """Get paginated return requests for a customer."""
        pagination = (
            ReturnRequest.query
            .filter_by(customer_id=customer_id)
            .order_by(ReturnRequest.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
        }

    @staticmethod
    def get_return_request(return_id: int, customer_id: int) -> Optional[ReturnRequest]:
        """Get a single return request."""
        return ReturnRequest.query.filter_by(id=return_id, customer_id=customer_id).first()
