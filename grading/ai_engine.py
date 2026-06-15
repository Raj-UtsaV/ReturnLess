"""
AI Engine for Quality Grading.

Assesses returned products and assigns grades based on condition scores.
All decisions include explanations.

Grading Scale:
- Grade A (90-100): Like new — minimal/no signs of use
- Grade B (70-89): Good — light wear, fully functional
- Grade C (50-69): Fair — visible wear, may need minor repair
- Grade D (0-49): Salvage — significant damage, parts only

Recommendations:
- refurbish: Can be restored and resold (Grade A-C)
- resell_as_is: Sell without refurbishment (Grade A)
- recycle: Extract components/materials (Grade D)
- dispose: Cannot be reused safely (Grade D, hazardous)
"""


class GradingEngine:
    """AI engine for product quality assessment."""

    GRADE_THRESHOLDS = {
        "A": (90, 100),
        "B": (70, 89),
        "C": (50, 69),
        "D": (0, 49),
    }

    # Carbon savings estimates by category (kg CO2 saved by refurbishing)
    CARBON_SAVINGS_BY_CATEGORY = {
        "electronics": {"base": 50, "per_kg": 20},
        "clothing": {"base": 5, "per_kg": 3},
        "home-kitchen": {"base": 15, "per_kg": 8},
        "sports": {"base": 8, "per_kg": 5},
        "beauty": {"base": 2, "per_kg": 1},
        "books": {"base": 1, "per_kg": 0.5},
    }

    def assess_product(
        self,
        product_name: str,
        product_category: str,
        product_price: float,
        return_reason: str,
        exterior_score: int = 100,
        functional_score: int = 100,
        cosmetic_score: int = 100,
        packaging_score: int = 100,
        defects: list = None,
        notes: str = None,
    ) -> dict:
        """
        Assess a returned product and assign a grade.

        Args:
            product_name: Name of the product
            product_category: Category slug
            product_price: Original price
            return_reason: Why it was returned
            exterior_score: Physical condition (0-100)
            functional_score: Functionality (0-100)
            cosmetic_score: Visual appearance (0-100)
            packaging_score: Packaging/accessories (0-100)
            defects: List of defect descriptions
            notes: Additional inspection notes

        Returns:
            dict with grade, scores, recommendation, explanation, carbon savings
        """
        defects = defects or []

        # Calculate overall score (weighted)
        overall_score = self._calculate_overall_score(
            exterior_score, functional_score, cosmetic_score, packaging_score
        )

        # Determine grade
        grade = self._score_to_grade(overall_score)

        # Generate explanation
        grade_explanation = self._explain_grade(
            grade, overall_score, exterior_score, functional_score,
            cosmetic_score, packaging_score, defects
        )

        # Determine recommendation
        recommendation, rec_explanation = self._determine_recommendation(
            grade, overall_score, functional_score, product_price, defects, return_reason
        )

        # Estimate refurbishment cost
        refurb_cost = self._estimate_refurb_cost(grade, product_price, defects)

        # Calculate carbon savings
        carbon_saved = self._estimate_carbon_savings(product_category, grade)

        # Determine possible warranty
        warranty_months = self._determine_warranty(grade, functional_score)

        return {
            "grade": grade,
            "overall_score": overall_score,
            "exterior_score": exterior_score,
            "functional_score": functional_score,
            "cosmetic_score": cosmetic_score,
            "packaging_score": packaging_score,
            "grade_explanation": grade_explanation,
            "recommendation": recommendation,
            "recommendation_explanation": rec_explanation,
            "refurb_cost_estimate": refurb_cost,
            "carbon_saved_if_refurbished": carbon_saved,
            "warranty_months_possible": warranty_months,
            "defects_found": defects,
        }

    def auto_assess_from_return(
        self,
        return_reason: str,
        product_category: str,
        product_price: float,
        product_name: str,
    ) -> dict:
        """
        Generate an automatic assessment based on return reason.
        Used when no manual inspection data is available.

        This is a mock/heuristic approach — in production, this would
        use YOLOv8 image analysis or manual warehouse input.
        """
        # Estimate scores based on return reason
        if return_reason in ("defective", "wrong_item"):
            exterior = 60
            functional = 40 if return_reason == "defective" else 90
            cosmetic = 70
            packaging = 50
            defects = ["Reported defective by customer"] if return_reason == "defective" else ["Wrong item shipped"]
        elif return_reason == "not_as_described":
            exterior = 85
            functional = 90
            cosmetic = 80
            packaging = 70
            defects = ["Product did not match listing description"]
        elif return_reason == "size_issue":
            exterior = 95
            functional = 100
            cosmetic = 95
            packaging = 85
            defects = []
        elif return_reason == "changed_mind":
            exterior = 95
            functional = 100
            cosmetic = 90
            packaging = 80
            defects = []
        else:
            exterior = 80
            functional = 85
            cosmetic = 80
            packaging = 70
            defects = ["Returned for unspecified reason"]

        return self.assess_product(
            product_name=product_name,
            product_category=product_category,
            product_price=product_price,
            return_reason=return_reason,
            exterior_score=exterior,
            functional_score=functional,
            cosmetic_score=cosmetic,
            packaging_score=packaging,
            defects=defects,
        )

    def _calculate_overall_score(
        self, exterior: int, functional: int, cosmetic: int, packaging: int
    ) -> int:
        """
        Calculate weighted overall score.
        Weights: Functional (40%), Exterior (30%), Cosmetic (20%), Packaging (10%)
        """
        score = (
            functional * 0.40 +
            exterior * 0.30 +
            cosmetic * 0.20 +
            packaging * 0.10
        )
        return min(100, max(0, round(score)))

    def _score_to_grade(self, score: int) -> str:
        """Convert overall score to letter grade."""
        for grade, (low, high) in self.GRADE_THRESHOLDS.items():
            if low <= score <= high:
                return grade
        return "D"

    def _explain_grade(
        self, grade: str, overall: int, exterior: int,
        functional: int, cosmetic: int, packaging: int, defects: list
    ) -> str:
        """Generate human-readable grade explanation."""
        grade_names = {"A": "Like New", "B": "Good", "C": "Fair", "D": "Salvage"}
        parts = [
            f"Grade {grade} ({grade_names[grade]}) — Overall score: {overall}/100."
        ]

        # Breakdown
        breakdown = []
        if functional < 80:
            breakdown.append(f"functional issues detected (score: {functional}/100)")
        if exterior < 70:
            breakdown.append(f"physical wear observed (score: {exterior}/100)")
        if cosmetic < 70:
            breakdown.append(f"cosmetic imperfections (score: {cosmetic}/100)")
        if packaging < 50:
            breakdown.append(f"packaging incomplete or damaged (score: {packaging}/100)")

        if breakdown:
            parts.append("Issues: " + "; ".join(breakdown) + ".")
        else:
            parts.append("All inspection areas passed with good scores.")

        if defects:
            parts.append(f"Defects noted: {', '.join(defects[:3])}.")

        return " ".join(parts)

    def _determine_recommendation(
        self, grade: str, score: int, functional: int, price: float, defects: list,
        return_reason: str = None,
    ) -> tuple:
        """
        Determine what to do with the product based on grade AND return reason.
        Returns (recommendation, explanation).

        Logic:
        - Size issue / changed mind → product is fine → resell_as_is or light refurbish
        - Defective → product needs repair → refurbish (not recycle, since it CAN be fixed)
        - Wrong item / not as described → product is fine → resell_as_is
        - Only truly destroyed items (Grade D, functional < 30) → recycle/dispose
        """
        # Products returned for non-defect reasons (size, changed mind) are typically fine
        non_defect_reasons = {"size_issue", "changed_mind", "ordered_wrong", "found_cheaper"}
        fine_product_reasons = {"wrong_item", "not_as_described"}

        if return_reason in non_defect_reasons:
            # Product is perfectly fine — customer just didn't want it
            if grade == "A":
                return (
                    "resell_as_is",
                    "Product returned unused/like-new (customer changed mind or size issue). "
                    "Can be resold directly as certified refurbished Grade A."
                )
            return (
                "refurbish",
                f"Product returned in {grade} condition (customer: {return_reason.replace('_', ' ')}). "
                f"Light cleaning/repackaging needed before resale."
            )

        if return_reason in fine_product_reasons:
            # Wrong item shipped or not as described — product itself is fine
            return (
                "resell_as_is",
                "Product returned due to fulfillment error (wrong item/description mismatch). "
                "Product itself is in original condition. Restock and resell."
            )

        if return_reason == "defective":
            # Defective — needs repair but should be REFURBISHED, not recycled
            if functional >= 50:
                return (
                    "refurbish",
                    f"Product reported defective (functional score: {functional}/100). "
                    f"Repair and refurbishment recommended. Can be resold as Grade B/C refurbished "
                    f"with appropriate warranty after fixing the defect."
                )
            elif functional >= 20:
                return (
                    "refurbish",
                    f"Product has significant functional issues (score: {functional}/100) "
                    f"but repair is still viable. Refurbish with component replacement "
                    f"and sell as Grade C at discount."
                )
            else:
                return (
                    "recycle",
                    f"Product severely damaged (functional: {functional}/100). "
                    f"Repair cost exceeds value. Component harvesting and recycling recommended."
                )

        # Fallback: use grade-based logic for unknown reasons
        if grade == "A" and not defects:
            return (
                "resell_as_is",
                "Product is in like-new condition with no defects. "
                "Can be resold directly as certified refurbished Grade A with full warranty."
            )

        if grade in ("A", "B"):
            return (
                "refurbish",
                f"Product scored {score}/100 (Grade {grade}). "
                f"Minor refurbishment recommended before resale. "
                f"Expected to sell well as certified refurbished."
            )

        if grade == "C":
            return (
                "refurbish",
                f"Product has wear (score: {score}/100) but is repairable. "
                f"Refurbishment recommended. Can be listed as Grade C at discount."
            )

        # Grade D — only truly destroyed items
        if functional < 30:
            return (
                "dispose",
                f"Product is significantly damaged (score: {score}/100, "
                f"functional: {functional}/100). Cannot be safely repaired or reused. "
                f"Responsible disposal recommended."
            )

        return (
            "recycle",
            f"Product heavily worn (score: {score}/100). "
            f"Component extraction and material recycling recommended."
        )

    def _estimate_refurb_cost(self, grade: str, price: float, defects: list) -> float:
        """Estimate refurbishment cost as percentage of product price."""
        base_pct = {"A": 0.02, "B": 0.08, "C": 0.20, "D": 0.50}
        pct = base_pct.get(grade, 0.30)

        # Additional cost per defect
        defect_cost = len(defects) * (price * 0.03)

        return round(price * pct + defect_cost, 2)

    def _estimate_carbon_savings(self, category: str, grade: str) -> float:
        """Estimate CO2 saved by refurbishing instead of manufacturing new."""
        savings_data = self.CARBON_SAVINGS_BY_CATEGORY.get(category, {"base": 10, "per_kg": 5})
        base = savings_data["base"]

        # Higher grade = more likely to be refurbished = more CO2 saved
        grade_multiplier = {"A": 1.0, "B": 0.85, "C": 0.60, "D": 0.20}
        multiplier = grade_multiplier.get(grade, 0.5)

        return round(base * multiplier, 1)

    def _determine_warranty(self, grade: str, functional_score: int) -> int:
        """Determine possible warranty months based on grade and functionality."""
        if grade == "A" and functional_score >= 95:
            return 12
        elif grade == "A":
            return 9
        elif grade == "B" and functional_score >= 85:
            return 6
        elif grade == "B":
            return 3
        elif grade == "C" and functional_score >= 70:
            return 3
        return 0
