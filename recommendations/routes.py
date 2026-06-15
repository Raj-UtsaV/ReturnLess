"""Size recommendation routes - thin controllers for AI size suggestions."""
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from recommendations.services import SizeRecommendationService

recommendations_bp = Blueprint(
    "recommendations",
    __name__,
    template_folder="templates",
    url_prefix="/recommendations",
)


@recommendations_bp.route("/size/<int:product_id>")
@login_required
def get_size_recommendation(product_id):
    """
    Get AI size recommendation for current user and product.

    - Old user (has history): Recommend from purchase history + reviews
    - New user (no history, has body data): Predict from height/weight ML model + reviews
    - New user (no history, no body data): Show height/weight form
    - Only works for clothing category products
    """
    from products.models import Product
    from shared.database import db

    product = db.session.get(Product, product_id)
    if not product or not product.available_sizes:
        if request.headers.get("HX-Request"):
            return render_template("recommendations/partials/no_sizes.html")
        return jsonify({"error": "No sizes available"}), 404

    # Only for clothing
    if product.category and product.category.slug != "clothing":
        if request.headers.get("HX-Request"):
            return render_template("recommendations/partials/no_sizes.html")
        return jsonify({"error": "Size recommendation only available for clothing"}), 404

    # Check if user has purchase history
    profile = SizeRecommendationService.get_customer_size_profile(current_user.id)

    if profile["has_history"]:
        # Old user → full recommendation (history + reviews)
        recommendation = SizeRecommendationService.get_recommendation(
            customer_id=current_user.id,
            product_id=product_id,
        )
    elif current_user.height_cm and current_user.weight_kg:
        # New user WITH body measurements → ML prediction + reviews
        recommendation = SizeRecommendationService.get_body_ml_recommendation(
            customer_id=current_user.id,
            product_id=product_id,
        )
    else:
        # New user WITHOUT body data → ask for height/weight
        if request.headers.get("HX-Request"):
            return render_template(
                "recommendations/partials/new_user_size_prompt.html",
                product_id=product_id,
            )
        return jsonify({"status": "new_user", "message": "Please provide height and weight."})

    if not recommendation:
        if request.headers.get("HX-Request"):
            return render_template("recommendations/partials/no_sizes.html")
        return jsonify({"error": "Cannot generate recommendation"}), 404

    if request.headers.get("HX-Request"):
        return render_template(
            "recommendations/partials/size_recommendation.html",
            recommendation=recommendation,
        )

    return jsonify(recommendation)

    return jsonify(recommendation)


@recommendations_bp.route("/api/size/<int:product_id>")
@login_required
def api_size_recommendation(product_id):
    """JSON API endpoint for size recommendation."""
    recommendation = SizeRecommendationService.get_recommendation(
        customer_id=current_user.id,
        product_id=product_id,
    )

    if not recommendation:
        return jsonify({"error": "No sizes available or no recommendation possible"}), 404

    return jsonify(recommendation)


@recommendations_bp.route("/api/size/<int:product_id>/refresh", methods=["POST"])
@login_required
def refresh_recommendation(product_id):
    """Force regenerate a size recommendation."""
    recommendation = SizeRecommendationService.generate_recommendation(
        customer_id=current_user.id,
        product_id=product_id,
    )

    if not recommendation:
        return jsonify({"error": "Cannot generate recommendation"}), 400

    return jsonify(recommendation)


@recommendations_bp.route("/profile")
@login_required
def size_profile():
    """Get current user's size profile."""
    profile = SizeRecommendationService.get_customer_size_profile(current_user.id)

    if request.headers.get("HX-Request"):
        return render_template(
            "recommendations/partials/size_profile.html",
            profile=profile,
        )

    return jsonify(profile)


@recommendations_bp.route("/body-measurements", methods=["POST"])
@login_required
def save_body_measurements():
    """Save body measurements for AI size prediction (HTMX)."""
    height_cm = request.form.get("height_cm", type=float)
    weight_kg = request.form.get("weight_kg", type=float)
    body_type = request.form.get("body_type", "regular").strip()
    product_id = request.form.get("product_id", type=int)

    if not height_cm or not weight_kg:
        return "<p class='text-xs text-error'>Please enter both height and weight.</p>", 400

    try:
        SizeRecommendationService.save_body_measurements(
            customer_id=current_user.id,
            height_cm=height_cm,
            weight_kg=weight_kg,
            body_type=body_type,
        )
    except ValueError as e:
        return f"<p class='text-xs text-error'>{e}</p>", 400

    # Now generate a body-based recommendation for the product
    if product_id:
        rec = SizeRecommendationService.get_recommendation(current_user.id, product_id)
        if rec:
            return render_template(
                "recommendations/partials/size_recommendation.html",
                recommendation=rec,
            )

    return "<p class='text-xs text-success mt-2'>✅ Measurements saved! Refresh page for size recommendation.</p>"
