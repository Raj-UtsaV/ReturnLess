"""Customer service layer - auth and profile operations."""
from typing import Optional
from shared.database import db
from customers.models import Customer, Address


class CustomerService:
    """Service for customer operations."""

    @staticmethod
    def create_customer(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
    ) -> Customer:
        """Register a new customer. Awards 100 welcome credits."""
        if Customer.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        customer = Customer(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            green_credits=100,
            lifetime_credits=100,
        )
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[Customer]:
        """Authenticate customer with email/password."""
        customer = Customer.query.filter_by(email=email, is_active=True).first()
        if customer and customer.check_password(password):
            return customer
        return None

    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        return Customer.query.get(customer_id)

    @staticmethod
    def update_profile(customer: Customer, **kwargs) -> Customer:
        """Update customer profile fields."""
        allowed_fields = ["first_name", "last_name", "phone", "preferences"]
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(customer, key, value)
        db.session.commit()
        return customer


class AddressService:
    """Service for address management."""

    @staticmethod
    def add_address(customer_id: int, **kwargs) -> Address:
        """Add address for customer."""
        if kwargs.get("is_default"):
            # Unset existing default
            Address.query.filter_by(
                customer_id=customer_id, is_default=True
            ).update({"is_default": False})

        address = Address(customer_id=customer_id, **kwargs)
        db.session.add(address)
        db.session.commit()
        return address

    @staticmethod
    def get_addresses(customer_id: int) -> list:
        """Get all addresses for a customer."""
        return Address.query.filter_by(customer_id=customer_id).all()
