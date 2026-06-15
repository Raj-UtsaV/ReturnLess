"""Routing service - AI warehouse selection for returned products."""
from typing import Optional
from shared.database import db
from routing.models import Warehouse, RoutingDecision


class RoutingService:
    """Service for intelligent warehouse routing."""

    @staticmethod
    def route_return(return_request_id: int, customer_state: str = "Maharashtra") -> Optional[RoutingDecision]:
        """
        Route a returned item to the optimal warehouse.

        Scoring factors:
        - Capacity (35%): Available space
        - Specialization (25%): Match to product category
        - Distance (20%): Proximity to customer
        - Demand (20%): Local demand for this product type

        Customer NEVER sees this decision.
        """
        from returns.models import ReturnRequest

        ret = db.session.get(ReturnRequest, return_request_id)
        if not ret:
            return None

        product_id = ret.order_item.product_id
        product = ret.order_item.product
        category = product.category.slug if product and product.category else "general"

        # Get active warehouses
        warehouses = Warehouse.query.filter_by(is_active=True).all()
        if not warehouses:
            return None

        # Score each warehouse
        scored = []
        for wh in warehouses:
            scores = RoutingService._score_warehouse(wh, category, customer_state)
            total = (
                scores["capacity"] * 0.35 +
                scores["specialization"] * 0.25 +
                scores["distance"] * 0.20 +
                scores["demand"] * 0.20
            )
            scored.append({
                "warehouse": wh,
                "total": round(total, 3),
                "capacity": scores["capacity"],
                "specialization": scores["specialization"],
                "distance": scores["distance"],
                "demand": scores["demand"],
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["total"], reverse=True)

        best = scored[0]
        alternatives = [
            {
                "warehouse_id": s["warehouse"].id,
                "warehouse_name": s["warehouse"].name,
                "score": s["total"],
                "reason": RoutingService._alternative_reason(s, best),
            }
            for s in scored[1:3]
        ]

        # Generate explanation
        explanation = RoutingService._generate_explanation(best, scored, customer_state, category)

        # Create routing decision
        decision = RoutingDecision(
            return_request_id=return_request_id,
            product_id=product_id,
            warehouse_id=best["warehouse"].id,
            routing_score=best["total"],
            demand_score=best["demand"],
            capacity_score=best["capacity"],
            distance_score=best["distance"],
            alternatives=alternatives,
            explanation=explanation,
        )
        db.session.add(decision)

        # Update warehouse load
        best["warehouse"].current_load += 1
        db.session.commit()

        return decision

    @staticmethod
    def _score_warehouse(warehouse: Warehouse, category: str, customer_state: str) -> dict:
        """Score a warehouse on all factors."""
        # Capacity score: higher = more available space
        capacity = 1.0 - (warehouse.utilization_pct / 100.0)
        capacity = max(0.05, capacity)  # Never fully zero

        # Specialization score: bonus if warehouse specializes in this category
        spec = warehouse.specialization or "general"
        if spec == category:
            specialization = 1.0
        elif spec == "general":
            specialization = 0.7
        else:
            specialization = 0.4

        # Distance score: simplified state-based proximity
        state_regions = {
            "Maharashtra": "west", "Gujarat": "west", "Goa": "west", "Rajasthan": "west",
            "Delhi": "north", "Uttar Pradesh": "north", "Haryana": "north", "Punjab": "north",
            "Madhya Pradesh": "central",
            "Karnataka": "south", "Tamil Nadu": "south", "Kerala": "south", "Telangana": "south",
            "West Bengal": "east", "Bihar": "east", "Odisha": "east", "Jharkhand": "east",
        }
        customer_region = state_regions.get(customer_state, "north")
        warehouse_region = state_regions.get(warehouse.state, "north")

        if customer_region == warehouse_region:
            distance = 1.0
        else:
            distance = 0.5

        # Demand score: mock based on specialization match and current load
        if spec == category and warehouse.utilization_pct < 60:
            demand = 0.9
        elif warehouse.utilization_pct < 40:
            demand = 0.7
        else:
            demand = 0.4

        return {
            "capacity": round(capacity, 3),
            "specialization": round(specialization, 3),
            "distance": round(distance, 3),
            "demand": round(demand, 3),
        }

    @staticmethod
    def _generate_explanation(best: dict, all_scored: list, state: str, category: str) -> str:
        """Generate human-readable routing explanation."""
        wh = best["warehouse"]
        return (
            f"Selected {wh.name} ({wh.city}, {wh.state}) with routing score {best['total']:.2f}. "
            f"Factors: capacity utilization {wh.utilization_pct}% "
            f"(available: {wh.available_capacity} slots), "
            f"specialization match ({wh.specialization or 'general'} vs {category}), "
            f"proximity to customer ({state}). "
            f"Evaluated {len(all_scored)} warehouses total."
        )

    @staticmethod
    def _alternative_reason(alt: dict, best: dict) -> str:
        """Generate reason why alternative wasn't chosen."""
        reasons = []
        if alt["capacity"] < best["capacity"]:
            reasons.append("higher utilization")
        if alt["specialization"] < best["specialization"]:
            reasons.append("less specialized")
        if alt["distance"] < best["distance"]:
            reasons.append("farther from customer")
        return "; ".join(reasons) if reasons else "lower overall score"

    @staticmethod
    def get_warehouses() -> list:
        """Get all warehouses."""
        return Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()

    @staticmethod
    def get_routing_decisions(page: int = 1, per_page: int = 20) -> dict:
        """Get paginated routing decisions."""
        pagination = (
            RoutingDecision.query
            .order_by(RoutingDecision.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def get_warehouse_stats() -> dict:
        """Get warehouse utilization stats."""
        warehouses = Warehouse.query.filter_by(is_active=True).all()
        return {
            "total_warehouses": len(warehouses),
            "total_capacity": sum(w.capacity for w in warehouses),
            "total_load": sum(w.current_load for w in warehouses),
            "avg_utilization": round(
                sum(w.utilization_pct for w in warehouses) / len(warehouses), 1
            ) if warehouses else 0,
            "warehouses": [w.to_dict() for w in warehouses],
        }
