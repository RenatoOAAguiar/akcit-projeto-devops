"""Regra de negócio: um desconto deve reduzir o subtotal de uma compra."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

MAX_SUBTOTAL = Decimal("999999999.99")


def _decimal(value: str | int | Decimal, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} deve ser um número válido") from exc
    if not number.is_finite():
        raise ValueError(f"{field} deve ser finito")
    return number


def calculate_total(
    subtotal: str | int | Decimal, discount_percent: str | int | Decimal
) -> Decimal:
    """Calcula o total, arredondando para centavos com ROUND_HALF_UP.

    Aceita subtotal entre zero e 999999999.99 e desconto entre zero e 100.
    """
    amount = _decimal(subtotal, "subtotal")
    percentage = _decimal(discount_percent, "desconto")
    if not 0 <= amount <= MAX_SUBTOTAL:
        raise ValueError("subtotal deve estar entre 0 e 999999999.99")
    if not 0 <= percentage <= 100:
        raise ValueError("desconto deve estar entre 0 e 100")
    with localcontext() as context:
        context.prec = 40
        discount = amount * percentage / Decimal("100")
        total = amount + discount  # LAB: discount operation
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
