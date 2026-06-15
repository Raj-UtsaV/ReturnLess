"""Grading models - inspection records and quality assessments."""
from shared.database import db, TimestampMixin


class InspectionRecord(db.Model, TimestampMixin):
    """Record of a product inspection after return."""
    __tablename__ = "inspection_records"

    id = db.Column(db.Integer, primary_key=True)
    return_request_id = db.Column(db.Integer, db.ForeignKey("return_requests.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    # Inspector info
    inspected_by = db.Column(db.String(100), default="AI Inspector")

    # Physical condition scores (0-100)
    exterior_score = db.Column(db.Integer, default=100)  # Scratches, dents, wear
    functional_score = db.Column(db.Integer, default=100)  # All features working
    cosmetic_score = db.Column(db.Integer, default=100)  # Visual appearance
    packaging_score = db.Column(db.Integer, default=100)  # Box, accessories

    # Overall grade: A (like-new), B (good), C (fair), D (salvage/parts)
    grade = db.Column(db.String(2), nullable=False)
    overall_score = db.Column(db.Integer, nullable=False)  # Computed 0-100

    # Detailed findings
    defects_found = db.Column(db.JSON, default=list)  # List of defect descriptions
    notes = db.Column(db.Text)

    # AI explanation
    grade_explanation = db.Column(db.Text, nullable=False)

    # Recommendation: refurbish, resell_as_is, recycle, dispose
    recommendation = db.Column(db.String(20), nullable=False)
    recommendation_explanation = db.Column(db.Text)

    # Estimated refurbishment cost
    refurb_cost_estimate = db.Column(db.Float, default=0)

    # Carbon impact
    carbon_saved_if_refurbished = db.Column(db.Float, default=0)

    # Warranty that can be offered
    warranty_months_possible = db.Column(db.Integer, default=0)

    # Relationships
    product = db.relationship("Product", backref=db.backref("inspections", lazy="dynamic"))
    return_request = db.relationship("ReturnRequest", backref=db.backref("inspection", uselist=False))

    def __repr__(self):
        return f"<Inspection product={self.product_id} grade={self.grade}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "grade": self.grade,
            "overall_score": self.overall_score,
            "exterior_score": self.exterior_score,
            "functional_score": self.functional_score,
            "cosmetic_score": self.cosmetic_score,
            "packaging_score": self.packaging_score,
            "defects_found": self.defects_found,
            "notes": self.notes,
            "grade_explanation": self.grade_explanation,
            "recommendation": self.recommendation,
            "recommendation_explanation": self.recommendation_explanation,
            "refurb_cost_estimate": self.refurb_cost_estimate,
            "carbon_saved_if_refurbished": self.carbon_saved_if_refurbished,
            "warranty_months_possible": self.warranty_months_possible,
            "inspected_by": self.inspected_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
