"""Credits routes - green credits dashboard and history."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from credits.services import CreditService

credits_bp = Blueprint(
    "credits",
    __name__,
    template_folder="templates",
    url_prefix="/credits",
)


@credits_bp.route("/")
@login_required
def dashboard():
    """Green credits dashboard."""
    summary = CreditService.get_credit_summary(current_user.id)
    return render_template("credits/dashboard.html", summary=summary)


@credits_bp.route("/history")
@login_required
def history():
    """Credit transaction history."""
    page = request.args.get("page", 1, type=int)
    history_data = CreditService.get_history(current_user.id, page=page)
    return render_template(
        "credits/history.html",
        history=history_data,
        transactions=history_data["items"],
    )


@credits_bp.route("/api/summary")
@login_required
def api_summary():
    """API: Credit summary."""
    return jsonify(CreditService.get_credit_summary(current_user.id))
