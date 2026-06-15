"""Customer routes - auth and profile management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from customers.services import CustomerService

customers_bp = Blueprint(
    "customers",
    __name__,
    template_folder="templates",
    url_prefix="/account",
)


@customers_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page and form handler."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        customer = CustomerService.authenticate(email, password)
        if customer:
            login_user(customer, remember=request.form.get("remember"))
            next_page = request.args.get("next")
            flash("Welcome back!", "success")
            return redirect(next_page or url_for("main.index"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("customers/login.html")


@customers_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page and form handler."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        try:
            customer = CustomerService.create_customer(
                email=request.form.get("email", "").strip(),
                password=request.form.get("password", ""),
                first_name=request.form.get("first_name", "").strip(),
                last_name=request.form.get("last_name", "").strip(),
                phone=request.form.get("phone", "").strip() or None,
            )
            login_user(customer)
            flash("Account created! Welcome to ReturnLess.", "success")
            return redirect(url_for("main.index"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("customers/register.html")


@customers_bp.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.index"))


@customers_bp.route("/profile")
@login_required
def profile():
    """Customer profile/dashboard."""
    return render_template("customers/profile.html")
