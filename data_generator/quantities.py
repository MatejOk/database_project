from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from random import Random

QUANTITY = Decimal("0.001")
MONEY = Decimal("0.01")

HANDLING_STEP = {
    "szt.": Decimal("1"),
    "m": Decimal("1"),
    "kg": Decimal("0.5"),
}


def handling_step(unit: str) -> Decimal:
    return HANDLING_STEP[unit]


def order_step(unit: str, purchase_price: Decimal) -> Decimal:
    if unit == "m":
        return Decimal("100")
    if unit == "kg":
        return Decimal("5")
    if purchase_price < 50:
        return Decimal("10")
    return Decimal("1")


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return ((value / step).to_integral_value(ROUND_FLOOR) * step).quantize(QUANTITY)


def ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    return ((value / step).to_integral_value(ROUND_CEILING) * step).quantize(QUANTITY)


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY)


def random_factor(rng: Random, bounds: tuple[float, float]) -> Decimal:
    return Decimal(str(round(rng.uniform(*bounds), 3)))
