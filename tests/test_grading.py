"""Tests for Quality Grading - Phase 6."""
import pytest
from grading.models import InspectionRecord
from grading.services import GradingService
from grading.ai_engine import GradingEngine


class TestGradingEngine:
    """Test the grading AI engine."""

    def setup_method(self):
        self.engine = GradingEngine()

    def test_grade_a_like_new(self):
        """Test Grade A for near-perfect product."""
        result = self.engine.assess_product(
            product_name="iPhone 14",
            product_category="electronics",
            product_price=80000,
            return_reason="changed_mind",
            exterior_score=95,
            functional_score=100,
            cosmetic_score=95,
            packaging_score=90,
        )
        assert result["grade"] == "A"
        assert result["overall_score"] >= 90
        assert len(result["grade_explanation"]) > 10

    def test_grade_b_good(self):
        """Test Grade B for good condition."""
        result = self.engine.assess_product(
            product_name="Laptop",
            product_category="electronics",
            product_price=60000,
            return_reason="changed_mind",
            exterior_score=75,
            functional_score=85,
            cosmetic_score=70,
            packaging_score=60,
        )
        assert result["grade"] == "B"
        assert 70 <= result["overall_score"] <= 89

    def test_grade_c_fair(self):
        """Test Grade C for fair condition."""
        result = self.engine.assess_product(
            product_name="Headphones",
            product_category="electronics",
            product_price=20000,
            return_reason="defective",
            exterior_score=55,
            functional_score=60,
            cosmetic_score=50,
            packaging_score=40,
        )
        assert result["grade"] == "C"
        assert 50 <= result["overall_score"] <= 69

    def test_grade_d_salvage(self):
        """Test Grade D for heavily damaged."""
        result = self.engine.assess_product(
            product_name="Phone",
            product_category="electronics",
            product_price=50000,
            return_reason="defective",
            exterior_score=20,
            functional_score=30,
            cosmetic_score=25,
            packaging_score=10,
        )
        assert result["grade"] == "D"
        assert result["overall_score"] < 50

    def test_recommendation_resell_as_is(self):
        """Test resell_as_is for Grade A with no defects."""
        result = self.engine.assess_product(
            product_name="Book",
            product_category="books",
            product_price=500,
            return_reason="changed_mind",
            exterior_score=98,
            functional_score=100,
            cosmetic_score=97,
            packaging_score=95,
        )
        assert result["recommendation"] == "resell_as_is"

    def test_recommendation_refurbish(self):
        """Test refurbish recommendation for Grade B."""
        result = self.engine.assess_product(
            product_name="Tablet",
            product_category="electronics",
            product_price=30000,
            return_reason="changed_mind",
            exterior_score=75,
            functional_score=85,
            cosmetic_score=70,
            packaging_score=60,
        )
        assert result["recommendation"] == "refurbish"

    def test_recommendation_recycle(self):
        """Test recycle for truly destroyed Grade D item."""
        result = self.engine.assess_product(
            product_name="Old phone",
            product_category="electronics",
            product_price=10000,
            return_reason="defective",
            exterior_score=10,
            functional_score=15,
            cosmetic_score=10,
            packaging_score=5,
        )
        assert result["recommendation"] in ("recycle", "dispose")

    def test_carbon_savings_calculated(self):
        """Test carbon savings estimation."""
        result = self.engine.assess_product(
            product_name="Laptop",
            product_category="electronics",
            product_price=80000,
            return_reason="changed_mind",
            exterior_score=90,
            functional_score=95,
            cosmetic_score=90,
            packaging_score=85,
        )
        assert result["carbon_saved_if_refurbished"] > 0

    def test_warranty_grade_a(self):
        """Test warranty for Grade A."""
        result = self.engine.assess_product(
            product_name="Phone",
            product_category="electronics",
            product_price=50000,
            return_reason="changed_mind",
            exterior_score=95,
            functional_score=98,
            cosmetic_score=95,
            packaging_score=90,
        )
        assert result["warranty_months_possible"] >= 9

    def test_warranty_grade_d(self):
        """Test no warranty for Grade D."""
        result = self.engine.assess_product(
            product_name="Broken item",
            product_category="electronics",
            product_price=5000,
            return_reason="defective",
            exterior_score=20,
            functional_score=10,
            cosmetic_score=15,
            packaging_score=5,
        )
        assert result["warranty_months_possible"] == 0

    def test_auto_assess_changed_mind(self):
        """Test auto assessment for changed mind returns."""
        result = self.engine.auto_assess_from_return(
            return_reason="changed_mind",
            product_category="electronics",
            product_price=30000,
            product_name="Gadget",
        )
        assert result["grade"] in ("A", "B")
        assert result["overall_score"] >= 70

    def test_auto_assess_defective(self):
        """Test auto assessment for defective returns."""
        result = self.engine.auto_assess_from_return(
            return_reason="defective",
            product_category="electronics",
            product_price=30000,
            product_name="Gadget",
        )
        assert result["grade"] in ("C", "D")
        assert result["functional_score"] < 50

    def test_refurb_cost_increases_with_grade(self):
        """Test that worse grades have higher refurb cost."""
        grade_a = self.engine.assess_product(
            "P", "electronics", 10000, "x", 95, 100, 95, 90)
        grade_c = self.engine.assess_product(
            "P", "electronics", 10000, "x", 55, 60, 50, 40)
        assert grade_c["refurb_cost_estimate"] > grade_a["refurb_cost_estimate"]

    def test_explanation_always_present(self):
        """Test explanations are always generated."""
        result = self.engine.assess_product(
            "Test", "electronics", 1000, "test", 50, 50, 50, 50)
        assert len(result["grade_explanation"]) > 10
        assert len(result["recommendation_explanation"]) > 10


class TestGradingService:
    """Test GradingService."""

    def test_inspect_product(self, app, db, sample_product):
        """Test creating an inspection record."""
        with app.app_context():
            record = GradingService.inspect_product(
                product_id=sample_product.id,
                exterior_score=85,
                functional_score=90,
                cosmetic_score=80,
                packaging_score=70,
                defects=["Minor scratch on back"],
                notes="Good overall condition",
            )

            assert record.id is not None
            assert record.grade in ("A", "B", "C", "D")
            assert record.overall_score > 0
            assert record.recommendation is not None

    def test_inspect_nonexistent_product(self, app, db):
        """Test inspecting non-existent product raises error."""
        with app.app_context():
            with pytest.raises(ValueError, match="Product not found"):
                GradingService.inspect_product(product_id=99999)

    def test_get_inspections_for_product(self, app, db, sample_product):
        """Test fetching inspections for a product."""
        with app.app_context():
            GradingService.inspect_product(product_id=sample_product.id)
            GradingService.inspect_product(product_id=sample_product.id, exterior_score=50)

            records = GradingService.get_inspections_for_product(sample_product.id)
            assert len(records) == 2

    def test_get_grading_stats(self, app, db, sample_product):
        """Test grading statistics."""
        with app.app_context():
            GradingService.inspect_product(product_id=sample_product.id, exterior_score=95, functional_score=100)
            GradingService.inspect_product(product_id=sample_product.id, exterior_score=50, functional_score=55)

            stats = GradingService.get_grading_stats()
            assert stats["total"] == 2
            assert stats["avg_score"] > 0


class TestGradingRoutes:
    """Test grading HTTP endpoints."""

    @pytest.fixture
    def admin_client(self, client, db):
        """Login as admin."""
        from customers.models import Customer
        admin = Customer(
            email="grading_admin@test.com",
            first_name="Admin",
            last_name="Grader",
            is_admin=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        client.post("/account/login", data={"email": "grading_admin@test.com", "password": "admin123"})
        return client

    def test_inspections_list_requires_admin(self, client, sample_customer):
        """Test non-admin gets 403."""
        client.post("/account/login", data={"email": "test@example.com", "password": "password123"})
        response = client.get("/grading/")
        assert response.status_code == 403

    def test_inspections_list_loads(self, admin_client):
        """Test inspections list page loads for admin."""
        response = admin_client.get("/grading/")
        assert response.status_code == 200
        assert b"Quality Grading" in response.data

    def test_inspect_product_page(self, admin_client, sample_product):
        """Test inspect product page loads."""
        response = admin_client.get(f"/grading/inspect/{sample_product.id}")
        assert response.status_code == 200
        assert b"Inspect Product" in response.data

    def test_submit_inspection(self, admin_client, sample_product):
        """Test submitting an inspection."""
        response = admin_client.post(f"/grading/inspect/{sample_product.id}", data={
            "exterior_score": "85",
            "functional_score": "90",
            "cosmetic_score": "80",
            "packaging_score": "70",
            "defects": "Small scratch\nMissing cable",
            "notes": "Good condition overall",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Grade" in response.data

    def test_inspection_detail(self, admin_client, app, db, sample_product):
        """Test inspection detail page."""
        # Create inspection via the admin route
        admin_client.post(f"/grading/inspect/{sample_product.id}", data={
            "exterior_score": "90",
            "functional_score": "95",
            "cosmetic_score": "85",
            "packaging_score": "80",
        })

        record = InspectionRecord.query.first()
        response = admin_client.get(f"/grading/inspection/{record.id}")
        assert response.status_code == 200

    def test_api_stats(self, admin_client):
        """Test stats API."""
        response = admin_client.get("/grading/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data
