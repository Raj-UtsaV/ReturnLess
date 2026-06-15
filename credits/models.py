"""Credit transaction history model."""
from shared.database import db, TimestampMixin


class CreditTransaction(db.Model, TimestampMixin):
    """Individual credit transaction record."""
    __tablename__ = "credit_transactions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    # Amount: positive = earned, negative = deducted
    amount = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)

    # Type: purchase, refurbished_purchase, eco_shipping, return_penalty, serial_return_penalty, cancel_penalty, order_cancel
    transaction_type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(300), nullable=False)

    # Reference
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    return_request_id = db.Column(db.Integer, db.ForeignKey("return_requests.id"), nullable=True)

    # Relationships
    customer = db.relationship("Customer", backref=db.backref("credit_history", lazy="dynamic"))

    def __repr__(self):
        return f"<CreditTx {self.amount:+d} for customer {self.customer_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
