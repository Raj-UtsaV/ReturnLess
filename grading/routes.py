"""Grading routes - inspection and quality assessment (admin-facing)."""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from shared.decorators import admin_required
from grading.services import GradingService

grading_bp = Blueprint(
    "grading",
    __name__,
    template_folder="templates",
    url_prefix="/grading",
)


@grading_bp.route("/")
@login_required
@admin_required
def inspections_list():
    """List all inspections (admin)."""
    page = request.args.get("page", 1, type=int)
    grade_filter = request.args.get("grade")

    inspections = GradingService.get_all_inspections(page=page, grade=grade_filter)
    stats = GradingService.get_grading_stats()

    return render_template(
        "grading/inspections_list.html",
        inspections=inspections,
        inspection_list=inspections["items"],
        stats=stats,
        current_grade=grade_filter,
    )


@grading_bp.route("/inspect/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def inspect_product(product_id):
    """Manual product inspection form (admin)."""
    from products.models import Product
    from shared.database import db

    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    if request.method == "POST":
        try:
            defects_raw = request.form.get("defects", "").strip()
            defects = [d.strip() for d in defects_raw.split("\n") if d.strip()] if defects_raw else []

            record = GradingService.inspect_product(
                product_id=product_id,
                exterior_score=request.form.get("exterior_score", 100, type=int),
                functional_score=request.form.get("functional_score", 100, type=int),
                cosmetic_score=request.form.get("cosmetic_score", 100, type=int),
                packaging_score=request.form.get("packaging_score", 100, type=int),
                defects=defects,
                notes=request.form.get("notes", "").strip() or None,
                inspected_by=current_user.full_name,
            )
            flash(f"Inspection complete! Grade: {record.grade} ({record.overall_score}/100)", "success")
            return redirect(url_for("grading.inspection_detail", inspection_id=record.id))
        except ValueError as e:
            flash(str(e), "error")

    # Get previous inspections
    previous = GradingService.get_inspections_for_product(product_id)

    return render_template(
        "grading/inspect_product.html",
        product=product,
        previous_inspections=previous,
    )


@grading_bp.route("/inspection/<int:inspection_id>")
@login_required
@admin_required
def inspection_detail(inspection_id):
    """View inspection detail (admin)."""
    record = GradingService.get_inspection(inspection_id)
    if not record:
        abort(404)

    return render_template("grading/inspection_detail.html", record=record)


@grading_bp.route("/auto-inspect/<int:return_id>", methods=["POST"])
@login_required
@admin_required
def auto_inspect(return_id):
    """Trigger auto-inspection for a return (admin)."""
    record = GradingService.auto_inspect_from_return(return_id)
    if not record:
        flash("Could not auto-inspect this return.", "error")
        return redirect(url_for("grading.inspections_list"))

    flash(f"Auto-inspection complete! Grade: {record.grade}", "success")
    return redirect(url_for("grading.inspection_detail", inspection_id=record.id))


@grading_bp.route("/api/stats")
@login_required
@admin_required
def api_stats():
    """API: Grading statistics."""
    stats = GradingService.get_grading_stats()
    return jsonify(stats)
