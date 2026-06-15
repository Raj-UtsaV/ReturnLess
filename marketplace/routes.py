"""Marketplace routes - dedicated refurbished shopping experience."""
from flask import Blueprint, render_template, request
from products.services import ProductService, CategoryService
from shared.database import db

marketplace_bp = Blueprint(
    "marketplace",
    __name__,
    template_folder="templates",
    url_prefix="/marketplace",
)


@marketplace_bp.route("/")
def refurbished_home():
    """Dedicated refurbished marketplace landing page."""
    from products.models import Product

    # Get refurbished products
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", None)
    sort_by = request.args.get("sort", "relevance")

    result = ProductService.get_catalog(
        page=page,
        per_page=12,
        product_type="refurbished",
        category_slug=category,
        sort_by=sort_by,
    )

    categories = CategoryService.get_categories_with_counts()

    # Marketplace stats
    total_refurbished = Product.query.filter_by(is_active=True, product_type="refurbished").count()
    total_co2_saved = db.session.query(
        db.func.sum(Product.carbon_saved_kg)
    ).filter(
        Product.product_type == "refurbished",
        Product.carbon_saved_kg.isnot(None),
    ).scalar() or 0

    total_savings = db.session.query(
        db.func.sum(Product.original_price - Product.price)
    ).filter(
        Product.product_type == "refurbished",
        Product.original_price.isnot(None),
        Product.original_price > Product.price,
    ).scalar() or 0

    stats = {
        "total_products": total_refurbished,
        "co2_saved": round(float(total_co2_saved), 1),
        "total_savings": round(float(total_savings)),
    }

    return render_template(
        "marketplace/refurbished_home.html",
        products=result["items"],
        pagination=result,
        categories=categories,
        stats=stats,
        current_category=category,
        current_sort=sort_by,
    )
