"""Routing routes - admin-only warehouse routing views."""
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required
from shared.decorators import admin_required
from routing.services import RoutingService

routing_bp = Blueprint(
    "routing",
    __name__,
    template_folder="templates",
    url_prefix="/routing",
)


@routing_bp.route("/")
@login_required
@admin_required
def routing_dashboard():
    """Routing dashboard with warehouse stats and recent decisions."""
    stats = RoutingService.get_warehouse_stats()
    decisions = RoutingService.get_routing_decisions(per_page=10)

    return render_template(
        "routing/dashboard.html",
        stats=stats,
        decisions=decisions,
        decision_list=decisions["items"],
    )


@routing_bp.route("/api/stats")
@login_required
@admin_required
def api_stats():
    """API: Warehouse stats."""
    return jsonify(RoutingService.get_warehouse_stats())
