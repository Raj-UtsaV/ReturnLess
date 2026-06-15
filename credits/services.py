"""Credits service - transaction logging and tier management."""
from typing import Optional
from shared.database import db
from credits.models import CreditTransaction


# Tier definitions
TIERS = [
    {"name": "Silver", "min": 0, "color": "slate", "icon": "🥈"},
    {"name": "Gold", "min": 500, "color": "amber", "icon": "🥇"},
    {"name": "Platinum", "min": 1500, "color": "violet", "icon": "💎"},
    {"name": "Green Hero", "min": 3000, "color": "emerald", "icon": "🌍"},
]


class CreditService:
    """Service for green credit operations."""

    @staticmethod
    def add_credits(
        customer_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        order_id: Optional[int] = None,
        return_request_id: Optional[int] = None,
    ) -> CreditTransaction:
        """
        Add or deduct credits and log the transaction.

        Args:
            amount: Positive to add, negative to deduct
        """
        from customers.models import Customer

        customer = db.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")

        # Apply credits
        customer.green_credits = max(0, customer.green_credits + amount)
        if amount > 0:
            customer.lifetime_credits += amount

        # Log transaction
        tx = CreditTransaction(
            customer_id=customer_id,
            amount=amount,
            balance_after=customer.green_credits,
            transaction_type=transaction_type,
            description=description,
            order_id=order_id,
            return_request_id=return_request_id,
        )
        db.session.add(tx)
        db.session.commit()
        return tx

    @staticmethod
    def get_history(customer_id: int, page: int = 1, per_page: int = 20) -> dict:
        """Get paginated credit history for a customer."""
        pagination = (
            CreditTransaction.query
            .filter_by(customer_id=customer_id)
            .order_by(CreditTransaction.created_at.desc())
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
    def get_tier_info(lifetime_credits: int) -> dict:
        """Get current tier and next tier info."""
        current_tier = TIERS[0]
        next_tier = None

        for i, tier in enumerate(TIERS):
            if lifetime_credits >= tier["min"]:
                current_tier = tier
                if i + 1 < len(TIERS):
                    next_tier = TIERS[i + 1]
                else:
                    next_tier = None

        progress = 0
        if next_tier:
            range_total = next_tier["min"] - current_tier["min"]
            range_current = lifetime_credits - current_tier["min"]
            progress = min(100, round((range_current / range_total) * 100))

        return {
            "current": current_tier,
            "next": next_tier,
            "progress": progress,
            "credits_to_next": (next_tier["min"] - lifetime_credits) if next_tier else 0,
        }

    @staticmethod
    def get_credit_summary(customer_id: int) -> dict:
        """Get credit summary for dashboard."""
        from customers.models import Customer

        customer = db.session.get(Customer, customer_id)
        if not customer:
            return {}

        tier_info = CreditService.get_tier_info(customer.lifetime_credits)

        # Recent transactions
        recent = (
            CreditTransaction.query
            .filter_by(customer_id=customer_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(5)
            .all()
        )

        # Stats
        total_earned = db.session.query(
            db.func.sum(CreditTransaction.amount)
        ).filter(
            CreditTransaction.customer_id == customer_id,
            CreditTransaction.amount > 0,
        ).scalar() or 0

        total_deducted = db.session.query(
            db.func.sum(CreditTransaction.amount)
        ).filter(
            CreditTransaction.customer_id == customer_id,
            CreditTransaction.amount < 0,
        ).scalar() or 0

        return {
            "balance": customer.green_credits,
            "lifetime": customer.lifetime_credits,
            "tier": tier_info,
            "total_earned": int(total_earned),
            "total_deducted": abs(int(total_deducted)),
            "recent_transactions": [tx.to_dict() for tx in recent],
        }
