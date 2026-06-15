"""Review routes - thin controllers for review operations."""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from ai_reviews.services import ReviewService

reviews_bp = Blueprint(
    "reviews",
    __name__,
    template_folder="templates",
    url_prefix="/reviews",
)


@reviews_bp.route("/product/<int:product_id>")
def product_reviews(product_id):
    """Get reviews for a product (HTMX partial or full page)."""
    from products.services import ProductService

    product = ProductService.get_product_by_id(product_id)
    if not product:
        abort(404)

    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort", "newest")
    filter_rating = request.args.get("rating", None, type=int)

    reviews = ReviewService.get_reviews_for_product(
        product_id=product_id,
        page=page,
        per_page=10,
        sort_by=sort_by,
        filter_rating=filter_rating,
    )

    stats = ReviewService.get_review_stats(product_id)
    summary = ReviewService.get_product_summary(product_id)

    # Check if current user can review
    can_review = False
    if current_user.is_authenticated:
        can_review = ReviewService.can_review(product_id, current_user.id)

    # Support HTMX partial rendering
    if request.headers.get("HX-Request"):
        return render_template(
            "reviews/partials/review_list.html",
            reviews=reviews["items"],
            pagination=reviews,
            product=product,
            stats=stats,
        )

    return render_template(
        "reviews/product_reviews.html",
        product=product,
        reviews=reviews["items"],
        pagination=reviews,
        stats=stats,
        summary=summary,
        can_review=can_review,
        current_sort=sort_by,
        current_rating_filter=filter_rating,
    )


@reviews_bp.route("/product/<int:product_id>/summary")
def product_review_summary(product_id):
    """Get AI-generated review summary (HTMX partial)."""
    summary = ReviewService.get_product_summary(product_id)
    stats = ReviewService.get_review_stats(product_id)

    return render_template(
        "reviews/partials/review_summary.html",
        summary=summary,
        stats=stats,
    )


@reviews_bp.route("/product/<int:product_id>/write", methods=["GET", "POST"])
@login_required
def write_review(product_id):
    """Write a review form and submission handler."""
    from products.services import ProductService

    product = ProductService.get_product_by_id(product_id)
    if not product:
        abort(404)

    if not ReviewService.can_review(product_id, current_user.id):
        flash("You have already reviewed this product.", "warning")
        return redirect(url_for("reviews.product_reviews", product_id=product_id))

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", 0))
            title = request.form.get("title", "").strip()
            body = request.form.get("body", "").strip()
            size_purchased = request.form.get("size_purchased", "").strip() or None

            if not title or not body:
                flash("Please provide both title and review text.", "error")
                return render_template(
                    "reviews/write_review.html", product=product
                )

            review = ReviewService.create_review(
                product_id=product_id,
                customer_id=current_user.id,
                rating=rating,
                title=title,
                body=body,
                verified_purchase=True,  # Simplified: assume verified
                size_purchased=size_purchased,
            )

            flash("Review submitted! AI analysis complete. 🤖", "success")
            return redirect(url_for("reviews.product_reviews", product_id=product_id))

        except ValueError as e:
            flash(str(e), "error")

    return render_template("reviews/write_review.html", product=product)


@reviews_bp.route("/<int:review_id>/vote", methods=["POST"])
def vote_helpful(review_id):
    """Vote a review as helpful/not helpful (HTMX)."""
    helpful = request.form.get("helpful", "true") == "true"
    review = ReviewService.vote_helpful(review_id, helpful)

    if not review:
        abort(404)

    # Return updated vote count partial
    return render_template("reviews/partials/vote_buttons.html", review=review)


@reviews_bp.route("/api/product/<int:product_id>/stats")
def api_review_stats(product_id):
    """API endpoint for review statistics."""
    stats = ReviewService.get_review_stats(product_id)
    return jsonify(stats)


@reviews_bp.route("/api/product/<int:product_id>/summary")
def api_review_summary(product_id):
    """API endpoint for AI review summary."""
    summary = ReviewService.get_product_summary(product_id)
    if summary:
        return jsonify(summary.to_dict())
    return jsonify({"error": "No summary available"}), 404


@reviews_bp.route("/api/product/<int:product_id>/regenerate-summary", methods=["POST"])
@login_required
def api_regenerate_summary(product_id):
    """Regenerate AI summary for a product (admin only)."""
    if not current_user.is_admin:
        abort(403)

    summary = ReviewService.generate_product_summary(product_id)
    if summary:
        return jsonify({"success": True, "summary": summary.to_dict()})
    return jsonify({"error": "No reviews to summarize"}), 400
