from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from model.customer import Customer
from model.discount import Discount
from model.order import Order


class CouponError(Exception):
    """Raised when a coupon cannot be applied."""


@dataclass(frozen=True)
class CouponResult:
    discount: Discount
    discount_amount: float
    new_total: float


def validate_and_calculate_coupon(
    *,
    customer_id: int,
    code: str,
    subtotal: float,
    now: Optional[datetime] = None,
) -> CouponResult:
    """
    Validate coupon against the database (Option B: per-customer limits via Order history)
    and calculate the discount amount for a given subtotal.
    """
    if not code or not str(code).strip():
        raise CouponError("Coupon code is required")

    if customer_id is None:
        raise CouponError("Customer is required")

    try:
        customer_id_int = int(customer_id)
    except (TypeError, ValueError) as e:
        raise CouponError("Invalid customer id") from e

    try:
        subtotal_f = float(subtotal)
    except (TypeError, ValueError) as e:
        raise CouponError("Invalid subtotal amount") from e

    if subtotal_f < 0:
        raise CouponError("Subtotal cannot be negative")

    customer = Customer.query.get(customer_id_int)
    if not customer:
        raise CouponError("Customer not found")

    now = now or datetime.utcnow()
    code_upper = str(code).strip().upper()

    discount = Discount.query.filter(
        Discount.code == code_upper,
        Discount.status == "active",
        Discount.expiry_date >= now,
    ).first()

    if not discount:
        raise CouponError("Coupon is invalid or expired")

    if discount.max_usage is not None and (discount.usage_count or 0) >= discount.max_usage:
        raise CouponError("This coupon has reached its maximum total usage")

    min_purchase = float(discount.min_purchase or 0)
    if subtotal_f < min_purchase:
        raise CouponError(f"Minimum purchase of {min_purchase:.2f} is required for this coupon")

    if discount.max_usage_per_customer is not None and discount.max_usage_per_customer > 0:
        used_times = (
            Order.query.filter_by(
                customer_id=customer_id_int,
                discount_id=discount.id,
                status="completed",
            ).count()
        )
        if used_times >= discount.max_usage_per_customer:
            raise CouponError(
                f"This coupon can only be used {discount.max_usage_per_customer} time(s) per customer"
            )

    # Calculate discount amount
    if discount.discount_type == "percentage":
        discount_amount = subtotal_f * (float(discount.discount_value) / 100.0)
    else:  # 'fixed'
        discount_amount = float(discount.discount_value)

    discount_amount = max(0.0, min(discount_amount, subtotal_f))
    new_total = subtotal_f - discount_amount

    return CouponResult(discount=discount, discount_amount=round(discount_amount, 2), new_total=round(new_total, 2))


def increment_global_usage_if_completed(*, discount_id: Optional[int], previous_status: str, new_status: str) -> None:
    """
    Increment Discount.usage_count exactly once when an order transitions
    to completed and has an associated discount.
    """
    if not discount_id:
        return
    if previous_status == "completed" or new_status != "completed":
        return

    discount = Discount.query.get(int(discount_id))
    if not discount:
        return

    discount.usage_count = (discount.usage_count or 0) + 1

