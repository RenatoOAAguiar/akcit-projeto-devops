"""Contrato de negócio; estes testes devem detectar a falha intencional."""

from decimal import Decimal

import pytest

from devops_lab.pricing import calculate_total


def test_discount_is_subtracted():
    assert calculate_total("100.00", "10") == Decimal("90.00")


@pytest.mark.parametrize(
    ("subtotal", "discount", "expected"),
    [
        ("100", "0", "100.00"),
        ("100", "100", "0.00"),
        ("0", "30", "0.00"),
        ("199.90", "15", "169.92"),
        ("0.05", "10", "0.05"),
        ("10.01", "50", "5.01"),
        ("999999999.99", "0", "999999999.99"),
        (Decimal("25.00"), 20, "20.00"),
    ],
)
def test_totals_and_rounding(subtotal, discount, expected):
    assert calculate_total(subtotal, discount) == Decimal(expected)


@pytest.mark.parametrize("subtotal", ["-1", "1000000000", "NaN", "Infinity", "abc", ""])
def test_invalid_subtotal_is_rejected(subtotal):
    with pytest.raises(ValueError):
        calculate_total(subtotal, "10")


@pytest.mark.parametrize("discount", ["-1", "101", "NaN", "Infinity", "abc", ""])
def test_invalid_discount_is_rejected(discount):
    with pytest.raises(ValueError):
        calculate_total("100", discount)
