"""Shared utility functions."""
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, upload_folder: str) -> str:
    """Save uploaded file with unique name. Returns relative path."""
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, unique_name)
    file.save(filepath)
    return unique_name


def format_price(price: float) -> str:
    """Format price for display."""
    return f"₹{price:,.2f}"


def calculate_savings(original_price: float, current_price: float) -> dict:
    """Calculate savings amount and percentage."""
    if original_price <= 0:
        return {"amount": 0, "percentage": 0}
    savings = original_price - current_price
    percentage = (savings / original_price) * 100
    return {
        "amount": round(savings, 2),
        "percentage": round(percentage, 1),
    }
