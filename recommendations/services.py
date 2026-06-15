"""Size recommendation service - business logic for AI size suggestions."""
from typing import Optional
from shared.database import db
from recommendations.models import SizePurchaseHistory, SizeRecommendation
from recommendations.ai_engine import SizeRecommendationEngine


class SizeRecommendationService:
    """Service for generating and managing size recommendations."""

    _engine = None

    @classmethod
    def _get_engine(cls) -> SizeRecommendationEngine:
        """Lazy-load recommendation engine."""
        if cls._engine is None:
            cls._engine = SizeRecommendationEngine()
        return cls._engine

    @staticmethod
    def get_recommendation(customer_id: int, product_id: int) -> Optional[dict]:
        """
        Get size recommendation for a customer-product pair.

        Checks cache first, generates new recommendation if needed.

        Returns:
            dict with: recommended_size, confidence, confidence_pct, explanation, factors
            or None if product has no sizes
        """
        from products.models import Product

        product = db.session.get(Product, product_id)
        if not product or not product.available_sizes:
            return None

        # Check cache
        cached = SizeRecommendation.query.filter_by(
            customer_id=customer_id, product_id=product_id
        ).first()
        if cached:
            return cached.to_dict()

        # Generate new recommendation
        return SizeRecommendationService.generate_recommendation(customer_id, product_id)

    @staticmethod
    def generate_recommendation(customer_id: int, product_id: int) -> Optional[dict]:
        """
        Generate a fresh size recommendation using AI engine.

        Fetches purchase history, reviews, and product info then runs
        the recommendation engine. If no history but body measurements exist,
        uses body-based prediction.
        """
        from products.models import Product
        from customers.models import Customer
        from ai_reviews.models import Review

        product = db.session.get(Product, product_id)
        if not product or not product.available_sizes:
            return None

        engine = SizeRecommendationService._get_engine()

        # Gather purchase history for this customer
        history_records = SizePurchaseHistory.query.filter_by(
            customer_id=customer_id
        ).all()

        purchase_history = [
            {
                "size": h.size_purchased,
                "kept": h.kept,
                "return_reason": h.return_reason,
                "brand": h.brand,
                "category": h.category_id,
            }
            for h in history_records
        ]

        # If no purchase history, try body measurement prediction
        if not purchase_history:
            customer = db.session.get(Customer, customer_id)
            if customer and customer.height_cm and customer.weight_kg:
                result = engine.predict_size_from_body(
                    height_cm=customer.height_cm,
                    weight_kg=customer.weight_kg,
                    body_type=customer.body_type,
                    available_sizes=product.available_sizes,
                )
                if result["recommended_size"]:
                    # Cache it
                    SizeRecommendationService._cache_recommendation(
                        customer_id, product_id, result
                    )
                    return {
                        "recommended_size": result["recommended_size"],
                        "confidence": result["confidence"],
                        "confidence_pct": round(result["confidence"] * 100),
                        "explanation": result["explanation"],
                        "factors": {"body_measurements": 1.0},
                        "method": "body_measurements",
                    }
            # No history and no body measurements — return None (new user prompt shown)
            return None

        # Gather relevant reviews for the product
        reviews = Review.query.filter_by(product_id=product_id).all()
        review_data = [
            {
                "body": r.body,
                "size_purchased": r.size_purchased,
                "rating": r.rating,
            }
            for r in reviews
        ]

        # Run AI engine
        result = engine.recommend_size(
            available_sizes=product.available_sizes,
            purchase_history=purchase_history,
            product_reviews=review_data,
            brand=product.brand,
            category=product.category.name if product.category else None,
        )

        if not result["recommended_size"]:
            return None

        # Cache the recommendation
        existing = SizeRecommendation.query.filter_by(
            customer_id=customer_id, product_id=product_id
        ).first()

        if existing:
            existing.recommended_size = result["recommended_size"]
            existing.confidence = result["confidence"]
            existing.explanation = result["explanation"]
            existing.factors = result["factors"]
        else:
            rec = SizeRecommendation(
                customer_id=customer_id,
                product_id=product_id,
                recommended_size=result["recommended_size"],
                confidence=result["confidence"],
                explanation=result["explanation"],
                factors=result["factors"],
            )
            db.session.add(rec)

        db.session.commit()

        return {
            "recommended_size": result["recommended_size"],
            "confidence": result["confidence"],
            "confidence_pct": round(result["confidence"] * 100),
            "explanation": result["explanation"],
            "factors": result["factors"],
        }

    @staticmethod
    def record_purchase(
        customer_id: int,
        product_id: int,
        category_id: int,
        size_purchased: str,
        brand: Optional[str] = None,
        kept: bool = True,
        return_reason: Optional[str] = None,
    ) -> SizePurchaseHistory:
        """
        Record a size purchase for future recommendations.

        Called when:
        - Customer completes checkout (kept=True by default)
        - Customer returns an item (kept=False with reason)
        """
        record = SizePurchaseHistory(
            customer_id=customer_id,
            product_id=product_id,
            category_id=category_id,
            size_purchased=size_purchased,
            brand=brand,
            kept=kept,
            return_reason=return_reason,
        )
        db.session.add(record)
        db.session.commit()

        # Invalidate cached recommendations for this customer
        # (new data means recommendations should be regenerated)
        SizeRecommendation.query.filter_by(customer_id=customer_id).delete()
        db.session.commit()

        return record

    @staticmethod
    def get_customer_size_profile(customer_id: int) -> dict:
        """
        Get a customer's size profile based on purchase history.

        Returns common sizes by category and overall preferences.
        """
        history = SizePurchaseHistory.query.filter_by(
            customer_id=customer_id, kept=True
        ).all()

        if not history:
            return {
                "has_history": False,
                "total_purchases": 0,
                "preferred_sizes": {},
                "brands": [],
            }

        # Group by category
        size_by_category = {}
        brands = set()

        for h in history:
            cat_id = h.category_id
            if cat_id not in size_by_category:
                size_by_category[cat_id] = []
            size_by_category[cat_id].append(h.size_purchased)
            if h.brand:
                brands.add(h.brand)

        # Find most common size per category
        preferred = {}
        for cat_id, sizes in size_by_category.items():
            most_common = max(set(sizes), key=sizes.count)
            preferred[cat_id] = {
                "size": most_common,
                "count": sizes.count(most_common),
                "total": len(sizes),
            }

        return {
            "has_history": True,
            "total_purchases": len(history),
            "preferred_sizes": preferred,
            "brands": list(brands),
        }

    @staticmethod
    def invalidate_cache(customer_id: int):
        """Clear cached recommendations for a customer."""
        SizeRecommendation.query.filter_by(customer_id=customer_id).delete()
        db.session.commit()

    @staticmethod
    def get_review_based_recommendation(product_id: int) -> dict:
        """
        Generate size recommendation from product reviews ONLY (for new users).
        """
        from products.models import Product
        from ai_reviews.models import Review

        product = db.session.get(Product, product_id)
        if not product or not product.available_sizes:
            return None

        reviews = Review.query.filter_by(product_id=product_id).all()

        engine = SizeRecommendationService._get_engine()
        review_data = [
            {"body": r.body, "size_purchased": r.size_purchased, "rating": r.rating}
            for r in reviews
        ]

        result = engine.recommend_from_reviews_only(
            available_sizes=product.available_sizes,
            reviews=review_data,
        )

        if not result or not result.get("recommended_size"):
            return None

        return {
            "recommended_size": result["recommended_size"],
            "confidence": result["confidence"],
            "confidence_pct": round(result["confidence"] * 100),
            "explanation": result["explanation"],
            "factors": result.get("factors", {"review_analysis": 1.0}),
        }

    @staticmethod
    def get_body_ml_recommendation(customer_id: int, product_id: int) -> dict:
        """
        Predict size from height/weight using ML (trained on other users' data)
        combined with product review analysis.

        Training data: all users who have height/weight AND purchase history.
        Model: RandomForest trained on (height, weight) → kept_size.
        Final prediction: ML body prediction + review analysis combined.
        """
        from products.models import Product
        from customers.models import Customer
        from ai_reviews.models import Review

        product = db.session.get(Product, product_id)
        if not product or not product.available_sizes:
            return None

        customer = db.session.get(Customer, customer_id)
        if not customer or not customer.height_cm or not customer.weight_kg:
            return None

        engine = SizeRecommendationService._get_engine()

        # Get training data from ALL users who have body measurements + kept purchases
        training_data = _gather_ml_training_data()

        # ML prediction from body measurements
        body_prediction = engine.predict_size_ml(
            height_cm=customer.height_cm,
            weight_kg=customer.weight_kg,
            body_type=customer.body_type,
            available_sizes=product.available_sizes,
            training_data=training_data,
        )

        # Also get review-based insight
        reviews = Review.query.filter_by(product_id=product_id).all()
        review_data = [{"body": r.body, "size_purchased": r.size_purchased, "rating": r.rating} for r in reviews]
        review_prediction = engine.recommend_from_reviews_only(
            available_sizes=product.available_sizes,
            reviews=review_data,
        )

        # Combine: body prediction (60% weight) + review analysis (40% weight)
        final = _combine_predictions(body_prediction, review_prediction, product.available_sizes)

        return final

    @staticmethod
    def _cache_recommendation(customer_id: int, product_id: int, result: dict):
        """Cache a recommendation result."""
        existing = SizeRecommendation.query.filter_by(
            customer_id=customer_id, product_id=product_id
        ).first()

        if existing:
            existing.recommended_size = result["recommended_size"]
            existing.confidence = result["confidence"]
            existing.explanation = result["explanation"]
            existing.factors = result.get("factors", {})
        else:
            rec = SizeRecommendation(
                customer_id=customer_id,
                product_id=product_id,
                recommended_size=result["recommended_size"],
                confidence=result["confidence"],
                explanation=result["explanation"],
                factors=result.get("factors", {}),
            )
            db.session.add(rec)

        db.session.commit()

    @staticmethod
    def save_body_measurements(
        customer_id: int,
        height_cm: float,
        weight_kg: float,
        body_type: Optional[str] = None,
    ) -> dict:
        """
        Save customer body measurements for size prediction.
        Invalidates any cached recommendations.
        """
        from customers.models import Customer

        customer = db.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")

        customer.height_cm = height_cm
        customer.weight_kg = weight_kg
        if body_type in ("slim", "regular", "athletic", "plus"):
            customer.body_type = body_type

        db.session.commit()

        # Invalidate cache so new predictions use body data
        SizeRecommendationService.invalidate_cache(customer_id)

        return {
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "body_type": body_type,
            "message": "Measurements saved! AI will now predict sizes based on your body.",
        }


def _gather_ml_training_data() -> list:
    """
    Gather training data from all users who have body measurements + kept purchases.
    Returns list of dicts: [{height, weight, body_type, size_kept}]
    """
    from customers.models import Customer

    # Get all customers with body measurements
    customers_with_body = Customer.query.filter(
        Customer.height_cm.isnot(None),
        Customer.weight_kg.isnot(None),
    ).all()

    training_data = []
    for customer in customers_with_body:
        # Get their kept sizes
        kept_records = SizePurchaseHistory.query.filter_by(
            customer_id=customer.id, kept=True
        ).all()
        for record in kept_records:
            training_data.append({
                "height": customer.height_cm,
                "weight": customer.weight_kg,
                "body_type": customer.body_type or "regular",
                "size_kept": record.size_purchased,
            })

    return training_data


def _combine_predictions(body_pred: dict, review_pred: dict, available_sizes: list) -> dict:
    """
    Combine body-based ML prediction (60%) with review analysis (40%).
    If they agree → high confidence. If they disagree → use body with warning.
    """
    if not body_pred or not body_pred.get("recommended_size"):
        # Body prediction failed, use review only
        if review_pred and review_pred.get("recommended_size"):
            return {
                "recommended_size": review_pred["recommended_size"],
                "confidence": review_pred["confidence"],
                "confidence_pct": round(review_pred["confidence"] * 100),
                "explanation": review_pred["explanation"],
                "factors": review_pred.get("factors", {}),
            }
        return None

    body_size = body_pred["recommended_size"]
    body_conf = body_pred.get("confidence", 0.6)

    review_size = review_pred.get("recommended_size") if review_pred else None
    review_conf = review_pred.get("confidence", 0.4) if review_pred else 0

    # If both agree → boost confidence
    if review_size and body_size == review_size:
        final_conf = min(0.92, body_conf * 0.6 + review_conf * 0.4 + 0.1)
        explanation = (
            f"{body_pred['explanation']} "
            f"Review analysis confirms this size. High confidence recommendation."
        )
        factors = {"body_ml": round(body_conf, 2), "review_analysis": round(review_conf, 2), "agreement": 1.0}
    elif review_size and body_size != review_size:
        # Disagree — trust body more but note the discrepancy
        final_conf = body_conf * 0.6 + review_conf * 0.2
        explanation = (
            f"{body_pred['explanation']} "
            f"Note: Reviews suggest {review_size} but your body measurements indicate {body_size}. "
            f"Going with body-based prediction."
        )
        factors = {"body_ml": round(body_conf, 2), "review_analysis": round(review_conf, 2), "disagreement": 1.0}
    else:
        # No review data, body only
        final_conf = body_conf
        explanation = body_pred["explanation"]
        factors = {"body_ml": round(body_conf, 2)}

    return {
        "recommended_size": body_size,
        "confidence": round(final_conf, 2),
        "confidence_pct": round(final_conf * 100),
        "explanation": explanation,
        "factors": factors,
    }
