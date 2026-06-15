"""Return models - return requests and processing."""
from shared.database import db, TimestampMixin


class ReturnRequest(db.Model, TimestampMixin):
    """Customer return/cancellation request."""
    __tablename__ = "return_requests"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    # Type: 'cancel' (pre-delivery) or 'return' (post-delivery)
    request_type = db.Column(db.String(20), nullable=False)  # cancel, return

    # Status: pending, approved, rejected, completed
    status = db.Column(db.String(20), default="pending", index=True)

    # Reason
    reason = db.Column(db.String(50), nullable=False)
    # Reasons for cancel: changed_mind, ordered_wrong, found_cheaper, other
    # Reasons for return: defective, wrong_item, not_as_described, size_issue, changed_mind, other
    reason_detail = db.Column(db.Text)

    # Whether the item has a genuine defect
    is_defective = db.Column(db.Boolean, default=False)

    # Credit adjustments applied
    credits_deducted = db.Column(db.Integer, default=0)
    credit_explanation = db.Column(db.Text)

    # Refund
    refund_amount = db.Column(db.Float, default=0)
    refund_status = db.Column(db.String(20), default="pending")  # pending, processed

    # Admin notes (customer never sees this)
    admin_notes = db.Column(db.Text)

    # Relationships
    order = db.relationship("Order", backref=db.backref("return_requests", lazy="dynamic"))
    order_item = db.relationship("OrderItem", backref=db.backref("return_request", uselist=False))
    customer = db.relationship("Customer", backref=db.backref("return_requests", lazy="dynamic"))

    def __repr__(self):
        return f"<ReturnRequest {self.id} type={self.request_type} status={self.status}>"

    @property
    def is_cancel(self) -> bool:
        return self.request_type == "cancel"

    @property
    def is_return(self) -> bool:
        return self.request_type == "return"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "request_type": self.request_type,
            "status": self.status,
            "reason": self.reason,
            "reason_detail": self.reason_detail,
            "is_defective": self.is_defective,
            "credits_deducted": self.credits_deducted,
            "credit_explanation": self.credit_explanation,
            "refund_amount": self.refund_amount,
            "refund_status": self.refund_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
