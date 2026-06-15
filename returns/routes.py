"""Return routes - cancellation and return management."""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from shared.database import db
from returns.services import ReturnService
from checkout.services import OrderService

returns_bp = Blueprint(
    "returns",
    __name__,
    template_folder="templates",
    url_prefix="/returns",
)


@returns_bp.route("/cancel/<int:order_id>", methods=["GET", "POST"])
@login_required
def cancel_order(order_id):
    """Cancel order page and handler."""
    from checkout.models import Order

    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()
    if not order:
        abort(404)

    cancel_info = ReturnService.can_cancel(order)

    if not cancel_info["can_cancel"]:
        flash(cancel_info["explanation"], "error")
        return redirect(url_for("checkout.order_confirmation", order_number=order.order_number))

    if request.method == "POST":
        reason = request.form.get("reason", "changed_mind")
        reason_detail = request.form.get("reason_detail", "").strip()

        try:
            result = ReturnService.cancel_order(
                order_id=order.id,
                customer_id=current_user.id,
                reason=reason,
                reason_detail=reason_detail,
            )
            flash(result["message"], "success")
            return redirect(url_for("checkout.order_history"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template(
        "returns/cancel_order.html",
        order=order,
        cancel_info=cancel_info,
        reasons=ReturnService.CANCEL_REASONS,
    )


@returns_bp.route("/return/<int:order_id>/<int:item_id>", methods=["GET", "POST"])
@login_required
def return_item(order_id, item_id):
    """Return item page and handler."""
    from checkout.models import Order, OrderItem

    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()
    if not order:
        abort(404)

    order_item = db.session.get(OrderItem, item_id)
    if not order_item or order_item.order_id != order.id:
        abort(404)

    return_check = ReturnService.can_return(order, order_item)

    if not return_check["can_return"]:
        flash(return_check["explanation"], "error")
        return redirect(url_for("checkout.order_confirmation", order_number=order.order_number))

    if request.method == "POST":
        reason = request.form.get("reason", "changed_mind")
        reason_detail = request.form.get("reason_detail", "").strip()

        try:
            result = ReturnService.request_return(
                order_id=order.id,
                order_item_id=item_id,
                customer_id=current_user.id,
                reason=reason,
                reason_detail=reason_detail or None,
            )
            flash(result["message"], "success")
            return redirect(url_for("returns.return_history"))
        except ValueError as e:
            flash(str(e), "error")

    # Preview penalty based on default reason
    penalty_preview = ReturnService.calculate_return_penalty(current_user.id, "changed_mind")

    return render_template(
        "returns/return_item.html",
        order=order,
        order_item=order_item,
        return_check=return_check,
        reasons=ReturnService.RETURN_REASONS,
        penalty=penalty_preview,
    )


@returns_bp.route("/history")
@login_required
def return_history():
    """Customer return history."""
    page = request.args.get("page", 1, type=int)
    returns_data = ReturnService.get_customer_returns(current_user.id, page=page)
    return render_template(
        "returns/return_history.html",
        returns=returns_data,
        return_list=returns_data["items"],
    )


@returns_bp.route("/api/penalty-preview/<int:order_id>")
@login_required
def api_penalty_preview(order_id):
    """API: Preview penalty for a return reason (HTMX)."""
    reason = request.args.get("reason", "changed_mind")
    penalty_info = ReturnService.calculate_return_penalty(current_user.id, reason)

    if request.headers.get("HX-Request"):
        return render_template("returns/partials/penalty_preview.html", penalty=penalty_info)

    return jsonify(penalty_info)
