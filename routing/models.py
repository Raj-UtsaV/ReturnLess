"""Routing models - warehouses and routing decisions."""
from shared.database import db, TimestampMixin


class Warehouse(db.Model, TimestampMixin):
    """Warehouse/fulfillment center."""
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, default=1000)  # Max items
    current_load = db.Column(db.Integer, default=0)
    specialization = db.Column(db.String(50))  # electronics, clothing, general
    is_active = db.Column(db.Boolean, default=True)

    # Performance metrics
    avg_processing_days = db.Column(db.Float, default=2.0)
    refurb_capability = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Warehouse {self.code} - {self.city}>"

    @property
    def utilization_pct(self) -> float:
        if self.capacity == 0:
            return 100
        return round((self.current_load / self.capacity) * 100, 1)

    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - self.current_load)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "city": self.city,
            "state": self.state,
            "capacity": self.capacity,
            "current_load": self.current_load,
            "utilization_pct": self.utilization_pct,
            "specialization": self.specialization,
            "avg_processing_days": self.avg_processing_days,
            "refurb_capability": self.refurb_capability,
        }


class RoutingDecision(db.Model, TimestampMixin):
    """AI routing decision for a return — admin only, invisible to customer."""
    __tablename__ = "routing_decisions"

    id = db.Column(db.Integer, primary_key=True)
    return_request_id = db.Column(db.Integer, db.ForeignKey("return_requests.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    # Selected warehouse
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)

    # Scoring
    routing_score = db.Column(db.Float, nullable=False)  # 0-1
    demand_score = db.Column(db.Float)  # Local demand for this product
    capacity_score = db.Column(db.Float)  # Available capacity
    distance_score = db.Column(db.Float)  # Proximity to customer

    # Alternatives considered
    alternatives = db.Column(db.JSON, default=list)  # [{warehouse_id, score, reason}]

    # AI explanation
    explanation = db.Column(db.Text, nullable=False)

    # Relationships
    return_request = db.relationship("ReturnRequest", backref=db.backref("routing_decision", uselist=False))
    product = db.relationship("Product")
    warehouse = db.relationship("Warehouse", backref=db.backref("routed_items", lazy="dynamic"))

    def __repr__(self):
        return f"<Routing return={self.return_request_id} -> warehouse={self.warehouse_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "warehouse": self.warehouse.to_dict() if self.warehouse else None,
            "routing_score": self.routing_score,
            "demand_score": self.demand_score,
            "capacity_score": self.capacity_score,
            "distance_score": self.distance_score,
            "alternatives": self.alternatives,
            "explanation": self.explanation,
        }
