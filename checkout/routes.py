"""Checkout routes - cart, checkout flow, and order management."""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from checkout.services import CartService, OrderService

checkout_bp = Blueprint(
    "checkout",
    __name__,
    template_folder="templates",
    url_prefix="/",
)


# ─── Cart Routes ─────────────────────────────────────────────────────────────

@checkout_bp.route("/cart")
@login_required
def cart():
    """Shopping cart page."""
    cart_data = CartService.get_cart(current_user.id)
    return render_template("checkout/cart.html", cart=cart_data, cart_items=cart_data["items"])


@checkout_bp.route("/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    """Add item to cart (HTMX or form POST)."""
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", 1, type=int)
    size = request.form.get("size", "").strip() or None

    try:
        CartService.add_to_cart(
            customer_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            size=size,
        )
        flash("Added to cart! 🛒", "success")
    except ValueError as e:
        flash(str(e), "error")

    # HTMX: return updated cart count badge
    if request.headers.get("HX-Request"):
        count = CartService.get_cart_count(current_user.id)
        return render_template("checkout/partials/cart_badge.html", cart_count=count)

    return redirect(request.referrer or url_for("main.index"))


@checkout_bp.route("/buy-now", methods=["POST"])
@login_required
def buy_now():
    """Buy Now — add to cart and go straight to checkout."""
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", 1, type=int)
    size = request.form.get("size", "").strip() or None

    try:
        # Clear cart first (Buy Now = only this item)
        CartService.clear_cart(current_user.id)
        CartService.add_to_cart(
            customer_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            size=size,
        )
        return redirect(url_for("checkout.checkout"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("main.index"))


@checkout_bp.route("/cart/update", methods=["POST"])
@login_required
def update_cart():
    """Update cart item quantity (HTMX)."""
    cart_item_id = request.form.get("cart_item_id", type=int)
    quantity = request.form.get("quantity", type=int)

    try:
        CartService.update_quantity(cart_item_id, current_user.id, quantity)
    except ValueError as e:
        flash(str(e), "error")

    if request.headers.get("HX-Request"):
        cart_data = CartService.get_cart(current_user.id)
        return render_template("checkout/partials/cart_content.html", cart=cart_data, cart_items=cart_data["items"])

    return redirect(url_for("checkout.cart"))


@checkout_bp.route("/cart/remove", methods=["POST"])
@login_required
def remove_from_cart():
    """Remove item from cart (HTMX)."""
    cart_item_id = request.form.get("cart_item_id", type=int)
    CartService.remove_from_cart(cart_item_id, current_user.id)

    if request.headers.get("HX-Request"):
        cart_data = CartService.get_cart(current_user.id)
        return render_template("checkout/partials/cart_content.html", cart=cart_data, cart_items=cart_data["items"])

    flash("Item removed from cart.", "info")
    return redirect(url_for("checkout.cart"))


@checkout_bp.route("/cart/count")
@login_required
def cart_count():
    """Get cart count (for navbar badge via HTMX)."""
    count = CartService.get_cart_count(current_user.id)
    return render_template("checkout/partials/cart_badge.html", cart_count=count)


# ─── Checkout Routes ─────────────────────────────────────────────────────────

@checkout_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout page - shipping details and order placement."""
    cart_data = CartService.get_cart(current_user.id)

    if not cart_data["items"]:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products.catalog"))

    if request.method == "POST":
        # Check if user acknowledged size warnings
        acknowledged = request.form.get("size_warning_acknowledged") == "true"

        try:
            order = OrderService.create_order(
                customer_id=current_user.id,
                shipping_name=request.form.get("shipping_name", "").strip(),
                shipping_address=request.form.get("shipping_address", "").strip(),
                shipping_city=request.form.get("shipping_city", "").strip(),
                shipping_state=request.form.get("shipping_state", "").strip(),
                shipping_postal=request.form.get("shipping_postal", "").strip(),
                shipping_phone=request.form.get("shipping_phone", "").strip(),
                eco_shipping=request.form.get("eco_shipping") == "on",
                payment_method=request.form.get("payment_method", "mock_card"),
            )
            flash(f"Order placed! 🎉 You earned +{order.credits_earned} Green Credits!", "success")
            return redirect(url_for("checkout.order_confirmation", order_number=order.order_number))
        except ValueError as e:
            flash(str(e), "error")

    # Get saved addresses
    from customers.services import AddressService
    addresses = AddressService.get_addresses(current_user.id)

    # --- Size Compatibility Check ---
    size_warnings = _check_size_compatibility(current_user.id, cart_data["items"])

    # --- Smart Checkout Insights (per-category) ---
    checkout_insights = _generate_checkout_insights(current_user.id, cart_data["items"])

    return render_template(
        "checkout/checkout.html",
        cart=cart_data,
        cart_items=cart_data["items"],
        addresses=addresses,
        size_warnings=size_warnings,
        checkout_insights=checkout_insights,
    )


def _check_size_compatibility(customer_id: int, cart_items: list) -> list:
    """
    Check if cart items with sizes match AI recommendations.
    Returns list of warning dicts for items that don't match.
    """
    warnings = []

    try:
        from recommendations.services import SizeRecommendationService

        for item in cart_items:
            if not item.size or not item.product.available_sizes:
                continue

            # Get AI recommendation for this product
            rec = SizeRecommendationService.get_recommendation(customer_id, item.product_id)
            if not rec or not rec.get("recommended_size"):
                continue

            recommended = rec["recommended_size"]
            confidence = rec.get("confidence_pct", rec.get("confidence", 0) * 100)

            if item.size != recommended and confidence >= 50:
                warnings.append({
                    "item": item,
                    "selected_size": item.size,
                    "recommended_size": recommended,
                    "confidence": int(confidence),
                    "explanation": rec.get("explanation", ""),
                    "product_name": item.product.name,
                })
    except Exception:
        pass  # Don't block checkout if recommendation service fails

    return warnings


def _generate_checkout_insights(customer_id: int, cart_items: list) -> dict:
    """
    Generate smart checkout insights per product category.

    Returns dict with:
    - clothing_insights: size auto-detection / first-order size prompts
    - electronics_insights: compatibility checklist from reviews
    - other_insights: general product tips
    """
    insights = {
        "clothing": [],
        "electronics": [],
        "other": [],
    }

    try:
        from recommendations.models import SizePurchaseHistory
        from ai_reviews.models import Review

        for item in cart_items:
            category_slug = item.product.category.slug if item.product.category else "other"

            # ─── CLOTHING: Auto-detect size or prompt for first order ────────
            if category_slug == "clothing" and item.product.available_sizes:
                # Check if customer has previous size history
                prev_sizes = SizePurchaseHistory.query.filter_by(
                    customer_id=customer_id, kept=True
                ).all()

                if prev_sizes:
                    # Auto-detect: find most common kept size
                    size_counts = {}
                    for h in prev_sizes:
                        size_counts[h.size_purchased] = size_counts.get(h.size_purchased, 0) + 1
                    best_size = max(size_counts, key=size_counts.get)
                    count = size_counts[best_size]

                    if item.size:
                        status = "match" if item.size == best_size else "mismatch"
                    else:
                        status = "no_size_selected"

                    insights["clothing"].append({
                        "product_name": item.product.name,
                        "product_thumbnail": item.product.thumbnail,
                        "selected_size": item.size,
                        "detected_size": best_size,
                        "detection_count": count,
                        "status": status,
                        "message": (
                            f"Based on {count} previous purchase{'s' if count > 1 else ''}, "
                            f"your preferred size is {best_size}."
                        ) if status != "no_size_selected" else (
                            f"We detected your usual size is {best_size} from {count} previous orders. "
                            f"Please confirm your size selection."
                        ),
                        "is_first_order": False,
                    })
                else:
                    # First clothing order — prompt for size confirmation
                    insights["clothing"].append({
                        "product_name": item.product.name,
                        "product_thumbnail": item.product.thumbnail,
                        "selected_size": item.size,
                        "detected_size": None,
                        "status": "first_order",
                        "message": (
                            "This is your first clothing order. Please double-check your size "
                            "selection. Check the size guide or use AI recommendations on the product page."
                        ),
                        "is_first_order": True,
                        "available_sizes": item.product.available_sizes,
                    })

            # ─── ELECTRONICS / HOME-KITCHEN: Compatibility checklist from reviews ──
            elif category_slug in ("electronics", "home-kitchen"):
                # Generate compatibility checklist from review topics
                reviews = Review.query.filter_by(product_id=item.product_id, ai_processed=True).all()

                checklist = _generate_compatibility_checklist(item.product, reviews, category_slug)

                if checklist:
                    insights["electronics"].append({
                        "product_name": item.product.name,
                        "product_thumbnail": item.product.thumbnail,
                        "category": category_slug,
                        "checklist": checklist,
                    })

            # ─── OTHER CATEGORIES: General purchase tips ─────────────────────
            else:
                reviews = Review.query.filter_by(product_id=item.product_id, ai_processed=True).limit(10).all()
                tips = _generate_product_tips(item.product, reviews, category_slug)

                if tips:
                    insights["other"].append({
                        "product_name": item.product.name,
                        "product_thumbnail": item.product.thumbnail,
                        "category": category_slug,
                        "tips": tips,
                    })

    except Exception:
        pass  # Don't block checkout if insights generation fails

    return insights


def _generate_compatibility_checklist(product, reviews: list, category: str) -> list:
    """Generate a compatibility checklist for electronics/appliances from review data."""
    checklist = []

    # Category-specific default checks
    if category == "electronics":
        checklist.append({"item": "Check if your existing charger/cable is compatible", "icon": "🔌"})

        # Analyze reviews for common compatibility mentions
        compatibility_keywords = {
            "power": ["voltage", "power", "adapter", "charger", "plug", "watt"],
            "connectivity": ["bluetooth", "wifi", "usb", "hdmi", "port", "wireless"],
            "storage": ["storage", "memory", "sd card", "expansion", "gb"],
            "os": ["android", "ios", "windows", "mac", "compatible", "software"],
            "size": ["desk", "space", "fits", "dimensions", "large", "small"],
        }

        review_text = " ".join(r.body.lower() for r in reviews) if reviews else ""

        for check_type, keywords in compatibility_keywords.items():
            if any(kw in review_text for kw in keywords):
                if check_type == "power":
                    checklist.append({"item": "Verify power requirements match your outlet/setup", "icon": "⚡"})
                elif check_type == "connectivity":
                    checklist.append({"item": "Confirm connectivity with your existing devices", "icon": "📶"})
                elif check_type == "storage":
                    checklist.append({"item": "Check if storage capacity meets your needs", "icon": "💾"})
                elif check_type == "os":
                    checklist.append({"item": "Verify OS/platform compatibility", "icon": "💻"})
                elif check_type == "size":
                    checklist.append({"item": "Measure your space to ensure proper fit", "icon": "📐"})

    elif category == "home-kitchen":
        checklist.append({"item": "Check if dimensions fit your kitchen/home space", "icon": "📐"})
        checklist.append({"item": "Verify voltage compatibility (110V/220V)", "icon": "⚡"})

        review_text = " ".join(r.body.lower() for r in reviews) if reviews else ""

        if any(kw in review_text for kw in ["noise", "loud", "quiet", "sound"]):
            checklist.append({"item": "Note: Reviewers mention noise levels — check if acceptable", "icon": "🔊"})
        if any(kw in review_text for kw in ["heavy", "weight", "lift", "carry"]):
            checklist.append({"item": "Consider weight — some reviewers find it heavy", "icon": "⚖️"})
        if any(kw in review_text for kw in ["clean", "maintenance", "wash"]):
            checklist.append({"item": "Review maintenance/cleaning requirements", "icon": "🧹"})

    # Add review-based warning if many negative reviews
    if reviews:
        negative_count = sum(1 for r in reviews if r.rating <= 2)
        if negative_count > len(reviews) * 0.3:
            checklist.append({
                "item": f"⚠️ {negative_count}/{len(reviews)} reviews report issues — review before purchasing",
                "icon": "⚠️",
            })

    return checklist[:6]  # Max 6 items


def _generate_product_tips(product, reviews: list, category: str) -> list:
    """Generate general purchase tips for non-clothing, non-electronics."""
    tips = []

    if category == "books":
        tips.append({"text": "Check if you prefer hardcover or paperback format", "icon": "📖"})
        if product.specifications:
            pages = product.specifications.get("Pages")
            if pages:
                tips.append({"text": f"This book has {pages} pages", "icon": "📄"})

    elif category == "sports":
        tips.append({"text": "Verify size/fit requirements for sports gear", "icon": "📏"})
        if reviews:
            review_text = " ".join(r.body.lower() for r in reviews)
            if any(kw in review_text for kw in ["battery", "charge", "charging"]):
                tips.append({"text": "Check battery life expectations from reviews", "icon": "🔋"})
            if any(kw in review_text for kw in ["water", "rain", "swim", "sweat"]):
                tips.append({"text": "Confirm water resistance level for your use case", "icon": "💧"})

    elif category == "beauty":
        tips.append({"text": "Check ingredient list for any allergies", "icon": "⚗️"})
        tips.append({"text": "Verify product is suitable for your skin type", "icon": "🧴"})
        if reviews:
            review_text = " ".join(r.body.lower() for r in reviews)
            if any(kw in review_text for kw in ["irritat", "breakout", "react", "sensitiv"]):
                tips.append({"text": "Some reviewers report sensitivity — patch test recommended", "icon": "⚠️"})

    # General tip from reviews
    if reviews and len(reviews) >= 3:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        if avg_rating >= 4.5:
            tips.append({"text": f"Highly rated ({avg_rating:.1f}★) — customers love this product", "icon": "⭐"})

    return tips[:4]  # Max 4 tips


# ─── Order Routes ────────────────────────────────────────────────────────────

@checkout_bp.route("/order/<order_number>")
@login_required
def order_confirmation(order_number):
    """Order confirmation/detail page."""
    order = OrderService.get_order_by_number(order_number, current_user.id)
    if not order:
        abort(404)
    return render_template("checkout/order_confirmation.html", order=order)


@checkout_bp.route("/orders")
@login_required
def order_history():
    """Customer order history."""
    page = request.args.get("page", 1, type=int)
    orders_data = OrderService.get_customer_orders(current_user.id, page=page)
    return render_template("checkout/order_history.html", orders=orders_data, order_list=orders_data["items"])


@checkout_bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    """Cancel an order (legacy route - redirects to returns module)."""
    return redirect(url_for("returns.cancel_order", order_id=order_id))


@checkout_bp.route("/order/<int:order_id>/debug-status", methods=["POST"])
@login_required
def debug_change_status(order_id):
    """DEBUG: Change order status for testing cancel/return flows."""
    order = OrderService.get_order(order_id, current_user.id)
    if not order:
        abort(404)

    new_status = request.form.get("status")
    if new_status in ("confirmed", "shipped", "delivered"):
        order.status = new_status
        from shared.database import db
        db.session.commit()
        flash(f"[Debug] Order status changed to: {new_status}", "info")

    return redirect(url_for("checkout.order_confirmation", order_number=order.order_number))


# ─── API Routes ──────────────────────────────────────────────────────────────

@checkout_bp.route("/api/cart")
@login_required
def api_cart():
    """JSON API for cart data."""
    cart_data = CartService.get_cart(current_user.id)
    return jsonify({
        "item_count": cart_data["item_count"],
        "subtotal": cart_data["subtotal"],
        "total": cart_data["total"],
        "green_credits_earn": cart_data["green_credits_earn"],
        "items": [item.to_dict() for item in cart_data["items"]],
    })
