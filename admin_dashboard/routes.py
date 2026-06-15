"""Admin Dashboard routes - unified analytics and management."""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from shared.decorators import admin_required
from shared.database import db

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    url_prefix="/admin",
)


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Main admin dashboard with all widgets."""
    stats = _gather_dashboard_stats()
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/returns")
@login_required
@admin_required
def admin_returns():
    """Admin returns tracking — shows all returns/cancellations with warehouse routing."""
    from returns.models import ReturnRequest
    from routing.models import RoutingDecision

    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")

    query = ReturnRequest.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(request_type=type_filter)

    pagination = query.order_by(ReturnRequest.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Gather routing info for each return
    returns_with_routing = []
    for ret in pagination.items:
        routing = RoutingDecision.query.filter_by(return_request_id=ret.id).first()
        returns_with_routing.append({
            "return_request": ret,
            "routing": routing,
        })

    # Stats
    total_returns = ReturnRequest.query.filter_by(request_type="return").count()
    total_cancels = ReturnRequest.query.filter_by(request_type="cancel").count()
    pending_count = ReturnRequest.query.filter_by(status="pending").count()
    routed_count = RoutingDecision.query.count()

    return render_template(
        "admin/returns_tracking.html",
        returns_list=returns_with_routing,
        pagination=pagination,
        stats={
            "total_returns": total_returns,
            "total_cancels": total_cancels,
            "pending": pending_count,
            "routed": routed_count,
        },
        current_status=status_filter,
        current_type=type_filter,
    )


@admin_bp.route("/api/stats")
@login_required
@admin_required
def api_stats():
    """API: Dashboard stats."""
    return jsonify(_gather_dashboard_stats())


def _gather_dashboard_stats() -> dict:
    """Aggregate stats from all modules."""
    from products.models import Product
    from customers.models import Customer
    from checkout.models import Order
    from returns.models import ReturnRequest
    from grading.models import InspectionRecord
    from routing.models import Warehouse
    from credits.models import CreditTransaction

    # Products
    total_products = Product.query.filter_by(is_active=True).count()
    refurbished_count = Product.query.filter_by(is_active=True, product_type="refurbished").count()

    # Customers
    total_customers = Customer.query.count()

    # Orders
    total_orders = Order.query.count()
    orders_by_status = {}
    for status in ["confirmed", "shipped", "delivered", "cancelled"]:
        orders_by_status[status] = Order.query.filter_by(status=status).count()

    total_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.status != "cancelled"
    ).scalar() or 0

    # Returns
    total_returns = ReturnRequest.query.count()
    returns_pending = ReturnRequest.query.filter_by(status="pending").count()
    returns_approved = ReturnRequest.query.filter_by(status="approved").count()
    returns_completed = ReturnRequest.query.filter_by(status="completed").count()

    # Credits
    total_credits_issued = db.session.query(
        db.func.sum(CreditTransaction.amount)
    ).filter(CreditTransaction.amount > 0).scalar() or 0

    total_credits_deducted = abs(db.session.query(
        db.func.sum(CreditTransaction.amount)
    ).filter(CreditTransaction.amount < 0).scalar() or 0)

    # Sustainability
    total_co2_saved = db.session.query(
        db.func.sum(Product.carbon_saved_kg)
    ).filter(Product.product_type == "refurbished", Product.carbon_saved_kg.isnot(None)).scalar() or 0

    refurbished_sold = Order.query.join(Order.items).filter(
        Order.status != "cancelled"
    ).count()  # Simplified

    # Grading
    total_inspections = InspectionRecord.query.count()
    grade_dist = {}
    for g in ["A", "B", "C", "D"]:
        grade_dist[g] = InspectionRecord.query.filter_by(grade=g).count()

    # Warehouses
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    warehouse_data = [w.to_dict() for w in warehouses]
    avg_utilization = (
        sum(w.utilization_pct for w in warehouses) / len(warehouses)
    ) if warehouses else 0

    return {
        "products": {"total": total_products, "refurbished": refurbished_count},
        "customers": {"total": total_customers},
        "orders": {
            "total": total_orders,
            "by_status": orders_by_status,
            "revenue": round(float(total_revenue), 2),
        },
        "returns": {
            "total": total_returns,
            "pending": returns_pending,
            "approved": returns_approved,
            "completed": returns_completed,
        },
        "credits": {
            "issued": int(total_credits_issued),
            "deducted": int(total_credits_deducted),
        },
        "sustainability": {
            "co2_saved_kg": round(float(total_co2_saved), 1),
            "refurbished_sold": refurbished_sold,
        },
        "grading": {
            "total": total_inspections,
            "distribution": grade_dist,
        },
        "warehouses": {
            "data": warehouse_data,
            "avg_utilization": round(avg_utilization, 1),
        },
    }
