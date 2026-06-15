"""Product service layer - business logic for catalog operations."""
from typing import Optional
from sqlalchemy import or_, desc, asc
from shared.database import db
from products.models import Product, Category


class ProductService:
    """Service for product catalog operations."""

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get a single active product by ID."""
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """Get a single active product by slug."""
        return Product.query.filter_by(slug=slug, is_active=True).first()

    @staticmethod
    def get_catalog(
        page: int = 1,
        per_page: int = 12,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "relevance",
        in_stock_only: bool = False,
    ) -> dict:
        """
        Get paginated product catalog with filters.
        Returns dict with items, pagination info, and applied filters.
        """
        query = Product.query.filter_by(is_active=True)

        # Apply filters
        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first()
            if category:
                query = query.filter_by(category_id=category.id)

        if product_type and product_type in ("standard", "refurbished"):
            query = query.filter_by(product_type=product_type)

        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.brand.ilike(search_term),
                )
            )

        if min_price is not None:
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)

        # Apply sorting
        sort_options = {
            "relevance": Product.created_at.desc(),
            "price_low": asc(Product.price),
            "price_high": desc(Product.price),
            "rating": desc(Product.avg_rating),
            "newest": desc(Product.created_at),
        }
        order = sort_options.get(sort_by, Product.created_at.desc())
        query = query.order_by(order)

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }

    @staticmethod
    def get_featured_products(limit: int = 8) -> list:
        """Get featured/top-rated products for homepage."""
        return (
            Product.query
            .filter_by(is_active=True)
            .filter(Product.stock_quantity > 0)
            .order_by(desc(Product.avg_rating), desc(Product.total_reviews))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_refurbished_products(limit: int = 8) -> list:
        """Get top refurbished products."""
        return (
            Product.query
            .filter_by(is_active=True, product_type="refurbished")
            .filter(Product.stock_quantity > 0)
            .order_by(desc(Product.avg_rating))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_related_products(product: Product, limit: int = 4) -> list:
        """Get related products based on category and brand."""
        return (
            Product.query
            .filter_by(is_active=True, category_id=product.category_id)
            .filter(Product.id != product.id)
            .filter(Product.stock_quantity > 0)
            .order_by(desc(Product.avg_rating))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_brands() -> list:
        """Get distinct brand names for filter."""
        brands = (
            db.session.query(Product.brand)
            .filter(Product.is_active == True, Product.brand.isnot(None))
            .distinct()
            .order_by(Product.brand)
            .all()
        )
        return [b[0] for b in brands]

    @staticmethod
    def get_price_range() -> dict:
        """Get min/max prices for filter slider."""
        result = db.session.query(
            db.func.min(Product.price),
            db.func.max(Product.price)
        ).filter(Product.is_active == True).first()
        return {
            "min": result[0] or 0,
            "max": result[1] or 10000,
        }


class CategoryService:
    """Service for category operations."""

    @staticmethod
    def get_all_categories() -> list:
        """Get all categories."""
        return Category.query.order_by(Category.name).all()

    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """Get category by slug."""
        return Category.query.filter_by(slug=slug).first()

    @staticmethod
    def get_categories_with_counts() -> list:
        """Get categories with product counts."""
        categories = Category.query.all()
        result = []
        for cat in categories:
            count = Product.query.filter_by(
                category_id=cat.id, is_active=True
            ).count()
            result.append({"category": cat, "count": count})
        return result
