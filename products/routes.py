"""Product routes - thin controllers delegating to services."""
from flask import Blueprint, render_template, request, jsonify, abort
from products.services import ProductService, CategoryService

products_bp = Blueprint(
    "products",
    __name__,
    template_folder="templates",
    url_prefix="/products",
)


@products_bp.route("/")
def catalog():
    """Product catalog page with filters and pagination."""
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", None)
    product_type = request.args.get("type", None)
    brand = request.args.get("brand", None)
    search = request.args.get("q", None)
    min_price = request.args.get("min_price", None, type=float)
    max_price = request.args.get("max_price", None, type=float)
    sort_by = request.args.get("sort", "relevance")

    result = ProductService.get_catalog(
        page=page,
        per_page=12,
        category_slug=category,
        product_type=product_type,
        brand=brand,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
    )

    categories = CategoryService.get_categories_with_counts()
    brands = ProductService.get_all_brands()
    price_range = ProductService.get_price_range()

    # Support HTMX partial rendering
    if request.headers.get("HX-Request"):
        return render_template(
            "products/partials/product_grid.html",
            products=result["items"],
            pagination=result,
        )

    return render_template(
        "products/catalog.html",
        products=result["items"],
        pagination=result,
        categories=categories,
        brands=brands,
        price_range=price_range,
        current_filters={
            "category": category,
            "type": product_type,
            "brand": brand,
            "search": search,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort_by,
        },
    )


@products_bp.route("/<slug>")
def product_detail(slug):
    """Product detail page."""
    product = ProductService.get_product_by_slug(slug)
    if not product:
        abort(404)

    related = ProductService.get_related_products(product)

    return render_template(
        "products/product_detail.html",
        product=product,
        related_products=related,
    )


@products_bp.route("/api/search")
def api_search():
    """API endpoint for live search (HTMX)."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    result = ProductService.get_catalog(search=query, per_page=5)
    products = [p.to_dict() for p in result["items"]]
    return jsonify(products)
