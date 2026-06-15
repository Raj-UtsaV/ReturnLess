"""Grading service layer - inspection and quality assessment operations."""
from typing import Optional
from shared.database import db
from grading.models import InspectionRecord
from grading.ai_engine import GradingEngine


class GradingService:
    """Service for product inspection and grading."""

    _engine = None

    @classmethod
    def _get_engine(cls) -> GradingEngine:
        if cls._engine is None:
            cls._engine = GradingEngine()
        return cls._engine

    @staticmethod
    def inspect_product(
        product_id: int,
        return_request_id: Optional[int] = None,
        exterior_score: int = 100,
        functional_score: int = 100,
        cosmetic_score: int = 100,
        packaging_score: int = 100,
        defects: list = None,
        notes: str = None,
        inspected_by: str = "AI Inspector",
    ) -> InspectionRecord:
        """
        Perform a full inspection on a product.

        Can be triggered manually (admin) or automatically after a return.
        """
        from products.models import Product

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found")

        engine = GradingService._get_engine()

        category_slug = product.category.slug if product.category else "electronics"

        result = engine.assess_product(
            product_name=product.name,
            product_category=category_slug,
            product_price=product.price,
            return_reason="manual_inspection",
            exterior_score=exterior_score,
            functional_score=functional_score,
            cosmetic_score=cosmetic_score,
            packaging_score=packaging_score,
            defects=defects or [],
            notes=notes,
        )

        record = InspectionRecord(
            product_id=product_id,
            return_request_id=return_request_id,
            inspected_by=inspected_by,
            exterior_score=exterior_score,
            functional_score=functional_score,
            cosmetic_score=cosmetic_score,
            packaging_score=packaging_score,
            grade=result["grade"],
            overall_score=result["overall_score"],
            defects_found=result["defects_found"],
            notes=notes,
            grade_explanation=result["grade_explanation"],
            recommendation=result["recommendation"],
            recommendation_explanation=result["recommendation_explanation"],
            refurb_cost_estimate=result["refurb_cost_estimate"],
            carbon_saved_if_refurbished=result["carbon_saved_if_refurbished"],
            warranty_months_possible=result["warranty_months_possible"],
        )

        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def auto_inspect_from_return(return_request_id: int) -> Optional[InspectionRecord]:
        """
        Automatically assess a product based on its return request.
        Uses heuristics when no manual inspection data is available.
        """
        from returns.models import ReturnRequest
        from products.models import Product

        ret = db.session.get(ReturnRequest, return_request_id)
        if not ret:
            return None

        product = db.session.get(Product, ret.order_item.product_id)
        if not product:
            return None

        engine = GradingService._get_engine()
        category_slug = product.category.slug if product.category else "electronics"

        result = engine.auto_assess_from_return(
            return_reason=ret.reason,
            product_category=category_slug,
            product_price=product.price,
            product_name=product.name,
        )

        record = InspectionRecord(
            product_id=product.id,
            return_request_id=return_request_id,
            inspected_by="AI Auto-Inspector",
            exterior_score=result["exterior_score"],
            functional_score=result["functional_score"],
            cosmetic_score=result["cosmetic_score"],
            packaging_score=result["packaging_score"],
            grade=result["grade"],
            overall_score=result["overall_score"],
            defects_found=result["defects_found"],
            notes=f"Auto-assessed from return reason: {ret.reason}",
            grade_explanation=result["grade_explanation"],
            recommendation=result["recommendation"],
            recommendation_explanation=result["recommendation_explanation"],
            refurb_cost_estimate=result["refurb_cost_estimate"],
            carbon_saved_if_refurbished=result["carbon_saved_if_refurbished"],
            warranty_months_possible=result["warranty_months_possible"],
        )

        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get_inspection(inspection_id: int) -> Optional[InspectionRecord]:
        """Get an inspection record by ID."""
        return db.session.get(InspectionRecord, inspection_id)

    @staticmethod
    def get_inspections_for_product(product_id: int) -> list:
        """Get all inspection records for a product."""
        return InspectionRecord.query.filter_by(product_id=product_id).order_by(
            InspectionRecord.created_at.desc()
        ).all()

    @staticmethod
    def get_all_inspections(page: int = 1, per_page: int = 20, grade: Optional[str] = None) -> dict:
        """Get paginated inspections (admin view)."""
        query = InspectionRecord.query

        if grade:
            query = query.filter_by(grade=grade)

        pagination = query.order_by(InspectionRecord.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
        }

    @staticmethod
    def get_grading_stats() -> dict:
        """Get aggregate grading statistics (admin dashboard)."""
        total = InspectionRecord.query.count()
        if total == 0:
            return {"total": 0, "by_grade": {}, "by_recommendation": {}}

        by_grade = {}
        for grade in ["A", "B", "C", "D"]:
            count = InspectionRecord.query.filter_by(grade=grade).count()
            by_grade[grade] = {"count": count, "pct": round(count / total * 100, 1)}

        by_rec = {}
        for rec in ["resell_as_is", "refurbish", "recycle", "dispose"]:
            count = InspectionRecord.query.filter_by(recommendation=rec).count()
            by_rec[rec] = count

        avg_score = db.session.query(db.func.avg(InspectionRecord.overall_score)).scalar() or 0
        total_carbon = db.session.query(
            db.func.sum(InspectionRecord.carbon_saved_if_refurbished)
        ).scalar() or 0

        return {
            "total": total,
            "by_grade": by_grade,
            "by_recommendation": by_rec,
            "avg_score": round(float(avg_score), 1),
            "total_carbon_saved": round(float(total_carbon), 1),
        }
